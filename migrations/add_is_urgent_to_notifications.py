"""
Migration script to add is_urgent column to notifications table
"""
from app import app, db
from flask_migrate import Migrate
from sqlalchemy import Column, Boolean

# Create a migration instance
migrate = Migrate(app, db)

def upgrade():
    """Add is_urgent column to notifications table"""
    with app.app_context():
        # Check if the column already exists
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('notification')]
        
        if 'is_urgent' not in columns:
            # Add the column
            db.engine.execute('ALTER TABLE notification ADD COLUMN is_urgent BOOLEAN DEFAULT FALSE')
            print("Added is_urgent column to notification table")
        else:
            print("is_urgent column already exists in notification table")

if __name__ == '__main__':
    upgrade()
