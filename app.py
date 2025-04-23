from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import current_user
import os

# Import extensions
from extensions import db, login_manager

# Import models
from models import User, Patient, Doctor, Appointment, Prescription

# Initialize Flask app
app = Flask(__name__)
app.config.from_object('config.Config')

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create database tables
with app.app_context():
    db.create_all()

# Register blueprints
from routes.auth import auth_bp
from routes.patient import patient_bp
from routes.doctor import doctor_bp

app.register_blueprint(auth_bp)
app.register_blueprint(patient_bp)
app.register_blueprint(doctor_bp)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
