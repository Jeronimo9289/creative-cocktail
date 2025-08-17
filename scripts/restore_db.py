# ================================
# scripts/restore_db.py
# ================================

"""Script de restauration de la base de données"""

import os
import subprocess
import sys
from app import create_app

def restore_database(backup_file):
    """Restaurer la base de données depuis un fichier de sauvegarde"""
    
    if not os.path.exists(backup_file):
        print(f"Fichier de sauvegarde non trouvé: {backup_file}")
        return False
    
    app = create_app()
    
    with app.app_context():
        database_url = app.config['SQLALCHEMY_DATABASE_URI']
        
        if 'mysql' in database_url:
            # Parser l'URL de la base de données
            parts = database_url.split('/')
            database = parts[-1]
            auth_host = parts[-2].split('@')
            host = auth_host[-1]
            user_pass = auth_host[0].split('//')[-1].split(':')
            user = user_pass[0]
            password = user_pass[1] if len(user_pass) > 1 else ''
            
            # Commande mysql pour restaurer
            cmd = [
                'mysql',
                '-h', host,
                '-u', user,
                f'-p{password}' if password else '',
                database
            ]
            
            cmd = [arg for arg in cmd if arg]
            
            try:
                with open(backup_file, 'r') as f:
                    subprocess.run(cmd, stdin=f, check=True)
                
                print(f"Base de données restaurée avec succès depuis: {backup_file}")
                return True
                
            except subprocess.CalledProcessError as e:
                print(f"Erreur lors de la restauration: {e}")
                return False
        else:
            print("Type de base de données non supporté pour la restauration")
            return False

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python restore_db.py <backup_file>")
        sys.exit(1)
    
    backup_file = sys.argv[1]
    success = restore_database(backup_file)
    sys.exit(0 if success else 1)