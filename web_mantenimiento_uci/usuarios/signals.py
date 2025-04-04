from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Incidencia, Notificacion

@receiver(post_save, sender=Incidencia)
def crear_notificacion(sender, instance, created, **kwargs):
    if created:  # Solo si es una nueva incidencia
        mensaje = f"Nueva incidencia: {instance.tipo}"
        Notificacion.objects.create(mensaje=mensaje)