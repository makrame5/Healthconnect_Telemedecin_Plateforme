# HealthConnect - Plateforme de Télémédecine

HealthConnect est une plateforme de télémédecine qui permet aux patients de consulter des médecins en ligne via des consultations vidéo en temps réel.

## Fonctionnalités

- **Authentification** : Inscription et connexion pour les patients et les médecins
- **Dashboard Patient** : Liste des médecins disponibles et demande de consultation
- **Dashboard Médecin** : Gestion des demandes de consultation (accepter/refuser)
- **Consultation Vidéo** : Consultation en temps réel entre patient et médecin
- **Chat en Temps Réel** : Communication textuelle pendant la consultation
- **Prescriptions** : Création et gestion des prescriptions médicales

## Technologies Utilisées

- **Backend** : Flask (Python)
- **Base de Données** : SQLite
- **Frontend** : HTML, CSS, JavaScript
- **Vidéo Consultation** : Flask-SocketIO

## Installation

1. Cloner le dépôt :
   ```
   git clone https://github.com/votre-utilisateur/healthconnect.git
   cd healthconnect
   ```

2. Créer un environnement virtuel :
   ```
   python -m venv venv
   source venv/bin/activate  # Sur Windows : venv\Scripts\activate
   ```

3. Installer les dépendances :
   ```
   pip install -r requirements.txt
   ```

4. Lancer l'application :
   ```
   python app.py
   ```

5. Accéder à l'application dans votre navigateur :
   ```
   http://localhost:5000
   ```

## Structure du Projet

```
Healthconnect/
├── app.py                  # Application principale Flask
├── config.py               # Configuration
├── models.py               # Modèles de base de données
├── routes/                 # Routes de l'application
│   ├── __init__.py
│   ├── auth.py             # Routes d'authentification
│   ├── patient.py          # Routes pour les patients
│   └── doctor.py           # Routes pour les médecins
├── static/                 # Fichiers statiques
│   ├── css/                # Feuilles de style
│   ├── js/                 # Scripts JavaScript
│   └── images/             # Images
├── templates/              # Templates HTML
│   ├── base.html           # Template de base
│   ├── index.html          # Page d'accueil
│   ├── auth/               # Templates d'authentification
│   ├── patient/            # Templates pour les patients
│   └── doctor/             # Templates pour les médecins
└── requirements.txt        # Dépendances du projet
```

## Contributeurs

- [Votre Nom](https://github.com/votre-utilisateur)

## Licence

Ce projet est sous licence MIT.
