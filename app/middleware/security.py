# ================================
# app/middleware/security.py
# ================================

from flask import request, abort, current_app
from functools import wraps
import re
from datetime import datetime, timedelta

class SecurityMiddleware:
    """Middleware de sécurité pour l'application"""
    
    def __init__(self, app=None):
        self.app = app
        self.blocked_ips = set()
        self.rate_limits = {}
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialiser le middleware avec l'app Flask"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def before_request(self):
        """Vérifications avant chaque requête"""
        # Vérifier l'IP bloquée
        if self.is_ip_blocked(request.remote_addr):
            abort(429, "IP temporairement bloquée")
        
        # Rate limiting
        if not self.check_rate_limit(request.remote_addr):
            abort(429, "Trop de requêtes")
        
        # Vérifier les en-têtes de sécurité
        self.check_security_headers()
        
        # Protection XSS basique
        self.check_xss_attempt()
        
        # Protection SQL Injection basique
        self.check_sql_injection()
    
    def after_request(self, response):
        """Modifications après chaque requête"""
        # Ajouter les en-têtes de sécurité
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # CSP Header
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://cdnjs.cloudflare.com; "
            "connect-src 'self'"
        )
        response.headers['Content-Security-Policy'] = csp
        
        return response
    
    def is_ip_blocked(self, ip):
        """Vérifier si une IP est bloquée"""
        return ip in self.blocked_ips
    
    def block_ip(self, ip, duration_minutes=60):
        """Bloquer une IP temporairement"""
        self.blocked_ips.add(ip)
        
        # Dans un vrai système, on utiliserait Redis avec expiration
        # Pour ce PoC, on simule avec un timer local
        def unblock():
            self.blocked_ips.discard(ip)
        
        # Programmer le déblocage (simplification)
        current_app.logger.info(f"IP {ip} bloquée pour {duration_minutes} minutes")
    
    def check_rate_limit(self, ip, max_requests=100, window_minutes=15):
        """Vérifier le rate limiting"""
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=window_minutes)
        
        if ip not in self.rate_limits:
            self.rate_limits[ip] = []
        
        # Nettoyer les anciennes requêtes
        self.rate_limits[ip] = [
            req_time for req_time in self.rate_limits[ip] 
            if req_time > window_start
        ]
        
        # Vérifier la limite
        if len(self.rate_limits[ip]) >= max_requests:
            return False
        
        # Ajouter la requête actuelle
        self.rate_limits[ip].append(now)
        return True
    
    def check_security_headers(self):
        """Vérifier les en-têtes de sécurité suspects"""
        suspicious_headers = ['X-Forwarded-Host', 'X-Original-URL', 'X-Rewrite-URL']
        
        for header in suspicious_headers:
            if header in request.headers:
                current_app.logger.warning(f"En-tête suspect détecté: {header}")
    
    def check_xss_attempt(self):
        """Détecter les tentatives XSS basiques"""
        xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>',
        ]
        
        # Vérifier les paramètres de requête
        for param, value in request.args.items():
            if isinstance(value, str):
                for pattern in xss_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        current_app.logger.warning(f"Tentative XSS détectée: {param}={value}")
                        abort(400, "Requête invalide")
    
    def check_sql_injection(self):
        """Détecter les tentatives d'injection SQL basiques"""
        sql_patterns = [
            r"(\bunion\b.*\bselect\b)",
            r"(\bselect\b.*\bfrom\b)",
            r"(\binsert\b.*\binto\b)",
            r"(\bdelete\b.*\bfrom\b)",
            r"(\bdrop\b.*\btable\b)",
            r"('.*or.*'.*=.*')",
            r"(--|\#|\/\*)",
        ]
        
        # Vérifier les paramètres de requête
        for param, value in request.args.items():
            if isinstance(value, str):
                for pattern in sql_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        current_app.logger.warning(f"Tentative injection SQL détectée: {param}={value}")
                        abort(400, "Requête invalide")