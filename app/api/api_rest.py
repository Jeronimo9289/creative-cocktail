# ================================
# app/api/__init__.py
# ================================

from flask import Blueprint

bp = Blueprint('api', __name__)

from app.api import routes

# ================================
# app/api/routes.py
# ================================

from flask import jsonify, request, current_app
from flask_login import login_required, current_user
from app import db
from app.api import bp
from app.models.user import User
from app.models.event import Event
from app.models.venue import Venue
from app.models.provider import Provider, ProviderRating
from app.models.services import Quote, QuoteItem
from datetime import datetime, timedelta
import json

# ================================
# ENDPOINTS DE RECHERCHE
# ================================

@bp.route('/search/venues')
def search_venues():
    """API de recherche de lieux"""
    query = request.args.get('q', '')
    city = request.args.get('city', '')
    capacity = request.args.get('capacity', type=int)
    
    venues_query = Venue.query.filter_by(is_active=True)
    
    if query:
        venues_query = venues_query.filter(
            Venue.name.ilike(f'%{query}%') |
            Venue.description.ilike(f'%{query}%')
        )
    if city:
        venues_query = venues_query.filter(Venue.city.ilike(f'%{city}%'))
    if capacity:
        venues_query = venues_query.filter(Venue.max_capacity >= capacity)
    
    venues = venues_query.limit(10).all()
    
    results = []
    for venue in venues:
        results.append({
            'id': venue.id,
            'name': venue.name,
            'city': venue.city,
            'address': venue.address,
            'max_capacity': venue.max_capacity,
            'base_price': float(venue.base_price) if venue.base_price else None,
            'is_verified': venue.is_verified
        })
    
    return jsonify(results)

@bp.route('/search/providers')
def search_providers():
    """API de recherche de prestataires"""
    query = request.args.get('q', '')
    category = request.args.get('category', '')
    city = request.args.get('city', '')
    
    providers_query = Provider.query.filter_by(is_verified=True).join(User)
    
    if query:
        providers_query = providers_query.filter(
            Provider.company_name.ilike(f'%{query}%') |
            Provider.description.ilike(f'%{query}%')
        )
    if category:
        providers_query = providers_query.filter_by(category=category)
    if city:
        providers_query = providers_query.filter(User.city.ilike(f'%{city}%'))
    
    providers = providers_query.order_by(
        Provider.is_premium.desc(),
        Provider.average_rating.desc()
    ).limit(10).all()
    
    results = []
    for provider in providers:
        results.append({
            'id': provider.id,
            'company_name': provider.company_name,
            'category': provider.category.value,
            'city': provider.user.city,
            'average_rating': float(provider.average_rating) if provider.average_rating else 0,
            'total_ratings': provider.total_ratings,
            'is_premium': provider.is_premium,
            'base_price': float(provider.base_price) if provider.base_price else None
        })
    
    return jsonify(results)

# ================================
# GESTION DES DEVIS
# ================================

