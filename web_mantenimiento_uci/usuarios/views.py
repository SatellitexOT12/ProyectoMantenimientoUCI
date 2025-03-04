from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse,JsonResponse
from django.template import loader
from django.contrib.auth import authenticate,login
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import Incidencia
from django.core.paginator import Paginator
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
    
    paginator = Paginator(tableUsuario,10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'tableUsuario': tableUsuario,
        'page_obj': page_obj
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
    
@login_required
def seleccionar_usuario(request,item_id):
        user = get_object_or_404(User, id=item_id)  # Buscar el ítem en la base de datos
        
        if request.method == 'POST':
            username = request.POST.get('username')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            
            # Actualizar los campos del usuario
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.save()  # Guardar los cambios en la base de datos
            return redirect('usuarios')
            
        else:
            return render(request, 'editar_usuario.html', {'user': user})
        
        
def incidencias(request):
    template = loader.get_template('all_incidencias.html')
    tableIncidencia = Incidencia.objects.all()
    
    paginator = Paginator(tableIncidencia,10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'tableIncidencia': tableIncidencia,
        'page_obj': page_obj
    }
    return HttpResponse(template.render(context,request))

def main(request):
    template = loader.get_template('main.html')
    return HttpResponse(template.render())




    
    
