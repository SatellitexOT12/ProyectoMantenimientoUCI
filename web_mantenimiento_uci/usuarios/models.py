from django.db import models
from django.contrib.auth.models import User

# Create your models here

class Incidencia(models.Model):
    
    PRIORIDAD_CHOICES = [
        ('3', 'Alta'),
        ('2', 'Media'),
        ('1', 'Baja'),
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
    
    
class Material(models.Model):
    
    nombre = models.CharField(max_length=100)
    tipo=models.CharField(max_length=100)
    cantidad=models.IntegerField()


class Reporte(models.Model):
    
        

    fecha = models.DateTimeField()
    descripcion = models.TextField()
    estado = models.CharField(max_length=50,blank=True)
    
    reporte_incidencia = models.ForeignKey(Incidencia,on_delete=models.CASCADE,null=True, blank=True)
    reporte_material = models.ForeignKey(Material,on_delete=models.CASCADE,null=True, blank=True)
    
    
    def save(self, *args, **kwargs):
        self.estado = self.reporte_incidencia.estado
        super().save(*args, **kwargs)
    

    @property
    def tipo(self):
        if self.reporte_incidencia is not None:
            return "Incidencia"
        elif self.reporte_material is not None:
            return "Material"
        else:
            return "Sin tipo"
        
class Notificacion(models.Model):
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.mensaje