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
    
    tecnico_asignado = models.ForeignKey(
        'Personal',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incidencias_asignadas'
    )
    
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
    
    @property
    def tipo(self):
        if self.reporte_incidencia is not None:
            return "Incidencia"
        elif self.reporte_material is not None:
            return "Material"
        else:
            return "Sin tipo"
        
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    urlAsociated = models.TextField(default="none")

    def __str__(self):
        return f"Noti para {self.user.username}"
    
    
class Personal(models.Model):
    trabajador = models.ForeignKey(User, on_delete=models.CASCADE)
    incidencia = models.ForeignKey(Incidencia,on_delete=models.CASCADE,null=True, blank=True)
    
class SolicitudSoporte(models.Model):
    TIPO_SOFTWARE = 'software'
    TIPO_HARDWARE = 'hardware'
    TIPO_OTRO = 'otro'
    TIPO_CHOICES = [
        (TIPO_SOFTWARE, 'Software'),
        (TIPO_HARDWARE, 'Hardware'),
        (TIPO_OTRO, 'Otro'),
    ]

    ESTADO_PENDIENTE = 'pendiente'
    ESTADO_RESUELTO = 'resuelto'
    ESTADO_CHOICES = [
        (ESTADO_PENDIENTE, 'Pendiente'),
        (ESTADO_RESUELTO, 'Resuelto'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    descripcion = models.TextField()
    respuesta = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default=ESTADO_PENDIENTE)
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_respuesta = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Solicitud de {self.usuario.username}"
    
class RespuestaSoporte(models.Model):
    solicitud = models.ForeignKey(SolicitudSoporte, on_delete=models.CASCADE, related_name='respuestas')
    autor = models.ForeignKey(User, on_delete=models.CASCADE)
    mensaje = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    leido = models.BooleanField(default=False)
    def __str__(self):
        return f"solicitud de {self.autor}"
    
class MaterialIncidencia(models.Model):
    incidencia = models.ForeignKey(Incidencia, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    cantidad_usada = models.PositiveIntegerField(default=1)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.material.nombre} - {self.cantidad_usada}"