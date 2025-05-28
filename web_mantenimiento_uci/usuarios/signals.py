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