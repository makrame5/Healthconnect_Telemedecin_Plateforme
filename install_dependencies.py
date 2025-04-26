"""
Script to install required dependencies for the appointment reminder system
"""
import subprocess
import sys

def install_dependencies():
    """Install required dependencies"""
    dependencies = [
        'schedule',  # For scheduling tasks
    ]
    
    print("Installing dependencies...")
    for dependency in dependencies:
        print(f"Installing {dependency}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", dependency])
    
    print("All dependencies installed successfully!")

if __name__ == '__main__':
    install_dependencies()
