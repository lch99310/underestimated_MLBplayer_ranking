# setup.py
import os
from pathlib import Path

def create_project_structure():
    """Create a simplified project directory structure"""
    # Create main directories
    directories = [
        "data/raw",
        "data/processed",
        "data/plots"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    # Create requirements.txt
    requirements_content = """pandas>=1.5.0
numpy>=1.20.0
matplotlib>=3.5.0
pybaseball>=2.2.0
"""
    
    with open("requirements.txt", "w") as f:
        f.write(requirements_content)
    
    print("Project structure created successfully!")
    print("\nNext steps:")
    print("1. python -m venv venv")
    print("2. source venv/bin/activate")
    print("3. pip install --upgrade pip")
    print("4. pip install -r requirements.txt")

if __name__ == "__main__":
    create_project_structure()