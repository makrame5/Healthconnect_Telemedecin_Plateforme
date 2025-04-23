from extensions import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'patient' or 'doctor'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    patient = db.relationship('Patient', backref='user', uselist=False, cascade='all, delete-orphan')
    doctor = db.relationship('Doctor', backref='user', uselist=False, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    birth_date = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(10), nullable=True)  # male, female, other
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    id_number = db.Column(db.String(50), nullable=True)  # National ID or patient ID
    insurance = db.Column(db.String(100), nullable=True)
    blood_type = db.Column(db.String(5), nullable=True)  # A+, B-, etc.
    allergies = db.Column(db.Text, nullable=True)
    chronic_diseases = db.Column(db.Text, nullable=True)
    current_medications = db.Column(db.Text, nullable=True)
    emergency_contact_name = db.Column(db.String(100), nullable=True)
    emergency_contact_phone = db.Column(db.String(20), nullable=True)
    social_security_number = db.Column(db.String(50), nullable=True)

    # Relationships
    appointments = db.relationship('Appointment', backref='patient', lazy='dynamic',
                                  foreign_keys='Appointment.patient_id', cascade='all, delete-orphan')
    prescriptions = db.relationship('Prescription', backref='patient', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Patient {self.user.first_name} {self.user.last_name}>'

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    speciality = db.Column(db.String(100), nullable=True)
    license_number = db.Column(db.String(50), nullable=True)
    years_experience = db.Column(db.Integer, nullable=True)
    education = db.Column(db.Text, nullable=True)
    bio = db.Column(db.Text, nullable=True)
    consultation_fee = db.Column(db.Float, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    languages = db.Column(db.String(200), nullable=True)  # Comma-separated list of languages
    profile_picture = db.Column(db.String(200), nullable=True)  # Path to profile picture
    document_path = db.Column(db.String(200), nullable=True)  # Path to uploaded documents
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected

    # Relationships
    appointments = db.relationship('Appointment', backref='doctor', lazy='dynamic',
                                  foreign_keys='Appointment.doctor_id', cascade='all, delete-orphan')
    prescriptions = db.relationship('Prescription', backref='doctor', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Doctor {self.user.first_name} {self.user.last_name}>'

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    date_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected, completed
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Appointment {self.id}>'

class Prescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship with appointment
    appointment = db.relationship('Appointment', backref='prescriptions')

    def __repr__(self):
        return f'<Prescription {self.id}>'
