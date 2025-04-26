from app import app, db
from models import Doctor, Availability
from datetime import date, time, timedelta

with app.app_context():
    # Récupérer tous les médecins
    doctors = Doctor.query.all()
    
    if not doctors:
        print("Aucun médecin trouvé dans la base de données.")
        exit()
    
    # Date de début (aujourd'hui)
    start_date = date.today()
    
    # Ajouter des disponibilités pour les 7 prochains jours
    for i in range(7):
        current_date = start_date + timedelta(days=i)
        
        # Pour chaque médecin
        for doctor in doctors:
            # Ajouter 2 créneaux par jour (matin et après-midi)
            morning_slot = Availability(
                doctor_id=doctor.id,
                date=current_date,
                start_time=time(9, 0),  # 9h00
                end_time=time(10, 0),   # 10h00
                status='available'
            )
            
            afternoon_slot = Availability(
                doctor_id=doctor.id,
                date=current_date,
                start_time=time(14, 0),  # 14h00
                end_time=time(15, 0),    # 15h00
                status='available'
            )
            
            db.session.add(morning_slot)
            db.session.add(afternoon_slot)
    
    # Enregistrer les modifications
    db.session.commit()
    print("Disponibilités ajoutées avec succès !")
