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
    path('marcar_leida/<int:notificacion_id>/', views.marcar_leida, name='marcar_leida'),
    path('obtener_notificaciones/', views.obtener_notificaciones, name='obtener_notificaciones'),
    path('logout/',views.logout_view,name='logout')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)