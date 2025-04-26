from app import app, db
from models import User, Doctor, Patient, Appointment, Prescription

def add_doctor_profile_columns():
    """Ajoute les nouvelles colonnes au modèle Doctor"""
    with app.app_context():
        # Vérifier si les colonnes existent déjà
        columns = db.engine.execute("PRAGMA table_info(doctor)").fetchall()
        column_names = [column[1] for column in columns]
        
        # Liste des nouvelles colonnes à ajouter
        new_columns = {
            "secondary_speciality": "VARCHAR(100)",
            "practice_location": "VARCHAR(200)",
            "previous_positions": "TEXT",
            "linkedin": "VARCHAR(200)",
            "website": "VARCHAR(200)",
            "available_days": "VARCHAR(100)",
            "available_hours": "VARCHAR(200)",
            "video_consultation": "BOOLEAN DEFAULT 1",
            "email_notifications": "BOOLEAN DEFAULT 1",
            "sms_notifications": "BOOLEAN DEFAULT 0",
            "do_not_disturb": "BOOLEAN DEFAULT 0"
        }
        
        # Ajouter les colonnes manquantes
        for column_name, column_type in new_columns.items():
            if column_name not in column_names:
                print(f"Ajout de la colonne {column_name} à la table doctor")
                db.engine.execute(f"ALTER TABLE doctor ADD COLUMN {column_name} {column_type}")
            else:
                print(f"La colonne {column_name} existe déjà dans la table doctor")
        
        print("Migration terminée avec succès!")

if __name__ == "__main__":
    add_doctor_profile_columns()
