from app import app
from extensions import db
from models import User, Patient, Doctor
from werkzeug.security import generate_password_hash
from datetime import datetime

def create_test_users():
    with app.app_context():
        # Check if test users already exist
        patient_email = "patient@test.com"
        doctor_email = "doctor@test.com"
        
        existing_patient = User.query.filter_by(email=patient_email).first()
        existing_doctor = User.query.filter_by(email=doctor_email).first()
        
        if existing_patient:
            print(f"Test patient with email {patient_email} already exists.")
        else:
            # Create test patient
            patient_user = User(
                email=patient_email,
                password_hash=generate_password_hash("password123"),
                first_name="Test",
                last_name="Patient",
                role="patient"
            )
            
            db.session.add(patient_user)
            db.session.flush()  # To get the ID
            
            # Create patient profile
            patient = Patient(
                user=patient_user,
                birth_date=datetime.strptime("1990-01-01", "%Y-%m-%d").date(),
                gender="Homme",
                phone="0123456789",
                address="123 Rue Test, Ville Test",
                blood_type="A+",
                allergies="Aucune",
                chronic_diseases="Aucune",
                current_medications="Aucun",
                emergency_contact_name="Contact d'urgence",
                emergency_contact_phone="9876543210"
            )
            
            db.session.add(patient)
            print(f"Test patient created with email: {patient_email} and password: password123")
        
        if existing_doctor:
            print(f"Test doctor with email {doctor_email} already exists.")
        else:
            # Create test doctor
            doctor_user = User(
                email=doctor_email,
                password_hash=generate_password_hash("password123"),
                first_name="Test",
                last_name="Doctor",
                role="doctor"
            )
            
            db.session.add(doctor_user)
            db.session.flush()  # To get the ID
            
            # Create doctor profile
            doctor = Doctor(
                user=doctor_user,
                speciality="Médecin généraliste",
                license_number="12345",
                years_experience=10,
                education="Doctorat en médecine",
                bio="Médecin généraliste expérimenté",
                consultation_fee=50.0,
                phone="0123456789",
                address="456 Rue Test, Ville Test",
                languages="Français, Anglais",
                status="approved"
            )
            
            db.session.add(doctor)
            print(f"Test doctor created with email: {doctor_email} and password: password123")
        
        db.session.commit()
        print("Test users created successfully!")

if __name__ == "__main__":
    create_test_users()
