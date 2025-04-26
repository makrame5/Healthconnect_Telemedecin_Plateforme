from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
import os

# Import extensions
from extensions import db, login_manager, migrate, socketio

# Import models
from models import User, Patient, Doctor, Appointment, Prescription, Availability, Notification

# Initialize Flask app
app = Flask(__name__)
app.config.from_object('config.Config')

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)
migrate.init_app(app, db)
socketio.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create database tables
with app.app_context():
    db.create_all()

# Register blueprints
from routes.auth import auth_bp
from routes.patient import patient_bp
from routes.doctor import doctor_bp
from routes.admin import admin_bp
from routes.api import api_bp
from routes.doctor_debug import debug_bp

app.register_blueprint(auth_bp)
app.register_blueprint(patient_bp)
app.register_blueprint(doctor_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(api_bp)
app.register_blueprint(debug_bp)

# Import Socket.IO events
from socket_events import register_socket_events
register_socket_events(socketio)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video/<room_id>')
@login_required
def video_room(room_id):
    # Rechercher le rendez-vous correspondant à ce room_id
    appointment = Appointment.query.filter_by(video_room_id=room_id).first_or_404()

    # Vérifier que l'utilisateur est soit le médecin, soit le patient de ce rendez-vous
    is_doctor = current_user.role == 'doctor' and current_user.doctor.id == appointment.doctor_id
    is_patient = current_user.role == 'patient' and current_user.patient.id == appointment.patient_id

    if not (is_doctor or is_patient):
        flash('Accès refusé. Vous n\'êtes pas autorisé à accéder à cette salle de consultation.', 'danger')
        return redirect(url_for('index'))

    # Vérifier que le rendez-vous est accepté
    if appointment.status != 'accepted':
        flash('Ce rendez-vous n\'est pas confirmé.', 'warning')
        if is_doctor:
            return redirect(url_for('doctor.dashboard'))
        else:
            return redirect(url_for('patient.dashboard'))

    # Vérifier que le rendez-vous est dans la plage horaire autorisée (10 minutes avant à 1 heure après)
    from utils.datetime_utils import get_current_time_naive
    current_time = get_current_time_naive()
    time_diff = (appointment.date_time - current_time).total_seconds()

    if time_diff > 600:  # Plus de 10 minutes avant le rendez-vous
        flash('La salle de consultation n\'est pas encore disponible. Elle sera accessible 10 minutes avant l\'heure du rendez-vous.', 'warning')
        if is_doctor:
            return redirect(url_for('doctor.virtual_office'))
        else:
            return redirect(url_for('patient.doctor_patient_space'))

    if time_diff < -3600:  # Plus d'une heure après le rendez-vous
        flash('Cette consultation est terminée. La salle n\'est plus accessible.', 'warning')
        if is_doctor:
            return redirect(url_for('doctor.virtual_office'))
        else:
            return redirect(url_for('patient.doctor_patient_space'))

    # Déterminer le nom et le rôle de l'utilisateur pour l'affichage
    user_name = f"{current_user.first_name} {current_user.last_name}"
    user_role = 'doctor' if is_doctor else 'patient'

    if is_doctor:
        user_name = f"Dr. {user_name}"

    # Déterminer le nom de l'autre participant
    if is_doctor:
        other_name = f"{appointment.patient.user.first_name} {appointment.patient.user.last_name}"
        other_role = 'patient'
    else:
        other_name = f"Dr. {appointment.doctor.user.first_name} {appointment.doctor.user.last_name}"
        other_role = 'doctor'

    # Journaliser l'accès à la salle
    print(f"Accès à la salle {room_id} par {user_name} ({user_role}) pour le rendez-vous {appointment.id}")

    return render_template('video_room.html',
                          appointment=appointment,
                          room_id=room_id,
                          user_name=user_name,
                          user_role=user_role,
                          other_name=other_name,
                          other_role=other_role)

if __name__ == '__main__':
    socketio.run(app, debug=True)
