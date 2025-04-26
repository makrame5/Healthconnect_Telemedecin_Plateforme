import re

# Lire le fichier
with open('routes/doctor.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remplacer les occurrences de datetime.now()
content = re.sub(r'datetime\.now\(\)\.timestamp\(\)', r'get_current_time().timestamp()', content)
content = re.sub(r'datetime\.now\(\)\.date\(\)', r'get_current_time_naive().date()', content)
content = re.sub(r'datetime\.now\(\)\.strftime', r'get_current_time().strftime', content)
content = re.sub(r'datetime\.combine\(today, datetime\.min\.time\(\)\)', r'datetime.combine(today, datetime.min.time())', content)
content = re.sub(r'datetime\.combine\(today, datetime\.max\.time\(\)\)', r'datetime.combine(today, datetime.max.time())', content)

# Écrire le fichier mis à jour
with open('routes/doctor.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Mise à jour terminée !")
