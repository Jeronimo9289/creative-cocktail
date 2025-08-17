# ================================
# app/services/notification_service.py
# ================================

from flask import current_app, url_for
from app import db, mail
from app.models.notification import Notification, NotificationType
from flask_mail import Message
import json

class NotificationService:
    """Service de gestion des notifications"""
    
    @staticmethod
    def create_notification(user_id, notification_type, title, message, link_url=None, data=None):
        """Créer une nouvelle notification"""
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            link_url=link_url,
            data=json.dumps(data) if data else None
        )
        
        db.session.add(notification)
        db.session.commit()
        
        # Envoyer email si activé
        NotificationService.send_email_notification(notification)
        
        return notification
    
    @staticmethod
    def send_email_notification(notification):
        """Envoyer notification par email"""
        try:
            user = notification.user
            
            if not user.email:
                return
            
            # Template email selon le type
            subject = f"Creative Cocktail - {notification.title}"
            
            msg = Message(
                subject=subject,
                sender=current_app.config['MAIL_USERNAME'],
                recipients=[user.email]
            )
            
            # Corps du message
            msg.body = f"""
            Bonjour {user.get_full_name() or user.username},
            
            {notification.message}
            
            {f"Lien: {current_app.config['BASE_URL']}{notification.link_url}" if notification.link_url else ""}
            
            Cordialement,
            L'équipe Creative Cocktail
            """
            
            msg.html = f"""
            <h2>Bonjour {user.get_full_name() or user.username},</h2>
            <p>{notification.message}</p>
            {f'<p><a href="{current_app.config["BASE_URL"]}{notification.link_url}">Voir les détails</a></p>' if notification.link_url else ""}
            <p>Cordialement,<br>L'équipe Creative Cocktail</p>
            """
            
            mail.send(msg)
            
            notification.is_email_sent = True
            db.session.commit()
            
        except Exception as e:
            current_app.logger.error(f"Erreur envoi email notification: {e}")
    
    @staticmethod
    def notify_quote_received(client_id, provider_name, quote_id):
        """Notification de réception de devis"""
        NotificationService.create_notification(
            user_id=client_id,
            notification_type=NotificationType.QUOTE_RECEIVED,
            title="Nouveau devis reçu",
            message=f"Vous avez reçu un devis de {provider_name}",
            link_url=url_for('frontend.quote_detail', id=quote_id),
            data={'quote_id': quote_id}
        )
    
    @staticmethod
    def notify_quote_accepted(provider_id, client_name, quote_id):
        """Notification d'acceptation de devis"""
        NotificationService.create_notification(
            user_id=provider_id,
            notification_type=NotificationType.QUOTE_ACCEPTED,
            title="Devis accepté",
            message=f"{client_name} a accepté votre devis",
            link_url=url_for('frontend.quote_detail', id=quote_id),
            data={'quote_id': quote_id}
        )
    
    @staticmethod
    def notify_provider_verified(provider_id):
        """Notification de vérification de prestataire"""
        NotificationService.create_notification(
            user_id=provider_id,
            notification_type=NotificationType.PROVIDER_VERIFIED,
            title="Profil vérifié",
            message="Votre profil prestataire a été vérifié et est maintenant visible",