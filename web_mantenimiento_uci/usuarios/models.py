from django.db import models
from django.contrib.auth.models import User

# Create your models here

class Incidencia(models.Model):
    
    PRIORIDAD_CHOICES = [
        ('alta', 'Alta'),
        ('media', 'Media'),
        ('baja', 'Baja'),
    ]
    
    TIPO_CHOICES = [
        ('plomeria', 'Plomeria'),
        ('electricidad', 'Electricidad'),
        ('infraestructura', 'Infraestructura'),
        ('mantenimiento_equipos', 'Mantenimiento de Equipos'),
        ('saneamiento', 'Saneamiento'),
        ('seguridad', 'Seguridad'),
        ('jardineria', 'Jardineria'),
        ('agua_potable', 'Sistema de Agua Potable'),
        ('gas', 'Sistema de Gas'),
        ('incendios', 'Sistema de Incendios')
    ]
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En Proceso'),
        ('resuelto', 'Resuelto'),
    ]
    
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, default='plomeria')
    prioridad = models.CharField(max_length=10, choices=PRIORIDAD_CHOICES, default='media')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    fecha = models.DateTimeField()
    ubicacion = models.CharField(max_length=100)
    descripcion = models.TextField()
    imagen = models.ImageField(upload_to='incidencias/', null=True, blank=True)
    
    #Llave foraneo del usuario que reporta la incidencia
    usuario_reporte = models.ForeignKey(User, on_delete=models.CASCADE)