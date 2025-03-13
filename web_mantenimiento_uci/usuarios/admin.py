from django.contrib import admin
from .models import Incidencia , Material , Reporte


# Register your models here.

class IncidenciaAdmin(admin.ModelAdmin):
    list_display = ("id","tipo", "prioridad", "fecha","ubicacion","descripcion","estado","usuario_reporte")

class MaterialAdmin(admin.ModelAdmin):
    list_display =("id","nombre","tipo","cantidad")
    
class ReporteAdmin(admin.ModelAdmin):
    list_display =("id","tipo","fecha","descripcion","estado","reporte_incidencia","reporte_material")

admin.site.register(Incidencia,IncidenciaAdmin)
admin.site.register(Material,MaterialAdmin)
admin.site.register(Reporte,ReporteAdmin)
