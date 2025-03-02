from django.shortcuts import render, redirect
from django.http import HttpResponse,JsonResponse
from django.template import loader
from django.contrib.auth import authenticate,login
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
import json
# Create your views here.

def custom_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        context = {
            'credenciales':1,
        }
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('main/')
        else:
            return render(request, 'login.html', {'error': 'Credenciales inválidas'})
    else:
        return render(request, 'login.html')

def usuarios(request):
    tableUsuario = User.objects.all().values()
    template = loader.get_template('all_usuarios.html')
    context = {
        'tableUsuario': tableUsuario,
    }
    
    if request.method == 'POST':
            action=request.POST.get('action')

            if action != 'delete':
                username = request.POST['username']
                name = request.POST['name']
                lastname = request.POST['lastname']  
                email = request.POST['email']
                password = request.POST['password']  
                if User.objects.filter(username=username).exists():
                    return HttpResponse("El usuario ya existe")
                else:
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        first_name=name,
                        last_name=lastname
                    )
            else:
                ids=request.POST.getlist('ids')
                User.objects.filter(id__in=ids).delete()
                return redirect('usuarios')
                
    return HttpResponse(template.render(context,request))
    

def main(request):
    template = loader.get_template('main.html')
    return HttpResponse(template.render())




    
    
