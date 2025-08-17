# ================================
# STRUCTURE DU PROJET
# ================================

# creative_cocktail_app/
# ├── app/
# │   ├── __init__.py
# │   ├── config.py
# │   ├── models/
# │   │   ├── __init__.py
# │   │   ├── user.py
# │   │   ├── event.py
# │   │   ├── venue.py
# │   │   ├── provider.py
# │   │   └── organization.py
# │   ├── frontend/
# │   │   ├── __init__.py
# │   │   ├── routes.py
# │   │   ├── forms.py
# │   │   └── utils.py
# │   ├── backoffice/
# │   │   ├── __init__.py
# │   │   ├── routes.py
# │   │   ├── forms.py
# │   │   └── admin.py
# │   ├── api/
# │   │   ├── __init__.py
# │   │   └── routes.py
# │   ├── static/
# │   │   ├── css/
# │   │   ├── js/
# │   │   └── images/
# │   └── templates/
# │       ├── base.html
# │       ├── frontend/
# │       └── backoffice/
# ├── migrations/
# ├── tests/
# ├── run.py
# ├── requirements.txt
# └── .env

# ================================
# app/__init__.py
# ================================

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_admin import Admin
import os

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()
admin = Admin()

def create_app(config_class='app.config.Config'):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    admin.init_app(app, name='Creative Cocktail Admin', template_mode='bootstrap4')
    
    # Configure login manager
    login_manager.login_view = 'frontend.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
    
    # Register blueprints
    from app.frontend import bp as frontend_bp
    app.register_blueprint(frontend_bp)
    
    from app.backoffice import bp as backoffice_bp
    app.register_blueprint(backoffice_bp, url_prefix='/admin')
    
    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Import models for migration
    from app.models import user, event, venue, provider, organization
    
    # Setup admin interface
    from app.backoffice.admin import setup_admin
    setup_admin(admin, db)
    
    return app

# ================================
# app/config.py
# ================================

import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '..', '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database configuration for MariaDB
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://user:password@localhost/creative_cocktail'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Mail configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'localhost'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Upload configuration
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Pagination
    ITEMS_PER_PAGE = 20
    
    # Redis for caching and Celery
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/0'

class DevelopmentConfig(Config):
    DEBUG = True
    
class ProductionConfig(Config):
    DEBUG = False
    
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

# ================================
# run.py
# ================================

import os
from app import create_app, db
from app.models.user import User
from app.models.event import Event
from app.models.venue import Venue
from app.models.provider import Provider

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'User': User, 
        'Event': Event, 
        'Venue': Venue, 
        'Provider': Provider
    }

@app.cli.command()
def init_db():
    """Initialize the database."""
    db.create_all()
    print('Database initialized!')

@app.cli.command()
def create_admin():
    """Create admin user."""
    from app.models.user import User
    admin = User(
        username='admin',
        email='admin@creativecocktail.com',
        first_name='Admin',
        last_name='System',
        is_admin=True,
        is_active=True
    )
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.commit()
    print('Admin user created!')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

# ================================
# .env
# ================================

SECRET_KEY=your-secret-key-here
DATABASE_URL=mysql+pymysql://username:password@localhost/creative_cocktail
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
REDIS_URL=redis://localhost:6379/0
FLASK_CONFIG=development