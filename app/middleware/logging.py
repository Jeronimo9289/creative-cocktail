# ================================
# app/middleware/logging.py
# ================================

import logging
from flask import request, g
import time
import json

class RequestLoggingMiddleware:
    """Middleware de logging des requêtes"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialiser le middleware"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        
        # Configurer le logger
        self.setup_logging(app)
    
    def setup_logging(self, app):
        """Configuration du logging"""
        if not app.debug:
            # Configuration pour la production
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s %(levelname)s %(name)s %(message)s'
            )
            
            # Logger pour les requêtes
            self.request_logger = logging.getLogger('requests')
            handler = logging.FileHandler('logs/requests.log')
            handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s %(message)s'
            ))
            self.request_logger.addHandler(handler)
        else:
            self.request_logger = app.logger
    
    def before_request(self):
        """Avant chaque requête"""
        g.start_time = time.time()
        
        # Logger les requêtes sensibles
        if request.method in ['POST', 'PUT', 'DELETE']:
            self.request_logger.info(
                f"Request started: {request.method} {request.path} "
                f"from {request.remote_addr}"
            )
    
    def after_request(self, response):
        """Après chaque requête"""
        duration = time.time() - g.get('start_time', time.time())
        
        # Logger la réponse
        log_data = {
            'method': request.method,
            'path': request.path,
            'status': response.status_code,
            'duration': round(duration * 1000, 2),  # en ms
            'ip': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
        }
        
        # Ajouter l'utilisateur si connecté
        if hasattr(g, 'current_user') and g.current_user.is_authenticated:
            log_data['user_id'] = g.current_user.id
        
        self.request_logger.info(json.dumps(log_data))
        
        # Alerter pour les requêtes lentes
        if duration > 2.0:  # Plus de 2 secondes
            self.request_logger.warning(
                f"Slow request: {request.method} {request.path} "
                f"took {duration:.2f}s"
            )
        
        return response