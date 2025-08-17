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