@bp.route('/quotes/request', methods=['POST'])
@login_required
def request_quote():
    """Demander un devis à un prestataire"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Données manquantes'}), 400
    
    provider_id = data.get('provider_id')
    event_id = data.get('event_id')
    
    # Vérifications
    provider = Provider.query.get_or_404(provider_id)
    event = Event.query.filter_by(id=event_id, organizer_id=current_user.id).first()
    
    if not event:
        return jsonify({'error': 'Événement non trouvé'}), 404
    
    # Générer un numéro de devis unique
    quote_number = f"DEV-{datetime.now().strftime('%Y%m%d')}-{Quote.query.count() + 1:04d}"
    
    # Créer le devis
    quote = Quote(
        quote_number=quote_number,
        event_id=event.id,
        provider_id=provider.id,
        client_id=current_user.id,
        category=provider.category.value,
        request_details=json.dumps({
            'description': data.get('description', ''),
            'date': data.get('date', ''),
            'participants': data.get('participants', 0),
            'budget': data.get('budget', 0),
            'special_requirements': data.get('special_requirements', '')
        }),
        client_message=data.get('description', ''),
        expires_at=datetime.utcnow() + timedelta(days=30)
    )
    
    db.session.add(quote)
    db.session.commit()
    
    # TODO: Envoyer notification email au prestataire
    
    return jsonify({
        'message': 'Demande de devis envoyée avec succès',
        'quote_number': quote_number
    })

@bp.route('/quotes/<int:quote_id>/respond', methods=['POST'])
@login_required
def respond_quote(quote_id):
    """Répondre à une demande de devis (prestataire)"""
    quote = Quote.query.get_or_404(quote_id)
    
    # Vérifier que l'utilisateur est le prestataire concerné
    if quote.provider.user_id != current_user.id:
        return jsonify({'error': 'Non autorisé'}), 403
    
    data = request.get_json()
    
    quote.quoted_price = data.get('price')
    quote.provider_message = data.get('message', '')
    quote.response_details = json.dumps(data.get('details', {}))
    quote.status = 'responded'
    quote.responded_at = datetime.utcnow()
    
    # Ajouter les éléments du devis
    items = data.get('items', [])
    for item_data in items:
        item = QuoteItem(
            quote_id=quote.id,
            description=item_data['description'],
            quantity=item_data.get('quantity', 1),
            unit_price=item_data['unit_price'],
            total_price=item_data['quantity'] * item_data['unit_price']
        )
        db.session.add(item)
    
    db.session.commit()
    
    # TODO: Envoyer notification email au client
    
    return jsonify({'message': 'Réponse envoyée avec succès'})

@bp.route('/quotes/<int:quote_id>/accept', methods=['POST'])
@login_required
def accept_quote(quote_id):
    """Accepter un devis (client)"""
    quote = Quote.query.get_or_404(quote_id)
    
    # Vérifier que l'utilisateur est le client
    if quote.client_id != current_user.id:
        return jsonify({'error': 'Non autorisé'}), 403
    
    quote.status = 'accepted'
    db.session.commit()
    
    return jsonify({'message': 'Devis accepté'})

@bp.route('/quotes/<int:quote_id>/decline', methods=['POST'])
@login_required
def decline_quote(quote_id):
    """Refuser un devis"""
    quote = Quote.query.get_or_404(quote_id)
    data = request.get_json()
    
    # Vérifier les autorisations
    if quote.client_id != current_user.id and quote.provider.user_id != current_user.id:
        return jsonify({'error': 'Non autorisé'}), 403
    
    quote.status = 'declined'
    quote.decline_reason = data.get('reason', '')
    db.session.commit()
    
    return jsonify({'message': 'Devis refusé'})

# ================================
# GESTION DES NOTES
# ================================

@bp.route('/ratings', methods=['POST'])
@login_required
def create_rating():
    """Créer une note pour un prestataire"""
    data = request.get_json()
    
    provider_id = data.get('provider_id')
    event_id = data.get('event_id')
    rating_value = data.get('rating')
    
    if not all([provider_id, rating_value]):
        return jsonify({'error': 'Données manquantes'}), 400
    
    if not (1 <= rating_value <= 5):
        return jsonify({'error': 'Note invalide (1-5)'}), 400
    
    # Vérifier que l'utilisateur a bien utilisé ce prestataire
    if event_id:
        event = Event.query.filter_by(id=event_id, organizer_id=current_user.id).first()
        if not event:
            return jsonify({'error': 'Événement non autorisé'}), 403
    
    # Vérifier qu'il n'y a pas déjà une note
    existing_rating = ProviderRating.query.filter_by(
        provider_id=provider_id,
        user_id=current_user.id,
        event_id=event_id
    ).first()
    
    if existing_rating:
        return jsonify({'error': 'Vous avez déjà noté ce prestataire'}), 400
    
    rating = ProviderRating(
        provider_id=provider_id,
        user_id=current_user.id,
        event_id=event_id,
        rating=rating_value,
        reactivity=data.get('reactivity'),
        price=data.get('price'),
        service_quality=data.get('service_quality'),
        welcome=data.get('welcome'),
        comment=data.get('comment', '')
    )
    
    db.session.add(rating)
    db.session.commit()
    
    # Mettre à jour la note moyenne du prestataire
    provider = Provider.query.get(provider_id)
    provider.update_rating()
    
    return jsonify({'message': 'Note enregistrée avec succès'})

# ================================
# CALENDRIER / AGENDA
# ================================

@bp.route('/events/calendar')
@login_required
def calendar_events():
    """API pour l'agenda - retourne les événements de l'utilisateur"""
    start = request.args.get('start')
    end = request.args.get('end')
    
    query = Event.query.filter_by(organizer_id=current_user.id)
    
    if start:
        start_date = datetime.fromisoformat(start.replace('Z', '+00:00'))
        query = query.filter(Event.start_date >= start_date)
    
    if end:
        end_date = datetime.fromisoformat(end.replace('Z', '+00:00'))
        query = query.filter(Event.end_date <= end_date)
    
    events = query.all()
    
    calendar_events = []
    for event in events:
        calendar_events.append({
            'id': f'event-{event.id}',
            'title': event.title,
            'start': event.start_date.isoformat() if event.start_date else None,
            'end': event.end_date.isoformat() if event.end_date else None,
            'color': '#0d6efd',
            'extendedProps': {
                'eventId': event.id,
                'status': event.status.value,
                'type': event.event_type.value
            }
        })
    
    return jsonify(calendar_events)

@bp.route('/tasks/calendar')
@login_required
def calendar_tasks():
    """API pour l'agenda - retourne les tâches de l'utilisateur"""
    from app.models.organization import EventTask
    
    start = request.args.get('start')
    end = request.args.get('end')
    
    # Récupérer les tâches des événements de l'utilisateur
    query = EventTask.query.join(Event).filter(Event.organizer_id == current_user.id)
    
    if start:
        start_date = datetime.fromisoformat(start.replace('Z', '+00:00'))
        query = query.filter(EventTask.due_date >= start_date)
    
    if end:
        end_date = datetime.fromisoformat(end.replace('Z', '+00:00'))
        query = query.filter(EventTask.due_date <= end_date)
    
    tasks = query.all()
    
    calendar_tasks = []
    for task in tasks:
        color = {
            'pending': '#ffc107',
            'in_progress': '#0dcaf0',
            'completed': '#198754',
            'cancelled': '#dc3545'
        }.get(task.status, '#6c757d')
        
        calendar_tasks.append({
            'id': f'task-{task.id}',
            'title': f'📋 {task.title}',
            'start': task.due_date.isoformat() if task.due_date else None,
            'color': color,
            'extendedProps': {
                'taskId': task.id,
                'eventId': task.event_id,
                'status': task.status,
                'type': 'task'
            }
        })
    
    return jsonify(calendar_tasks)

# ================================
# STATISTIQUES
# ================================

@bp.route('/stats/dashboard')
@login_required
def dashboard_stats():
    """Statistiques pour le tableau de bord"""
    user_events = Event.query.filter_by(organizer_id=current_user.id).all()
    
    stats = {
        'total_events': len(user_events),
        'active_events': len([e for e in user_events if e.status.value in ['pending', 'confirmed', 'in_progress']]),
        'completed_events': len([e for e in user_events if e.status.value == 'completed']),
        'total_budget': sum([e.total_budget or 0 for e in user_events]),
        'this_month_events': len([e for e in user_events if e.created_at.month == datetime.now().month]),
        'budget_by_category': {
            'venues': 0,  # À calculer depuis les EventVenue
            'catering': 0,  # À calculer depuis les EventCatering
            'transport': 0,  # À calculer depuis les EventTransport
            'decoration': 0,  # À calculer depuis les EventDecoration
            'animation': 0,  # À calculer depuis les EventActivity
            'technical': 0,  # À calculer depuis les EventTechnical
            'communication': 0,  # À calculer depuis les EventCommunication
            'other': 0
        }
    }
    
    return jsonify(stats)

# ================================
# NOTIFICATIONS
# ================================

@bp.route('/notifications')
@login_required
def get_notifications():
    """Récupérer les notifications de l'utilisateur"""
    # TODO: Implémenter un système de notifications
    notifications = [
        {
            'id': 1,
            'type': 'quote_received',
            'title': 'Nouveau devis reçu',
            'message': 'Vous avez reçu un devis pour votre événement',
            'created_at': datetime.now().isoformat(),
            'is_read': False
        }
    ]
    
    return jsonify(notifications)

