from django.contrib import admin
from .models import (
    Incidencia,
    Material,
    MaterialIncidencia,
    Notification,
    Personal,
    Reporte,
    RespuestaSoporte,
    SolicitudSoporte,
)


# Register your models here.

class IncidenciaAdmin(admin.ModelAdmin):
    list_display = ("id","tipo", "prioridad", "prioridad_confirmada", "fecha","ubicacion","descripcion","estado","usuario_reporte","tecnico_asignado")
    list_filter = ("estado", "prioridad", "prioridad_confirmada", "tipo")
    search_fields = ("ubicacion", "descripcion", "usuario_reporte__username")

class MaterialAdmin(admin.ModelAdmin):
    list_display =("id","nombre","tipo","cantidad")
    search_fields = ("nombre", "tipo")

class ReporteAdmin(admin.ModelAdmin):
    list_display =("id","tipo","fecha","descripcion","estado","reporte_incidencia","reporte_material")

class PersonalAdmin(admin.ModelAdmin):
    list_display = ("id", "trabajador", "incidencia")

class MaterialIncidenciaAdmin(admin.ModelAdmin):
    list_display = ("id", "incidencia", "material", "cantidad_usada", "fecha_asignacion")

class RespuestaSoporteAdmin(admin.ModelAdmin):
    list_display = ("id", "solicitud", "autor", "fecha", "leido")

admin.site.register(Incidencia,IncidenciaAdmin)
admin.site.register(Material,MaterialAdmin)
admin.site.register(Reporte,ReporteAdmin)
admin.site.register(Notification)
admin.site.register(SolicitudSoporte)
admin.site.register(Personal, PersonalAdmin)
admin.site.register(MaterialIncidencia, MaterialIncidenciaAdmin)
admin.site.register(RespuestaSoporte, RespuestaSoporteAdmin)
