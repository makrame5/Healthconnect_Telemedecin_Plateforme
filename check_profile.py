from app import app
from models import User, Doctor
from flask import Flask

with app.app_context():
    doctors = Doctor.query.all()
    for doctor in doctors:
        print(f"Doctor ID: {doctor.id}")
        print(f"User ID: {doctor.user_id}")
        print(f"Name: {User.query.get(doctor.user_id).first_name} {User.query.get(doctor.user_id).last_name}")
        print(f"Profile picture: {doctor.profile_picture}")
        print("-" * 50)
