# ================================
# scripts/init_db.py
# ================================

"""Script d'initialisation de la base de données"""

from app import create_app, db
from app.models.user import User, UserType
from app.models.provider import Provider, ProviderCategory
from app.models.venue import Venue
from app.models.event import Event, EventType, EventStatus
from datetime import datetime, timedelta
import random

def init_database():
    """Initialiser la base de données avec des données de test"""
    
    app = create_app()
    
    with app.app_context():
        # Créer les tables
        db.create_all()
        
        print("Tables créées avec succès")
        
        # Créer un administrateur
        admin = User(
            username='admin',
            email='admin@creativecocktail.com',
            first_name='Admin',
            last_name='System',
            user_type=UserType.ADMIN,
            is_admin=True,
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        # Créer des utilisateurs clients de test
        clients = []
        for i in range(10):
            client = User(
                username=f'client{i+1}',
                email=f'client{i+1}@example.com',
                first_name=f'Client{i+1}',
                last_name='Test',
                user_type=UserType.CLIENT,
                is_active=True,
                city=['Paris', 'Lyon', 'Marseille', 'Toulouse', 'Nice'][i % 5]
            )
            client.set_password('password123')
            clients.append(client)
            db.session.add(client)
        
        # Créer des prestataires de test
        providers_data = [
            {
                'company_name': 'Château de Versailles Events',
                'category': ProviderCategory.VENUE,
                'description': 'Location de salles prestigieuses pour vos événements',
                'city': 'Versailles'
            },
            {
                'company_name': 'Délices et Saveurs',
                'category': ProviderCategory.CATERING,
                'description': 'Traiteur gastronomique pour tous vos événements',
                'city': 'Paris'
            },
            {
                'company_name': 'Transport VIP',
                'category': ProviderCategory.TRANSPORT,
                'description': 'Solutions de transport haut de gamme',
                'city': 'Lyon'
            },
            {
                'company_name': 'Déco Événements',
                'category': ProviderCategory.DECORATION,
                'description': 'Décoration et mobilier pour événements',
                'city': 'Marseille'
            },
            {
                'company_name': 'Animation Pro',
                'category': ProviderCategory.ANIMATION,
                'description': 'Animations et spectacles pour tous âges',
                'city': 'Toulouse'
            }
        ]
        
        providers = []
        for i, provider_data in enumerate(providers_data):
            # Créer l'utilisateur prestataire
            user = User(
                username=f'provider{i+1}',
                email=f'provider{i+1}@example.com',
                first_name=f'Provider{i+1}',
                last_name='Test',
                user_type=UserType.PROVIDER,
                is_active=True,
                city=provider_data['city']
            )
            user.set_password('password123')
            db.session.add(user)
            db.session.flush()  # Pour récupérer l'ID
            
            # Créer le profil prestataire
            provider = Provider(
                user_id=user.id,
                company_name=provider_data['company_name'],
                category=provider_data['category'],
                description=provider_data['description'],
                is_verified=True,
                base_price=random.randint(500, 5000),
                average_rating=random.uniform(3.5, 5.0),
                total_ratings=random.randint(5, 50)
            )
            providers.append(provider)
            db.session.add(provider)
        
        # Créer des lieux de test
        venues_data = [
            {
                'name': 'Palais des Congrès de Paris',
                'city': 'Paris',
                'max_capacity': 1000,
                'base_price': 5000
            },
            {
                'name': 'Centre de Conférences Lyon',
                'city': 'Lyon',
                'max_capacity': 500,
                'base_price': 2500
            },
            {
                'name': 'Espace Marseille Provence',
                'city': 'Marseille',
                'max_capacity': 300,
                'base_price': 1500
            }
        ]
        
        venues = []
        for venue_data in venues_data:
            venue = Venue(
                name=venue_data['name'],
                city=venue_data['city'],
                max_capacity=venue_data['max_capacity'],
                base_price=venue_data['base_price'],
                is_verified=True,
                is_active=True
            )
            venues.append(venue)
            db.session.add(venue)
        
        # Créer des événements de test
        event_titles = [
            'Conférence Annuelle Tech 2024',
            'Mariage de Sophie et Pierre',
            'Séminaire Équipe Marketing',
            'Anniversaire Entreprise 10 ans',
            'Formation Leadership'
        ]
        
        for i, title in enumerate(event_titles):
            event = Event(
                title=title,
                organizer_id=clients[i].id if i < len(clients) else clients[0].id,
                event_type=EventType.PROFESSIONAL if i % 2 == 0 else EventType.PERSONAL,
                status=EventStatus.CONFIRMED,
                total_budget=random.randint(1000, 20000),
                expected_participants=random.randint(20, 200),
                start_date=datetime.now() + timedelta(days=random.randint(30, 365)),
                end_date=datetime.now() + timedelta(days=random.randint(30, 365) + 1)
            )
            db.session.add(event)
        
        # Valider toutes les modifications
        db.session.commit()
        
        print("Données de test créées avec succès")
        print("Utilisateurs créés:")
        print("- Admin: admin / admin123")
        print("- Clients: client1-client10 / password123")
        print("- Prestataires: provider1-provider5 / password123")

if __name__ == '__main__':
    init_database()