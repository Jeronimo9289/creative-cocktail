# ================================
# app/models/__init__.py
# ================================

from app import db

# ================================
# app/models/user.py
# ================================

from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import enum

class UserType(enum.Enum):
    CLIENT = "client"
    PROVIDER = "provider"
    ADMIN = "admin"

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Informations personnelles
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    mobile = db.Column(db.String(20))
    
    # Adresse
    address = db.Column(db.Text)
    postal_code = db.Column(db.String(10))
    city = db.Column(db.String(100))
    country = db.Column(db.String(100))
    
    # Informations professionnelles
    company = db.Column(db.String(200))
    position = db.Column(db.String(100))
    sector = db.Column(db.String(100))
    vat_number = db.Column(db.String(50))
    siret_number = db.Column(db.String(50))
    
    # Type d'utilisateur et statut
    user_type = db.Column(db.Enum(UserType), default=UserType.CLIENT)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Dates
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relations
    events = db.relationship('Event', backref='organizer', lazy='dynamic')
    provider_profile = db.relationship('Provider', backref='user', uselist=False)
    
    def set_password(self, password):
        """Hasher le mot de passe"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Vérifier le mot de passe"""
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        """Retourner le nom complet"""
        return f"{self.first_name} {self.last_name}".strip()
    
    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ================================
# app/models/provider.py
# ================================

from app import db
from datetime import datetime
import enum

class ProviderCategory(enum.Enum):
    VENUE = "lieu"
    DECORATION = "decoration_mobilier" 
    TRANSPORT = "transport"
    CATERING = "restauration"
    ANIMATION = "animation"
    ACTIVITY = "activite"
    COMMUNICATION = "support_communication"
    TECHNICAL = "technique"

class Provider(db.Model):
    __tablename__ = 'providers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Informations entreprise
    company_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    website = db.Column(db.String(200))
    
    # Catégories et services
    category = db.Column(db.Enum(ProviderCategory), nullable=False)
    services = db.Column(db.Text)  # JSON des services proposés
    
    # Zone d'intervention
    intervention_zone = db.Column(db.Text)  # JSON des zones
    
    # Tarification
    base_price = db.Column(db.Decimal(10, 2))
    price_per_person = db.Column(db.Decimal(10, 2))
    price_type = db.Column(db.String(50))  # 'global' ou 'per_person'
    
    # Notation
    average_rating = db.Column(db.Float, default=0.0)
    total_ratings = db.Column(db.Integer, default=0)
    
    # Statut
    is_verified = db.Column(db.Boolean, default=False)
    is_premium = db.Column(db.Boolean, default=False)
    subscription_end = db.Column(db.DateTime)
    
    # Dates
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    quotes = db.relationship('Quote', backref='provider', lazy='dynamic')
    ratings = db.relationship('ProviderRating', backref='provider', lazy='dynamic')
    
    def update_rating(self):
        """Mettre à jour la note moyenne"""
        ratings = self.ratings.all()
        if ratings:
            self.average_rating = sum(r.rating for r in ratings) / len(ratings)
            self.total_ratings = len(ratings)
        else:
            self.average_rating = 0.0
            self.total_ratings = 0
        db.session.commit()
    
    def __repr__(self):
        return f'<Provider {self.company_name}>'

# ================================
# app/models/rating.py
# ================================

class ProviderRating(db.Model):
    __tablename__ = 'provider_ratings'
    
    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.Integer, db.ForeignKey('providers.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))
    
    # Critères de notation
    rating = db.Column(db.Float, nullable=False)  # Note globale
    reactivity = db.Column(db.Integer)  # Sur 5
    price = db.Column(db.Integer)  # Sur 5
    service_quality = db.Column(db.Integer)  # Sur 5
    welcome = db.Column(db.Integer)  # Sur 5
    
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    user = db.relationship('User', backref='provider_ratings')
    event = db.relationship('Event', backref='provider_ratings')

class ClientRating(db.Model):
    __tablename__ = 'client_ratings'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    provider_id = db.Column(db.Integer, db.ForeignKey('providers.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))
    
    # Critères de notation
    professionalism = db.Column(db.Integer)  # Sur 5
    communication = db.Column(db.Integer)  # Sur 5
    payment = db.Column(db.Integer)  # Sur 5
    
    comment = db.Column(db.Text)
    is_anonymous = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    client = db.relationship('User', backref='client_ratings')
    provider = db.relationship('Provider', backref='client_ratings')
    event = db.relationship('Event', backref='client_ratings')