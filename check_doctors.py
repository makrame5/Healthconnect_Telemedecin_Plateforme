from app import app, db
from models import Doctor, User

with app.app_context():
    doctors = Doctor.query.all()
    print(f'Nombre de médecins: {len(doctors)}')
    for d in doctors:
        print(f'- Dr. {d.user.first_name} {d.user.last_name}, Spécialité: {d.speciality}, Status: {d.status}')
