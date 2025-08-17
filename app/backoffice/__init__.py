# ================================
# app/backoffice/__init__.py
# ================================

from flask import Blueprint

bp = Blueprint('backoffice', __name__)

from app.backoffice import routes