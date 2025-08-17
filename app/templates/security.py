# ================================
# app/security.py
# ================================

from functools import wraps
from flask import request, jsonify, current_app, abort
from flask_login import current_user
import hashlib
import hmac
import time
from datetime import datetime, timedelta

class SecurityManager:
    """Gestionnaire de sécurité pour l'application"""
    
    @staticmethod
    def rate_limit_key(identifier):
        """Générer une clé pour le rate limiting"""
        return f"rate_limit:{identifier}:{int(time.time() // 60)}"
    
    @staticmethod
    def check_rate_limit(identifier, limit=60):
        """Vérifier le rate limiting"""
        # À implémenter avec Redis
        # Pour l'instant, retourne toujours True
        return True
    
    @staticmethod
    def validate_api_signature(signature, data, secret):
        """Valider une signature API"""
        expected = hmac.new(
            secret.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected)
    
    @staticmethod
    def sanitize_filename(filename):
        """Nettoyer un nom de fichier"""
        import re
        # Supprimer les caractères dangereux
        filename = re.sub(r'[^\w\-_\.]', '', filename)
        # Limiter la longueur
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1)
            filename = name[:250] + '.' + ext
        return filename
    
    @staticmethod
    def validate_file_type(filename, allowed_extensions):
        """Valider le type de fichier"""
        if '.' not in filename:
            return False
        
        extension = filename.rsplit('.', 1)[1].lower()
        return extension in allowed_extensions
    
    @staticmethod
    def generate_csrf_token():
        """Générer un token CSRF"""
        import secrets
        return secrets.token_hex(16)

def require_api_key(f):
    """Décorateur pour vérifier la clé API"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({'error': 'Clé API manquante'}), 401
        
        # Vérifier la clé API en base de données
        # Pour l'instant, on utilise une clé fixe
        if api_key != current_app.config.get('API_KEY'):
            return jsonify({'error': 'Clé API invalide'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

def require_admin(f):
    """Décorateur pour vérifier les droits administrateur"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def rate_limit(limit=60):
    """Décorateur pour le rate limiting"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Identifier l'utilisateur (IP ou user_id)
            identifier = request.remote_addr
            if current_user.is_authenticated:
                identifier = f"user:{current_user.id}"
            
            if not SecurityManager.check_rate_limit(identifier, limit):
                return jsonify({'error': 'Trop de requêtes'}), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator