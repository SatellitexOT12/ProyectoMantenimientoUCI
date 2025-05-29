from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse,JsonResponse, HttpResponseForbidden
from django.template import loader
from django.contrib.auth import authenticate,login, logout
from django.contrib.auth.models import User,Group
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import Incidencia,Material,Reporte,Notification, Personal
from django.core.paginator import Paginator
from functools import wraps
from django.core import serializers
from django.contrib import messages
# Create your views here.

#Decorador personalizado para verificar los grupos a q mi usuario pertenece
#Se pasan por parametro los nombre de los grupos
def grupo_requerido(*nombres_grupos):
    """Decorador para verificar pertenencia a grupos"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            """
            Función principal que realiza la verificación:
            
            - Comprueba si el usuario autenticado pertenece a alguno de los grupos indicados.
            - Si pertenece: ejecuta la vista original.
            - Si NO pertenece: devuelve un error 403 (acceso prohibido).
            """
            if request.user.groups.filter(name__in=nombres_grupos).exists():
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden("No tienes permiso para acceder")
        return wrapper
    return decorator



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



@login_required
@grupo_requerido('administrador')
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
@grupo_requerido('administrador')
def seleccionar_usuario(request,item_id):
        user = get_object_or_404(User, id=item_id)  # Buscar el ítem en la base de datos
        
        if request.method == 'POST':
            username = request.POST.get('username')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            rol = request.POST.get('rol')
            
            #limpiar todos los roles 
            user.groups.clear()
            grupo = Group.objects.get(name=rol)
            
            # Actualizar los campos del usuario
            user.groups.add(grupo)
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.save()  # Guardar los cambios en la base de datos
            
            if rol == "tecnico":
                trabajador = Personal.objects.filter(trabajador=user).exists()
                
                if not trabajador:
                    personal = Personal(
                        trabajador = user
                    )
                    personal.save()
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
        
        if action == "eliminar":
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
    
    tecnicos_disponibles = Personal.objects.filter(
        trabajador__groups__name='tecnico',
        incidencia__isnull=True
    )
    tecnicos = Personal.objects.all()
    
    context = {
        'tableIncidencia': tableIncidencia,
        'page_obj': page_obj,
        'tecnicos_disponibles': tecnicos_disponibles,
        'tecnicos':tecnicos
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
        reporte = Reporte (
            fecha = timezone.now(),
            descripcion = " Reporte de Incidencia en el Servidor",
            estado ="pendiente",
            reporte_incidencia = incidencia
        )
        incidencia.save()
        reporte.save()
        return redirect('incidencias')
    
    return render(request , 'reportar_incidencia.html')


@login_required
def seleccionar_incidencia(request,item_id):
        incidencia = get_object_or_404(Incidencia, id=item_id)  # Buscar el ítem de incidencia en la base de datos
        reporte = get_object_or_404(Reporte,reporte_incidencia=incidencia) #Buscar el item de reporte para actualizar en la tabla de reportes
        
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
            incidencia.fecha = fecha
            incidencia.ubicacion = ubicacion
            incidencia.descripcion = descripcion
           
            
            if estado is None:
                incidencia.estado = "pendiente"
                reporte.estado = "pendiente"
            else:
                incidencia.estado = estado
                reporte.estado = estado
            
            # Guardar los cambios en la base de datos
            incidencia.save()  
            reporte.save()
            return redirect('incidencias')
            
        else:
            return render(request, 'editar_incidencia.html', {'incidencia': incidencia})
    
@login_required
@grupo_requerido('almacenero','administrador')
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
        
        nombre = request.POST.get('username')
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

@grupo_requerido('almacenero','administrador')
def seleccionar_material(request,item_id):
    material= get_object_or_404(Material,id = item_id)
    
    if request.method == 'POST':
        nombre = request.POST.get('username')
        tipo = request.POST.get('tipo')
        cantidad = request.POST.get('cantidad')
        
        material.nombre = nombre
        material.tipo = tipo
        material.cantidad = cantidad
        material.save()
        return redirect('materiales')
    else:
        return render(request, 'editar_material.html', {'material': material})

@grupo_requerido('almacenero','administrador')
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


def logout_view(request):
    logout(request)
    return redirect('login')

def main(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    unread_count = notifications.filter(is_read=False).count()
    return render(request, 'main.html', {
        'notifications': notifications,
        'unread_count': unread_count
    })



@require_POST
@login_required
def mark_as_read(request, notification_id):
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({'status': 'success'})
    except Notification.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Notificación no encontrada'}, status=404)

def get_notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    data = serializers.serialize('json', notifications)
    return JsonResponse({'notifications': data}, safe=False)

@require_POST
@login_required
def delete_notification(request, notification_id):
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.delete()
        return JsonResponse({'status': 'success'})
    except Notification.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Notificación no encontrada'}, status=404)
    

@login_required
@grupo_requerido('administrador')
def personal(request):
    tablePersonal = Personal.objects.all()
    template = loader.get_template('all_personal.html')
    
    #Obtener palabra a buscar
    query = request.GET.get('q')
    
    #Condicion para buscar elementos en la tabla
    if query:
        tablePersonal = (tablePersonal.filter(username__icontains=query) | tablePersonal.filter(email__icontains=query) 
        | tablePersonal.filter(is_active__icontains=query) | tablePersonal.filter(last_login__icontains=query)
        | tablePersonal.filter(date_joined__icontains=query) 
        )
    #Paginacion
    paginator = Paginator(tablePersonal,10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    
    #Contenido mostrado en la pagina
    context = {
        'tablePersonal': tablePersonal,
        'page_obj': page_obj
    }
    
    return HttpResponse(template.render(context,request))

# views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Incidencia, Personal

def asignar_tecnico(request):
    if request.method == 'POST':
        incidencia_id = request.POST.get('incidencia_id')
        tecnico_id = request.POST.get('tecnico_id')

        try:
            incidencia = Incidencia.objects.get(id=incidencia_id)
            
            # Desasignar cualquier técnico anterior
            if incidencia.tecnico_asignado:
                antiguo_tecnico = incidencia.tecnico_asignado
                antiguo_tecnico.incidencia = None
                antiguo_tecnico.save()

            # Asignar nuevo técnico
            tecnico = Personal.objects.get(id=tecnico_id)
            incidencia.tecnico_asignado = tecnico
            incidencia.save()

            tecnico.incidencia = incidencia  # Asegúrate de actualizar también el modelo Personal si lo usas
            tecnico.save()

            messages.success(request, f"Técnico {tecnico.trabajador.username} asignado correctamente.")

        except (Incidencia.DoesNotExist, Personal.DoesNotExist) as e:
            messages.error(request, "Error al asignar el técnico.")

        return redirect('incidencias')