from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import User, Patient, Appointment, Prescription, Availability
from datetime import datetime, date, timedelta
import os, time
from werkzeug.utils import secure_filename
from utils.datetime_utils import get_current_time, get_current_time_naive, format_datetime

doctor_bp = Blueprint('doctor', __name__, url_prefix='/doctor')

@doctor_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'doctor':
        flash('Access denied. You must be a doctor to view this page.', 'danger')
        return redirect(url_for('index'))

    # Get pending appointment requests
    pending_appointments = Appointment.query.filter_by(
        doctor_id=current_user.doctor.id,
        status='pending'
    ).order_by(
        Appointment.date_time
    ).all()

    # Get upcoming accepted appointments
    upcoming_appointments = Appointment.query.filter_by(
        doctor_id=current_user.doctor.id,
        status='accepted'
    ).filter(
        Appointment.date_time >= get_current_time_naive()
    ).order_by(
        Appointment.date_time
    ).all()

    return render_template('doctor/dashboard.html',
                          pending_appointments=pending_appointments,
                          upcoming_appointments=upcoming_appointments)

@doctor_bp.route('/appointments')
@login_required
def appointments():
    if current_user.role != 'doctor':
        flash('Accès refusé. Vous devez être un médecin pour voir cette page.', 'danger')
        return redirect(url_for('index'))

    # Récupérer tous les rendez-vous du médecin
    appointments = Appointment.query.filter_by(
        doctor_id=current_user.doctor.id
    ).order_by(
        Appointment.date_time.desc()
    ).all()

    # Compter les rendez-vous par statut
    pending_count = sum(1 for a in appointments if a.status == 'pending')
    accepted_count = sum(1 for a in appointments if a.status == 'accepted')
    completed_count = sum(1 for a in appointments if a.status == 'completed')
    rejected_count = sum(1 for a in appointments if a.status == 'rejected')
    cancelled_count = sum(1 for a in appointments if a.status == 'cancelled')

    # Passer les données au template
    return render_template('doctor/appointments.html',
                          appointments=appointments,
                          pending_count=pending_count,
                          accepted_count=accepted_count,
                          completed_count=completed_count,
                          rejected_count=rejected_count,
                          cancelled_count=cancelled_count)

@doctor_bp.route('/appointment/<int:appointment_id>/<string:action>')
@login_required
def appointment_action(appointment_id, action):
    if current_user.role != 'doctor':
        flash('Accès refusé. Vous devez être un médecin pour voir cette page.', 'danger')
        return redirect(url_for('index'))

    appointment = Appointment.query.get_or_404(appointment_id)

    # Vérifier que le rendez-vous appartient au médecin connecté
    if appointment.doctor_id != current_user.doctor.id:
        flash('Accès refusé. Ce rendez-vous ne vous appartient pas.', 'danger')
        return redirect(url_for('doctor.appointments'))

    patient = appointment.patient
    patient_user = patient.user
    formatted_date = appointment.date_time.strftime('%d/%m/%Y à %H:%M')

    if action == 'accept':
        appointment.status = 'accepted'

        # Générer un identifiant unique pour la salle de visioconférence
        import uuid
        import hashlib

        # Créer un identifiant unique basé sur l'ID du rendez-vous et un timestamp
        unique_id = f"{appointment.id}-{int(get_current_time().timestamp())}"
        # Créer un hash court pour l'identifiant de la salle
        room_id = hashlib.md5(unique_id.encode()).hexdigest()[:12]

        # Stocker l'identifiant de la salle dans la base de données
        appointment.video_room_id = room_id

        # Créer les liens de visioconférence pour le médecin et le patient
        base_url = request.host_url.rstrip('/')
        video_link = f"{base_url}/video/{room_id}"
        appointment.video_link = video_link

        print(f"Rendez-vous accepté - ID: {appointment.id}, Room ID: {room_id}, Video Link: {video_link}")
        print(f"Statut du rendez-vous: {appointment.status}")
        print(f"Patient ID: {appointment.patient_id}, Médecin ID: {appointment.doctor_id}")
        print(f"Date et heure: {appointment.date_time}")

        flash('Rendez-vous accepté avec succès !', 'success')

        # Envoyer une notification au patient avec le lien de visioconférence
        from socket_events import send_notification
        notification_title = "Rendez-vous confirmé"
        notification_content = f"Votre rendez-vous avec Dr. {current_user.first_name} {current_user.last_name} pour le {formatted_date} a été confirmé. Un lien de visioconférence a été généré."

        send_notification(
            user_id=patient_user.id,
            title=notification_title,
            content=notification_content,
            notification_type="appointment_accepted",
            related_id=appointment.id
        )

    elif action == 'reject':
        appointment.status = 'rejected'
        flash('Rendez-vous refusé.', 'info')

        # Envoyer une notification au patient
        from socket_events import send_notification
        notification_title = "Rendez-vous refusé"
        notification_content = f"Votre rendez-vous avec Dr. {current_user.first_name} {current_user.last_name} pour le {formatted_date} a été refusé."

        send_notification(
            user_id=patient_user.id,
            title=notification_title,
            content=notification_content,
            notification_type="appointment_rejected",
            related_id=appointment.id
        )

        # Remettre la disponibilité à "available"
        availability = Availability.query.filter_by(
            doctor_id=current_user.doctor.id,
            date=appointment.date_time.date(),
            start_time=appointment.date_time.time()
        ).first()

        if availability:
            availability.status = 'available'
    else:
        flash('Action invalide !', 'danger')
        return redirect(url_for('doctor.appointments'))

    db.session.commit()

    # Rediriger vers la page des rendez-vous
    return redirect(url_for('doctor.appointments'))

