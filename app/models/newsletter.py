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