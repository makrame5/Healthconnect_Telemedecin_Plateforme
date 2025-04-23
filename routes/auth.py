from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User, Patient, Doctor
import json

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET'])
def register():
    return render_template('auth/register_choice.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'patient':
            return redirect(url_for('patient.dashboard'))
        elif current_user.role == 'doctor':
            return redirect(url_for('doctor.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')

            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                if user.role == 'patient':
                    next_page = url_for('patient.dashboard')
                elif user.role == 'doctor':
                    next_page = url_for('doctor.dashboard')

            return redirect(next_page)
        else:
            flash('Invalid email or password', 'danger')

    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@auth_bp.route('/register-patient')
def register_patient():
    return render_template('auth/register_patient.html')

@auth_bp.route('/register-doctor')
def register_doctor():
    return render_template('auth/register_doctor.html')

@auth_bp.route('/api/auth/register/patient', methods=['POST'])
def api_register_patient():
    try:
        # Get JSON data from request
        data = request.get_json()

        # Extract basic user information
        email = data.get('email')
        password = data.get('password')
        first_name = data.get('firstName')
        last_name = data.get('lastName')

        # Check if user already exists
        user = User.query.filter_by(email=email).first()
        if user:
            return jsonify({
                'success': False,
                'message': 'Cette adresse email est déjà utilisée.'
            }), 400

        # Create new user
        new_user = User(email=email, first_name=first_name, last_name=last_name, role='patient')
        new_user.set_password(password)
        db.session.add(new_user)

        # Create patient profile with additional information
        patient = Patient(
            user=new_user,
            birth_date=data.get('birthDate'),
            gender=data.get('gender'),
            phone=data.get('phone'),
            address=data.get('address'),
            id_number=data.get('idNumber'),
            insurance=data.get('insurance'),
            blood_type=data.get('bloodType'),
            allergies=data.get('allergies'),
            chronic_diseases=data.get('chronicDiseases'),
            current_medications=data.get('currentMedications'),
            emergency_contact_name=data.get('emergencyContactName'),
            emergency_contact_phone=data.get('emergencyContactPhone'),
            social_security_number=data.get('socialSecurityNumber')
        )
        db.session.add(patient)

        # Commit changes to database
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Votre compte a été créé avec succès !'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Une erreur est survenue lors de l\'inscription: {str(e)}'
        }), 500

@auth_bp.route('/api/auth/register/doctor', methods=['POST'])
def api_register_doctor():
    try:
        # Handle form data for file uploads
        data = {}
        for key in request.form:
            data[key] = request.form[key]

        # Extract basic user information
        email = data.get('email')
        password = data.get('password')
        first_name = data.get('firstName')
        last_name = data.get('lastName')

        # Check if user already exists
        user = User.query.filter_by(email=email).first()
        if user:
            return jsonify({
                'success': False,
                'message': 'Cette adresse email est déjà utilisée.'
            }), 400

        # Create new user
        new_user = User(email=email, first_name=first_name, last_name=last_name, role='doctor')
        new_user.set_password(password)
        db.session.add(new_user)

        # Create doctor profile with additional information
        doctor = Doctor(
            user=new_user,
            speciality=data.get('speciality'),
            license_number=data.get('licenseNumber'),
            years_experience=data.get('yearsExperience'),
            education=data.get('education'),
            bio=data.get('bio'),
            consultation_fee=data.get('consultationFee'),
            phone=data.get('phone'),
            address=data.get('address'),
            languages=data.get('languages'),
            status='pending'  # Doctors need approval before they can use the platform
        )
        db.session.add(doctor)

        # Handle file uploads
        if 'document' in request.files:
            document_file = request.files['document']
            # Save file logic here
            # This would typically involve saving to a file system or cloud storage
            # and storing the file path in the database

        if 'profilePicture' in request.files:
            profile_picture = request.files['profilePicture']
            # Save file logic here

        # Commit changes to database
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Votre compte a été créé avec succès ! Votre profil sera vérifié par notre équipe avant activation.'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Une erreur est survenue lors de l\'inscription: {str(e)}'
        }), 500
