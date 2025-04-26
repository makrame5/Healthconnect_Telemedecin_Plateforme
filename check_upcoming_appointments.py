"""
Script to check for upcoming appointments and send notifications
This script should be run every minute using a scheduler like cron
"""
from app import app, db
from socket_events import check_upcoming_appointments

# Run the check within the application context
with app.app_context():
    num_appointments = check_upcoming_appointments()
    print(f"Checked for upcoming appointments. Found {num_appointments} appointments starting in 5 minutes.")
