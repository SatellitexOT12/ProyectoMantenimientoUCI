from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from .models import Usuario
# Create your views here.

def login(request):
    template = loader.get_template('login.html')
    return HttpResponse(template.render())

def usuarios(request):
    tableUsuario = Usuario.objects.all().values()
    template = loader.get_template('all_usuarios.html')
    
    context = {
        'tableUsuario': tableUsuario,
    }
    
    return HttpResponse(template.render(context,request))

def main(request):
    template = loader.get_template('main.html')
    return HttpResponse(template.render())