from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse,JsonResponse
from django.template import loader
from django.contrib.auth import authenticate,login
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required ,permission_required,user_passes_test
from django.utils import timezone
from .models import Incidencia,Material,Reporte
from django.core.paginator import Paginator
from datetime import datetime
import json
# Create your views here.


#Vista para el login
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

def es_administrador(user):
    return user.groups.filter(name='Administradores').exists()

@login_required
@user_passes_test(es_administrador)
def usuarios(request):
    tableUsuario = User.objects.all()
    template = loader.get_template('all_usuarios.html')
    
    #Obtener palabra a buscar
    query = request.GET.get('q')
    
    #Condicion para buscar elementos en la tabla
    if query:
        tableUsuario = (tableUsuario.filter(username__icontains=query) | tableUsuario.filter(email__icontains=query) 
        | tableUsuario.filter(is_active__icontains=query) | tableUsuario.filter(last_login__icontains=query)
        | tableUsuario.filter(date_joined__icontains=query) 
        )
    #Paginacion
    paginator = Paginator(tableUsuario,10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    
    #Contenido mostrado en la pagina
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
                    return redirect('usuarios')
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
        
@login_required  
def incidencias(request):
    template = loader.get_template('all_incidencias.html')
    
    if request.user.is_superuser:
        tableIncidencia = Incidencia.objects.all()
    else:
        current_user = request.user
        tableIncidencia = Incidencia.objects.filter(usuario_reporte=current_user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == "delete":
                ids=request.POST.getlist('ids')
                Incidencia.objects.filter(id__in=ids).delete()
                return redirect('incidencias')
    
    #Obtener elemento a buscar
    query = request.GET.get('q')
    
    #Condicion para buscar elementos en la tabla
    if query:
        tableIncidencia =( tableIncidencia.filter(tipo__icontains=query) | tableIncidencia.filter(prioridad__icontains=query)
        | tableIncidencia.filter(estado__icontains=query) | tableIncidencia.filter(fecha__icontains=query)
        | tableIncidencia.filter(ubicacion__icontains=query) | tableIncidencia.filter(descripcion__icontains=query)
        )
        
    #Paginacion
    paginator = Paginator(tableIncidencia,10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'tableIncidencia': tableIncidencia,
        'page_obj': page_obj
    }
    return HttpResponse(template.render(context,request))

@login_required
def reportar_incidencia(request):
    
    if request.method == "POST":
            
        
        tipo = request.POST.get('tipo_incidencia')
        prioridad = request.POST.get('prioridad')
        ubicacion = request.POST.get('ubicacion')
        descripcion = request.POST.get('descripcion')
        imagen = request.FILES.get('imagen')
        
        incidencia = Incidencia (
            tipo=tipo,
            prioridad=prioridad,
            ubicacion=ubicacion,
            descripcion=descripcion,
            fecha = timezone.now(),
            usuario_reporte=request.user,
            imagen=imagen
        )
        incidencia.save()
        return redirect('incidencias')
    
    return render(request , 'reportar_incidencia.html')


@login_required
@permission_required('usuarios.change_incidencia', raise_exception=True)
def seleccionar_incidencia(request,item_id):
        incidencia = get_object_or_404(Incidencia, id=item_id)  # Buscar el ítem en la base de datos
        
        if request.method == 'POST':
            tipo = request.POST.get('tipo')
            prioridad = request.POST.get('prioridad')
            estado = request.POST.get('estado')
            fecha = request.POST.get('fecha')
            ubicacion = request.POST.get('ubicacion')
            descripcion = request.POST.get('descripcion')
            
            # Actualizar los campos del usuario
            incidencia.tipo = tipo
            incidencia.prioridad = prioridad
            incidencia.estado = estado
            incidencia.fecha = fecha
            incidencia.ubicacion = ubicacion
            incidencia.descripcion = descripcion
            incidencia.save()  # Guardar los cambios en la base de datos
            return redirect('incidencias')
            
        else:
            return render(request, 'editar_incidencia.html', {'incidencia': incidencia})
    
@login_required
def materiales(request):
    tableMaterial = Material.objects.all()
    
    #Paginacion
    paginator = Paginator(tableMaterial,10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'tableMaterial':tableMaterial,
        'page_obj':page_obj
    }
    
    if request.method == 'POST':
        
        action = request.POST.get('action')
        
        if action == "delete":
                ids=request.POST.getlist('ids')
                Material.objects.filter(id__in=ids).delete()
                return redirect('materiales')
        
        nombre = request.POST.get('nombre')
        tipo = request.POST.get('tipo_material')
        cantidad = request.POST.get('cantidad')
        
        material = Material(
            nombre = nombre,
            tipo = tipo,
            cantidad = cantidad
        )
        material.save()
        return redirect('materiales')
    
    return render(request,'all_materiales.html',context)

def seleccionar_material(request,item_id):
    material= get_object_or_404(Material,id = item_id)
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        tipo = request.POST.get('tipo')
        cantidad = request.POST.get('cantidad')
        
        material.nombre = nombre
        material.tipo = tipo
        material.cantidad = cantidad
        material.save()
        return redirect('materiales')
    else:
        return render(request, 'editar_material.html', {'material': material})

def reportes(request):
    tableReporte = Reporte.objects.all()
    
    totalReportes = tableReporte.count()
    reporte_resuelto = tableReporte.filter(estado='resuelto').count()
    reporte_pendiente = tableReporte.filter(estado='pendiente').count()
    reporte_enProceso = tableReporte.filter(estado = 'en_proceso').count()
    context = {
        'tableReporte' : tableReporte,
        'totalReportes' : totalReportes,
        'reporte_resuelto' : reporte_resuelto,
        'reporte_pendiente' : reporte_pendiente,
        'reporte_enProceso' : reporte_enProceso
    }
    
    return render(request,'all_reportes.html',context)

def main(request):
    
    return render(request,'main.html')




    
    