@doctor_bp.route('/consultation/<int:appointment_id>')
@login_required
def consultation(appointment_id):
    if current_user.role != 'doctor':
        flash('Accès refusé. Vous devez être un médecin pour voir cette page.', 'danger')
        return redirect(url_for('index'))

    appointment = Appointment.query.get_or_404(appointment_id)

    # Vérifier que le rendez-vous appartient au médecin connecté
    if appointment.doctor_id != current_user.doctor.id:
        flash('Accès refusé. Ce rendez-vous ne vous appartient pas.', 'danger')
        return redirect(url_for('doctor.dashboard'))

    # Vérifier que le rendez-vous est accepté
    if appointment.status != 'accepted':
        flash('Ce rendez-vous n\'a pas encore été accepté.', 'warning')
        return redirect(url_for('doctor.dashboard'))

    # Si le lien de visioconférence n'existe pas encore, le générer
    if not appointment.video_link or not appointment.video_room_id:
        import hashlib

        # Créer un identifiant unique basé sur l'ID du rendez-vous et un timestamp
        unique_id = f"{appointment.id}-{int(get_current_time().timestamp())}"
        # Créer un hash court pour l'identifiant de la salle
        room_id = hashlib.md5(unique_id.encode()).hexdigest()[:12]

        # Stocker l'identifiant de la salle dans la base de données
        appointment.video_room_id = room_id

        # Créer le lien de visioconférence
        base_url = request.host_url.rstrip('/')
        video_link = f"{base_url}/video/{room_id}"
        appointment.video_link = video_link

        db.session.commit()

    return render_template('doctor/consultation.html', appointment=appointment)

