# ================================
# app/models/event.py
# ================================

from app import db
from datetime import datetime
import enum
import json

class EventType(enum.Enum):
    PERSONAL = "particulier"
    PROFESSIONAL = "professionnel"

class EventStatus(enum.Enum):
    DRAFT = "brouillon"
    PENDING = "en_attente"
    CONFIRMED = "confirme"
    IN_PROGRESS = "en_cours"
    COMPLETED = "termine"
    CANCELLED = "annule"

class Event(db.Model):
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    organizer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Informations générales
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    event_type = db.Column(db.Enum(EventType), nullable=False)
    status = db.Column(db.Enum(EventStatus), default=EventStatus.DRAFT)
    
    # Budget
    total_budget = db.Column(db.Decimal(10, 2))
    budget_per_person = db.Column(db.Decimal(10, 2))
    budget_type = db.Column(db.String(20))  # 'global' ou 'per_person'
    
    # Participants
    expected_participants = db.Column(db.Integer)
    min_age = db.Column(db.Integer)
    max_age = db.Column(db.Integer)
    gender_target = db.Column(db.String(20))  # 'homme', 'femme', 'mixte'
    
    # Dates
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    venues = db.relationship('EventVenue', backref='event', lazy='dynamic', cascade='all, delete-orphan')
    activities = db.relationship('EventActivity', backref='event', lazy='dynamic', cascade='all, delete-orphan')
    transports = db.relationship('EventTransport', backref='event', lazy='dynamic', cascade='all, delete-orphan')
    catering = db.relationship('EventCatering', backref='event', lazy='dynamic', cascade='all, delete-orphan')
    decorations = db.relationship('EventDecoration', backref='event', lazy='dynamic', cascade='all, delete-orphan')
    communications = db.relationship('EventCommunication', backref='event', lazy='dynamic', cascade='all, delete-orphan')
    technical = db.relationship('EventTechnical', backref='event', lazy='dynamic', cascade='all, delete-orphan')
    participants = db.relationship('EventParticipant', backref='event', lazy='dynamic', cascade='all, delete-orphan')
    tasks = db.relationship('EventTask', backref='event', lazy='dynamic', cascade='all, delete-orphan')
    quotes = db.relationship('Quote', backref='event', lazy='dynamic')
    
    def get_total_cost(self):
        """Calculer le coût total de l'événement"""
        total = 0
        # Additionner tous les coûts des différents onglets
        for venue in self.venues:
            if venue.cost:
                total += venue.cost
        for activity in self.activities:
            if activity.cost:
                total += activity.cost
        # ... autres onglets
        return total
    
    def get_progress_percentage(self):
        """Calculer le pourcentage d'avancement de l'organisation"""
        total_tasks = self.tasks.count()
        if total_tasks == 0:
            return 0
        completed_tasks = self.tasks.filter_by(status='completed').count()
        return (completed_tasks / total_tasks) * 100
    
    def __repr__(self):
        return f'<Event {self.title}>'

# ================================
# app/models/venue.py
# ================================

class Venue(db.Model):
    __tablename__ = 'venues'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Adresse
    address = db.Column(db.Text)
    postal_code = db.Column(db.String(10))
    city = db.Column(db.String(100))
    country = db.Column(db.String(100))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    
    # Capacités
    max_capacity = db.Column(db.Integer)
    min_capacity = db.Column(db.Integer)
    
    # Services et équipements
    services = db.Column(db.Text)  # JSON
    equipment = db.Column(db.Text)  # JSON
    
    # Tarification
    base_price = db.Column(db.Decimal(10, 2))
    price_per_person = db.Column(db.Decimal(10, 2))
    price_per_hour = db.Column(db.Decimal(10, 2))
    
    # Contacts
    contact_person = db.Column(db.String(100))
    contact_position = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    website = db.Column(db.String(200))
    
    # Statut
    is_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Dates
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    event_venues = db.relationship('EventVenue', backref='venue', lazy='dynamic')
    
    def __repr__(self):
        return f'<Venue {self.name}>'

class EventVenue(db.Model):
    """Association entre un événement et un lieu avec configurations spécifiques"""
    __tablename__ = 'event_venues'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'))
    
    # Configuration spécifique pour cet événement
    custom_name = db.Column(db.String(200))
    purpose = db.Column(db.String(100))  # dormir, manger, travailler, s'amuser
    start_datetime = db.Column(db.DateTime)
    end_datetime = db.Column(db.DateTime)
    
    # Coût pour cet événement
    cost = db.Column(db.Decimal(10, 2))
    cost_type = db.Column(db.String(20))  # 'global', 'per_person', 'per_hour'
    
    # Participants assignés
    assigned_participants = db.Column(db.Text)  # JSON des IDs des participants
    
    # Statut
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, cancelled
    
    # Notes
    notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ================================
# app/models/organization.py
# ================================

class EventTask(db.Model):
    """Tâches d'organisation pour un événement"""
    __tablename__ = 'event_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    
    # Informations de la tâche
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # lieu, decoration, transport, etc.
    
    # Assignation
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('event_teams.id'))
    
    # Dates
    start_date = db.Column(db.DateTime)
    due_date = db.Column(db.DateTime)
    completed_date = db.Column(db.DateTime)
    
    # Statut et priorité
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed, cancelled
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, urgent
    
    # Validation
    validated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    validated_at = db.Column(db.DateTime)
    
    # Notes
    notes = db.Column(db.Text)
    completion_notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id], backref='assigned_tasks')
    validated_by = db.relationship('User', foreign_keys=[validated_by_id], backref='validated_tasks')
    
    def __repr__(self):
        return f'<EventTask {self.title}>'

class EventTeam(db.Model):
    """Équipes d'organisation pour un événement"""
    __tablename__ = 'event_teams'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    color = db.Column(db.String(7))  # Code couleur hex
    
    # Chef d'équipe
    leader_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    leader = db.relationship('User', backref='led_teams')
    members = db.relationship('EventTeamMember', backref='team', lazy='dynamic', cascade='all, delete-orphan')
    tasks = db.relationship('EventTask', backref='team', lazy='dynamic')
    
    def __repr__(self):
        return f'<EventTeam {self.name}>'

class EventTeamMember(db.Model):
    """Membres d'une équipe d'organisation"""
    __tablename__ = 'event_team_members'
    
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('event_teams.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    role = db.Column(db.String(100))  # Rôle dans l'équipe
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    user = db.relationship('User', backref='team_memberships')

class EventParticipant(db.Model):
    """Participants/invités d'un événement"""
    __tablename__ = 'event_participants'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    
    # Informations personnelles
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    
    # Informations professionnelles
    company = db.Column(db.String(200))
    position = db.Column(db.String(100))
    
    # Groupes
    group_name = db.Column(db.String(100))  # ex: "équipe rouge", "VIP", etc.
    
    # Statut
    status = db.Column(db.String(20), default='invited')  # invited, confirmed, declined, attended
    
    # Besoins spéciaux
    dietary_requirements = db.Column(db.Text)
    accessibility_needs = db.Column(db.Text)
    notes = db.Column(db.Text)
    
    # QR Code pour l'enregistrement
    qr_code = db.Column(db.String(100), unique=True)
    
    # Dates
    invited_at = db.Column(db.DateTime, default=datetime.utcnow)
    responded_at = db.Column(db.DateTime)
    checked_in_at = db.Column(db.DateTime)
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def __repr__(self):
        return f'<EventParticipant {self.get_full_name()}>'