# projects/security/validators.py
"""
Validadores de seguridad para el proyecto EYL
"""
import re
import logging
from django.core.exceptions import ValidationError
from django.utils.html import escape

# Logger de seguridad
security_logger = logging.getLogger('django.security')

def validate_project_id(project_id):
    """
    Validar formato seguro de project_id
    """
    if not project_id:
        raise ValidationError("Project ID is required")
    
    # Solo permitir caracteres alfanuméricos, guiones y guiones bajos
    if not re.match(r'^[a-zA-Z0-9\-_]+$', project_id):
        security_logger.warning(f"Invalid project ID format attempted: {escape(project_id)}")
        raise ValidationError("Invalid project ID format. Only alphanumeric characters, hyphens and underscores are allowed")
    
    if len(project_id) > 50:
        security_logger.warning(f"Project ID too long attempted: {len(project_id)} characters")
        raise ValidationError("Project ID too long (max 50 characters)")
    
    return project_id

def validate_search_query(query):
    """
    Validar consultas de búsqueda para prevenir inyección
    """
    if not query:
        return ""
    
    # Escapar caracteres peligrosos
    query = escape(query.strip())
    
    # Limitar longitud
    if len(query) > 100:
        query = query[:100]
    
    # Log búsquedas sospechosas
    if any(char in query for char in ['<', '>', '&', '"', "'", ';', '(', ')']):
        security_logger.warning(f"Potentially malicious search query: {query}")
    
    return query

def validate_date_range(date_from, date_to):
    """
    Validar rango de fechas
    """
    from datetime import datetime, timedelta
    
    if date_from and date_to:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            
            # Verificar que la fecha de inicio no sea mayor que la de fin
            if from_date > to_date:
                raise ValidationError("Start date cannot be after end date")
            
            # Verificar que el rango no sea mayor a 2 años
            if (to_date - from_date).days > 730:
                security_logger.warning(f"Large date range requested: {from_date} to {to_date}")
                raise ValidationError("Date range cannot exceed 2 years")
                
        except ValueError:
            raise ValidationError("Invalid date format. Use YYYY-MM-DD")
    
    return date_from, date_to

def validate_file_upload(file):
    """
    Validar archivos subidos
    """
    if not file:
        return True
    
    # Verificar tamaño (máximo 10MB)
    if file.size > 10 * 1024 * 1024:
        security_logger.warning(f"Large file upload attempted: {file.size} bytes")
        raise ValidationError("File too large. Maximum size is 10MB")
    
    # Verificar extensión
    allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.xlsx', '.xls', '.csv']
    file_extension = file.name.lower().split('.')[-1] if '.' in file.name else ''
    
    if f'.{file_extension}' not in allowed_extensions:
        security_logger.warning(f"Invalid file type attempted: {file.name}")
        raise ValidationError(f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}")
    
    return True

def sanitize_input(data):
    """
    Sanitizar entrada de datos
    """
    if isinstance(data, str):
        # Escapar HTML
        data = escape(data)
        # Remover caracteres de control
        data = ''.join(char for char in data if ord(char) >= 32 or char in '\t\n\r')
        # Limitar longitud
        data = data[:1000]
    
    return data

def validate_pagination_params(page, page_size):
    """
    Validar parámetros de paginación
    """
    try:
        page = int(page) if page else 1
        page_size = int(page_size) if page_size else 25
    except (ValueError, TypeError):
        raise ValidationError("Invalid pagination parameters")
    
    # Limitar tamaño de página
    if page_size > 100:
        security_logger.warning(f"Large page size requested: {page_size}")
        page_size = 100
    
    if page < 1:
        page = 1
    
    return page, page_size
