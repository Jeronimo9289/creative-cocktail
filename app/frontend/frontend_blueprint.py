# ================================
# app/frontend/__init__.py
# ================================

from flask import Blueprint

bp = Blueprint('frontend', __name__)

from app.frontend import routes

# ================================
# app/frontend/routes.py
# ================================

from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.frontend import bp
from app.frontend.forms import LoginForm, RegisterForm, EventForm, VenueForm
from app.models.user import User
from app.models.event import Event, EventStatus
from app.models.venue import Venue
from app.models.provider import Provider, ProviderCategory
from werkzeug.urls import url_parse
from datetime import datetime

@bp.route('/')
@bp.route('/index')
def index():
    """Page d'accueil"""
    recent_events = Event.query.filter_by(organizer_id=current_user.id).order_by(Event.created_at.desc()).limit(5).all() if current_user.is_authenticated else []
    featured_providers = Provider.query.filter_by(is_premium=True, is_verified=True).limit(6).all()
    
    return render_template('frontend/index.html', 
                         recent_events=recent_events,
                         featured_providers=featured_providers)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Connexion utilisateur"""
    if current_user.is_authenticated:
        return redirect(url_for('frontend.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Nom d\'utilisateur ou mot de passe incorrect', 'error')
            return redirect(url_for('frontend.login'))
        
        if not user.is_active:
            flash('Votre compte est désactivé', 'error')
            return redirect(url_for('frontend.login'))
        
        login_user(user, remember=form.remember_me.data)
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('frontend.dashboard')
        return redirect(next_page)
    
    return render_template('frontend/auth/login.html', form=form)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Inscription utilisateur"""
    if current_user.is_authenticated:
        return redirect(url_for('frontend.dashboard'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            user_type=form.user_type.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        flash('Félicitations, vous êtes maintenant inscrit !', 'success')
        return redirect(url_for('frontend.login'))
    
    return render_template('frontend/auth/register.html', form=form)

@bp.route('/logout')
def logout():
    """Déconnexion"""
    logout_user()
    return redirect(url_for('frontend.index'))

@bp.route('/dashboard')
@login_required
def dashboard():
    """Tableau de bord utilisateur"""
    user_events = Event.query.filter_by(organizer_id=current_user.id).order_by(Event.created_at.desc()).all()
    
    # Statistiques
    stats = {
        'total_events': len(user_events),
        'active_events': len([e for e in user_events if e.status in [EventStatus.PENDING, EventStatus.CONFIRMED, EventStatus.IN_PROGRESS]]),
        'completed_events': len([e for e in user_events if e.status == EventStatus.COMPLETED]),
        'total_budget': sum([e.total_budget or 0 for e in user_events])
    }
    
    return render_template('frontend/dashboard.html', 
                         events=user_events, 
                         stats=stats)

# ================================
# GESTION DES ÉVÉNEMENTS
# ================================

@bp.route('/events')
@login_required
def events():
    """Liste des événements de l'utilisateur"""
    page = request.args.get('page', 1, type=int)
    events = Event.query.filter_by(organizer_id=current_user.id)\
                       .order_by(Event.created_at.desc())\
                       .paginate(page=page, per_page=current_app.config['ITEMS_PER_PAGE'])
    
    return render_template('frontend/events/list.html', events=events)

@bp.route('/events/create', methods=['GET', 'POST'])
@login_required
def create_event():
    """Créer un nouvel événement"""
    form = EventForm()
    if form.validate_on_submit():
        event = Event(
            title=form.title.data,
            description=form.description.data,
            event_type=form.event_type.data,
            total_budget=form.total_budget.data,
            expected_participants=form.expected_participants.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            organizer_id=current_user.id
        )
        db.session.add(event)
        db.session.commit()
        
        flash('Événement créé avec succès !', 'success')
        return redirect(url_for('frontend.event_detail', id=event.id))
    
    return render_template('frontend/events/create.html', form=form)

@bp.route('/events/<int:id>')
@login_required
def event_detail(id):
    """Détail d'un événement"""
    event = Event.query.filter_by(id=id, organizer_id=current_user.id).first_or_404()
    
    # Récupérer les données des différents onglets
    venues = event.venues.all()
    activities = event.activities.all()
    transports = event.transports.all()
    catering = event.catering.all()
    decorations = event.decorations.all()
    communications = event.communications.all()
    technical = event.technical.all()
    participants = event.participants.all()
    tasks = event.tasks.all()
    
    return render_template('frontend/events/detail.html', 
                         event=event,
                         venues=venues,
                         activities=activities,
                         transports=transports,
                         catering=catering,
                         decorations=decorations,
                         communications=communications,
                         technical=technical,
                         participants=participants,
                         tasks=tasks)

@bp.route('/events/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_event(id):
    """Modifier un événement"""
    event = Event.query.filter_by(id=id, organizer_id=current_user.id).first_or_404()
    
    form = EventForm(obj=event)
    if form.validate_on_submit():
        form.populate_obj(event)
        event.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash('Événement modifié avec succès !', 'success')
        return redirect(url_for('frontend.event_detail', id=event.id))
    
    return render_template('frontend/events/edit.html', form=form, event=event)

# ================================
# GESTION DES LIEUX
# ================================

@bp.route('/venues')
def venues():
    """Annuaire des lieux"""
    page = request.args.get('page', 1, type=int)
    city = request.args.get('city', '')
    capacity = request.args.get('capacity', type=int)
    
    query = Venue.query.filter_by(is_active=True)
    
    if city:
        query = query.filter(Venue.city.ilike(f'%{city}%'))
    if capacity:
        query = query.filter(Venue.max_capacity >= capacity)
    
    venues = query.paginate(page=page, per_page=current_app.config['ITEMS_PER_PAGE'])
    
    return render_template('frontend/venues/list.html', venues=venues)

@bp.route('/venues/<int:id>')
def venue_detail(id):
    """Détail d'un lieu"""
    venue = Venue.query.filter_by(id=id, is_active=True).first_or_404()
    return render_template('frontend/venues/detail.html', venue=venue)

# ================================
# ANNUAIRE DES PRESTATAIRES
# ================================

@bp.route('/providers')
def providers():
    """Annuaire des prestataires"""
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    city = request.args.get('city', '')
    
    query = Provider.query.filter_by(is_verified=True)
    
    if category:
        query = query.filter_by(category=category)
    if city:
        query = query.join(User).filter(User.city.ilike(f'%{city}%'))
    
    providers = query.order_by(Provider.is_premium.desc(), Provider.average_rating.desc())\
                    .paginate(page=page, per_page=current_app.config['ITEMS_PER_PAGE'])
    
    categories = ProviderCategory
    
    return render_template('frontend/providers/list.html', 
                         providers=providers, 
                         categories=categories)

@bp.route('/providers/<int:id>')
def provider_detail(id):
    """Détail d'un prestataire"""
    provider = Provider.query.filter_by(id=id, is_verified=True).first_or_404()
    ratings = provider.ratings.order_by(ProviderRating.created_at.desc()).limit(10).all()
    
    return render_template('frontend/providers/detail.html', 
                         provider=provider, 
                         ratings=ratings)

# ================================
# API ENDPOINTS
# ================================

@bp.route('/api/search/venues')
def api_search_venues():
    """API de recherche de lieux"""
    query = request.args.get('q', '')
    city = request.args.get('city', '')
    
    venues_query = Venue.query.filter_by(is_active=True)
    
    if query:
        venues_query = venues_query.filter(Venue.name.ilike(f'%{query}%'))
    if city:
        venues_query = venues_query.filter(Venue.city.ilike(f'%{city}%'))
    
    venues = venues_query.limit(10).all()
    
    results = []
    for venue in venues:
        results.append({
            'id': venue.id,
            'name': venue.name,
            'city': venue.city,
            'address': venue.address,
            'max_capacity': venue.max_capacity
        })
    
    return jsonify(results)

@bp.route('/api/search/providers')
def api_search_providers():
    """API de recherche de prestataires"""
    category = request.args.get('category', '')
    city = request.args.get('city', '')
    
    query = Provider.query.filter_by(is_verified=True)
    
    if category:
        query = query.filter_by(category=category)
    if city:
        query = query.join(User).filter(User.city.ilike(f'%{city}%'))
    
    providers = query.limit(10).all()
    
    results = []
    for provider in providers:
        results.append({
            'id': provider.id,
            'company_name': provider.company_name,
            'category': provider.category.value,
            'city': provider.user.city,
            'average_rating': float(provider.average_rating) if provider.average_rating else 0
        })
    
    return jsonify(results)