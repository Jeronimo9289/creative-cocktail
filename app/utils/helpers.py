# ================================
# app/utils/helpers.py
# ================================

from flask import current_app, url_for
from datetime import datetime, timedelta
import hashlib
import secrets
import re
from PIL import Image
import os

def generate_unique_filename(original_filename):
    """Générer un nom de fichier unique"""
    ext = os.path.splitext(original_filename)[1]
    unique_name = secrets.token_hex(16)
    return f"{unique_name}{ext}"

def resize_image(image_path, max_width=800, max_height=600):
    """Redimensionner une image"""
    try:
        with Image.open(image_path) as img:
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            img.save(image_path, optimize=True, quality=85)
        return True
    except Exception as e:
        current_app.logger.error(f"Erreur redimensionnement image: {e}")
        return False

def validate_email(email):
    """Valider un email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Valider un numéro de téléphone français"""
    # Supporte formats: 01.23.45.67.89, 01 23 45 67 89, 0123456789, +33123456789
    cleaned = re.sub(r'[^\d+]', '', phone)
    patterns = [
        r'^0[1-9](\d{8})$',  # Format français
        r'^\+33[1-9](\d{8})$',  # Format international
    ]
    return any(re.match(pattern, cleaned) for pattern in patterns)

def format_price(amount, currency='EUR'):
    """Formater un prix"""
    if amount is None:
        return "N/A"
    
    if currency == 'EUR':
        return f"{amount:.2f} €"
    else:
        return f"{amount:.2f} {currency}"

def calculate_event_progress(event):
    """Calculer le pourcentage d'avancement d'un événement"""
    total_steps = 8  # Nombre d'onglets
    completed_steps = 0
    
    # Vérifier chaque onglet
    if event.venues.count() > 0:
        completed_steps += 1
    if event.decorations.count() > 0:
        completed_steps += 1
    if event.transports.count() > 0:
        completed_steps += 1
    if event.catering.count() > 0:
        completed_steps += 1
    if event.activities.count() > 0:
        completed_steps += 1
    if event.communications.count() > 0:
        completed_steps += 1
    if event.technical.count() > 0:
        completed_steps += 1
    if event.participants.count() > 0:
        completed_steps += 1
    
    return int((completed_steps / total_steps) * 100)

def generate_qr_code(data, size=(200, 200)):
    """Générer un QR code"""
    try:
        import qrcode
        from io import BytesIO
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img = img.resize(size)
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return buffer
    except ImportError:
        current_app.logger.error("qrcode library not installed")
        return None

def sanitize_filename(filename):
    """Nettoyer un nom de fichier"""
    # Supprimer les caractères dangereux
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    # Limiter la longueur
    name, ext = os.path.splitext(filename)
    if len(name) > 50:
        name = name[:50]
    return f"{name}{ext}"

def get_file_hash(file_path):
    """Calculer le hash MD5 d'un fichier"""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except FileNotFoundError:
        return None

def format_datetime(dt, format_string='%d/%m/%Y %H:%M'):
    """Formater une datetime"""
    if dt is None:
        return "Non défini"
    return dt.strftime(format_string)

def calculate_age(birth_date):
    """Calculer l'âge depuis une date de naissance"""
    if birth_date is None:
        return None
    
    today = datetime.today()
    age = today.year - birth_date.year
    
    if today.month < birth_date.month or \
       (today.month == birth_date.month and today.day < birth_date.day):
        age -= 1
    
    return age

def generate_password(length=12):
    """Générer un mot de passe sécurisé"""
    import string
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def validate_password_strength(password):
    """Valider la force d'un mot de passe"""
    if len(password) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères"
    
    if not re.search(r'[A-Z]', password):
        return False, "Le mot de passe doit contenir au moins une majuscule"
    
    if not re.search(r'[a-z]', password):
        return False, "Le mot de passe doit contenir au moins une minuscule"
    
    if not re.search(r'\d', password):
        return False, "Le mot de passe doit contenir au moins un chiffre"
    
    return True, "Mot de passe valide"