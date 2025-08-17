# ================================
# app/security/security_utils.py
# ================================

from functools import wraps
from flask import request, jsonify, current_app, abort
from flask_login import current_user
import hashlib
import hmac
import time
import jwt
from datetime import datetime, timedelta
import re

class SecurityManager:
    """Gestionnaire de sécurité de l'application"""
    
    @staticmethod
    def rate_limit_key(identifier, endpoint):
        """Générer une clé pour le rate limiting"""
        return f"rate_limit:{identifier}:{endpoint}:{int(time.time() // 60)}"
    
    @staticmethod
    def check_rate_limit(identifier, endpoint, limit=60):
        """Vérifier les limites de taux (rate limiting)"""
        from app import redis_client
        
        key = SecurityManager.rate_limit_key(identifier, endpoint)
        current_requests = redis_client.get(key)
        
        if current_requests is None:
            redis_client.setex(key, 60, 1)
            return True
        
        if int(current_requests) >= limit:
            return False
        
        redis_client.incr(key)
        return True
    
    @staticmethod
    def validate_password_strength(password):
        """Valider la force d'un mot de passe"""
        errors = []
        
        if len(password) < 8:
            errors.append("Le mot de passe doit contenir au moins 8 caractères")
        
        if not re.search(r"[A-Z]", password):
            errors.append("Le mot de passe doit contenir au moins une majuscule")
        
        if not re.search(r"[a-z]", password):
            errors.append("Le mot de passe doit contenir au moins une minuscule")
        
        if not re.search(r"\d", password):
            errors.append("Le mot de passe doit contenir au moins un chiffre")
        
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            errors.append("Le mot de passe doit contenir au moins un caractère spécial")
        
        # Vérifier les mots de passe communs
        common_passwords = [
            'password', '123456', 'password123', 'admin', 'qwerty',
            'letmein', 'welcome', 'monkey', '1234567890'
        ]
        
        if password.lower() in common_passwords:
            errors.append("Ce mot de passe est trop commun")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def sanitize_filename(filename):
        """Nettoyer un nom de fichier pour éviter les injections"""
        # Supprimer les caractères dangereux
        filename = re.sub(r'[^\w\s.-]', '', filename)
        # Limiter la longueur
        filename = filename[:100]
        # Éviter les noms réservés
        reserved = ['CON', 'PRN', 'AUX', 'NUL'] + [f'COM{i}' for i in range(1, 10)] + [f'LPT{i}' for i in range(1, 10)]
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        if name.upper() in reserved:
            name = f"file_{name}"
        return f"{name}.{ext}" if ext else name
    
    @staticmethod
    def generate_csrf_token():
        """Générer un token CSRF"""
        return hmac.new(
            current_app.config['SECRET_KEY'].encode(),
            f"{current_user.id if current_user.is_authenticated else 'anonymous'}:{time.time()}".encode(),
            hashlib.sha256
        ).hexdigest()
    
    @staticmethod
    def verify_csrf_token(token):
        """Vérifier un token CSRF"""
        # Implémentation simplifiée - utiliser Flask-WTF en production
        return True

