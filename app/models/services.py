# ================================
# app/models/services.py
# ================================

from app import db
from datetime import datetime
import enum

# Activités
class EventActivity(db.Model):
    __tablename__ = 'event_activities'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    
    name = db.Column(db.String(200), nullable=False)
    activity_type = db.Column(db.String(100))
    description = db.Column(db.Text)
    
    # Dates et durée
    start_datetime = db.Column(db.DateTime)
    end_datetime = db.Column(db.DateTime)
    duration_minutes = db.Column(db.Integer)
    is_recurring = db.Column(db.Boolean, default=False)
    
    # Lieu (peut être différent du lieu principal)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'))
    custom_location = db.Column(db.String(200))
    
    # Participants
    max_participants = db.Column(db.Integer)
    assigned_participants = db.Column(db.Text)  # JSON
    
    # Objectifs
    objectives = db.Column(db.Text)  # amuser, fédérer, dynamiser
    
    # Coût
    total_cost = db.Column(db.Decimal(10, 2))
    cost_per_person = db.Column(db.Decimal(10, 2))
    
    # Besoins techniques
    technical_requirements = db.Column(db.Text)  # JSON
    
    # Résultats (pour les activités avec résultats)
    results = db.Column(db.Text)  # JSON
    
    status = db.Column(db.String(20), default='planned')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Transports
class EventTransport(db.Model):
    __tablename__ = 'event_transports'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    
    name = db.Column(db.String(200), nullable=False)  # ex: "Transport hôtel A/R"
    transport_type = db.Column(db.String(100))  # bus, train, avion, bateau, etc.
    
    # Itinéraire
    departure_address = db.Column(db.Text)
    arrival_address = db.Column(db.Text)
    departure_datetime = db.Column(db.DateTime)
    arrival_datetime = db.Column(db.DateTime)
    
    # Participants
    capacity = db.Column(db.Integer)
    assigned_participants = db.Column(db.Text)  # JSON
    
    # Services et options
    services = db.Column(db.Text)  # JSON: wifi, bar, vidéo, etc.
    special_options = db.Column(db.Text)  # JSON: champagne pour VIP, etc.
    
    # Coût
    total_cost = db.Column(db.Decimal(10, 2))
    cost_per_person = db.Column(db.Decimal(10, 2))
    
    status = db.Column(db.String(20), default='planned')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Restauration
class EventCatering(db.Model):
    __tablename__ = 'event_catering'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    
    name = db.Column(db.String(200), nullable=False)  # ex: "Déjeuner clients"
    meal_type = db.Column(db.String(100))  # déjeuner, dîner, cocktail, etc.
    
    # Dates
    start_datetime = db.Column(db.DateTime)
    end_datetime = db.Column(db.DateTime)
    
    # Lieu
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'))
    custom_location = db.Column(db.String(200))
    
    # Service
    service_level = db.Column(db.String(50))  # haut de gamme, moyen, etc.
    cuisine_type = db.Column(db.String(100))
    special_requirements = db.Column(db.Text)  # végétarien, sans gluten, etc.
    
    # Participants
    expected_guests = db.Column(db.Integer)
    assigned_participants = db.Column(db.Text)  # JSON
    
    # Services
    services = db.Column(db.Text)  # JSON: service, vaisselle, etc.
    
    # Coût
    total_cost = db.Column(db.Decimal(10, 2))
    cost_per_person = db.Column(db.Decimal(10, 2))
    
    # Options
    tasting_requested = db.Column(db.Boolean, default=False)
    
    status = db.Column(db.String(20), default='planned')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Décoration/Mobilier
class EventDecoration(db.Model):
    __tablename__ = 'event_decorations'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100))  # décoration, mobilier
    item_type = db.Column(db.String(100))  # tables, chaises, éclairage, etc.
    
    # Spécifications
    specifications = db.Column(db.Text)  # JSON: couleur, matériaux, dimensions
    quantity = db.Column(db.Integer)
    
    # Lieu d'installation
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'))
    installation_location = db.Column(db.String(200))
    
    # Services
    delivery_required = db.Column(db.Boolean, default=False)
    installation_required = db.Column(db.Boolean, default=False)
    pickup_required = db.Column(db.Boolean, default=False)
    
    # Dates
    delivery_date = db.Column(db.DateTime)
    pickup_date = db.Column(db.DateTime)
    
    # Coût
    unit_cost = db.Column(db.Decimal(10, 2))
    total_cost = db.Column(db.Decimal(10, 2))
    
    status = db.Column(db.String(20), default='planned')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Support de communication
