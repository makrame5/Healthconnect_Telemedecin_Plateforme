from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import User, Patient, Appointment, Prescription
from datetime import datetime

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
        Appointment.date_time >= datetime.utcnow()
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
        flash('Access denied. You must be a doctor to view this page.', 'danger')
        return redirect(url_for('index'))

    # Get all appointments
    appointments = Appointment.query.filter_by(
        doctor_id=current_user.doctor.id
    ).order_by(
        Appointment.date_time.desc()
    ).all()

    return render_template('doctor/appointments.html', appointments=appointments)

@doctor_bp.route('/appointment/<int:appointment_id>/<string:action>')
@login_required
def appointment_action(appointment_id, action):
    if current_user.role != 'doctor':
        flash('Access denied. You must be a doctor to view this page.', 'danger')
        return redirect(url_for('index'))

    appointment = Appointment.query.get_or_404(appointment_id)

    # Check if the appointment belongs to the current user
    if appointment.doctor_id != current_user.doctor.id:
        flash('Access denied. This appointment does not belong to you.', 'danger')
        return redirect(url_for('doctor.dashboard'))

    if action == 'accept':
        appointment.status = 'accepted'
        flash('Appointment accepted!', 'success')
    elif action == 'reject':
        appointment.status = 'rejected'
        flash('Appointment rejected!', 'info')
    else:
        flash('Invalid action!', 'danger')
        return redirect(url_for('doctor.dashboard'))

    db.session.commit()
    return redirect(url_for('doctor.dashboard'))

@doctor_bp.route('/consultation/<int:appointment_id>')
@login_required
def consultation(appointment_id):
    if current_user.role != 'doctor':
        flash('Access denied. You must be a doctor to view this page.', 'danger')
        return redirect(url_for('index'))

    appointment = Appointment.query.get_or_404(appointment_id)

    # Check if the appointment belongs to the current user
    if appointment.doctor_id != current_user.doctor.id:
        flash('Access denied. This appointment does not belong to you.', 'danger')
        return redirect(url_for('doctor.dashboard'))

    # Check if the appointment is accepted
    if appointment.status != 'accepted':
        flash('This appointment has not been accepted yet.', 'warning')
        return redirect(url_for('doctor.dashboard'))

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
