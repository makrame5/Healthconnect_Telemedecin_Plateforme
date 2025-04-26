from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Availability
from datetime import date

debug_bp = Blueprint('debug', __name__, url_prefix='/debug')

@debug_bp.route('/doctor/availability')
@login_required
def doctor_availability():
    if current_user.role != 'doctor':
        return jsonify({'error': 'Access denied. You must be a doctor to view this page.'}), 403
    
    doctor = current_user.doctor
    today = date.today()
    
    # Récupérer les disponibilités futures du médecin
    availabilities = Availability.query.filter(
        Availability.doctor_id == doctor.id,
        Availability.date >= today
    ).order_by(Availability.date, Availability.start_time).all()
    
    # Organiser les disponibilités par date et statut
    availability_stats = {
        'total': len(availabilities),
        'available': 0,
        'booked': 0,
        'other': 0,
        'by_date': {}
    }
    
    for avail in availabilities:
        date_str = avail.date.strftime('%Y-%m-%d')
        
        if date_str not in availability_stats['by_date']:
            availability_stats['by_date'][date_str] = {
                'total': 0,
                'available': 0,
                'booked': 0,
                'other': 0
            }
        
        availability_stats['by_date'][date_str]['total'] += 1
        
        if avail.status == 'available':
            availability_stats['available'] += 1
            availability_stats['by_date'][date_str]['available'] += 1
        elif avail.status == 'booked':
            availability_stats['booked'] += 1
            availability_stats['by_date'][date_str]['booked'] += 1
        else:
            availability_stats['other'] += 1
            availability_stats['by_date'][date_str]['other'] += 1
    
    # Récupérer les informations de disponibilité du médecin
    doctor_info = {
        'id': doctor.id,
        'name': f"{current_user.first_name} {current_user.last_name}",
        'available_days': doctor.available_days,
        'available_hours': doctor.available_hours,
        'video_consultation': doctor.video_consultation
    }
    
    # Créer une réponse JSON pour le débogage
    debug_info = {
        'doctor': doctor_info,
        'availability_stats': availability_stats,
        'availabilities': [
            {
                'id': avail.id,
                'date': avail.date.strftime('%Y-%m-%d'),
                'start_time': avail.start_time.strftime('%H:%M'),
                'end_time': avail.end_time.strftime('%H:%M'),
                'status': avail.status
            }
            for avail in availabilities
        ]
    }
    
    return jsonify(debug_info)

@debug_bp.route('/doctor/availability/html')
@login_required
def doctor_availability_html():
    if current_user.role != 'doctor':
        return jsonify({'error': 'Access denied. You must be a doctor to view this page.'}), 403
    
    doctor = current_user.doctor
    today = date.today()
    
    # Récupérer les disponibilités futures du médecin
    availabilities = Availability.query.filter(
        Availability.doctor_id == doctor.id,
        Availability.date >= today
    ).order_by(Availability.date, Availability.start_time).all()
    
    # Organiser les disponibilités par date et statut
    availability_stats = {
        'total': len(availabilities),
        'available': 0,
        'booked': 0,
        'other': 0,
        'by_date': {}
    }
    
    for avail in availabilities:
        date_str = avail.date.strftime('%Y-%m-%d')
        
        if date_str not in availability_stats['by_date']:
            availability_stats['by_date'][date_str] = {
                'total': 0,
                'available': 0,
                'booked': 0,
                'other': 0
            }
        
        availability_stats['by_date'][date_str]['total'] += 1
        
        if avail.status == 'available':
            availability_stats['available'] += 1
            availability_stats['by_date'][date_str]['available'] += 1
        elif avail.status == 'booked':
            availability_stats['booked'] += 1
            availability_stats['by_date'][date_str]['booked'] += 1
        else:
            availability_stats['other'] += 1
            availability_stats['by_date'][date_str]['other'] += 1
    
    # Récupérer les informations de disponibilité du médecin
    doctor_info = {
        'id': doctor.id,
        'name': f"{current_user.first_name} {current_user.last_name}",
        'available_days': doctor.available_days,
        'available_hours': doctor.available_hours,
        'video_consultation': doctor.video_consultation
    }
    
    return render_template('doctor/debug_availability.html', 
                          doctor=doctor_info,
                          availability_stats=availability_stats,
                          availabilities=availabilities)
