# Lire le contenu du fichier
with open('routes/doctor.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Ajouter la nouvelle route à la fin du fichier
new_route = """
@doctor_bp.route('/save_notes/<int:appointment_id>', methods=['POST'])
@login_required
def save_notes(appointment_id):
    # Vérifier que l'utilisateur est un médecin
    if current_user.role != 'doctor':
        flash('Accès refusé. Vous devez être un médecin pour voir cette page.', 'danger')
        return redirect(url_for('index'))
    
    # Récupérer le rendez-vous
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Vérifier que le rendez-vous appartient au médecin connecté
    if appointment.doctor_id != current_user.doctor.id:
        flash('Accès refusé. Ce rendez-vous ne vous appartient pas.', 'danger')
        return redirect(url_for('doctor.dashboard'))
    
    # Récupérer les notes du formulaire
    notes = request.form.get('notes', '')
    
    # Enregistrer les notes
    appointment.notes = notes
    db.session.commit()
    
    flash('Notes enregistrées avec succès.', 'success')
    return redirect(url_for('doctor.consultation', appointment_id=appointment_id))
"""

# Écrire le contenu mis à jour
with open('routes/doctor.py', 'w', encoding='utf-8') as f:
    f.write(content + new_route)

print("Route ajoutée avec succès !")
