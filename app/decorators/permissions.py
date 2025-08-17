# ================================
# app/decorators/permissions.py
# ================================

from functools import wraps
from flask import current_user, abort, redirect, url_for, flash
from app.models.user import UserType

def admin_required(f):
    """Décorateur pour vérifier les droits administrateur"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('frontend.login'))
        
        if not current_user.is_admin:
            flash('Accès refusé. Droits administrateur requis.', 'error')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function

def provider_required(f):
    """Décorateur pour vérifier que l'utilisateur est un prestataire"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('frontend.login'))
        
        if current_user.user_type != UserType.PROVIDER:
            flash('Accès réservé aux prestataires.', 'error')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function

def event_owner_required(f):
    """Décorateur pour vérifier que l'utilisateur est propriétaire de l'événement"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('frontend.login'))
        
        # L'ID de l'événement doit être dans les arguments
        event_id = kwargs.get('id') or kwargs.get('event_id')
        if not event_id:
            abort(400, "ID d'événement manquant")
        
        from app.models.event import Event
        event = Event.query.get_or_404(event_id)
        
        if event.organizer_id != current_user.id and not current_user.is_admin:
            flash('Accès refusé. Vous n\'êtes pas le propriétaire de cet événement.', 'error')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function

def rate_limit(max_requests=10, window_minutes=15):
    """Décorateur de rate limiting"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Dans un vrai système, on utiliserait Redis
            # Ici c'est une implémentation simplifiée
            from flask import request, session
            
            key = f"rate_limit_{request.remote_addr}_{f.__name__}"
            now = datetime.utcnow()
            
            if key not in session:
                session[key] = []
            
            # Nettoyer les anciennes requêtes
            cutoff = now - timedelta(minutes=window_minutes)
            session[key] = [
                req_time for req_time in session[key] 
                if datetime.fromisoformat(req_time) > cutoff
            ]
            
            # Vérifier la limite
            if len(session[key]) >= max_requests:
                abort(429, "Trop de requêtes. Veuillez réessayer plus tard.")
            
            # Ajouter la requête actuelle
            session[key].append(now.isoformat())
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator