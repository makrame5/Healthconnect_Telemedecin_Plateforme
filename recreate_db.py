from app import app
from extensions import db
from models import User, Patient, Doctor, Appointment, Prescription

# Drop and recreate all tables
with app.app_context():
    db.drop_all()
    db.create_all()
    print("Database tables have been recreated successfully!")