@bp.route('/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Marquer une notification comme lue"""
    # TODO: Implémenter
    return jsonify({'message': 'Notification marquée comme lue'})

# ================================
# EXPORT DE DONNÉES
# ================================

@bp.route('/export/event/<int:event_id>')
@login_required
def export_event(event_id):
    """Exporter un événement en JSON"""
    event = Event.query.filter_by(id=event_id, organizer_id=current_user.id).first_or_404()
    
    export_data = {
        'event': {
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'event_type': event.event_type.value,
            'status': event.status.value,
            'start_date': event.start_date.isoformat() if event.start_date else None,
            'end_date': event.end_date.isoformat() if event.end_date else None,
            'total_budget': float(event.total_budget) if event.total_budget else None,
            'expected_participants': event.expected_participants
        },
        'venues': [
            {
                'id': v.id,
                'name': v.custom_name,
                'purpose': v.purpose,
                'start_datetime': v.start_datetime.isoformat() if v.start_datetime else None,
                'end_datetime': v.end_datetime.isoformat() if v.end_datetime else None,
                'cost': float(v.cost) if v.cost else None
            }
            for v in event.venues
        ],
        'participants': [
            {
                'id': p.id,
                'first_name': p.first_name,
                'last_name': p.last_name,
                'email': p.email,
                'status': p.status,
                'group_name': p.group_name
            }
            for p in event.participants
        ]
        # Ajouter autres onglets...
    }
    
    return jsonify(export_data)

# ================================
# UPLOAD DE FICHIERS
# ================================

@bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """Upload de fichiers (images, documents)"""
    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Aucun fichier sélectionné'}), 400
    
    # Vérifications de sécurité
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'xls', 'xlsx'}
    if not ('.' in file.filename and 
            file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
        return jsonify({'error': 'Type de fichier non autorisé'}), 400
    
    # Générer un nom unique
    import uuid
    filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
    
    # Sauvegarder le fichier
    import os
    upload_folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)
    
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)
    
    return jsonify({
        'filename': filename,
        'url': f'/static/uploads/{filename}',
        'size': os.path.getsize(file_path)
    })

# ================================
# GESTION D'ERREURS API
# ================================

@bp.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Requête invalide'}), 400

@bp.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'Non autorisé'}), 401

@bp.errorhandler(403)
def forbidden(error):
    return jsonify({'error': 'Accès interdit'}), 403

@bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Ressource non trouvée'}), 404

@bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Erreur interne du serveur'}), 500