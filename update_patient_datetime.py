import re

# Lire le fichier
with open('routes/patient.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remplacer les occurrences de datetime.now()
content = content.replace('Appointment.date_time >= datetime.now()', 'Appointment.date_time >= get_current_time_naive()')
content = content.replace('now = datetime.now()', 'now = get_current_time_naive()')
content = content.replace('Appointment.date_time < datetime.now()', 'Appointment.date_time < get_current_time_naive()')

# Écrire le fichier mis à jour
with open('routes/patient.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Mise à jour terminée !")
