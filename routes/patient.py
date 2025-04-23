from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import User, Doctor, Appointment
from datetime import datetime

patient_bp = Blueprint('patient', __name__, url_prefix='/patient')

@patient_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'patient':
        flash('Access denied. You must be a patient to view this page.', 'danger')
        return redirect(url_for('index'))

    # Get upcoming appointments
    upcoming_appointments = Appointment.query.filter_by(
        patient_id=current_user.patient.id
    ).filter(
        Appointment.date_time >= datetime.utcnow()
    ).order_by(
        Appointment.date_time
    ).all()

    return render_template('patient/dashboard.html', appointments=upcoming_appointments)

@patient_bp.route('/doctors')
@login_required
def doctors():
    if current_user.role != 'patient':
        flash('Access denied. You must be a patient to view this page.', 'danger')
        return redirect(url_for('index'))

    # Get all doctors
    doctors = Doctor.query.all()

    return render_template('patient/doctors.html', doctors=doctors)

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
        flash('Access denied. You must be a patient to view this page.', 'danger')
        return redirect(url_for('index'))

    # Get all appointments
    appointments = Appointment.query.filter_by(
        patient_id=current_user.patient.id
    ).order_by(
        Appointment.date_time.desc()
    ).all()

    return render_template('patient/appointments.html', appointments=appointments)

@patient_bp.route('/consultation/<int:appointment_id>')
@login_required
def consultation(appointment_id):
    if current_user.role != 'patient':
        flash('Access denied. You must be a patient to view this page.', 'danger')
        return redirect(url_for('index'))

    appointment = Appointment.query.get_or_404(appointment_id)

    # Check if the appointment belongs to the current user
    if appointment.patient_id != current_user.patient.id:
        flash('Access denied. This appointment does not belong to you.', 'danger')
        return redirect(url_for('patient.dashboard'))

    # Check if the appointment is accepted
    if appointment.status != 'accepted':
        flash('This appointment has not been accepted by the doctor yet.', 'warning')
        return redirect(url_for('patient.dashboard'))

    return render_template('patient/consultation.html', appointment=appointment)
