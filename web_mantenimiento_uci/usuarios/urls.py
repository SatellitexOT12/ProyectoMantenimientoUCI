from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', views.custom_login, name='login'),
    path('usuarios/', views.usuarios, name='usuarios'),
    path('incidencias/',views.incidencias,name='incidencias'),
    path('materiales/',views.materiales,name="materiales"),
    path('reportes/',views.reportes,name="reportes"),
    path('main/', views.main, name='main'),
    path('usuarios/editar/<int:item_id>/',views.seleccionar_usuario,name='editar_usuario'),
    path('incidencia/editar/<int:item_id>/',views.seleccionar_incidencia,name='editar_incidencia'),
    path('material/editar/<int:item_id>/',views.seleccionar_material, name='editar_material'),
    path('reportar_incidencia',views.reportar_incidencia, name='reportar_incidencia'),
    path('notifications/<int:notification_id>/read/', views.mark_as_read, name='mark_as_read'),
    path('notifications/', views.get_notifications, name='get_notifications'),
    path('notifications/<int:notification_id>/delete/', views.delete_notification, name='delete_notification'),
    path('logout/',views.logout_view,name='logout'),
    path('personal/',views.personal, name = 'personal'),
    path('asignar-tecnico/', views.asignar_tecnico, name='asignar_tecnico'),
    path('quitar-tecnico/<int:incidencia_id>/', views.quitar_tecnico, name='quitar_tecnico'),
    path('soporte/', views.solicitar_soporte, name='solicitar_soporte'),
    path('soporte/admin/', views.bandeja_entrada_soporte, name='bandeja_entrada_soporte'),
    path('soporte/detalle/<int:solicitud_id>/', views.detalle_solicitud, name='detalle_solicitud'),
    path('soporte/completar/<int:solicitud_id>/', views.completar_solicitud, name='completar_solicitud'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)