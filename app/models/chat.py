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