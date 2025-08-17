# ================================
# tests/test_api.py
# ================================

import unittest
import json
from app import create_app, db
from app.models.user import User
from app.models.venue import Venue
from app.models.provider import Provider, ProviderCategory

class APITestCase(unittest.TestCase):
    """Tests pour l'API REST"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        self.app = create_app('app.config.TestingConfig')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        db.create_all()
        
        # Créer des données de test
        self.venue = Venue(
            name='Test Venue',
            city='Paris',
            max_capacity=100,
            is_active=True
        )
        db.session.add(self.venue)
        
        self.user = User(
            username='provider',
            email='provider@example.com',
            user_type='provider'
        )
        self.user.set_password('password123')
        db.session.add(self.user)
        db.session.flush()
        
        self.provider = Provider(
            user_id=self.user.id,
            company_name='Test Provider',
            category=ProviderCategory.VENUE,
            is_verified=True
        )
        db.session.add(self.provider)
        db.session.commit()
    
    def tearDown(self):
        """Nettoyage après chaque test"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_search_venues_api(self):
        """Test de l'API de recherche de lieux"""
        response = self.client.get('/api/search/venues?q=Test')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        self.assertEqual(data[0]['name'], 'Test Venue')
    
    def test_search_providers_api(self):
        """Test de l'API de recherche de prestataires"""
        response = self.client.get('/api/search/providers?category=lieu')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        self.assertEqual(data[0]['company_name'], 'Test Provider')
    
    def test_api_error_handling(self):
        """Test de gestion d'erreurs API"""
        response = self.client.get('/api/nonexistent')
        self.assertEqual(response.status_code, 404)