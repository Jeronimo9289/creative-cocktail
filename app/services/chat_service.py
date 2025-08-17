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
    