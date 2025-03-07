from django.contrib import admin
from .models import Incidencia , Material


# Register your models here.

class IncidenciaAdmin(admin.ModelAdmin):
    list_display = ("id","tipo", "prioridad", "fecha","ubicacion","descripcion","estado","usuario_reporte")

class MaterialAdmin(admin.ModelAdmin):
    list_display =("id","nombre","tipo","cantidad")

admin.site.register(Incidencia,IncidenciaAdmin)
admin.site.register(Material,MaterialAdmin)
