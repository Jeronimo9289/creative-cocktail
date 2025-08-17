# ================================
# app/tasks.py
# ================================

from app.celery_app import make_celery
from app import db, mail
from app.models.user import User
from app.models.notification import Notification
from app.models.newsletter import NewsletterCampaign, NewsletterSubscription
from app.services.notification_service import NotificationService
from app.services.newsletter_service import NewsletterService
from flask_mail import Message
from datetime import datetime, timedelta
import logging

celery = make_celery()

@celery.task
def send_email_async(subject, recipients, body, html_body=None):
    """Envoyer un email de manière asynchrone"""
    try:
        msg = Message(
            subject=subject,
            recipients=recipients,
            body=body,
            html=html_body
        )
        mail.send(msg)
        return f"Email envoyé à {', '.join(recipients)}"
    except Exception as e:
        logging.error(f"Erreur envoi email: {e}")
        return f"Erreur: {e}"

@celery.task
def send_newsletter_campaign(campaign_id):
    """Envoyer une campagne de newsletter"""
    try:
        campaign = NewsletterCampaign.query.get(campaign_id)
        if not campaign:
            return "Campagne non trouvée"
        
        result = NewsletterService.send_campaign(campaign_id)
        return f"Campagne envoyée à {result.sent_count} destinataires"
    except Exception as e:
        logging.error(f"Erreur envoi newsletter: {e}")
        return f"Erreur: {e}"

@celery.task
def process_event_reminders():
    """Traiter les rappels d'événements"""
    try:
        from app.models.event import Event
        
        # Événements dans 7 jours
        week_reminder_date = datetime.utcnow() + timedelta(days=7)
        events_week = Event.query.filter(
            Event.start_date.between(
                week_reminder_date.date(),
                week_reminder_date.date()
            )
        ).all()
        
        # Événements dans 1 jour
        day_reminder_date = datetime.utcnow() + timedelta(days=1)
        events_day = Event.query.filter(
            Event.start_date.between(
                day_reminder_date.date(),
                day_reminder_date.date()
            )
        ).all()
        
        reminders_sent = 0
        
        # Envoyer rappels 7 jours
        for event in events_week:
            send_event_reminder.delay(event.id, 7)
            reminders_sent += 1
        
        # Envoyer rappels 1 jour
        for event in events_day:
            send_event_reminder.delay(event.id, 1)
            reminders_sent += 1
        
        return f"{reminders_sent} rappels programmés"
        
    except Exception as e:
        logging.error(f"Erreur traitement rappels: {e}")
        return f"Erreur: {e}"

@celery.task
def send_event_reminder(event_id, days_remaining):
    """Envoyer un rappel d'événement"""
    try:
        from app.models.event import Event
        from flask import render_template, current_app
        
        event = Event.query.get(event_id)
        if not event:
            return "Événement non trouvé"
        
        user = event.organizer
        
        # Créer notification
        NotificationService.create_notification(
            user_id=user.id,
            notification_type='event_reminder',
            title=f"Rappel : {event.title}",
            message=f"Votre événement aura lieu dans {days_remaining} jour{'s' if days_remaining > 1 else ''}",
            link_url=f"/events/{event.id}"
        )
        
        # Envoyer email
        html_body = render_template('emails/event_reminder.html',
                                  event=event,
                                  user=user,
                                  days_remaining=days_remaining,
                                  event_url=f"{current_app.config['BASE_URL']}/events/{event.id}")
        
        send_email_async.delay(
            subject=f"Rappel : {event.title}",
            recipients=[user.email],
            body=f"Rappel : Votre événement {event.title} aura lieu dans {days_remaining} jour{'s' if days_remaining > 1 else ''}",
            html_body=html_body
        )
        
        return f"Rappel envoyé pour l'événement {event.title}"
        
    except Exception as e:
        logging.error(f"Erreur envoi rappel événement: {e}")
        return f"Erreur: {e}"

@celery.task
def cleanup_old_notifications():
    """Nettoyer les anciennes notifications"""
    try:
        # Supprimer les notifications lues de plus de 30 jours
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        old_notifications = Notification.query.filter(
            Notification.is_read == True,
            Notification.created_at < cutoff_date
        ).all()
        
        count = len(old_notifications)
        
        for notification in old_notifications:
            db.session.delete(notification)
        
        db.session.commit()
        
        return f"{count} anciennes notifications supprimées"
        
    except Exception as e:
        logging.error(f"Erreur nettoyage notifications: {e}")
        return f"Erreur: {e}"

@celery.task
def generate_monthly_stats():
    """Générer les statistiques mensuelles"""
    try:
        from app.services.statistics_service import StatisticsService
        
        # Générer rapport mensuel
        stats = StatisticsService.get_dashboard_stats()
        user_registrations = StatisticsService.get_user_registrations_by_month()
        
        # Envoyer rapport aux admins
        admins = User.query.filter_by(is_admin=True, is_active=True).all()
        
        for admin in admins:
            send_monthly_report.delay(admin.id, stats)
        
        return f"Rapport mensuel envoyé à {len(admins)} administrateurs"
        
    except Exception as e:
        logging.error(f"Erreur génération stats: {e}")
        return f"Erreur: {e}"

@celery.task
def send_monthly_report(admin_id, stats):
    """Envoyer le rapport mensuel à un admin"""
    try:
        admin = User.query.get(admin_id)
        if not admin:
            return "Admin non trouvé"
        
        # Template du rapport
        html_body = f"""
        <h2>Rapport mensuel Creative Cocktail</h2>
        <p>Bonjour {admin.first_name},</p>
        
        <h3>Statistiques du mois</h3>
        <ul>
            <li>Utilisateurs totaux : {stats['total_users']}</li>
            <li>Nouveaux utilisateurs ce mois : {stats['this_month_users']}</li>
            <li>Événements totaux : {stats['total_events']}</li>
            <li>Prestataires vérifiés : {stats['verified_providers']}</li>
        </ul>
        
        <p>Cordialement,<br>Le système Creative Cocktail</p>
        """
        
        send_email_async.delay(
            subject=f"Rapport mensuel Creative Cocktail - {datetime.now().strftime('%B %Y')}",
            recipients=[admin.email],
            body="Voir le rapport en HTML",
            html_body=html_body
        )
        
        return f"Rapport envoyé à {admin.email}"
        
    except Exception as e:
        logging.error(f"Erreur envoi rapport: {e}")
        return f"Erreur: {e}"

# Configuration périodique des tâches
celery.conf.beat_schedule = {
    'process-event-reminders': {
        'task': 'app.tasks.process_event_reminders',
        'schedule': 3600.0,  # Toutes les heures
    },
    'cleanup-old-notifications': {
        'task': 'app.tasks.cleanup_old_notifications',
        'schedule': 86400.0,  # Tous les jours
    },
    'generate-monthly-stats': {
        'task': 'app.tasks.generate_monthly_stats',
        'schedule': 2592000.0,  # Tous les mois
    },
}

celery.conf.timezone = 'Europe/Paris'