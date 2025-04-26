from app import app, db
from models import Doctor, User, Availability
from datetime import date

with app.app_context():
    today = date.today()
    availabilities = Availability.query.filter(Availability.date >= today).all()
    print(f'Nombre de disponibilités futures: {len(availabilities)}')
    for a in availabilities:
        doctor = Doctor.query.get(a.doctor_id)
        doctor_name = f"Dr. {doctor.user.first_name} {doctor.user.last_name}" if doctor else "Unknown"
        print(f'- {doctor_name}, Date: {a.date}, Heure: {a.start_time}-{a.end_time}, Status: {a.status}')
