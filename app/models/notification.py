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