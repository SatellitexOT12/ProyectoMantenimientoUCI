"""Datos que el sistema necesita y correcciones de datos antiguos.

- Asegura los cuatro grupos de rol (instalaciones nuevas).
- Los incidentes con tipo «limpieza» (valor que el formulario antiguo ofrecía
  pero el modelo no tiene) pasan a «saneamiento».
- Cada incidencia tiene su Reporte, con la descripción real (antes texto fijo).
- Las notificaciones antiguas reciben una ruta absoluta y accesible.

Solo usa ORM portable (sirve igual en PostgreSQL y SQLite) y es idempotente.
"""
from django.db import migrations

GRUPOS = ('administrador', 'tecnico', 'almacenero', 'cliente')
TEXTO_FIJO_ANTIGUO = 'Reporte de Incidencia en el Servidor'


def crear_grupos(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    for nombre in GRUPOS:
        Group.objects.get_or_create(name=nombre)


def corregir_incidencias_y_reportes(apps, schema_editor):
    Incidencia = apps.get_model('usuarios', 'Incidencia')
    Reporte = apps.get_model('usuarios', 'Reporte')

    Incidencia.objects.filter(tipo='limpieza').update(tipo='saneamiento')

    con_reporte = set(
        Reporte.objects.filter(reporte_incidencia__isnull=False)
        .values_list('reporte_incidencia_id', flat=True)
    )
    faltantes = []
    for inc in Incidencia.objects.exclude(pk__in=con_reporte):
        faltantes.append(Reporte(
            reporte_incidencia=inc,
            fecha=inc.fecha,
            descripcion=inc.descripcion,
            estado=inc.estado,
        ))
    Reporte.objects.bulk_create(faltantes)

    for reporte in Reporte.objects.filter(reporte_incidencia__isnull=False).select_related('reporte_incidencia'):
        inc = reporte.reporte_incidencia
        cambios = []
        if reporte.descripcion.strip() == TEXTO_FIJO_ANTIGUO:
            reporte.descripcion = inc.descripcion
            cambios.append('descripcion')
        if reporte.estado != inc.estado:
            reporte.estado = inc.estado
            cambios.append('estado')
        if cambios:
            reporte.save(update_fields=cambios)


def normalizar_notificaciones(apps, schema_editor):
    Notification = apps.get_model('usuarios', 'Notification')
    User = apps.get_model('auth', 'User')
    admin_ids = set(
        User.objects.filter(groups__name='administrador').values_list('id', flat=True)
    ) | set(User.objects.filter(is_superuser=True).values_list('id', flat=True))

    for noti in Notification.objects.all():
        destino = (noti.urlAsociated or '').strip()
        if destino in ('', 'none'):
            nuevo = '/main/'
        elif destino.startswith('/'):
            continue
        else:
            nuevo = '/' + destino
            if not nuevo.endswith('/'):
                nuevo += '/'
            # La bandeja de soporte solo la abren los administradores.
            if nuevo == '/soporte/admin/' and noti.user_id not in admin_ids:
                nuevo = '/soporte/'
        if nuevo != noti.urlAsociated:
            noti.urlAsociated = nuevo
            noti.save(update_fields=['urlAsociated'])


def no_hacer_nada(apps, schema_editor):
    """Los datos corregidos no se pueden (ni conviene) volver al estado anterior."""


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('usuarios', '0033_prioridad_confirmada_y_fechas'),
    ]

    operations = [
        migrations.RunPython(crear_grupos, no_hacer_nada),
        migrations.RunPython(corregir_incidencias_y_reportes, no_hacer_nada),
        migrations.RunPython(normalizar_notificaciones, no_hacer_nada),
    ]
