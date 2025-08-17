# ================================
# scripts/backup_db.py
# ================================

"""Script de sauvegarde de la base de données"""

import os
import subprocess
from datetime import datetime
from app import create_app

def backup_database():
    """Créer une sauvegarde de la base de données"""
    
    app = create_app()
    
    with app.app_context():
        # Récupérer les informations de connexion
        database_url = app.config['SQLALCHEMY_DATABASE_URI']
        
        # Parser l'URL de la base de données
        # Format: mysql+pymysql://user:password@host/database
        if 'mysql' in database_url:
            # Extraire les informations de connexion
            parts = database_url.split('/')
            database = parts[-1]
            auth_host = parts[-2].split('@')
            host = auth_host[-1]
            user_pass = auth_host[0].split('//')[-1].split(':')
            user = user_pass[0]
            password = user_pass[1] if len(user_pass) > 1 else ''
            
            # Créer le nom du fichier de sauvegarde
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = f'backup_creative_cocktail_{timestamp}.sql'
            backup_path = os.path.join('backups', backup_file)
            
            # Créer le répertoire s'il n'existe pas
            os.makedirs('backups', exist_ok=True)
            
            # Commande mysqldump
            cmd = [
                'mysqldump',
                '-h', host,
                '-u', user,
                f'-p{password}' if password else '',
                '--single-transaction',
                '--routines',
                '--triggers',
                database
            ]
            
            # Filtrer les éléments vides
            cmd = [arg for arg in cmd if arg]
            
            try:
                with open(backup_path, 'w') as f:
                    subprocess.run(cmd, stdout=f, check=True)
                
                print(f"Sauvegarde créée avec succès: {backup_path}")
                return backup_path
                
            except subprocess.CalledProcessError as e:
                print(f"Erreur lors de la sauvegarde: {e}")
                return None
        else:
            print("Type de base de données non supporté pour la sauvegarde")
            return None

if __name__ == '__main__':
    backup_database()