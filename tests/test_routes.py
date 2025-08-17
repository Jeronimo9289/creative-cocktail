# ================================
# tests/test_routes.py
# ================================

import unittest
from app import create_app, db
from app.models.user import User, UserType

class RouteTestCase(unittest.TestCase):
    """Tests pour les routes de l'application"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        self.app = create_app('app.config.TestingConfig')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        db.create_all()
        
        # Créer un utilisateur de test
        self.user = User(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )
        self.user.set_password('password123')
        db.session.add(self.user)
        db.session.commit()
    
    def tearDown(self):
        """Nettoyage après chaque test"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def login(self, username='testuser', password='password123'):
        """Helper pour se connecter"""
        return self.client.post('/login', data={
            'username': username,
            'password': password
        }, follow_redirects=True)
    
    def logout(self):
        """Helper pour se déconnecter"""
        return self.client.get('/logout', follow_redirects=True)
    
    def test_index_page(self):
        """Test de la page d'accueil"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Creative Cocktail', response.data)
    
    def test_login_logout(self):
        """Test de connexion/déconnexion"""
        # Test page de connexion
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        
        # Test connexion réussie
        response = self.login()
        self.assertEqual(response.status_code, 200)
        
        # Test déconnexion
        response = self.logout()
        self.assertEqual(response.status_code, 200)
    
    def test_login_invalid_credentials(self):
        """Test de connexion avec identifiants invalides"""
        response = self.login('wronguser', 'wrongpassword')
        self.assertIn(b'incorrect', response.data)
    
    def test_protected_route_requires_login(self):
        """Test qu'une route protégée nécessite une connexion"""
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 302)  # Redirection vers login
    
    def test_dashboard_access_after_login(self):
        """Test d'accès au dashboard après connexion"""
        self.login()
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Tableau de bord', response.data)
    
    def test_providers_page(self):
        """Test de la page des prestataires"""
        response = self.client.get('/providers')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'prestataires', response.data)
    
    def test_venues_page(self):
        """Test de la page des lieux"""
        response = self.client.get('/venues')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Lieux', response.data)