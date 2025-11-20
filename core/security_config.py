# core/security_config.py
"""
Configuraciones de seguridad adicionales para el proyecto EYL
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def get_security_headers():
    """
    Headers de seguridad adicionales
    """
    return {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
    }

def get_csp_policy():
    """
    Content Security Policy
    """
    return {
        'default-src': ["'self'"],
        'script-src': ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"],
        'style-src': ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"],
        'img-src': ["'self'", "data:", "https:"],
        'font-src': ["'self'", "https://cdn.jsdelivr.net"],
        'connect-src': ["'self'"],
        'frame-ancestors': ["'none'"],
    }

def get_rate_limits():
    """
    Límites de rate limiting por vista
    """
    return {
        'dashboard_view': '100/h',
        'grid_costos_variables': '200/h',
        'purchase_order_index': '300/h',
        'pre_sale': '100/h',
    }

def get_file_upload_limits():
    """
    Límites para archivos subidos
    """
    return {
        'max_size': 10 * 1024 * 1024,  # 10MB
        'allowed_types': [
            'application/pdf',
            'image/jpeg',
            'image/png',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'text/csv'
        ],
        'max_files_per_request': 5,
    }

def get_database_security():
    """
    Configuraciones de seguridad de base de datos
    """
    return {
        'connection_max_age': 0,  # No reutilizar conexiones
        'connection_health_checks': True,
        'autocommit': True,
    }

def get_cache_security():
    """
    Configuraciones de seguridad de cache
    """
    return {
        'key_prefix': 'eyl_secure_',
        'default_timeout': 300,  # 5 minutos
        'max_entries': 1000,
    }

def get_logging_security():
    """
    Configuraciones de logging de seguridad
    """
    return {
        'security_log_file': BASE_DIR / 'logs' / 'security.log',
        'access_log_file': BASE_DIR / 'logs' / 'access.log',
        'max_log_size': 10 * 1024 * 1024,  # 10MB
        'backup_count': 5,
        'log_rotation': 'daily',
    }

def get_environment_security():
    """
    Configuraciones de seguridad por ambiente
    """
    env = os.getenv('DJANGO_ENV', 'development')
    
    if env == 'production':
        return {
            'debug': False,
            'allowed_hosts': os.getenv('DJANGO_ALLOWED_HOSTS', '').split(','),
            'secure_ssl_redirect': True,
            'secure_hsts_seconds': 31536000,
            'secure_hsts_include_subdomains': True,
            'secure_hsts_preload': True,
            'secure_content_type_nosniff': True,
            'secure_browser_xss_filter': True,
            'x_frame_options': 'DENY',
            'session_cookie_secure': True,
            'csrf_cookie_secure': True,
        }
    elif env == 'staging':
        return {
            'debug': False,
            'allowed_hosts': ['staging.eyl.com'],
            'secure_ssl_redirect': True,
            'secure_hsts_seconds': 86400,  # 1 día
            'secure_hsts_include_subdomains': False,
            'secure_hsts_preload': False,
            'secure_content_type_nosniff': True,
            'secure_browser_xss_filter': True,
            'x_frame_options': 'SAMEORIGIN',
            'session_cookie_secure': True,
            'csrf_cookie_secure': True,
        }
    else:  # development
        return {
            'debug': True,
            'allowed_hosts': ['localhost', '127.0.0.1', '0.0.0.0'],
            'secure_ssl_redirect': False,
            'secure_hsts_seconds': 0,
            'secure_hsts_include_subdomains': False,
            'secure_hsts_preload': False,
            'secure_content_type_nosniff': True,
            'secure_browser_xss_filter': True,
            'x_frame_options': 'SAMEORIGIN',
            'session_cookie_secure': False,
            'csrf_cookie_secure': False,
        }