@doctor_bp.route('/prescription/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
def prescription(appointment_id):
    if current_user.role != 'doctor':
        flash('Access denied. You must be a doctor to view this page.', 'danger')
        return redirect(url_for('index'))

    appointment = Appointment.query.get_or_404(appointment_id)

    # Check if the appointment belongs to the current user
    if appointment.doctor_id != current_user.doctor.id:
        flash('Access denied. This appointment does not belong to you.', 'danger')
        return redirect(url_for('doctor.dashboard'))

    if request.method == 'POST':
        # Get form data
        content = request.form.get('content')

        # Create new prescription
        prescription = Prescription(
            patient_id=appointment.patient_id,
            doctor_id=current_user.doctor.id,
            appointment_id=appointment.id,
            content=content
        )

        db.session.add(prescription)
        db.session.commit()

        flash('Prescription created successfully!', 'success')
        return redirect(url_for('doctor.consultation', appointment_id=appointment.id))

    return render_template('doctor/prescription.html', appointment=appointment)

@doctor_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if current_user.role != 'doctor':
        flash('Access denied. You must be a doctor to view this page.', 'danger')
        return redirect(url_for('index'))

    doctor = current_user.doctor

    if request.method == 'POST':
        # Déterminer quelle section du formulaire a été soumise
        form_type = request.form.get('form_type')

        if form_type == 'professional':
            # Mise à jour des informations professionnelles
            current_user.first_name = request.form.get('first_name')
            current_user.last_name = request.form.get('last_name')
            doctor.speciality = request.form.get('primary_specialty')
            doctor.secondary_speciality = request.form.get('secondary_specialty')
            doctor.license_number = request.form.get('registration_number')
            doctor.practice_location = request.form.get('practice_location')
            doctor.years_experience = request.form.get('experience_years')
            doctor.previous_positions = request.form.get('previous_positions')

        elif form_type == 'biography':
            # Mise à jour de la biographie et des langues
            doctor.bio = request.form.get('biography')
            doctor.languages = request.form.get('languages')

        elif form_type == 'contact':
            # Mise à jour des coordonnées
            current_user.email = request.form.get('email')
            doctor.phone = request.form.get('phone')
            doctor.linkedin = request.form.get('linkedin')
            doctor.website = request.form.get('website')

        elif form_type == 'availability':
            # Mise à jour des disponibilités
            old_available_days = doctor.available_days
            old_available_hours = doctor.available_hours

            doctor.available_days = request.form.get('available_days')
            doctor.available_hours = request.form.get('available_hours')
            doctor.video_consultation = request.form.get('video_consultation') == 'on'

            # Log pour le débogage
            print(f"Mise à jour des disponibilités du médecin {doctor.id}:")
            print(f"- Anciens jours disponibles: {old_available_days}")
            print(f"- Nouveaux jours disponibles: {doctor.available_days}")
            print(f"- Anciens heures disponibles: {old_available_hours}")
            print(f"- Nouvelles heures disponibles: {doctor.available_hours}")
            print(f"- Video consultation: {doctor.video_consultation}")

            # Synchroniser avec la table Availability si demandé
            sync_availabilities = request.form.get('sync_availabilities') == 'on'
            if sync_availabilities:
                try:
                    # Utiliser une transaction explicite pour éviter les problèmes de verrouillage
                    today = date.today()

                    # Récupérer les anciennes disponibilités à supprimer
                    to_delete = Availability.query.filter(
                        Availability.doctor_id == doctor.id,
                        Availability.date >= today,
                        Availability.status == 'available'
                    ).all()

                    # Supprimer les disponibilités une par une au lieu d'utiliser delete()
                    for avail in to_delete:
                        db.session.delete(avail)

                    # Créer de nouvelles disponibilités basées sur les jours et heures sélectionnés
                    days = [int(day) for day in doctor.available_days.split(',') if day]
                    hours_ranges = [hr.split('-') for hr in doctor.available_hours.split(',') if hr]

                    # Préparer toutes les nouvelles disponibilités
                    new_availabilities = []

                    # Générer des disponibilités pour les 4 prochaines semaines
                    for i in range(28):  # 4 semaines
                        current_date = today + timedelta(days=i)
                        weekday = current_date.weekday() + 1  # 1 = Lundi, 7 = Dimanche

                        # Vérifier si ce jour de la semaine est disponible
                        if weekday in days:
                            for hour_range in hours_ranges:
                                if len(hour_range) == 2:
                                    start_hour, end_hour = int(hour_range[0]), int(hour_range[1])

                                    # Créer des créneaux d'une heure
                                    for hour in range(start_hour, end_hour):
                                        start_time = time(hour, 0)
                                        end_time = time(hour + 1, 0)

                                        # Vérifier si ce créneau existe déjà (en mémoire pour éviter trop de requêtes)
                                        # Nous ne vérifions que les créneaux réservés, car nous voulons remplacer les créneaux disponibles
                                        exists = False
                                        for existing_avail in Availability.query.filter_by(
                                            doctor_id=doctor.id,
                                            date=current_date
                                        ).all():
                                            if (existing_avail.start_time == start_time and
                                                existing_avail.end_time == end_time):
                                                if existing_avail.status != 'available':
                                                    # Si le créneau existe et n'est pas disponible (réservé), on ne le remplace pas
                                                    exists = True
                                                    break
                                                else:
                                                    # Si le créneau existe mais est disponible, on le supprime pour le remplacer
                                                    db.session.delete(existing_avail)
                                                    # Pas besoin de break, car on veut supprimer tous les doublons potentiels

                                        if not exists:
                                            new_availability = Availability(
                                                doctor_id=doctor.id,
                                                date=current_date,
                                                start_time=start_time,
                                                end_time=end_time,
                                                status='available'
                                            )
                                            new_availabilities.append(new_availability)

                    # Ajouter toutes les nouvelles disponibilités en une seule fois
                    if new_availabilities:
                        db.session.add_all(new_availabilities)

                    # Commit des changements
                    db.session.commit()

                    # Log pour le débogage
                    print(f"Synchronisation des disponibilités pour le médecin {doctor.id}:")
                    print(f"- Jours disponibles: {doctor.available_days}")
                    print(f"- Heures disponibles: {doctor.available_hours}")
                    print(f"- Nombre de créneaux supprimés: {len(to_delete)}")
                    print(f"- Nombre de nouveaux créneaux créés: {len(new_availabilities)}")

                    # Vérifier les disponibilités après la synchronisation
                    availabilities_after = Availability.query.filter(
                        Availability.doctor_id == doctor.id,
                        Availability.date >= today,
                        Availability.status == 'available'
                    ).count()
                    print(f"- Nombre total de créneaux disponibles après synchronisation: {availabilities_after}")

                    # Informer le médecin que ses disponibilités ont été synchronisées
                    flash(f'Vos disponibilités ont été synchronisées avec succès. {len(new_availabilities)} créneaux ont été créés. Les patients peuvent maintenant réserver ces créneaux.', 'success')

                    # Ajouter un lien vers la page de débogage
                    flash(f'Vous pouvez vérifier vos disponibilités en détail sur la <a href="{url_for("debug.doctor_availability_html")}">page de débogage</a>.', 'info')

                except Exception as e:
                    # En cas d'erreur, annuler la transaction et afficher un message d'erreur
                    db.session.rollback()
                    flash(f'Une erreur est survenue lors de la synchronisation des disponibilités : {str(e)}', 'danger')
                    print(f"Erreur de synchronisation des disponibilités : {str(e)}")
                    # Continuer avec les autres mises à jour du profil

        elif form_type == 'preferences':
            # Mise à jour des préférences
            doctor.email_notifications = request.form.get('email_notifications') == 'on'
            doctor.sms_notifications = request.form.get('sms_notifications') == 'on'
            doctor.do_not_disturb = request.form.get('do_not_disturb') == 'on'

            # Changement de mot de passe
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

            if current_password and new_password and confirm_password:
                if not current_user.check_password(current_password):
                    flash('Le mot de passe actuel est incorrect.', 'danger')
                    return redirect(url_for('doctor.profile'))

                if new_password != confirm_password:
                    flash('Les nouveaux mots de passe ne correspondent pas.', 'danger')
                    return redirect(url_for('doctor.profile'))

                current_user.set_password(new_password)
                flash('Mot de passe mis à jour avec succès.', 'success')

        # Traitement de la photo de profil
        if 'avatar' in request.files:
            avatar_file = request.files['avatar']
            if avatar_file.filename != '':
                try:
                    # S'assurer que le dossier existe
                    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    avatar_dir = os.path.join(base_dir, 'static', 'uploads', 'avatars')
                    if not os.path.exists(avatar_dir):
                        os.makedirs(avatar_dir)

                    # Sauvegarder le fichier avec un nom unique basé sur l'horodatage
                    import time
                    timestamp = int(time.time())
                    filename = f"{timestamp}_{secure_filename(avatar_file.filename)}"
                    avatar_path = os.path.join(avatar_dir, filename)
                    avatar_file.save(avatar_path)

                    # Mettre à jour le chemin dans la base de données (chemin relatif)
                    doctor.profile_picture = f"uploads/avatars/{filename}"

                    # Afficher un message de succès
                    flash('Photo de profil mise à jour avec succès !', 'success')
                    print(f"Photo de profil enregistrée : {avatar_path}")
                except Exception as e:
                    # Afficher l'erreur pour le débogage
                    print(f"Erreur lors de l'upload de la photo : {str(e)}")
                    flash(f"Erreur lors de l'upload de la photo : {str(e)}", 'danger')

        try:
            # Enregistrer les modifications dans la base de données
            db.session.commit()
            flash('Profil mis à jour avec succès !', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Une erreur est survenue lors de la mise à jour du profil : {str(e)}', 'danger')
            print(f"Erreur de mise à jour du profil : {str(e)}")

        return redirect(url_for('doctor.profile'))

    return render_template('doctor/Profile_Doctor.html')

@doctor_bp.route('/patients')
@login_required
def patients():
    if current_user.role != 'doctor':
        flash('Access denied. You must be a doctor to view this page.', 'danger')
        return redirect(url_for('index'))

    # Get active patients (patients with at least one appointment)
    active_patients = Patient.query.join(Appointment).filter(
        Appointment.doctor_id == current_user.doctor.id,
        Appointment.status.in_(['accepted', 'completed'])
    ).distinct().all()

    # Get pending patients (patients with pending appointments)
    pending_patients = Patient.query.join(Appointment).filter(
        Appointment.doctor_id == current_user.doctor.id,
        Appointment.status == 'pending'
    ).distinct().all()

    return render_template('doctor/patients.html',
                          active_patients=active_patients,
                          pending_patients=pending_patients)

@doctor_bp.route('/patient/<int:patient_id>')
@login_required
def patient_details(patient_id):
    if current_user.role != 'doctor':
        flash('Access denied. You must be a doctor to view this page.', 'danger')
        return redirect(url_for('index'))

    patient = Patient.query.get_or_404(patient_id)

    # Check if the patient has appointments with the current doctor
    appointments = Appointment.query.filter_by(
        doctor_id=current_user.doctor.id,
        patient_id=patient.id
    ).all()

    if not appointments:
        flash('Access denied. This patient does not have appointments with you.', 'danger')
        return redirect(url_for('doctor.patients'))

    return render_template('doctor/patient_details.html', patient=patient, appointments=appointments)

@doctor_bp.route('/virtual_office')
@doctor_bp.route('/virtual_office/<int:appointment_id>')
@login_required
def virtual_office(appointment_id=None):
    if current_user.role != 'doctor':
        flash('Access denied. You must be a doctor to view this page.', 'danger')
        return redirect(url_for('index'))

    # Get today's appointments
    today = get_current_time_naive().date()
    today_appointments = Appointment.query.filter_by(
        doctor_id=current_user.doctor.id,
        status='accepted'
    ).filter(
        Appointment.date_time >= datetime.combine(today, datetime.min.time()),
        Appointment.date_time <= datetime.combine(today, datetime.max.time())
    ).order_by(
        Appointment.date_time
    ).all()

    # Get the current appointment if an ID is provided
    current_appointment = None
    patient_history = None

    if appointment_id:
        current_appointment = Appointment.query.get_or_404(appointment_id)

        # Verify that the appointment belongs to the logged-in doctor
        if current_appointment.doctor_id != current_user.doctor.id:
            flash('Access denied. This appointment does not belong to you.', 'danger')
            return redirect(url_for('doctor.virtual_office'))

        # Ensure the appointment has a video room ID if it's accepted
        if current_appointment.status == 'accepted' and not current_appointment.video_room_id:
            import hashlib
            unique_id = f"{current_appointment.id}-{int(get_current_time().timestamp())}"
            room_id = hashlib.md5(unique_id.encode()).hexdigest()[:12]

            # Stocker l'identifiant de la salle dans la base de données
            current_appointment.video_room_id = room_id

            # Créer les liens de visioconférence
            base_url = request.host_url.rstrip('/')
            video_link = f"{base_url}/video/{room_id}"
            current_appointment.video_link = video_link

            print(f"ID de salle généré dans virtual_office - ID: {current_appointment.id}, Room ID: {room_id}")

            db.session.commit()

        # Get patient history (past appointments)
        patient_history = Appointment.query.filter_by(
            doctor_id=current_user.doctor.id,
            patient_id=current_appointment.patient_id,
            status='completed'
        ).order_by(
            Appointment.date_time.desc()
        ).all()

        # Convert appointments to a format suitable for the history table
        formatted_history = []
        for appt in patient_history:
            history_item = {
                'appointment_date': appt.date_time,
                'appointment_type': appt.appointment_type if hasattr(appt, 'appointment_type') else 'Consultation',
                'procedures': appt.procedures if hasattr(appt, 'procedures') else '-',
                'diagnosis': appt.diagnosis if hasattr(appt, 'diagnosis') else '-',
                'prescriptions': appt.prescription if hasattr(appt, 'prescription') else '-',
                'next_appointment': appt.next_appointment_date if hasattr(appt, 'next_appointment_date') else None,
                'doctor_notes': appt.doctor_notes if hasattr(appt, 'doctor_notes') else '-'
            }
            formatted_history.append(history_item)

        patient_history = formatted_history

    # Get current time for enabling/disabling consultation buttons
    current_time = get_current_time_naive()

    return render_template('doctor/virtual_office.html',
                          today_appointments=today_appointments,
                          today_date=today.strftime('%d/%m/%Y'),
                          current_appointment=current_appointment,
                          patient_history=patient_history,
                          current_time=current_time)

@doctor_bp.route('/get_appointment_data/<int:appointment_id>')
@login_required
def get_appointment_data(appointment_id):
    if current_user.role != 'doctor':
        return jsonify({'error': 'Access denied'}), 403

    # Get the appointment
    appointment = Appointment.query.get_or_404(appointment_id)

    # Verify that the appointment belongs to the logged-in doctor
    if appointment.doctor_id != current_user.doctor.id:
        return jsonify({'error': 'This appointment does not belong to you'}), 403

    # Ensure the appointment has a video room ID
    if not appointment.video_room_id and appointment.status == 'accepted':
        # Generate a unique room ID if not already set
        import hashlib
        unique_id = f"{appointment.id}-{int(get_current_time().timestamp())}"
        room_id = hashlib.md5(unique_id.encode()).hexdigest()[:12]

        # Stocker l'identifiant de la salle dans la base de données
        appointment.video_room_id = room_id

        # Créer les liens de visioconférence
        base_url = request.host_url.rstrip('/')
        video_link = f"{base_url}/video/{room_id}"
        appointment.video_link = video_link

        print(f"ID de salle généré dans get_appointment_data - ID: {appointment.id}, Room ID: {room_id}")

        db.session.commit()

    # Prepare the response data
    data = {
        'appointment_id': appointment.id,
        'patient_id': appointment.patient.id,
        'patient_name': f"{appointment.patient.user.first_name} {appointment.patient.user.last_name}",
        'gender': appointment.patient.gender,
        'blood_type': appointment.patient.blood_type,
        'age': appointment.patient.age,
        'specialty': appointment.doctor.specialty,
        'appointment_date': appointment.date_time.strftime('%d/%m/%Y à %H:%M'),
        'status': appointment.status,
        'video_room_id': appointment.video_room_id
    }

    return jsonify(data)

@doctor_bp.route('/smart_agenda')
@login_required
def smart_agenda():
    if current_user.role != 'doctor':
        flash('Access denied. You must be a doctor to view this page.', 'danger')
        return redirect(url_for('index'))

    # Cette page sera développée ultérieurement
    flash('Fonctionnalité en cours de développement', 'info')
    return redirect(url_for('doctor.dashboard'))

@doctor_bp.route('/waiting_room')
@login_required
def waiting_room():
    if current_user.role != 'doctor':
        flash('Access denied. You must be a doctor to view this page.', 'danger')
        return redirect(url_for('index'))

    # Cette page sera développée ultérieurement
    flash('Fonctionnalité en cours de développement', 'info')
    return redirect(url_for('doctor.dashboard'))

@doctor_bp.route('/medical_network')
@login_required
def medical_network():
    if current_user.role != 'doctor':
        flash('Access denied. You must be a doctor to view this page.', 'danger')
        return redirect(url_for('index'))

    # Cette page sera développée ultérieurement
    flash('Fonctionnalité en cours de développement', 'info')
    return redirect(url_for('doctor.dashboard'))

@doctor_bp.route('/hospital_references')
@login_required
def hospital_references():
    if current_user.role != 'doctor':
        flash('Access denied. You must be a doctor to view this page.', 'danger')
        return redirect(url_for('index'))

    # Cette page sera développée ultérieurement
    flash('Fonctionnalité en cours de développement', 'info')
    return redirect(url_for('doctor.dashboard'))

@doctor_bp.route('/settings')
@login_required
def settings():
    if current_user.role != 'doctor':
        flash('Access denied. You must be a doctor to view this page.', 'danger')
        return redirect(url_for('index'))

    # Cette page sera développée ultérieurement
    flash('Fonctionnalité en cours de développement', 'info')
    return redirect(url_for('doctor.dashboard'))

@doctor_bp.route('/availability', methods=['GET', 'POST'])
@login_required
def availability():
    if current_user.role != 'doctor':
        flash('Access denied. You must be a doctor to view this page.', 'danger')
        return redirect(url_for('index'))

    doctor = current_user.doctor

    if request.method == 'POST':
        # Traitement du formulaire d'ajout de disponibilité
        try:
            date_str = request.form.get('date')
            start_time_str = request.form.get('start_time')
            end_time_str = request.form.get('end_time')

            # Validation des données
            if not all([date_str, start_time_str, end_time_str]):
                flash('Tous les champs sont obligatoires.', 'danger')
                return redirect(url_for('doctor.availability'))

            # Conversion des chaînes en objets date et time
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time_obj = datetime.strptime(start_time_str, '%H:%M').time()
            end_time_obj = datetime.strptime(end_time_str, '%H:%M').time()

            # Vérification que l'heure de fin est après l'heure de début
            if start_time_obj >= end_time_obj:
                flash('L\'heure de fin doit être après l\'heure de début.', 'danger')
                return redirect(url_for('doctor.availability'))

            # Vérification des chevauchements et des doublons
            existing_availabilities = Availability.query.filter_by(
                doctor_id=doctor.id,
                date=date_obj
            ).all()

            for avail in existing_availabilities:
                # Vérifier si c'est exactement le même créneau
                if (start_time_obj == avail.start_time and end_time_obj == avail.end_time):
                    flash(f'Ce créneau ({start_time_obj.strftime("%H:%M")} - {end_time_obj.strftime("%H:%M")}) est déjà disponible pour cette date.', 'info')
                    return redirect(url_for('doctor.availability'))

                # Vérifier s'il y a chevauchement
                if (start_time_obj < avail.end_time and end_time_obj > avail.start_time):
                    flash(f'Ce créneau chevauche un créneau existant ({avail.start_time.strftime("%H:%M")} - {avail.end_time.strftime("%H:%M")}).', 'danger')
                    return redirect(url_for('doctor.availability'))

            # Création de la nouvelle disponibilité
            new_availability = Availability(
                doctor_id=doctor.id,
                date=date_obj,
                start_time=start_time_obj,
                end_time=end_time_obj,
                status='available'
            )

            # Mettre à jour les champs available_days et available_hours du médecin
            # pour assurer la cohérence avec la table Availability
            weekday = date_obj.weekday() + 1  # 1 = Lundi, 7 = Dimanche

            # Mettre à jour available_days
            available_days = doctor.available_days or ""
            days_list = [int(day) for day in available_days.split(',') if day]
            if weekday not in days_list:
                days_list.append(weekday)
                days_list.sort()
                doctor.available_days = ','.join(str(day) for day in days_list)

            # Mettre à jour available_hours
            start_hour = start_time_obj.hour
            end_hour = end_time_obj.hour
            hour_range = f"{start_hour}-{end_hour}"

            available_hours = doctor.available_hours or ""
            hours_list = [hr for hr in available_hours.split(',') if hr]
            if hour_range not in hours_list:
                hours_list.append(hour_range)
                doctor.available_hours = ','.join(hours_list)

            # Journaliser les modifications
            print(f"Mise à jour des disponibilités du médecin {doctor.id}:")
            print(f"- Jours disponibles: {doctor.available_days}")
            print(f"- Heures disponibles: {doctor.available_hours}")
            print(f"- Nouvelle disponibilité: {date_obj} {start_time_obj}-{end_time_obj}")

            db.session.add(new_availability)
            db.session.commit()

            flash('Créneau de disponibilité ajouté avec succès.', 'success')
            return redirect(url_for('doctor.availability'))

        except Exception as e:
            db.session.rollback()
            flash(f'Une erreur est survenue: {str(e)}', 'danger')
            print(f"Erreur lors de l'ajout de disponibilité: {str(e)}")
            return redirect(url_for('doctor.availability'))

    # Récupération des disponibilités existantes
    today = get_current_time_naive().date()
    availabilities = Availability.query.filter(
        Availability.doctor_id == doctor.id,
        Availability.date >= today
    ).order_by(Availability.date, Availability.start_time).all()

    # Obtenir la date d'aujourd'hui au format YYYY-MM-DD pour le champ date
    today_str = get_current_time().strftime('%Y-%m-%d')

    # Journaliser les disponibilités existantes
    print(f"Disponibilités existantes pour le médecin {doctor.id}:")
    print(f"- Nombre de créneaux: {len(availabilities)}")
    for avail in availabilities:
        print(f"  - {avail.date} {avail.start_time}-{avail.end_time} ({avail.status})")

    return render_template('doctor/availability.html', availabilities=availabilities, today=today_str)

@doctor_bp.route('/accept_patient/<int:patient_id>')
@login_required
def accept_patient(patient_id):
    if current_user.role != 'doctor':
        flash('Access denied. You must be a doctor to view this page.', 'danger')
        return redirect(url_for('index'))

    # Cette fonctionnalité sera développée ultérieurement
    flash('Fonctionnalité en cours de développement', 'info')
    return redirect(url_for('doctor.patients'))

@doctor_bp.route('/reject_patient/<int:patient_id>')
@login_required
def reject_patient(patient_id):
    if current_user.role != 'doctor':
        flash('Access denied. You must be a doctor to view this page.', 'danger')
        return redirect(url_for('index'))

    # Cette fonctionnalité sera développée ultérieurement
    flash('Fonctionnalité en cours de développement', 'info')
    return redirect(url_for('doctor.patients'))

@doctor_bp.route('/schedule_appointment/<int:patient_id>')
@login_required
def schedule_appointment(patient_id):
    if current_user.role != 'doctor':
        flash('Access denied. You must be a doctor to view this page.', 'danger')
        return redirect(url_for('index'))

    # Cette fonctionnalité sera développée ultérieurement
    flash('Fonctionnalité en cours de développement', 'info')
    return redirect(url_for('doctor.patients'))

@doctor_bp.route('/delete_availability/<int:availability_id>')
@login_required
def delete_availability(availability_id):
    if current_user.role != 'doctor':
        flash('Access denied. You must be a doctor to view this page.', 'danger')
        return redirect(url_for('index'))

    availability = Availability.query.get_or_404(availability_id)

    # Vérifier que la disponibilité appartient au médecin connecté
    if availability.doctor_id != current_user.doctor.id:
        flash('Vous n\'êtes pas autorisé à supprimer cette disponibilité.', 'danger')
        return redirect(url_for('doctor.availability'))

    # Vérifier que la disponibilité n'est pas déjà réservée
    if availability.status != 'available':
        flash('Vous ne pouvez pas supprimer un créneau déjà réservé.', 'danger')
        return redirect(url_for('doctor.availability'))

    try:
        db.session.delete(availability)
        db.session.commit()
        flash('Créneau de disponibilité supprimé avec succès.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Une erreur est survenue: {str(e)}', 'danger')

    return redirect(url_for('doctor.availability'))

@doctor_bp.route('/save_notes/<int:appointment_id>', methods=['POST'])
@login_required
def save_notes(appointment_id):
    # Vérifier que l'utilisateur est un médecin
    if current_user.role != 'doctor':
        flash('Accès refusé. Vous devez être un médecin pour voir cette page.', 'danger')
        return redirect(url_for('index'))

    # Récupérer le rendez-vous
    appointment = Appointment.query.get_or_404(appointment_id)

    # Vérifier que le rendez-vous appartient au médecin connecté
    if appointment.doctor_id != current_user.doctor.id:
        flash('Accès refusé. Ce rendez-vous ne vous appartient pas.', 'danger')
        return redirect(url_for('doctor.dashboard'))

    # Récupérer les notes du formulaire
    notes = request.form.get('notes', '')

    # Enregistrer les notes
    appointment.notes = notes
    db.session.commit()

    flash('Notes enregistrées avec succès.', 'success')
    return redirect(url_for('doctor.consultation', appointment_id=appointment_id))
