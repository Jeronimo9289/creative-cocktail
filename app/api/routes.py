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