def rate_limit(limit=60, window=60):
    """Décorateur pour limiter le taux de requêtes"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            identifier = request.remote_addr
            if current_user.is_authenticated:
                identifier = f"user_{current_user.id}"
            
            endpoint = f"{request.endpoint}"
            
            if not SecurityManager.check_rate_limit(identifier, endpoint, limit):
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Maximum {limit} requests per {window} seconds'
                }), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_api_key(f):
    """Décorateur pour vérifier une clé API"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        # Vérifier la clé API (à implémenter selon vos besoins)
        valid_keys = current_app.config.get('API_KEYS', [])
        if api_key not in valid_keys:
            return jsonify({'error': 'Invalid API key'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

def validate_json_schema(schema):
    """Décorateur pour valider le schéma JSON des requêtes"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400
            
            try:
                data = request.get_json()
                # Ici vous pourriez utiliser jsonschema pour une validation plus robuste
                for field in schema.get('required', []):
                    if field not in data:
                        return jsonify({'error': f'Missing required field: {field}'}), 400
                
                request.validated_json = data
                return f(*args, **kwargs)
                
            except Exception as e:
                return jsonify({'error': 'Invalid JSON format'}), 400
        return decorated_function
    return decorator

# ================================
# app/monitoring/logging_config.py
# ================================

import logging
import logging.handlers
import os
from datetime import datetime
from flask import request, current_user, has_request_context
import json

class CustomFormatter(logging.Formatter):
    """Formateur de logs personnalisé avec informations contextuelles"""
    
    def format(self, record):
        # Ajouter des informations contextuelles
        if has_request_context():
            record.url = request.url
            record.method = request.method
            record.ip = request.remote_addr
            record.user_agent = request.headers.get('User-Agent', '')
            
            if current_user.is_authenticated:
                record.user_id = current_user.id
                record.username = current_user.username
            else:
                record.user_id = None
                record.username = 'anonymous'
        else:
            record.url = None
            record.method = None
            record.ip = None
            record.user_agent = None
            record.user_id = None
            record.username = None
        
        return super().format(record)

def setup_logging(app):
    """Configuration du système de logging"""
    
    # Créer le répertoire de logs
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    # Format des logs
    formatter = CustomFormatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s '
        '[%(method)s %(url)s] [User: %(username)s] [IP: %(ip)s]'
    )
    
    # Logger principal de l'application
    file_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(log_dir, 'creative_cocktail.log'),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    # Logger pour les erreurs
    error_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(log_dir, 'errors.log'),
        maxBytes=10 * 1024 * 1024,
        backupCount=5
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    
    # Logger pour les accès
    access_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(log_dir, 'access.log'),
        maxBytes=10 * 1024 * 1024,
        backupCount=10
    )
    access_formatter = logging.Formatter(
        '%(asctime)s - %(ip)s - "%(method)s %(url)s" - %(status_code)s - %(username)s'
    )
    access_handler.setFormatter(access_formatter)
    
    # Ajouter les handlers
    app.logger.addHandler(file_handler)
    app.logger.addHandler(error_handler)
    app.logger.setLevel(logging.INFO)
    
    # Logger spécifique pour les accès
    access_logger = logging.getLogger('access')
    access_logger.addHandler(access_handler)
    access_logger.setLevel(logging.INFO)
    
    # Logger pour les actions de sécurité
    security_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(log_dir, 'security.log'),
        maxBytes=5 * 1024 * 1024,
        backupCount=5
    )
    security_handler.setFormatter(formatter)
    
    security_logger = logging.getLogger('security')
    security_logger.addHandler(security_handler)
    security_logger.setLevel(logging.WARNING)
    
    return app.logger

def log_user_action(action, details=None):
    """Logger une action utilisateur"""
    logger = logging.getLogger('security')
    
    log_data = {
        'action': action,
        'timestamp': datetime.utcnow().isoformat(),
        'details': details or {}
    }
    
    if has_request_context():
        log_data.update({
            'ip': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
            'url': request.url,
            'method': request.method
        })
        
        if current_user.is_authenticated:
            log_data.update({
                'user_id': current_user.id,
                'username': current_user.username
            })
    
    logger.info(f"User action: {json.dumps(log_data)}")

# ================================
# app/monitoring/metrics.py
# ================================

from flask import g
import time
import psutil
import threading
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json

class MetricsCollector:
    """Collecteur de métriques de performance"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.request_times = deque(maxlen=1000)
        self.error_counts = defaultdict(int)
        self.endpoint_stats = defaultdict(lambda: {'count': 0, 'total_time': 0})
        self._lock = threading.Lock()
    
    def record_request_time(self, endpoint, duration):
        """Enregistrer le temps de traitement d'une requête"""
        with self._lock:
            self.request_times.append({
                'endpoint': endpoint,
                'duration': duration,
                'timestamp': datetime.utcnow()
            })
            
            self.endpoint_stats[endpoint]['count'] += 1
            self.endpoint_stats[endpoint]['total_time'] += duration
    
    def record_error(self, error_type, endpoint=None):
        """Enregistrer une erreur"""
        with self._lock:
            key = f"{error_type}:{endpoint}" if endpoint else error_type
            self.error_counts[key] += 1
    
    def get_system_metrics(self):
        """Récupérer les métriques système"""
        return {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_request_metrics(self):
        """Récupérer les métriques de requêtes"""
        with self._lock:
            if not self.request_times:
                return {}
            
            recent_requests = [
                r for r in self.request_times 
                if r['timestamp'] > datetime.utcnow() - timedelta(minutes=5)
            ]
            
            if not recent_requests:
                return {}
            
            durations = [r['duration'] for r in recent_requests]
            
            return {
                'request_count': len(recent_requests),
                'avg_response_time': sum(durations) / len(durations),
                'max_response_time': max(durations),
                'min_response_time': min(durations),
                'requests_per_minute': len(recent_requests) / 5
            }
    
    def get_endpoint_stats(self):
        """Récupérer les statistiques par endpoint"""
        with self._lock:
            stats = {}
            for endpoint, data in self.endpoint_stats.items():
                if data['count'] > 0:
                    stats[endpoint] = {
                        'count': data['count'],
                        'avg_time': data['total_time'] / data['count']
                    }
            return stats
    
    def get_error_stats(self):
        """Récupérer les statistiques d'erreurs"""
        with self._lock:
            return dict(self.error_counts)

# Instance globale du collecteur
metrics_collector = MetricsCollector()

def track_request_metrics(f):
    """Décorateur pour tracker les métriques de requêtes"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = f(*args, **kwargs)
            return result
        except Exception as e:
            metrics_collector.record_error(type(e).__name__, request.endpoint)
            raise
        finally:
            duration = time.time() - start_time
            metrics_collector.record_request_time(request.endpoint, duration)
    
    return decorated_function

# ================================
# app/monitoring/health_check.py
# ================================

from flask import Blueprint, jsonify
from app import db
import redis
import os

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
    """Check de santé global de l'application"""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'checks': {}
    }
    
    # Vérifier la base de données
    try:
        db.session.execute('SELECT 1')
        health_status['checks']['database'] = {'status': 'healthy'}
    except Exception as e:
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_status['status'] = 'unhealthy'
    
    # Vérifier Redis
    try:
        from app import redis_client
        redis_client.ping()
        health_status['checks']['redis'] = {'status': 'healthy'}
    except Exception as e:
        health_status['checks']['redis'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_status['status'] = 'degraded'
    
    # Vérifier l'espace disque
    try:
        disk_usage = psutil.disk_usage('/').percent
        if disk_usage > 90:
            health_status['checks']['disk'] = {
                'status': 'warning',
                'usage_percent': disk_usage
            }
        else:
            health_status['checks']['disk'] = {
                'status': 'healthy',
                'usage_percent': disk_usage
            }
    except Exception as e:
        health_status['checks']['disk'] = {
            'status': 'unknown',
            'error': str(e)
        }
    
    # Vérifier la mémoire
    try:
        memory_usage = psutil.virtual_memory().percent
        if memory_usage > 85:
            health_status['checks']['memory'] = {
                'status': 'warning',
                'usage_percent': memory_usage
            }
        else:
            health_status['checks']['memory'] = {
                'status': 'healthy',
                'usage_percent': memory_usage
            }
    except Exception as e:
        health_status['checks']['memory'] = {
            'status': 'unknown',
            'error': str(e)
        }
    
    status_code = 200
    if health_status['status'] == 'unhealthy':
        status_code = 503
    elif health_status['status'] == 'degraded':
        status_code = 206
    
    return jsonify(health_status), status_code

@health_bp.route('/metrics')
def metrics():
    """Endpoint pour les métriques de monitoring"""
    from app.monitoring.metrics import metrics_collector
    
    return jsonify({
        'system': metrics_collector.get_system_metrics(),
        'requests': metrics_collector.get_request_metrics(),
        'endpoints': metrics_collector.get_endpoint_stats(),
        'errors': metrics_collector.get_error_stats()
    })

# ================================
# app/cache/cache_manager.py
# ================================

from flask import current_app
import json
import hashlib
from functools import wraps
import pickle

class CacheManager:
    """Gestionnaire de cache centralisé"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.default_timeout = 300  # 5 minutes
    
    def _make_key(self, key, prefix='app'):
        """Créer une clé de cache normalisée"""
        return f"{prefix}:{key}"
    
    def get(self, key, prefix='app'):
        """Récupérer une valeur du cache"""
        cache_key = self._make_key(key, prefix)
        value = self.redis.get(cache_key)
        
        if value is None:
            return None
        
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            try:
                return pickle.loads(value)
            except:
                return value.decode('utf-8') if isinstance(value, bytes) else value
    
    def set(self, key, value, timeout=None, prefix='app'):
        """Stocker une valeur dans le cache"""
        cache_key = self._make_key(key, prefix)
        timeout = timeout or self.default_timeout
        
        try:
            serialized_value = json.dumps(value)
        except (TypeError, ValueError):
            try:
                serialized_value = pickle.dumps(value)
            except:
                serialized_value = str(value)
        
        return self.redis.setex(cache_key, timeout, serialized_value)
    
    def delete(self, key, prefix='app'):
        """Supprimer une valeur du cache"""
        cache_key = self._make_key(key, prefix)
        return self.redis.delete(cache_key)
    
    def clear_pattern(self, pattern, prefix='app'):
        """Supprimer toutes les clés correspondant à un pattern"""
        pattern_key = self._make_key(pattern, prefix)
        keys = self.redis.keys(pattern_key)
        if keys:
            return self.redis.delete(*keys)
        return 0
    
    def cache_key_for_request(self, *args, **kwargs):
        """Générer une clé de cache pour une requête"""
        key_data = {
            'args': args,
            'kwargs': kwargs,
            'user_id': getattr(current_user, 'id', None) if 'current_user' in globals() else None
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()

def cached(timeout=300, key_prefix='view', unless=None):
    """Décorateur pour mettre en cache le résultat d'une fonction"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from app import cache_manager
            
            # Vérifier la condition unless
            if unless and unless():
                return f(*args, **kwargs)
            
            # Générer la clé de cache
            cache_key = f"{f.__name__}:{cache_manager.cache_key_for_request(*args, **kwargs)}"
            
            # Essayer de récupérer du cache
            cached_result = cache_manager.get(cache_key, key_prefix)
            if cached_result is not None:
                return cached_result
            
            # Exécuter la fonction et mettre en cache
            result = f(*args, **kwargs)
            cache_manager.set(cache_key, result, timeout, key_prefix)
            
            return result
        return decorated_function
    return decorator

# ================================
# app/tasks/celery_tasks.py
# ================================

from celery import Celery
from app import create_app, db
from app.models.notification import Notification
from app.services.notification_service import NotificationService
from app.services.newsletter_service import NewsletterService
import os

# Configuration Celery
def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    
    celery.conf.update(app.config)
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery

# Créer l'instance Celery
app = create_app()
celery = make_celery(app)

@celery.task(bind=True)
def send_email_notification(self, notification_id):
    """Tâche pour envoyer une notification par email"""
    try:
        notification = Notification.query.get(notification_id)
        if notification and not notification.is_email_sent:
            NotificationService.send_email_notification(notification)
        return f"Email sent for notification {notification_id}"
    except Exception as exc:
        self.retry(exc=exc, countdown=60, max_retries=3)

@celery.task(bind=True)
def send_newsletter_campaign(self, campaign_id):
    """Tâche pour envoyer une campagne de newsletter"""
    try:
        NewsletterService.send_campaign(campaign_id)
        return f"Newsletter campaign {campaign_id} sent successfully"
    except Exception as exc:
        self.retry(exc=exc, countdown=300, max_retries=2)

@celery.task
def cleanup_old_notifications():
    """Nettoyer les anciennes notifications"""
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=30)
    
    old_notifications = Notification.query.filter(
        Notification.created_at < cutoff_date,
        Notification.is_read == True
    ).all()
    
    count = len(old_notifications)
    
    for notification in old_notifications:
        db.session.delete(notification)
    
    db.session.commit()
    
    return f"Deleted {count} old notifications"

@celery.task
def generate_daily_reports():
    """Générer les rapports quotidiens"""
    from app.services.statistics_service import StatisticsService
    
    # Générer statistiques quotidiennes
    stats = StatisticsService.get_dashboard_stats()
    
    # Ici vous pourriez envoyer un rapport par email aux administrateurs
    # ou sauvegarder les statistiques dans une table dédiée
    
    return f"Daily report generated: {stats}"

@celery.task
def backup_database():
    """Tâche de sauvegarde de la base de données"""
    try:
        from scripts.backup_db import backup_database
        backup_file = backup_database()
        return f"Database backup created: {backup_file}"
    except Exception as e:
        return f"Backup failed: {str(e)}"

# Configuration des tâches périodiques
from celery.schedules import crontab

celery.conf.beat_schedule = {
    'cleanup-notifications': {
        'task': 'app.tasks.celery_tasks.cleanup_old_notifications',
        'schedule': crontab(hour=2, minute=0),  # Tous les jours à 2h
    },
    'daily-reports': {
        'task': 'app.tasks.celery_tasks.generate_daily_reports',
        'schedule': crontab(hour=6, minute=0),  # Tous les jours à 6h
    },
    'backup-database': {
        'task': 'app.tasks.celery_tasks.backup_database',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),  # Tous les dimanches à 3h
    },
}

celery.conf.timezone = 'Europe/Paris'