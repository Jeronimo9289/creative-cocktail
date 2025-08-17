# ================================
# app/backoffice/routes.py
# ================================

from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.backoffice import bp
from app.models.user import User
from app.models.event import Event
from app.models.provider import Provider
from app.models.venue import Venue
from functools import wraps

def admin_required(f):
    """Décorateur pour vérifier les droits admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Accès refusé. Droits administrateur requis.', 'error')
            return redirect(url_for('frontend.index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@login_required
@admin_required
def dashboard():
    """Tableau de bord administrateur"""
    
    # Statistiques générales
    stats = {
        'total_users': User.query.count(),
        'total_events': Event.query.count(),
        'total_providers': Provider.query.count(),
        'total_venues': Venue.query.count(),
        'active_users': User.query.filter_by(is_active=True).count(),
        'verified_providers': Provider.query.filter_by(is_verified=True).count(),
        'pending_providers': Provider.query.filter_by(is_verified=False).count()
    }
    
    # Événements récents
    recent_events = Event.query.order_by(Event.created_at.desc()).limit(10).all()
    
    # Nouveaux utilisateurs
    new_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    
    return render_template('backoffice/dashboard.html', 
                         stats=stats,
                         recent_events=recent_events,
                         new_users=new_users)

@bp.route('/users')
@login_required
@admin_required
def users():
    """Gestion des utilisateurs"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    user_type = request.args.get('user_type', '')
    
    query = User.query
    
    if search:
        query = query.filter(
            User.username.ilike(f'%{search}%') |
            User.email.ilike(f'%{search}%') |
            User.first_name.ilike(f'%{search}%') |
            User.last_name.ilike(f'%{search}%')
        )
    
    if user_type:
        query = query.filter_by(user_type=user_type)
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, 
        per_page=20
    )
    
    return render_template('backoffice/users.html', users=users)

@bp.route('/users/<int:id>')
@login_required
@admin_required
def user_detail(id):
    """Détail d'un utilisateur"""
    user = User.query.get_or_404(id)
    return render_template('backoffice/user_detail.html', user=user)

@bp.route('/users/<int:id>/toggle_status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(id):
    """Activer/désactiver un utilisateur"""
    user = User.query.get_or_404(id)
    user.is_active = not user.is_active
    db.session.commit()
    
    status = "activé" if user.is_active else "désactivé"
    flash(f'Utilisateur {user.username} {status}', 'success')
    
    return redirect(url_for('backoffice.user_detail', id=id))

@bp.route('/providers')
@login_required
@admin_required
def providers():
    """Gestion des prestataires"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    category = request.args.get('category', '')
    
    query = Provider.query.join(User)
    
    if status == 'verified':
        query = query.filter_by(is_verified=True)
    elif status == 'pending':
        query = query.filter_by(is_verified=False)
    
    if category:
        query = query.filter_by(category=category)
    
    providers = query.order_by(Provider.created_at.desc()).paginate(
        page=page,
        per_page=20
    )
    
    return render_template('backoffice/providers.html', providers=providers)

@bp.route('/providers/<int:id>')
@login_required
@admin_required
def provider_detail(id):
    """Détail d'un prestataire"""
    provider = Provider.query.get_or_404(id)
    return render_template('backoffice/provider_detail.html', provider=provider)

@bp.route('/providers/<int:id>/verify', methods=['POST'])
@login_required
@admin_required
def verify_provider(id):
    """Vérifier un prestataire"""
    provider = Provider.query.get_or_404(id)
    provider.is_verified = True
    db.session.commit()
    
    flash(f'Prestataire {provider.company_name} vérifié', 'success')
    return redirect(url_for('backoffice.provider_detail', id=id))

@bp.route('/events')
@login_required
@admin_required
def events():
    """Gestion des événements"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    event_type = request.args.get('event_type', '')
    
    query = Event.query.join(User)
    
    if status:
        query = query.filter_by(status=status)
    if event_type:
        query = query.filter_by(event_type=event_type)
    
    events = query.order_by(Event.created_at.desc()).paginate(
        page=page,
        per_page=20
    )
    
    return render_template('backoffice/events.html', events=events)

@bp.route('/venues')
@login_required
@admin_required
def venues():
    """Gestion des lieux"""
    page = request.args.get('page', 1, type=int)
    city = request.args.get('city', '')
    
    query = Venue.query
    
    if city:
        query = query.filter(Venue.city.ilike(f'%{city}%'))
    
    venues = query.order_by(Venue.created_at.desc()).paginate(
        page=page,
        per_page=20
    )
    
    return render_template('backoffice/venues.html', venues=venues)

@bp.route('/statistics')
@login_required
@admin_required
def statistics():
    """Statistiques avancées"""
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    # Statistiques par mois
    monthly_stats = db.session.query(
        func.date_format(Event.created_at, '%Y-%m').label('month'),
        func.count(Event.id).label('events_count')
    ).group_by('month').order_by('month').all()
    
    # Répartition par type d'événement
    event_types = db.session.query(
        Event.event_type,
        func.count(Event.id).label('count')
    ).group_by(Event.event_type).all()
    
    # Top prestataires par notes
    top_providers = Provider.query.filter(Provider.total_ratings > 0)\
                                 .order_by(Provider.average_rating.desc())\
                                 .limit(10).all()
    
    return render_template('backoffice/statistics.html',
                         monthly_stats=monthly_stats,
                         event_types=event_types,
                         top_providers=top_providers)