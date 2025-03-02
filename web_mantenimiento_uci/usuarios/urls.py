from django.urls import path
from django.contrib.auth import views as auth_views
from . import views


urlpatterns = [
    path('', views.custom_login, name='login'),
    path('usuarios/', views.usuarios, name='usuarios'),
    path('main/', views.main, name='main'),
    path('usuarios/editar/<int:item_id>/',views.seleccionar_usuario,name='editar_usuario')
]
