# ================================
# README.md
# ================================

# Creative Cocktail - Plateforme d'Organisation d'Événements

Creative Cocktail est une plateforme web complète dédiée à l'organisation d'événements professionnels et particuliers. Basée sur la méthode "6 Questions, 8 Onglets, 1 Solution", elle permet aux utilisateurs de planifier, organiser et gérer tous les aspects de leurs événements.

## 🎯 Fonctionnalités Principales

### Pour les Organisateurs d'Événements
- **Création et gestion d'événements** avec interface intuitive
- **8 onglets d'organisation** : Lieu, Décoration, Transport, Restauration, Animation, Activité, Communication, Technique
- **Gestion des participants** avec import/export CSV, groupes personnalisés
- **Agenda intégré** avec planning détaillé et timeline
- **Système de devis** avec demandes multiples aux prestataires
- **Budget management** avec répartition par catégories
- **Récapitulatifs et exports** en PDF/Excel

### Pour les Prestataires
- **Profil professionnel complet** avec portfolio et services
- **Réception et gestion des demandes de devis**
- **Système de notation et avis clients**
- **Abonnements Premium** avec mise en avant
- **Statistiques détaillées** sur les demandes et conversions

### Fonctionnalités Avancées
- **Chat en ligne** avec conseillers spécialisés
- **Système de notifications** email et in-app
- **Newsletters** ciblées (particuliers/professionnels)
- **Annuaire des prestataires** avec recherche avancée
- **API REST** complète pour intégrations tierces
- **Back-office administrateur** avec statistiques

## 🛠 Technologies Utilisées

### Backend
- **Python 3.11+** - Langage principal
- **Flask** - Framework web avec architecture modulaire
- **SQLAlchemy** - ORM pour la base de données
- **Flask-Login** - Gestion d'authentification
- **Flask-Admin** - Interface d'administration
- **Flask-Mail** - Envoi d'emails
- **Celery** - Tâches asynchrones
- **Redis** - Cache et broker Celery

### Frontend
- **HTML5/CSS3** - Structure et style
- **Bootstrap 5** - Framework CSS responsive
- **JavaScript ES6+** - Interactivité côté client
- **Chart.js** - Graphiques et statistiques
- **Font Awesome** - Icônes

### Base de Données
- **MariaDB** - Base de données relationnelle
- **Flask-Migrate** - Migrations de schéma

### Infrastructure
- **Docker & Docker Compose** - Conteneurisation
- **Nginx** - Reverse proxy et serveur web
- **Gunicorn** - Serveur WSGI Python

## 🚀 Installation et Déploiement

### Prérequis
- Python 3.11+
- Node.js 16+ (pour les outils frontend)
- MariaDB 10.9+
- Redis 6+
- Docker et Docker Compose (optionnel)

### Installation en Développement

1. **Cloner le repository**
```bash
git clone https://github.com/votre-org/creative-cocktail.git
cd creative-cocktail
```

2. **Créer un environnement virtuel**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

4. **Configuration**
```bash
cp .env.example .env
# Éditer .env avec vos paramètres
```

5. **Initialiser la base de données**
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
python scripts/init_db.py
```

6. **Lancer l'application**
```bash
python run.py
```

L'application sera accessible sur http://localhost:5000

### Déploiement avec Docker

1. **Cloner et configurer**
```bash
git clone https://github.com/votre-org/creative-cocktail.git
cd creative-cocktail
cp .env.example .env
# Configurer les variables d'environnement
```

2. **Lancer avec Docker Compose**
```bash
docker-compose up -d
```

3. **Initialiser la base de données**
```bash
docker-compose exec web flask db upgrade
docker-compose exec web python scripts/init_db.py
```

L'application sera accessible sur http://localhost

## 📊 Structure du Projet

```
creative_cocktail_app/
├── app/
│   ├── __init__.py              # Factory de l'application
│   ├── config.py               # Configuration
│   ├── models/                 # Modèles de données
│   │   ├── user.py            # Utilisateurs et prestataires
│   │   ├── event.py           # Événements
│   │   ├── venue.py           # Lieux
│   │   ├── services.py        # Services (transport, catering...)
│   │   └── organization.py    # Tâches et équipes
│   ├── frontend/              # Interface utilisateur
│   │   ├── routes.py         # Routes frontend
│   │   └── forms.py          # Formulaires
│   ├── backoffice/           # Administration
│   │   ├── routes.py         # Routes admin
│   │   └── admin.py          # Interface admin
│   ├── api/                  # API REST
│   │   └── routes.py         # Endpoints API
│   ├── services/             # Services métier
│   │   ├── notification_service.py
│   │   ├── chat_service.py
│   │   └── newsletter_service.py
│   ├── static/               # Fichiers statiques
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   └── templates/            # Templates HTML
│       ├── frontend/
│       └── backoffice/
├── migrations/               # Migrations base de données
├── tests/                   # Tests unitaires
├── scripts/                 # Scripts utilitaires
├── docker-compose.yml       # Configuration Docker
├── requirements.txt         # Dépendances Python
└── run.py                  # Point d'entrée
```

## 🧪 Tests

### Lancer les tests
```bash
# Tests unitaires
python -m pytest tests/

# Avec couverture
python -m pytest tests/ --cov=app --cov-report=html

# Tests spécifiques
python -m pytest tests/test_models.py
python -m pytest tests/test_routes.py
python -m pytest tests/test_api.py
```

### Types de tests
- **Tests de modèles** - Validation des modèles de données
- **Tests de routes** - Vérification des endpoints web
- **Tests d'API** - Validation de l'API REST
- **Tests d'intégration** - Scénarios complets

## 📈 Monitoring et Maintenance

### Logs
```bash
# Logs de l'application
docker-compose logs web

# Logs de la base de données
docker-compose logs db

# Logs en temps réel
docker-compose logs -f
```

### Sauvegarde
```bash
# Sauvegarde manuelle
python scripts/backup_db.py

# Restauration
python scripts/restore_db.py backup_file.sql
```

### Mise à jour
```bash
# Mettre à jour le code
git pull origin main

# Migrer la base de données
docker-compose exec web flask db upgrade

# Redémarrer les services
docker-compose restart
```

## 🔧 Configuration

### Variables d'environnement principales
```env
# Application
SECRET_KEY=votre-clé-secrète
FLASK_ENV=production

# Base de données
DATABASE_URL=mysql+pymysql://user:password@host/database

# Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=votre-email@domain.com
MAIL_PASSWORD=votre-mot-de-passe

# Redis
REDIS_URL=redis://localhost:6379/0

# Upload
MAX_CONTENT_LENGTH=16777216  # 16MB
```

### Paramètres avancés
- **Pagination** : ITEMS_PER_PAGE=20
- **Session** : Durée de vie des sessions
- **Cache** : Configuration Redis
- **Celery** : Configuration des workers

## 🤝 Contribution

### Guide de contribution
1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commiter les changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

### Standards de code
- **PEP 8** pour Python
- **ESLint** pour JavaScript
- **Tests** obligatoires pour nouvelles fonctionnalités
- **Documentation** des APIs

## 📄 License

Distribué sous licence MIT. Voir `LICENSE` pour plus d'informations.

## 👥 Équipe

- **Développement** - Équipe Creative Cocktail
- **Design** - Studio Creative
- **Product Owner** - Creative Cocktail

## 📞 Support

- **Documentation** : [docs.creativecocktail.com](https://docs.creativecocktail.com)
- **Support** : support@creativecocktail.com
- **Issues** : [GitHub Issues](https://github.com/votre-org/creative-cocktail/issues)

---

Créé avec ❤️ par l'équipe Creative Cocktail