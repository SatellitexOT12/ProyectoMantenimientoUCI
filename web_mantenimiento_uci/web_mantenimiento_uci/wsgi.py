"""
WSGI config for web_mantenimiento_uci project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web_mantenimiento_uci.settings')

# Migraciones en runtime: si Vercel resuelve el entrypoint vía la detección de
# manage.py + WSGI_APPLICATION, server.py nunca se importa — por eso migrate
# vive también aquí. Es idempotente y el error queda visible en `vercel logs`.
print('[sgum] wsgi.py importado — entrypoint activo', flush=True)
try:
    import django
    django.setup()  # poblar el registry de apps: call_command lo exige
    from django.core.management import call_command
    call_command('migrate', '--noinput')
    print('[sgum] migrate OK (wsgi.py)', flush=True)
except Exception:
    # No bloquear el arranque; el traceback queda en `vercel logs`.
    import traceback
    print('[sgum] migrate FALLÓ (wsgi.py):', flush=True)
    traceback.print_exc()

application = get_wsgi_application()
