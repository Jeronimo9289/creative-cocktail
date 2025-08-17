# ================================
# app/frontend/forms.py
# ================================

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, BooleanField, SelectField, IntegerField, DecimalField, DateTimeField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional
from wtforms.widgets import TextArea
from app.models.user import UserType
from app.models.event import EventType

class LoginForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[DataRequired()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    remember_me = BooleanField('Se souvenir de moi')

class RegisterForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('Prénom', validators=[DataRequired()])
    last_name = StringField('Nom', validators=[DataRequired()])
    password = PasswordField('Mot de passe', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField('Confirmer le mot de passe', 
                             validators=[DataRequired(), EqualTo('password')])
    user_type = SelectField('Type de compte', 
                          choices=[(UserType.CLIENT.value, 'Client'), 
                                  (UserType.PROVIDER.value, 'Prestataire')],
                          default=UserType.CLIENT.value)
    
    def validate_username(self, username):
        from app.models.user import User
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Ce nom d\'utilisateur est déjà pris.')
    
    def validate_email(self, email):
        from app.models.user import User
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Cette adresse email est déjà utilisée.')

class EventForm(FlaskForm):
    title = StringField('Titre de l\'événement', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description')
    event_type = SelectField('Type d\'événement',
                            choices=[(EventType.PERSONAL.value, 'Particulier'),
                                   (EventType.PROFESSIONAL.value, 'Professionnel')],
                            validators=[DataRequired()])
    total_budget = DecimalField('Budget total (€)', validators=[Optional(), NumberRange(min=0)])
    expected_participants = IntegerField('Nombre de participants attendus', 
                                       validators=[Optional(), NumberRange(min=1)])
    start_date = DateTimeField('Date de début', validators=[Optional()])
    end_date = DateTimeField('Date de fin', validators=[Optional()])

class VenueForm(FlaskForm):
    name = StringField('Nom du lieu', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description')
    address = TextAreaField('Adresse', validators=[DataRequired()])
    postal_code = StringField('Code postal', validators=[Length(max=10)])
    city = StringField('Ville', validators=[DataRequired(), Length(max=100)])
    country = StringField('Pays', validators=[Length(max=100)])
    max_capacity = IntegerField('Capacité maximale', validators=[Optional(), NumberRange(min=1)])
    min_capacity = IntegerField('Capacité minimale', validators=[Optional(), NumberRange(min=1)])
    base_price = DecimalField('Prix de base (€)', validators=[Optional(), NumberRange(min=0)])
    contact_person = StringField('Personne de contact', validators=[Length(max=100)])
    phone = StringField('Téléphone', validators=[Length(max=20)])
    email = StringField('Email', validators=[Optional(), Email()])
    website = StringField('Site web', validators=[Length(max=200)])

# ================================
# app/backoffice/__init__.py
# ================================

from flask import Blueprint

bp = Blueprint('backoffice', __name__)

from app.backoffice import routes

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

# ================================
# app/backoffice/admin.py
# ================================

from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from app.models.user import User
from app.models.event import Event
from app.models.provider import Provider
from app.models.venue import Venue

class AdminModelView(ModelView):
    """Vue de base pour l'admin avec contrôle d'accès"""
    
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('frontend.login'))

class UserAdminView(AdminModelView):
    column_list = ['username', 'email', 'first_name', 'last_name', 'user_type', 'is_active', 'created_at']
    column_searchable_list = ['username', 'email', 'first_name', 'last_name']
    column_filters = ['user_type', 'is_active', 'created_at']
    form_excluded_columns = ['password_hash', 'last_login']

class EventAdminView(AdminModelView):
    column_list = ['title', 'organizer', 'event_type', 'status', 'start_date', 'total_budget']
    column_searchable_list = ['title', 'description']
    column_filters = ['event_type', 'status', 'created_at']

class ProviderAdminView(AdminModelView):
    column_list = ['company_name', 'user', 'category', 'is_verified', 'average_rating', 'created_at']
    column_searchable_list = ['company_name', 'description']
    column_filters = ['category', 'is_verified', 'created_at']

class VenueAdminView(AdminModelView):
    column_list = ['name', 'city', 'max_capacity', 'is_verified', 'is_active', 'created_at']
    column_searchable_list = ['name', 'city', 'address']
    column_filters = ['city', 'is_verified', 'is_active', 'created_at']

def setup_admin(admin, db):
    """Configuration de l'interface d'administration"""
    admin.add_view(UserAdminView(User, db.session, name='Utilisateurs'))
    admin.add_view(EventAdminView(Event, db.session, name='Événements'))
    admin.add_view(ProviderAdminView(Provider, db.session, name='Prestataires'))
    admin.add_view(VenueAdminView(Venue, db.session, name='Lieux'))