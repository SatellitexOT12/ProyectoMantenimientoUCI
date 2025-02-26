from django.urls import path
from . import views

urlpatterns = [
    path('', views.login, name='index'),
    path('usuarios/', views.usuarios, name='usuarios'),
    path('main/', views.main, name='usuarios'),
]
