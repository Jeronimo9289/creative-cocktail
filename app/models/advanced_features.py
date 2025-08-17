# ================================
# app/models/chat.py
# ================================

from app import db
from datetime import datetime
import enum

class ChatSession(db.Model):
    """Sessions de chat en ligne avec les conseillers"""
    __tablename__ = 'chat_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    advisor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Informations de session
    category = db.Column(db.String(50))  # technique, organisation, activité, etc.
    subject = db.Column(db.String(200))
    status = db.Column(db.String(20), default='waiting')  # waiting, active, closed
    
    # Dates
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)
    
    # Satisfaction
    client_rating = db.Column(db.Integer)  # 1-5
    client_feedback = db.Column(db.Text)
    
    # Relations
    client = db.relationship('User', foreign_keys=[client_id], backref='chat_sessions_as_client')
    advisor = db.relationship('User', foreign_keys=[advisor_id], backref='chat_sessions_as_advisor')
    messages = db.relationship('ChatMessage', backref='session', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ChatSession {self.id}>'

class ChatMessage(db.Model):
    """Messages de chat"""
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_sessions.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    message = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(20), default='text')  # text, link, file
    
    # Statut
    is_read = db.Column(db.Boolean, default=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    sender = db.relationship('User', backref='chat_messages')
    
    def __repr__(self):
        return f'<ChatMessage {self.id}>'

# ================================
# app/models/notification.py
# ================================

class NotificationType(enum.Enum):
    QUOTE_RECEIVED = "quote_received"
    QUOTE_ACCEPTED = "quote_accepted"
    QUOTE_DECLINED = "quote_declined"
    EVENT_REMINDER = "event_reminder"
    PROVIDER_VERIFIED = "provider_verified"
    NEW_RATING = "new_rating"
    SYSTEM_UPDATE = "system_update"

class Notification(db.Model):
    """Système de notifications"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Contenu
    type = db.Column(db.Enum(NotificationType), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text)
    
    # Liens et données
    link_url = db.Column(db.String(300))
    data = db.Column(db.Text)  # JSON avec données additionnelles
    
    # Statut
    is_read = db.Column(db.Boolean, default=False)
    is_email_sent = db.Column(db.Boolean, default=False)
    
    # Dates
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime)
    
    # Relations
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic'))
    
    def mark_as_read(self):
        """Marquer comme lu"""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.utcnow()
            db.session.commit()
    
    def __repr__(self):
        return f'<Notification {self.id}: {self.title}>'

# ================================
# app/models/newsletter.py
# ================================

class NewsletterSubscription(db.Model):
    """Abonnements aux newsletters"""
    __tablename__ = 'newsletter_subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Types d'abonnement
    newsletter_type = db.Column(db.String(50), default='general')  # general, providers, events
    is_active = db.Column(db.Boolean, default=True)
    
    # Préférences
    frequency = db.Column(db.String(20), default='weekly')  # daily, weekly, monthly
    
    # Dates
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)
    unsubscribed_at = db.Column(db.DateTime)
    
    # Token pour désabonnement
    unsubscribe_token = db.Column(db.String(100), unique=True)
    
    # Relations
    user = db.relationship('User', backref='newsletter_subscriptions')
    
    def __repr__(self):
        return f'<NewsletterSubscription {self.email}>'

class NewsletterCampaign(db.Model):
    """Campagnes de newsletter"""
    __tablename__ = 'newsletter_campaigns'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Contenu
    title = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    content_html = db.Column(db.Text)
    content_text = db.Column(db.Text)
    
    # Ciblage
    target_type = db.Column(db.String(50))  # all, clients, providers, custom
    target_criteria = db.Column(db.Text)  # JSON avec critères
    
    # Statut
    status = db.Column(db.String(20), default='draft')  # draft, scheduled, sending, sent
    
    # Statistiques
    recipients_count = db.Column(db.Integer, default=0)
    sent_count = db.Column(db.Integer, default=0)
    opened_count = db.Column(db.Integer, default=0)
    clicked_count = db.Column(db.Integer, default=0)
    
    # Dates
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    scheduled_at = db.Column(db.DateTime)
    sent_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<NewsletterCampaign {self.title}>'

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
            link_url=url_for('frontend.provider_profile')
        )

# ================================
# app/services/chat_service.py
# ================================

from app.models.chat import ChatSession, ChatMessage
from app.models.user import User, UserType
import json

class ChatService:
    """Service de gestion du chat"""
    
    @staticmethod
    def start_chat_session(client_id, category, subject):
        """Démarrer une session de chat"""
        session = ChatSession(
            client_id=client_id,
            category=category,
            subject=subject,
            status='waiting'
        )
        
        db.session.add(session)
        db.session.commit()
        
        # Assigner un conseiller disponible
        ChatService.assign_advisor(session)
        
        return session
    
    @staticmethod
    def assign_advisor(session):
        """Assigner un conseiller à la session"""
        # Logique simple : prendre le premier admin disponible
        # Dans un vrai système, on aurait une gestion plus sophistiquée
        advisor = User.query.filter_by(is_admin=True, is_active=True).first()
        
        if advisor:
            session.advisor_id = advisor.id
            session.status = 'active'
            db.session.commit()
            
            # Créer message de bienvenue
            welcome_msg = ChatMessage(
                session_id=session.id,
                sender_id=advisor.id,
                message=f"Bonjour ! Je suis {advisor.get_full_name()}, votre conseiller pour cette session. Comment puis-je vous aider ?",
                message_type='text'
            )
            
            db.session.add(welcome_msg)
            db.session.commit()
    
    @staticmethod
    def send_message(session_id, sender_id, message, message_type='text'):
        """Envoyer un message dans le chat"""
        chat_message = ChatMessage(
            session_id=session_id,
            sender_id=sender_id,
            message=message,
            message_type=message_type
        )
        
        db.session.add(chat_message)
        db.session.commit()
        
        return chat_message
    
    @staticmethod
    def close_session(session_id, rating=None, feedback=None):
        """Fermer une session de chat"""
        session = ChatSession.query.get(session_id)
        if session:
            session.status = 'closed'
            session.ended_at = datetime.utcnow()
            
            if rating:
                session.client_rating = rating
            if feedback:
                session.client_feedback = feedback
                
            db.session.commit()
        
        return session
    
    @staticmethod
    def get_session_history(session_id):
        """Récupérer l'historique d'une session"""
        session = ChatSession.query.get_or_404(session_id)
        messages = session.messages.order_by(ChatMessage.sent_at.asc()).all()
        
        return {
            'session': session,
            'messages': messages
        }

# ================================
# app/services/newsletter_service.py
# ================================

from app.models.newsletter import NewsletterSubscription, NewsletterCampaign
import uuid

class NewsletterService:
    """Service de gestion des newsletters"""
    
    @staticmethod
    def subscribe(email, newsletter_type='general', user_id=None):
        """S'abonner à la newsletter"""
        # Vérifier si déjà abonné
        existing = NewsletterSubscription.query.filter_by(
            email=email,
            newsletter_type=newsletter_type
        ).first()
        
        if existing:
            if not existing.is_active:
                existing.is_active = True
                existing.subscribed_at = datetime.utcnow()
                existing.unsubscribed_at = None
                db.session.commit()
            return existing
        
        subscription = NewsletterSubscription(
            email=email,
            user_id=user_id,
            newsletter_type=newsletter_type,
            unsubscribe_token=str(uuid.uuid4())
        )
        
        db.session.add(subscription)
        db.session.commit()
        
        return subscription
    
    @staticmethod
    def unsubscribe(email, newsletter_type=None, token=None):
        """Se désabonner de la newsletter"""
        query = NewsletterSubscription.query.filter_by(email=email, is_active=True)
        
        if newsletter_type:
            query = query.filter_by(newsletter_type=newsletter_type)
        
        if token:
            query = query.filter_by(unsubscribe_token=token)
        
        subscriptions = query.all()
        
        for subscription in subscriptions:
            subscription.is_active = False
            subscription.unsubscribed_at = datetime.utcnow()
        
        db.session.commit()
        
        return len(subscriptions)
    
    @staticmethod
    def create_campaign(title, subject, content_html, content_text, target_type='all'):
        """Créer une campagne de newsletter"""
        campaign = NewsletterCampaign(
            title=title,
            subject=subject,
            content_html=content_html,
            content_text=content_text,
            target_type=target_type
        )
        
        db.session.add(campaign)
        db.session.commit()
        
        return campaign
    
    @staticmethod
    def send_campaign(campaign_id):
        """Envoyer une campagne de newsletter"""
        campaign = NewsletterCampaign.query.get_or_404(campaign_id)
        
        # Récupérer les destinataires selon le ciblage
        if campaign.target_type == 'all':
            subscriptions = NewsletterSubscription.query.filter_by(is_active=True).all()
        elif campaign.target_type == 'clients':
            subscriptions = NewsletterSubscription.query.join(User).filter(
                NewsletterSubscription.is_active == True,
                User.user_type == UserType.CLIENT
            ).all()
        elif campaign.target_type == 'providers':
            subscriptions = NewsletterSubscription.query.join(User).filter(
                NewsletterSubscription.is_active == True,
                User.user_type == UserType.PROVIDER
            ).all()
        else:
            subscriptions = []
        
        campaign.recipients_count = len(subscriptions)
        campaign.status = 'sending'
        db.session.commit()
        
        # Dans un vrai système, on utiliserait Celery pour l'envoi en arrière-plan
        sent_count = 0
        for subscription in subscriptions:
            try:
                NewsletterService._send_email_to_subscriber(campaign, subscription)
                sent_count += 1
            except Exception as e:
                current_app.logger.error(f"Erreur envoi newsletter à {subscription.email}: {e}")
        
        campaign.sent_count = sent_count
        campaign.status = 'sent'
        campaign.sent_at = datetime.utcnow()
        db.session.commit()
        
        return campaign

    @staticmethod
    def _send_email_to_subscriber(campaign, subscription):
        """Envoyer l'email à un abonné"""
        unsubscribe_url = url_for('frontend.newsletter_unsubscribe', 
                                 token=subscription.unsubscribe_token, 
                                 _external=True)
        
        # Personnaliser le contenu
        content_html = campaign.content_html.replace(
            '{{unsubscribe_url}}', unsubscribe_url
        ).replace(
            '{{email}}', subscription.email
        )
        
        content_text = campaign.content_text.replace(
            '{{unsubscribe_url}}', unsubscribe_url
        ).replace(
            '{{email}}', subscription.email
        )
        
        msg = Message(
            subject=campaign.subject,
            sender=current_app.config['MAIL_USERNAME'],
            recipients=[subscription.email]
        )
        
        msg.body = content_text
        msg.html = content_html
        
        mail.send(msg)

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