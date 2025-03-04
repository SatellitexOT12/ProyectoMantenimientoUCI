from django.contrib import admin
from .models import Incidencia

# Register your models here.

class IncidenciaAdmin(admin.ModelAdmin):
    list_display = ("id","tipo", "prioridad", "fecha","ubicacion","descripcion","estado","usuario_reporte")

admin.site.register(Incidencia,IncidenciaAdmin)