class EventCommunication(db.Model):
    __tablename__ = 'event_communications'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    
    name = db.Column(db.String(200), nullable=False)
    communication_type = db.Column(db.String(100))  # invitation, badge, signalétique
    
    # Spécifications
    format = db.Column(db.String(100))  # A4, A3, numérique, etc.
    quantity = db.Column(db.Integer)
    specifications = db.Column(db.Text)  # JSON: couleurs, matériaux, etc.
    
    # Contenu
    target_participants = db.Column(db.Text)  # JSON des participants ciblés
    content_brief = db.Column(db.Text)
    
    # Services
    design_required = db.Column(db.Boolean, default=False)
    printing_required = db.Column(db.Boolean, default=False)
    delivery_required = db.Column(db.Boolean, default=False)
    
    # Lieu de placement/distribution
    placement_location = db.Column(db.String(200))
    
    # Coût
    total_cost = db.Column(db.Decimal(10, 2))
    
    # Dates
    deadline = db.Column(db.DateTime)
    delivery_date = db.Column(db.DateTime)
    
    status = db.Column(db.String(20), default='planned')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Technique
class EventTechnical(db.Model):
    __tablename__ = 'event_technical'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100))  # son, lumière, vidéo, structure, etc.
    
    # Spécifications
    specifications = db.Column(db.Text)  # JSON des spécifications techniques
    purpose = db.Column(db.String(200))  # à quoi ça sert
    
    # Dates
    start_datetime = db.Column(db.DateTime)
    end_datetime = db.Column(db.DateTime)
    is_recurring = db.Column(db.Boolean, default=False)
    
    # Lieu
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'))
    installation_location = db.Column(db.String(200))
    
    # Services
    services = db.Column(db.Text)  # JSON: montage, démontage, personnel, etc.
    
    # Participants assignés
    assigned_participants = db.Column(db.Text)  # JSON
    
    # Coût
    total_cost = db.Column(db.Decimal(10, 2))
    
    status = db.Column(db.String(20), default='planned')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ================================
# app/models/quote.py
# ================================

class Quote(db.Model):
    """Devis entre un client et un prestataire"""
    __tablename__ = 'quotes'
    
    id = db.Column(db.Integer, primary_key=True)
    quote_number = db.Column(db.String(50), unique=True, nullable=False)
    
    # Relations
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    provider_id = db.Column(db.Integer, db.ForeignKey('providers.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Contenu de la demande
    category = db.Column(db.String(50))  # lieu, transport, etc.
    request_details = db.Column(db.Text)  # JSON de la demande
    
    # Réponse du prestataire
    response_details = db.Column(db.Text)  # JSON de la réponse
    quoted_price = db.Column(db.Decimal(10, 2))
    alternative_offers = db.Column(db.Text)  # JSON des offres alternatives
    
    # Statut
    status = db.Column(db.String(20), default='sent')  # sent, viewed, responded, accepted, declined
    
    # Messages
    client_message = db.Column(db.Text)
    provider_message = db.Column(db.Text)
    decline_reason = db.Column(db.Text)
    
    # Dates
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    viewed_at = db.Column(db.DateTime)
    responded_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    
    # Relations
    client = db.relationship('User', backref='sent_quotes')
    
    def __repr__(self):
        return f'<Quote {self.quote_number}>'

class QuoteItem(db.Model):
    """Éléments détaillés d'un devis"""
    __tablename__ = 'quote_items'
    
    id = db.Column(db.Integer, primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey('quotes.id'), nullable=False)
    
    description = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Decimal(10, 2))
    total_price = db.Column(db.Decimal(10, 2))
    
    # Relations
    quote = db.relationship('Quote', backref=db.backref('items', lazy='dynamic', cascade='all, delete-orphan'))
    
    def __repr__(self):
        return f'<QuoteItem {self.description}>'