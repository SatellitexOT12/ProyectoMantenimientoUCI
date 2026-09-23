from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


# Create your models here


class Incidencia(models.Model):
    
    PRIORIDAD_CHOICES = [
        ('3', 'Alta'),
        ('2', 'Media'),
        ('1', 'Baja'),
    ]
    
    TIPO_CHOICES = [
        ('plomeria', 'Plomería'),
        ('electricidad', 'Electricidad'),
        ('infraestructura', 'Infraestructura'),
        ('mantenimiento_equipos', 'Mantenimiento de equipos'),
        ('saneamiento', 'Saneamiento'),
        ('seguridad', 'Seguridad'),
        ('jardineria', 'Jardinería'),
        ('agua_potable', 'Sistema de agua potable'),
        ('gas', 'Sistema de gas'),
        ('incendios', 'Sistema de incendios')
    ]
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En proceso'),
        ('resuelto', 'Resuelto'),
    ]
    
    # Límites que valida el servidor (no son columnas). El formulario de
    # reporte debe usar los mismos valores (se pasan al contexto).
    UBICACION_MAX = 50
    DESCRIPCION_MAX = 1000
    IMAGEN_MAX_BYTES = 8 * 1024 * 1024

    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, default='plomeria')
    # El solicitante la propone; el administrador la confirma o la corrige.
    prioridad = models.CharField(max_length=10, choices=PRIORIDAD_CHOICES, default='2')
    prioridad_confirmada = models.BooleanField(default=False)
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

    # Marcas de tiempo del ciclo (para medir los tiempos de respuesta).
    fecha_asignacion = models.DateTimeField(null=True, blank=True)
    fecha_resolucion = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Incidencia {self.pk}: {self.get_tipo_display()} en {self.ubicacion}"

    @property
    def prioridad_situacion(self):
        """Texto para la interfaz: «Confirmada» o «Propuesta»."""
        return "Confirmada" if self.prioridad_confirmada else "Propuesta"

    @property
    def esta_abierta(self):
        return self.estado != 'resuelto'

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

    @property
    def url(self):
        """Ruta absoluta a la que lleva la notificación (nunca vacía)."""
        destino = (self.urlAsociated or '').strip()
        if not destino or destino == 'none':
            return reverse('main')
        return destino if destino.startswith('/') else '/' + destino
    
    
class Personal(models.Model):
    trabajador = models.ForeignKey(User, on_delete=models.CASCADE)
    # Reflejo de la incidencia abierta más reciente del técnico. La fuente de
    # verdad de la asignación es Incidencia.tecnico_asignado; este campo se
    # mantiene sincronizado (usuarios.servicios.sincronizar_personal). Si se
    # elimina la incidencia, el técnico NO se elimina (antes CASCADE).
    incidencia = models.ForeignKey(Incidencia,on_delete=models.SET_NULL,null=True, blank=True)

    def __str__(self):
        return self.trabajador.get_username()

    @property
    def incidencias_abiertas(self):
        return self.incidencias_asignadas.exclude(estado='resuelto')

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