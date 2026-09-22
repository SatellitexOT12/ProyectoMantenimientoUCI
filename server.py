"""
Entry point para Vercel (Python Runtime).
Ejecuta migraciones al inicio y expone la aplicación WSGI de Django.
"""
import os
import sys

# Añadir el directorio del proyecto al path
PROJECT_DIR = os.path.join(os.path.dirname(__file__), 'web_mantenimiento_uci')
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web_mantenimiento_uci.settings')

# Ejecutar migraciones al iniciar (Vercel: build ≠ runtime)
from django.core.management import call_command
call_command('migrate', '--noinput', verbosity=0)

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
