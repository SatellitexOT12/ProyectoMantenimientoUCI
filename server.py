"""
Entry point para Vercel (Python Runtime).
Ejecuta migraciones al iniciar (DATABASE_URL solo está disponible en runtime)
y expone la aplicación WSGI de Django.
"""
import os
import sys

# Añadir el directorio del proyecto al path
PROJECT_DIR = os.path.join(os.path.dirname(__file__), 'web_mantenimiento_uci')
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web_mantenimiento_uci.settings')

# Migraciones en runtime: Vercel no expone env vars del dashboard durante
# buildCommand, solo en runtime. Por eso migrate va aquí.
print('[sgum] server.py importado — entrypoint activo', flush=True)
try:
    from django.core.management import call_command
    call_command('migrate', '--noinput')
    print('[sgum] migrate OK (server.py)', flush=True)
except Exception:
    # No bloquear el arranque si la BD no está lista aún,
    # pero dejar el error visible en `vercel logs`.
    import traceback
    print('[sgum] migrate FALLÓ (server.py):', flush=True)
    traceback.print_exc()

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
