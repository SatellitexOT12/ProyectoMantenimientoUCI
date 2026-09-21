"""Notificaciones dentro del sistema.

Cada notificación guarda en ``urlAsociated`` una ruta absoluta (con barra
inicial, generada con ``reverse``) a una página a la que su destinatario sí
puede entrar. Los textos se dirigen al destinatario de usted.
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.html import strip_tags

from .models import Incidencia, Notification, RespuestaSoporte, SolicitudSoporte
from .permisos import usuarios_administradores, usuarios_que_atienden_soporte


def notificar(usuario, mensaje, url):
    return Notification.objects.create(user=usuario, message=mensaje, urlAsociated=url)


def _texto_plano(texto):
    """Texto sin marcado: las notificaciones se guardan como texto plano y la
    interfaz puede mostrarlas sin riesgo (no llevan < ni >)."""
    return strip_tags(texto or '').replace('<', '').replace('>', '').strip()


def _resumen(texto, largo=50):
    texto = _texto_plano(texto)
    return texto[:largo] + ('...' if len(texto) > largo else '')


def _url_incidencias():
    return reverse('incidencias')


def _url_solicitud(solicitud):
    return reverse('detalle_solicitud', args=[solicitud.pk])


# --------------------------------------------------------------- incidencias

@receiver(pre_save, sender=Incidencia)
def recordar_valores_previos(sender, instance, **kwargs):
    """Guarda estado y técnico anteriores para detectar cambios en post_save."""
    instance._estado_previo = None
    instance._tecnico_previo_id = None
    if instance.pk:
        previo = (
            Incidencia.objects.filter(pk=instance.pk)
            .values('estado', 'tecnico_asignado_id')
            .first()
        )
        if previo:
            instance._estado_previo = previo['estado']
            instance._tecnico_previo_id = previo['tecnico_asignado_id']


@receiver(post_save, sender=Incidencia)
def notificar_incidencia(sender, instance, created, **kwargs):
    url = _url_incidencias()
    tipo = instance.get_tipo_display()

    if created:
        notificar(
            instance.usuario_reporte,
            f"Su incidencia n.º {instance.pk} ({tipo}) fue registrada. "
            "Un administrador la revisará y asignará un técnico.",
            url,
        )
        for admin in usuarios_administradores().exclude(pk=instance.usuario_reporte_id):
            notificar(
                admin,
                f"{instance.usuario_reporte.get_username()} ha reportado una nueva "
                f"incidencia n.º {instance.pk} ({tipo}) en {_texto_plano(instance.ubicacion)}. "
                "Confirme su prioridad y asigne un técnico.",
                url,
            )
        return

    # Técnico recién asignado (o cambiado).
    nuevo_tecnico = instance.tecnico_asignado_id
    if nuevo_tecnico and nuevo_tecnico != getattr(instance, '_tecnico_previo_id', None):
        notificar(
            instance.tecnico_asignado.trabajador,
            f"Se le asignó la incidencia n.º {instance.pk} ({tipo}) en "
            f"{_texto_plano(instance.ubicacion)}.",
            url,
        )

    # Cambio de estado: se avisa al solicitante.
    previo = getattr(instance, '_estado_previo', None)
    if previo is not None and previo != instance.estado:
        etiquetas = dict(Incidencia.ESTADO_CHOICES)
        notificar(
            instance.usuario_reporte,
            f"Su incidencia n.º {instance.pk} ({tipo}) cambió de estado: "
            f"{etiquetas.get(previo, previo)} a {instance.get_estado_display()}.",
            url,
        )


# ------------------------------------------------------------------- soporte

@receiver(pre_save, sender=SolicitudSoporte)
def recordar_respuesta_previa(sender, instance, **kwargs):
    instance._respuesta_previa = None
    if instance.pk:
        instance._respuesta_previa = (
            SolicitudSoporte.objects.filter(pk=instance.pk)
            .values_list('respuesta', flat=True)
            .first()
        )


@receiver(post_save, sender=SolicitudSoporte)
def notificar_solicitud(sender, instance, created, **kwargs):
    url = _url_solicitud(instance)
    if created:
        notificar(
            instance.usuario,
            f"Su solicitud de soporte fue recibida: {_resumen(instance.descripcion)}",
            url,
        )
        # Administradores y técnicos atienden el soporte.
        for atiende in usuarios_que_atienden_soporte().exclude(pk=instance.usuario_id):
            notificar(
                atiende,
                f"{instance.usuario.get_username()} ha enviado una nueva solicitud de soporte.",
                url,
            )
        return

    # Campo heredado «respuesta» (se rellena desde el sitio de administración).
    if instance.respuesta and instance.respuesta != getattr(instance, '_respuesta_previa', None):
        notificar(instance.usuario, "Se respondió su solicitud de soporte.", url)


@receiver(post_save, sender=RespuestaSoporte)
def notificar_respuesta(sender, instance, created, **kwargs):
    if not created:
        return
    solicitud = instance.solicitud
    autor = instance.autor
    url = _url_solicitud(solicitud)
    resumen = _resumen(instance.mensaje)

    if autor.pk == solicitud.usuario_id:
        # El solicitante escribió: se avisa a administradores y técnicos.
        for atiende in usuarios_que_atienden_soporte().exclude(pk=autor.pk):
            notificar(
                atiende,
                f"{autor.get_username()} escribió un mensaje en la solicitud de soporte "
                f"n.º {solicitud.pk}: {resumen}",
                url,
            )
    else:
        # Respondió un administrador o un técnico: se avisa a quien hizo la solicitud.
        notificar(
            solicitud.usuario,
            f"{autor.get_username()} respondió a su solicitud de soporte: {resumen}",
            url,
        )
