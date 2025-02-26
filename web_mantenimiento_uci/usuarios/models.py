from django.db import models

# Create your models here.
class Usuario(models.Model):
    nombre = models.CharField(max_length=255)
    apellido = models.CharField(max_length=255)
    telefono = models.IntegerField()
    fecha = models.DateField()