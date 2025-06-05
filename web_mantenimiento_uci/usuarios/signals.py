from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Incidencia, Notification

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

        if not already_notified:
            Notification.objects.create(
                user=instance.tecnico_asignado.trabajador,
                message=f"Se te ha asignado una nueva incidencia: {instance.get_tipo_display()}"
            )