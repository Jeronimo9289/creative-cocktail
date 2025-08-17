# ================================
# tests/test_models.py
# ================================

import unittest
from app import create_app, db
from app.models.user import User, UserType
from app.models.event import Event, EventType, EventStatus
from app.models.provider import Provider, ProviderCategory
from app.models.venue import Venue
from datetime import datetime

class ModelTestCase(unittest.TestCase):
    """Tests pour les modèles de données"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        self.app = create_app('app.config.TestingConfig')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
    
    def tearDown(self):
        """Nettoyage après chaque test"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_password_hashing(self):
        """Test du hashage des mots de passe"""
        user = User(username='test', email='test@example.com')
        user.set_password('password123')
        
        self.assertFalse(user.check_password('wrongpassword'))
        self.assertTrue(user.check_password('password123'))
    
    def test_user_creation(self):
        """Test de création d'utilisateur"""
        user = User(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            user_type=UserType.CLIENT
        )
        user.set_password('password123')
        
        db.session.add(user)
        db.session.commit()
        
        self.assertEqual(user.get_full_name(), 'Test User')
        self.assertEqual(user.user_type, UserType.CLIENT)
        self.assertTrue(user.check_password('password123'))
    
    def test_event_creation(self):
        """Test de création d'événement"""
        # Créer un utilisateur d'abord
        user = User(username='organizer', email='organizer@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        
        # Créer un événement
        event = Event(
            title='Test Event',
            organizer_id=user.id,
            event_type=EventType.PROFESSIONAL,
            status=EventStatus.DRAFT,
            total_budget=5000,
            expected_participants=50
        )
        
        db.session.add(event)
        db.session.commit()
        
        self.assertEqual(event.title, 'Test Event')
        self.assertEqual(event.organizer, user)
        self.assertEqual(event.status, EventStatus.DRAFT)
    
    def test_provider_creation(self):
        """Test de création de prestataire"""
        # Créer un utilisateur d'abord
        user = User(
            username='provider',
            email='provider@example.com',
            user_type=UserType.PROVIDER
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        
        # Créer le profil prestataire
        provider = Provider(
            user_id=user.id,
            company_name='Test Company',
            category=ProviderCategory.VENUE,
            description='Test description',
            base_price=1000
        )
        
        db.session.add(provider)
        db.session.commit()
        
        self.assertEqual(provider.company_name, 'Test Company')
        self.assertEqual(provider.user, user)
        self.assertEqual(provider.category, ProviderCategory.VENUE)
        self.assertEqual(provider.average_rating, 0.0)
        self.assertEqual(provider.total_ratings, 0)
    
    def test_venue_creation(self):
        """Test de création de lieu"""
        venue = Venue(
            name='Test Venue',
            city='Paris',
            max_capacity=100,
            base_price=500,
            is_active=True
        )
        
        db.session.add(venue)
        db.session.commit()
        
        self.assertEqual(venue.name, 'Test Venue')
        self.assertEqual(venue.city, 'Paris')
        self.assertTrue(venue.is_active)