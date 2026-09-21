"""
Entry point para Vercel (Python Runtime).
Expone la aplicación WSGI de Django como 'application'.
"""
import os
import sys

# Añadir el directorio del proyecto al path para que Django encuentre el módulo
PROJECT_DIR = os.path.join(os.path.dirname(__file__), 'web_mantenimiento_uci')
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web_mantenimiento_uci.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
