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