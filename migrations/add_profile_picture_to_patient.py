import sqlite3
import os

# Chemin vers la base de données
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'healthconnect.db')

# Vérifier si le fichier de base de données existe
if not os.path.exists(db_path):
    print(f"La base de données n'existe pas à l'emplacement: {db_path}")
    exit(1)

# Connexion à la base de données
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Vérifier si la colonne existe déjà
cursor.execute("PRAGMA table_info(patient)")
columns = cursor.fetchall()
column_names = [column[1] for column in columns]

if 'profile_picture' not in column_names:
    print("Ajout de la colonne 'profile_picture' à la table 'patient'...")

    # Ajouter la colonne
    cursor.execute("ALTER TABLE patient ADD COLUMN profile_picture TEXT")

    # Valider les modifications
    conn.commit()
    print("Colonne ajoutée avec succès!")
else:
    print("La colonne 'profile_picture' existe déjà dans la table 'patient'.")

# Fermer la connexion
conn.close()
