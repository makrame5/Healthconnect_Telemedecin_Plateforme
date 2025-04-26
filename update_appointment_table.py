import sqlite3

# Connexion à la base de données
conn = sqlite3.connect('healthconnect.db')
cursor = conn.cursor()

# Vérifier si les colonnes existent déjà
cursor.execute("PRAGMA table_info(appointment)")
columns = cursor.fetchall()
column_names = [column[1] for column in columns]

# Ajouter la colonne video_link si elle n'existe pas
if 'video_link' not in column_names:
    print("Ajout de la colonne video_link à la table appointment...")
    cursor.execute("ALTER TABLE appointment ADD COLUMN video_link TEXT")

# Ajouter la colonne video_room_id si elle n'existe pas
if 'video_room_id' not in column_names:
    print("Ajout de la colonne video_room_id à la table appointment...")
    cursor.execute("ALTER TABLE appointment ADD COLUMN video_room_id TEXT")

# Valider les modifications
conn.commit()

# Vérifier que les colonnes ont été ajoutées
cursor.execute("PRAGMA table_info(appointment)")
columns = cursor.fetchall()
column_names = [column[1] for column in columns]
print("Colonnes de la table appointment après mise à jour:", column_names)

# Fermer la connexion
conn.close()

print("Mise à jour de la base de données terminée avec succès!")
