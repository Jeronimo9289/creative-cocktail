# ================================
# scripts/production_setup.py
# ================================

"""Script de configuration pour la production"""

import os
import sys
from pathlib import Path

def setup_production():
    """Configurer l'environnement de production"""
    
    print("🚀 Configuration de Creative Cocktail pour la production")
    
    # Créer les dossiers nécessaires
    folders = [
        'logs',
        'backups', 
        'app/static/uploads',
        'ssl'
    ]
    
    for folder in folders:
        Path(folder).mkdir(parents=True, exist_ok=True)
        print(f"✅ Dossier créé: {folder}")
    
    # Vérifier les variables d'environnement critiques
    required_vars = [
        'SECRET_KEY',
        'DATABASE_URL',
        'MAIL_USERNAME',
        'MAIL_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Variables d'environnement manquantes: {', '.join(missing_vars)}")
        print("Veuillez configurer ces variables avant de continuer.")
        sys.exit(1)
    
    # Vérifier les permissions
    upload_dir = Path('app/static/uploads')
    if not os.access(upload_dir, os.W_OK):
        print("❌ Permissions d'écriture manquantes sur le dossier uploads")
        sys.exit(1)
    
    print("✅ Configuration terminée avec succès!")
    print("\nPour démarrer l'application:")
    print("docker-compose up -d")

if __name__ == '__main__':
    setup_production()