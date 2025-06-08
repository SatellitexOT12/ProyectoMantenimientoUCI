from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Incidencia, Notification,SolicitudSoporte
from django.contrib.auth.models import Group, User
from django.utils.html import strip_tags
from django.utils import timezone

@receiver(post_save, sender=Incidencia)  # Cambia SomeModel por tu modelo real
def create_notification(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            user=instance.usuario_reporte,
            message=f"Nueva acción: Incidencia Reportada"
        )
    
    # Notificar al técnico solo si acaba de ser asignado
    if instance.tecnico_asignado and instance.tecnico_asignado.trabajador:
        # Verifica que no haya una notificación previa para esta incidencia y este técnico
        already_notified = Notification.objects.filter(
            user=instance.tecnico_asignado.trabajador,
            message__icontains=f"Incidencia: {instance.get_tipo_display()}"
        ).exists()


@receiver(post_save, sender=SolicitudSoporte)
def create_notification_on_solicitud(sender, instance, created, **kwargs):
    # Notificación al crear la solicitud
    if created:
        # Notificar al usuario que reportó
        Notification.objects.create(
            user=instance.usuario,
            message=f"Has enviado una nueva solicitud de soporte: {strip_tags(instance.descripcion[:50])}..."
        )

        # Notificar a todos los administradores
        admins = User.objects.filter(groups__name='administrador')
        for admin in admins:
            Notification.objects.create(
                user=admin,
                message=f"{instance.usuario.username} ha enviado una nueva solicitud de soporte."
            )

    # Notificar al usuario cuando se responde la solicitud
    if instance.respuesta and not hasattr(instance, '_respuesta_enviada'):
        if instance.fecha_respuesta is None or instance.fecha_respuesta < timezone.now():
            try:
                # Notificar al usuario si hay respuesta
                Notification.objects.create(
                    user=instance.usuario,
                    message=f"Se ha respondido tu solicitud de soporte."
                )
                
                # Marcar como notificado para evitar duplicados
                instance._respuesta_enviada = True
            except Exception as e:
                print("Error al enviar notificación:", str(e))