# ================================
# app/services/statistics_service.py
# ================================

from sqlalchemy import func, extract
from app.models.user import User
from app.models.event import Event
from app.models.provider import Provider
from datetime import datetime, timedelta

class StatisticsService:
    """Service de statistiques avancées"""
    
    @staticmethod
    def get_dashboard_stats():
        """Statistiques pour le dashboard admin"""
        return {
            'total_users': User.query.count(),
            'total_events': Event.query.count(),
            'total_providers': Provider.query.count(),
            'active_users': User.query.filter_by(is_active=True).count(),
            'verified_providers': Provider.query.filter_by(is_verified=True).count(),
            'pending_providers': Provider.query.filter_by(is_verified=False).count(),
            'this_month_users': User.query.filter(
                extract('month', User.created_at) == datetime.now().month,
                extract('year', User.created_at) == datetime.now().year
            ).count()
        }
    
    @staticmethod
    def get_user_registrations_by_month(year=None):
        """Inscriptions d'utilisateurs par mois"""
        if not year:
            year = datetime.now().year
        
        query = db.session.query(
            extract('month', User.created_at).label('month'),
            func.count(User.id).label('count')
        ).filter(
            extract('year', User.created_at) == year
        ).group_by('month').order_by('month')
        
        return query.all()
    
    @staticmethod
    def get_events_by_type():
        """Répartition des événements par type"""
        return db.session.query(
            Event.event_type,
            func.count(Event.id).label('count')
        ).group_by(Event.event_type).all()
    
    @staticmethod
    def get_providers_by_category():
        """Répartition des prestataires par catégorie"""
        return db.session.query(
            Provider.category,
            func.count(Provider.id).label('count')
        ).group_by(Provider.category).all()
    
    @staticmethod
    def get_top_rated_providers(limit=10):
        """Top des prestataires les mieux notés"""
        return Provider.query.filter(
            Provider.total_ratings > 0
        ).order_by(
            Provider.average_rating.desc(),
            Provider.total_ratings.desc()
        ).limit(limit).all()
    
    @staticmethod
    def get_monthly_revenue(year=None):
        """Chiffre d'affaires mensuel estimé (basé sur les budgets des événements)"""
        if not year:
            year = datetime.now().year
        
        query = db.session.query(
            extract('month', Event.created_at).label('month'),
            func.sum(Event.total_budget).label('total_budget')
        ).filter(
            extract('year', Event.created_at) == year,
            Event.total_budget.isnot(None)
        ).group_by('month').order_by('month')
        
        return query.all()