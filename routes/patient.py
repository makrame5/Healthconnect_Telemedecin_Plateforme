from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import User, Doctor, Appointment, Prescription, Availability
from datetime import datetime, date
from sqlalchemy import func
from utils.datetime_utils import get_current_time, get_current_time_naive, format_datetime

patient_bp = Blueprint('patient', __name__, url_prefix='/patient')

@patient_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'patient':
        flash('Accès refusé. Vous devez être un patient pour voir cette page.', 'danger')
        return redirect(url_for('index'))

    # Get upcoming appointments
    upcoming_appointments = Appointment.query.filter_by(
        patient_id=current_user.patient.id
    ).filter(
        Appointment.date_time >= get_current_time_naive()
    ).order_by(
        Appointment.date_time
    ).all()

    return render_template('patient/dashboard.html', appointments=upcoming_appointments)

@patient_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if current_user.role != 'patient':
        flash('Accès refusé. Vous devez être un patient pour voir cette page.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            # Traitement de la photo de profil
            if 'avatar' in request.files:
                avatar_file = request.files['avatar']
                if avatar_file.filename != '':
                    # S'assurer que le dossier existe
                    import os
                    from werkzeug.utils import secure_filename

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
                    current_user.patient.profile_picture = f"uploads/avatars/{filename}"

                    # Journaliser pour le débogage
                    print(f"Photo de profil enregistrée : {avatar_path}")
                    print(f"Chemin relatif enregistré en base : {current_user.patient.profile_picture}")

                    # Enregistrer les modifications dans la base de données
                    db.session.commit()

                    flash('Photo de profil mise à jour avec succès !', 'success')
                    return redirect(url_for('patient.profile'))

            # Si on arrive ici, c'est qu'il n'y a pas eu d'upload de photo
            flash('Aucune photo sélectionnée.', 'warning')

        except Exception as e:
            db.session.rollback()
            print(f"Erreur lors de la mise à jour de la photo de profil : {str(e)}")
            flash(f'Une erreur est survenue lors de la mise à jour de la photo de profil : {str(e)}', 'danger')

    return render_template('patient/profile.html')

@patient_bp.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if current_user.role != 'patient':
        flash('Accès refusé. Vous devez être un patient pour voir cette page.', 'danger')
        return redirect(url_for('index'))

    patient = current_user.patient

    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            current_user.first_name = request.form.get('first_name')
            current_user.last_name = request.form.get('last_name')
            current_user.email = request.form.get('email')

            # Informations personnelles
            if request.form.get('birth_date'):
                from datetime import datetime
                patient.birth_date = datetime.strptime(request.form.get('birth_date'), '%Y-%m-%d').date()
            patient.gender = request.form.get('gender')
            patient.phone = request.form.get('phone')
            patient.address = request.form.get('address')
            patient.id_number = request.form.get('id_number')
            patient.insurance = request.form.get('insurance')

            # Informations médicales
            patient.blood_type = request.form.get('blood_type')
            patient.allergies = request.form.get('allergies')
            patient.chronic_diseases = request.form.get('chronic_diseases')
            patient.current_medications = request.form.get('current_medications')

            # Contact d'urgence
            patient.emergency_contact_name = request.form.get('emergency_contact_name')
            patient.emergency_contact_phone = request.form.get('emergency_contact_phone')
            patient.social_security_number = request.form.get('social_security_number')

            # Enregistrer les modifications
            db.session.commit()

            flash('Profil mis à jour avec succès !', 'success')
            return redirect(url_for('patient.profile'))

        except Exception as e:
            db.session.rollback()
            print(f"Erreur lors de la mise à jour du profil : {str(e)}")
            flash(f'Une erreur est survenue lors de la mise à jour du profil : {str(e)}', 'danger')

    return render_template('patient/edit_profile.html', patient=patient)

@patient_bp.route('/find-doctor')
@login_required
def find_doctor():
    if current_user.role != 'patient':
        flash('Accès refusé. Vous devez être un patient pour voir cette page.', 'danger')
        return redirect(url_for('index'))

    # Récupérer les médecins qui ont des disponibilités
    today = date.today()

    # Journaliser la date actuelle pour le débogage
    print(f"Recherche de médecins disponibles à partir de la date: {today}")

    # Vérifier d'abord s'il y a des disponibilités dans la base de données
    availability_count = Availability.query.filter(
        Availability.date >= today,
        Availability.status == 'available'
    ).count()
    print(f"Nombre total de créneaux disponibles dans la base de données: {availability_count}")

    # Sous-requête pour trouver les médecins avec des disponibilités futures
    # Utiliser une jointure externe pour inclure également les médecins qui ont des jours disponibles
    # mais pas encore de créneaux spécifiques dans la table Availability
    doctors_query = db.session.query(Doctor).outerjoin(
        Availability, Doctor.id == Availability.doctor_id
    ).filter(
        db.or_(
            db.and_(Availability.date >= today, Availability.status == 'available'),
            Doctor.available_days != None  # Inclure les médecins qui ont des jours disponibles
        )
    ).group_by(Doctor.id)

    # Récupérer les spécialités uniques pour le filtre
    specialities = db.session.query(Doctor.speciality).distinct().all()
    specialities = [s[0] for s in specialities if s[0]]  # Filtrer les valeurs None

    # Appliquer les filtres
    # 1. Filtre par spécialité
    speciality = request.args.get('speciality')
    if speciality:
        doctors_query = doctors_query.filter(Doctor.speciality == speciality)

    # 2. Filtre par tarif maximum
    max_fee = request.args.get('max_fee')
    if max_fee and max_fee.isdigit():
        doctors_query = doctors_query.filter(Doctor.consultation_fee <= int(max_fee))

    # 3. Filtre par disponibilité
    availability_filter = request.args.get('availability')
    if availability_filter:
        from datetime import timedelta

        if availability_filter == 'today':
            doctors_query = doctors_query.filter(
                db.or_(
                    Availability.date == today,
                    Doctor.available_days.contains(str(today.weekday() + 1))
                )
            )
        elif availability_filter == 'tomorrow':
            tomorrow = today + timedelta(days=1)
            doctors_query = doctors_query.filter(
                db.or_(
                    Availability.date == tomorrow,
                    Doctor.available_days.contains(str(tomorrow.weekday() + 1))
                )
            )
        elif availability_filter == 'this_week':
            # Calculer le début et la fin de la semaine actuelle
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            doctors_query = doctors_query.filter(
                db.or_(
                    db.and_(Availability.date >= start_of_week, Availability.date <= end_of_week),
                    Doctor.available_days != None  # Tous les médecins avec des jours disponibles
                )
            )
        elif availability_filter == 'next_week':
            # Calculer le début et la fin de la semaine prochaine
            start_of_week = today - timedelta(days=today.weekday()) + timedelta(days=7)
            end_of_week = start_of_week + timedelta(days=6)
            doctors_query = doctors_query.filter(
                db.or_(
                    db.and_(Availability.date >= start_of_week, Availability.date <= end_of_week),
                    Doctor.available_days != None  # Tous les médecins avec des jours disponibles
                )
            )

    # 4. Recherche par nom
    search_query = request.args.get('search')
    if search_query:
        search_term = f"%{search_query}%"
        doctors_query = doctors_query.join(User, Doctor.user_id == User.id).filter(
            db.or_(
                User.first_name.ilike(search_term),
                User.last_name.ilike(search_term),
                db.func.concat(User.first_name, ' ', User.last_name).ilike(search_term)
            )
        )

    # Exécuter la requête
    doctors = doctors_query.all()

    # Journaliser les résultats pour le débogage
    print(f"Nombre de médecins trouvés: {len(doctors)}")
    for doctor in doctors:
        print(f"- Dr. {doctor.user.first_name} {doctor.user.last_name} (ID: {doctor.id})")
        print(f"  - Jours disponibles: {doctor.available_days}")
        print(f"  - Heures disponibles: {doctor.available_hours}")

        # Compter les disponibilités pour ce médecin
        avail_count = Availability.query.filter(
            Availability.doctor_id == doctor.id,
            Availability.date >= today,
            Availability.status == 'available'
        ).count()
        print(f"  - Nombre de créneaux disponibles: {avail_count}")

    return render_template('patient/find_doctor.html',
                          doctors=doctors,
                          specialities=specialities,
                          selected_speciality=speciality)

@patient_bp.route('/doctor-availability/<int:doctor_id>')
@login_required
def doctor_availability(doctor_id):
    if current_user.role != 'patient':
        flash('Accès refusé. Vous devez être un patient pour voir cette page.', 'danger')
        return redirect(url_for('index'))

    doctor = Doctor.query.get_or_404(doctor_id)

    # Log pour le débogage
    print(f"Récupération des disponibilités pour le médecin {doctor_id} (Dr. {doctor.user.first_name} {doctor.user.last_name})")
    print(f"- Jours disponibles: {doctor.available_days}")
    print(f"- Heures disponibles: {doctor.available_hours}")

    # Récupérer les disponibilités futures du médecin
    today = date.today()
    print(f"- Date d'aujourd'hui: {today}")

    # Compter toutes les disponibilités (pour le débogage)
    all_availabilities_count = Availability.query.filter(
        Availability.doctor_id == doctor_id,
        Availability.date >= today
    ).count()
    print(f"- Nombre total de créneaux (tous statuts): {all_availabilities_count}")

    # Récupérer uniquement les disponibilités avec statut 'available'
    availabilities = Availability.query.filter(
        Availability.doctor_id == doctor_id,
        Availability.date >= today,
        Availability.status == 'available'
    ).order_by(Availability.date, Availability.start_time).all()

    print(f"- Nombre de créneaux disponibles: {len(availabilities)}")

    # Nous ne générons plus de disponibilités temporaires
    # Nous n'affichons que les disponibilités explicitement définies par le médecin
    if len(availabilities) == 0:
        print("Aucune disponibilité trouvée pour ce médecin")
        flash("Ce médecin n'a pas encore défini de disponibilités. Veuillez réessayer ultérieurement.", "info")

    # Organiser les disponibilités par date
    availability_by_date = {}
    for avail in availabilities:
        date_str = avail.date.strftime('%Y-%m-%d')
        if date_str not in availability_by_date:
            availability_by_date[date_str] = []
        availability_by_date[date_str].append(avail)
        print(f"  - Créneau disponible: {date_str} {avail.start_time.strftime('%H:%M')}-{avail.end_time.strftime('%H:%M')}")

    return render_template('patient/doctor_availability.html',
                          doctor=doctor,
                          availability_by_date=availability_by_date)

@patient_bp.route('/book-appointment/<int:availability_id>', methods=['GET', 'POST'])
@login_required
def book_appointment(availability_id):
    if current_user.role != 'patient':
        flash('Accès refusé. Vous devez être un patient pour voir cette page.', 'danger')
        return redirect(url_for('index'))

    # Récupérer la disponibilité normale depuis la base de données
    availability = Availability.query.get_or_404(availability_id)
    doctor = Doctor.query.get_or_404(availability.doctor_id)

    # Vérifier que la disponibilité est toujours disponible
    if availability.status != 'available':
        flash('Ce créneau n\'est plus disponible.', 'danger')
        return redirect(url_for('patient.doctor_availability', doctor_id=doctor.id))

    if request.method == 'POST':
        try:
            # Créer un rendez-vous à partir de la disponibilité
            appointment_datetime = datetime.combine(availability.date, availability.start_time)

            # Créer le rendez-vous
            appointment = Appointment(
                patient_id=current_user.patient.id,
                doctor_id=doctor.id,
                date_time=appointment_datetime,
                status='pending',
                notes=request.form.get('notes', '')
            )

            # Mettre à jour le statut de la disponibilité
            availability.status = 'booked'

            db.session.add(appointment)
            db.session.commit()

            # Envoyer une notification au médecin
            from socket_events import send_notification
            doctor_user_id = doctor.user_id
            formatted_date = appointment_datetime.strftime('%d/%m/%Y à %H:%M')
            notification_title = "Nouvelle demande de rendez-vous"
            notification_content = f"Nouveau rendez-vous de la part de {current_user.first_name} {current_user.last_name} pour le {formatted_date}"

            send_notification(
                user_id=doctor_user_id,
                title=notification_title,
                content=notification_content,
                notification_type="appointment",
                related_id=appointment.id
            )

            flash('Votre rendez-vous a été réservé avec succès ! Le médecin doit maintenant confirmer.', 'success')
            return redirect(url_for('patient.appointments'))

        except Exception as e:
            db.session.rollback()
            print(f"Erreur lors de la réservation du rendez-vous: {str(e)}")
            flash(f'Une erreur est survenue lors de la réservation: {str(e)}', 'danger')
            return redirect(url_for('patient.doctor_availability', doctor_id=doctor.id))

    return render_template('patient/book_appointment.html',
                          doctor=doctor,
                          availability=availability)

@patient_bp.route('/book-temp-appointment/<int:doctor_id>/<string:date_str>/<int:start_hour>', methods=['GET', 'POST'])
@login_required
def book_temp_appointment(doctor_id, date_str, start_hour):
    if current_user.role != 'patient':
        flash('Accès refusé. Vous devez être un patient pour voir cette page.', 'danger')
        return redirect(url_for('index'))

    try:
        # Reconstruire la date et l'heure
        date_obj = datetime.strptime(date_str, '%Y%m%d').date()
        start_time = datetime.strptime(f"{start_hour}:00", '%H:%M').time()
        end_time = datetime.strptime(f"{start_hour+1}:00", '%H:%M').time()

        # Récupérer le médecin
        doctor = Doctor.query.get_or_404(doctor_id)

        # Vérifier si une disponibilité existe déjà pour ce créneau
        existing_availability = Availability.query.filter_by(
            doctor_id=doctor.id,
            date=date_obj,
            start_time=start_time,
            end_time=end_time
        ).first()

        if existing_availability:
            # Utiliser la disponibilité existante
            if existing_availability.status != 'available':
                flash('Ce créneau n\'est plus disponible.', 'danger')
                return redirect(url_for('patient.doctor_availability', doctor_id=doctor.id))

            # Rediriger vers la route normale avec l'ID de la disponibilité existante
            return redirect(url_for('patient.book_appointment', availability_id=existing_availability.id))

        # Créer une disponibilité temporaire
        availability = Availability(
            doctor_id=doctor_id,
            date=date_obj,
            start_time=start_time,
            end_time=end_time,
            status='available'
        )

        # Sauvegarder la nouvelle disponibilité
        db.session.add(availability)
        db.session.commit()

        # Rediriger vers la route normale avec l'ID de la nouvelle disponibilité
        return redirect(url_for('patient.book_appointment', availability_id=availability.id))

    except Exception as e:
        print(f"Erreur lors de la reconstruction de la disponibilité temporaire: {str(e)}")
        flash('Disponibilité invalide.', 'danger')
        return redirect(url_for('patient.find_doctor'))

@patient_bp.route('/request_appointment/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
def request_appointment(doctor_id):
    if current_user.role != 'patient':
        flash('Access denied. You must be a patient to view this page.', 'danger')
        return redirect(url_for('index'))

    doctor = Doctor.query.get_or_404(doctor_id)

    if request.method == 'POST':
        # Get form data
        date_str = request.form.get('date')
        time_str = request.form.get('time')

        # Convert to datetime
        date_time_str = f"{date_str} {time_str}"
        date_time = datetime.strptime(date_time_str, '%Y-%m-%d %H:%M')

        # Create new appointment
        appointment = Appointment(
            patient_id=current_user.patient.id,
            doctor_id=doctor.id,
            date_time=date_time,
            status='pending'
        )

        db.session.add(appointment)
        db.session.commit()

        flash('Appointment request sent successfully!', 'success')
        return redirect(url_for('patient.dashboard'))

    return render_template('patient/request_appointment.html', doctor=doctor)

@patient_bp.route('/appointments')
@login_required
def appointments():
    if current_user.role != 'patient':
        flash('Accès refusé. Vous devez être un patient pour voir cette page.', 'danger')
        return redirect(url_for('index'))

    # Get all appointments
    appointments = Appointment.query.filter_by(
        patient_id=current_user.patient.id
    ).order_by(
        Appointment.date_time.desc()
    ).all()

    # Debug: afficher tous les rendez-vous et leur statut
    print(f"Rendez-vous trouvés pour le patient {current_user.patient.id}:")
    for appt in appointments:
        print(f"- ID: {appt.id}, Date: {appt.date_time}, Statut: {appt.status}, Médecin: {appt.doctor.user.first_name} {appt.doctor.user.last_name}")

    # Pass current datetime to template for comparison
    now = get_current_time_naive()

    return render_template('patient/appointments.html', appointments=appointments, now=now)

@patient_bp.route('/cancel-appointment/<int:appointment_id>')
@login_required
def cancel_appointment(appointment_id):
    if current_user.role != 'patient':
        flash('Accès refusé. Vous devez être un patient pour voir cette page.', 'danger')
        return redirect(url_for('index'))

    appointment = Appointment.query.get_or_404(appointment_id)

    # Vérifier que le rendez-vous appartient à l'utilisateur connecté
    if appointment.patient_id != current_user.patient.id:
        flash('Accès refusé. Ce rendez-vous ne vous appartient pas.', 'danger')
        return redirect(url_for('patient.appointments'))

    # Vérifier que le rendez-vous est en attente
    if appointment.status != 'pending':
        flash('Vous ne pouvez annuler que les rendez-vous en attente de confirmation.', 'warning')
        return redirect(url_for('patient.appointments'))

    # Mettre à jour le statut du rendez-vous
    appointment.status = 'cancelled'

    # Remettre la disponibilité à "available"
    availability = Availability.query.filter_by(
        doctor_id=appointment.doctor_id,
        date=appointment.date_time.date(),
        start_time=appointment.date_time.time()
    ).first()

    if availability:
        availability.status = 'available'

    db.session.commit()

    # Envoyer une notification au médecin
    from socket_events import send_notification
    doctor_user_id = appointment.doctor.user_id
    formatted_date = appointment.date_time.strftime('%d/%m/%Y à %H:%M')
    notification_title = "Rendez-vous annulé"
    notification_content = f"Le rendez-vous avec {current_user.first_name} {current_user.last_name} pour le {formatted_date} a été annulé par le patient."

    send_notification(
        user_id=doctor_user_id,
        title=notification_title,
        content=notification_content,
        notification_type="appointment_cancelled",
        related_id=appointment.id
    )

    flash('Votre rendez-vous a été annulé avec succès.', 'success')
    return redirect(url_for('patient.appointments'))

@patient_bp.route('/consultation/<int:appointment_id>')
@login_required
def consultation(appointment_id):
    if current_user.role != 'patient':
        flash('Accès refusé. Vous devez être un patient pour voir cette page.', 'danger')
        return redirect(url_for('index'))

    appointment = Appointment.query.get_or_404(appointment_id)

    # Vérifier que le rendez-vous appartient au patient connecté
    if appointment.patient_id != current_user.patient.id:
        flash('Accès refusé. Ce rendez-vous ne vous appartient pas.', 'danger')
        return redirect(url_for('patient.dashboard'))

    # Vérifier que le rendez-vous est accepté
    if appointment.status != 'accepted':
        flash('Ce rendez-vous n\'a pas encore été accepté par le médecin.', 'warning')
        return redirect(url_for('patient.dashboard'))

    # Vérifier que le lien de visioconférence existe
    if not appointment.video_link:
        flash('Le lien de visioconférence n\'a pas encore été généré par le médecin.', 'warning')
        return redirect(url_for('patient.appointments'))

    return render_template('patient/consultation.html', appointment=appointment)

@patient_bp.route('/doctor-patient-space')
@login_required
def doctor_patient_space():
    if current_user.role != 'patient':
        flash('Accès refusé. Vous devez être un patient pour voir cette page.', 'danger')
        return redirect(url_for('index'))

    # Récupérer tous les rendez-vous du patient pour le débogage
    all_appointments = Appointment.query.filter_by(
        patient_id=current_user.patient.id
    ).all()

    print(f"Tous les rendez-vous du patient {current_user.patient.id}:")
    for appt in all_appointments:
        print(f"- ID: {appt.id}, Date: {appt.date_time}, Statut: {appt.status}, Médecin: {appt.doctor.user.first_name} {appt.doctor.user.last_name}")
        print(f"  Video Room ID: {appt.video_room_id}, Video Link: {appt.video_link}")

    # Récupérer les rendez-vous acceptés à venir
    upcoming_appointments = Appointment.query.filter_by(
        patient_id=current_user.patient.id,
        status='accepted'
    ).filter(
        Appointment.date_time >= get_current_time_naive()
    ).order_by(
        Appointment.date_time
    ).all()

    print(f"Rendez-vous acceptés à venir pour le patient {current_user.patient.id}:")
    for appt in upcoming_appointments:
        print(f"- ID: {appt.id}, Date: {appt.date_time}, Médecin: {appt.doctor.user.first_name} {appt.doctor.user.last_name}")
        print(f"  Video Room ID: {appt.video_room_id}, Video Link: {appt.video_link}")

    # Récupérer les rendez-vous passés
    past_appointments = Appointment.query.filter_by(
        patient_id=current_user.patient.id
    ).filter(
        Appointment.status.in_(['accepted', 'completed']),
        Appointment.date_time < get_current_time_naive()
    ).order_by(
        Appointment.date_time.desc()
    ).all()

    print(f"Rendez-vous passés pour le patient {current_user.patient.id}:")
    for appt in past_appointments:
        print(f"- ID: {appt.id}, Date: {appt.date_time}, Statut: {appt.status}, Médecin: {appt.doctor.user.first_name} {appt.doctor.user.last_name}")

    # Obtenir l'heure actuelle pour la comparaison dans le template
    now = get_current_time_naive()
    print(f"Heure actuelle: {now}")

    return render_template('patient/doctor_patient_space.html',
                          upcoming_appointments=upcoming_appointments,
                          past_appointments=past_appointments,
                          now=now)
