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
from app.models.notification import Notification
from app.models.newsletter import NewsletterSubscription
from app.services.newsletter_service import NewsletterService
from app import db
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