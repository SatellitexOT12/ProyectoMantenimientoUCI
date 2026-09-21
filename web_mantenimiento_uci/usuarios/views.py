"""Vistas de SGUM-UCI.

Convenciones:
- Permisos: siempre por ``usuarios.permisos`` (decorador ``rol_requerido`` y
  funciones ``puede_*``); ninguna vista decide permisos por su cuenta.
- Toda acción que cambia datos exige POST y responde con redirección
  (patrón POST-redirect-GET) y un mensaje de ``django.contrib.messages``.
- Todo lo que llega por formulario se valida con ``usuarios.validaciones``.
"""
import json
import unicodedata

import openpyxl
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import Group, User
from django.contrib.auth.password_validation import password_validators_help_texts
from django.core import serializers
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, F, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from openpyxl.chart import BarChart, PieChart, Reference
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from openpyxl.styles import Alignment, Font

from . import estadisticas, servicios, validaciones
from .models import (
    Incidencia,
    Material,
    Notification,
    Personal,
    Reporte,
    RespuestaSoporte,
    SolicitudSoporte,
)
from .permisos import (
    ADMINISTRADOR,
    ALMACENERO,
    ROLES,
    ROLES_CHOICES,
    TECNICO,
    capacidades_incidencia,
    denegar,
    es_administrador,
    es_almacenero,
    es_dueno,
    es_tecnico,
    es_tecnico_asignado,
    grupo_requerido,  # noqa: F401  (nombre antiguo, por compatibilidad)
    puede_asignar_material,
    puede_atender_soporte,
    puede_eliminar_incidencia,
    redirigir_atras,
    rol_principal,
    rol_requerido,
    roles_texto,
)
from .validaciones import (
    MATERIAL_CANTIDAD_MAX,
    SOPORTE_DESCRIPCION_MAX,
    MENSAJE_SOPORTE_MAX,
    ids_validos,
    limpiar,
)

POR_PAGINA = 10


# =========================================================== utilidades

def _paginar(request, queryset, por_pagina=POR_PAGINA):
    return Paginator(queryset, por_pagina).get_page(request.GET.get('page'))


def _qs(request):
    """Parámetros GET sin ``page``, codificados: para enlaces de paginación
    que conserven búsqueda y filtros (``?{{ qs }}&page=N``)."""
    params = request.GET.copy()
    params.pop('page', None)
    return params.urlencode()


def _sin_acentos(texto):
    normal = unicodedata.normalize('NFD', str(texto))
    return ''.join(c for c in normal if unicodedata.category(c) != 'Mn').lower()


def _codigos_que_coinciden(choices, consulta, por_codigo=True):
    """Códigos de ``choices`` cuyo texto visible (o código) contiene la consulta.

    Permite buscar «plomería», «mantenimiento» o «alta» aunque en la base se
    guarde ``plomeria`` o ``3``. La comparación ignora acentos y mayúsculas.
    """
    buscada = _sin_acentos(consulta)
    if not buscada:
        return []
    return [
        codigo
        for codigo, etiqueta in choices
        if buscada in _sin_acentos(etiqueta) or (por_codigo and buscada in _sin_acentos(codigo))
    ]


def _mensajes_de_errores(request, errores):
    """Un aviso general cuando un formulario se devuelve con errores."""
    if errores:
        messages.error(request, "Revise los campos marcados: no se guardó nada.")


# ================================================================ acceso

def custom_login(request):
    """Inicio de sesión. Acepta ``next`` (solo rutas del propio sitio)."""
    siguiente = request.POST.get('next') or request.GET.get('next') or ''
    if siguiente and not url_has_allowed_host_and_scheme(
        siguiente, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        siguiente = ''

    if request.user.is_authenticated:
        return redirect(siguiente or 'main')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        usuario = authenticate(request, username=username, password=password)
        if usuario is not None:
            login(request, usuario)
            return redirect(siguiente or 'main')
        # El mensaje no revela cuál de los dos datos falló. Solo quien acierta
        # la contraseña de una cuenta desactivada sabe que está desactivada.
        error = "Usuario o contraseña incorrectos. Revise los datos e inténtelo de nuevo."
        desactivada = False
        inactivo = User.objects.filter(username=username, is_active=False).first()
        if inactivo is not None and inactivo.check_password(password):
            desactivada = True
            error = (
                "Su cuenta está desactivada. Comuníquese con la Dirección de "
                "Mantenimiento para que la reactiven."
            )
        return render(request, 'login.html', {
            'error': error,
            'cuenta_desactivada': desactivada,
            'next': siguiente,
            'username': username,
        })
    return render(request, 'login.html', {'next': siguiente})


def logout_view(request):
    logout(request)
    return redirect('login')


# ============================================================== usuarios

def _filtrar_por_rol(queryset, rol):
    if rol == 'cliente':
        return queryset.exclude(is_superuser=True).exclude(
            groups__name__in=[ADMINISTRADOR, TECNICO, ALMACENERO]
        )
    if rol == ADMINISTRADOR:
        return queryset.filter(Q(groups__name=ADMINISTRADOR) | Q(is_superuser=True)).distinct()
    return queryset.filter(groups__name=rol).distinct()


def _motivo_no_desactivar(quien, usuario):
    """Texto con la razón por la que `quien` no puede desactivar la cuenta, o None."""
    if usuario.pk == quien.pk:
        return "No puede desactivar su propia cuenta."
    if usuario.is_superuser and not quien.is_superuser:
        return f"«{usuario.username}» es superusuario; solo otro superusuario puede desactivarlo."
    abiertas = Incidencia.objects.filter(
        tecnico_asignado__trabajador=usuario).exclude(estado='resuelto').count()
    if abiertas:
        return (
            f"«{usuario.username}» tiene {abiertas} incidencia(s) abiertas asignadas. "
            "Reasígnelas antes de desactivar la cuenta."
        )
    return None


def _asegurar_personal(usuario):
    if not Personal.objects.filter(trabajador=usuario).exists():
        Personal.objects.create(trabajador=usuario)


def _grupo(rol):
    grupo, _ = Group.objects.get_or_create(name=rol)
    return grupo


@rol_requerido(ADMINISTRADOR)
def usuarios(request):
    if request.method == 'POST':
        if request.POST.get('action') == 'delete':
            return _eliminar_usuarios(request)
        return _crear_usuario(request)

    consulta = limpiar(request.GET.get('q'))
    rol_filtro = limpiar(request.GET.get('rol'))
    tabla = User.objects.prefetch_related('groups').order_by('-date_joined', '-id')
    if consulta:
        tabla = tabla.filter(
            Q(username__icontains=consulta)
            | Q(email__icontains=consulta)
            | Q(first_name__icontains=consulta)
            | Q(last_name__icontains=consulta)
        )
    if rol_filtro in ROLES:
        tabla = _filtrar_por_rol(tabla, rol_filtro)
    else:
        rol_filtro = ''
    activo_filtro = limpiar(request.GET.get('activo'))
    if activo_filtro in ('1', '0'):
        tabla = tabla.filter(is_active=activo_filtro == '1')
    else:
        activo_filtro = ''

    page_obj = _paginar(request, tabla)
    page_obj.object_list = list(page_obj.object_list)
    for fila in page_obj.object_list:
        fila.rol_codigo = rol_principal(fila)
        fila.rol_display = roles_texto(fila)
        fila.es_propio = fila.pk == request.user.pk
        fila.puede_cambiar_activo = (
            not fila.es_propio and (request.user.is_superuser or not fila.is_superuser))

    return render(request, 'all_usuarios.html', {
        'tableUsuario': tabla,
        'page_obj': page_obj,
        'q': consulta,
        'qs': _qs(request),
        'rol_filtro': rol_filtro,
        'activo_filtro': activo_filtro,
        'roles': ROLES_CHOICES,
        'password_ayuda': password_validators_help_texts(),
    })


def _crear_usuario(request):
    """Alta de usuario por AJAX. Responde JSON: {'success': True, ...} o
    {'errors': {campo: texto}} con estado 400."""
    post = request.POST
    errores = {}
    username, err = validaciones.validar_username(post.get('username'))
    if err:
        errores['usuario'] = err
    nombre, err = validaciones.validar_nombre_persona(
        post.get('name', post.get('first_name')), 'el nombre', obligatorio=True)
    if err:
        errores['nombre'] = err
    apellidos, err = validaciones.validar_nombre_persona(
        post.get('lastname', post.get('last_name')), 'los apellidos', obligatorio=True)
    if err:
        errores['apellidos'] = err
    email, err = validaciones.validar_email(post.get('email'))
    if err:
        errores['email'] = err
    rol = limpiar(post.get('rol')) or 'cliente'
    if rol not in ROLES:
        errores['rol'] = "Seleccione un rol de la lista."

    contrasena = post.get('password', '')
    confirmacion = post.get('confirmPassword')
    candidato = User(username=username, first_name=nombre, last_name=apellidos, email=email)
    if confirmacion is not None and contrasena != confirmacion:
        errores['confirmPassword'] = "Las contraseñas no coinciden. Escríbalas de nuevo."
    else:
        _, err = validaciones.validar_contrasena(contrasena, usuario=candidato)
        if err:
            errores['password'] = err

    if errores:
        respuesta = {'success': False, 'errors': dict(errores)}
        # Resumen para interfaces que solo muestran «usuario», «email» y «general».
        resto = [texto for campo, texto in errores.items() if campo not in ('usuario', 'email')]
        if resto:
            respuesta['errors']['general'] = ' '.join(resto)
        return JsonResponse(respuesta, status=400)

    with transaction.atomic():
        usuario = User.objects.create_user(
            username=username, email=email, password=contrasena,
            first_name=nombre, last_name=apellidos,
        )
        usuario.groups.set([_grupo(rol)])
        if rol == TECNICO:
            _asegurar_personal(usuario)
    return JsonResponse({
        'success': True,
        'mensaje': 'Usuario creado correctamente',
        'id': usuario.pk,
    })


def _eliminar_usuarios(request):
    ids = ids_validos(request.POST.getlist('ids'))
    if not ids:
        messages.warning(request, "Seleccione al menos un usuario para eliminar.")
        return redirect('usuarios')

    candidatos = User.objects.filter(pk__in=ids).annotate(
        n_reportadas=Count('incidencia', distinct=True),
        n_atendidas=Count('personal__incidencias_asignadas', distinct=True),
    )
    eliminables, rechazos = [], []
    for candidato in candidatos:
        if candidato.pk == request.user.pk:
            rechazos.append("No puede eliminar su propia cuenta.")
        elif candidato.is_superuser and not request.user.is_superuser:
            rechazos.append(
                f"«{candidato.username}» es superusuario; solo otro superusuario puede eliminarlo.")
        elif candidato.n_reportadas or candidato.n_atendidas:
            rechazos.append(
                f"«{candidato.username}» tiene incidencias registradas o atendidas; "
                "desactive la cuenta en lugar de eliminarla para conservar el historial."
            )
        else:
            eliminables.append(candidato.pk)
    if eliminables:
        User.objects.filter(pk__in=eliminables).delete()
        messages.success(
            request,
            "Se eliminó 1 usuario." if len(eliminables) == 1
            else f"Se eliminaron {len(eliminables)} usuarios.",
        )
    for texto in rechazos:
        messages.warning(request, texto)
    return redirect('usuarios')


@rol_requerido(ADMINISTRADOR)
def seleccionar_usuario(request, item_id):
    editado = get_object_or_404(User, pk=item_id)
    es_propio = editado.pk == request.user.pk
    rol_actual = rol_principal(editado)

    def contexto(errores=None, valores=None):
        return {
            'usuario_editado': editado,
            # Compatibilidad: la plantilla antigua usa «user» (que además tapa
            # al usuario en sesión). La nueva debe usar «usuario_editado».
            'user': editado,
            'oc_b': True,
            'roles': ROLES_CHOICES,
            'rol_actual': rol_actual,
            'es_propio': es_propio,
            'password_ayuda': password_validators_help_texts(),
            'errores': errores or {},
            'valores': valores or {},
        }

    if request.method != 'POST':
        return render(request, 'editar_usuario.html', contexto())

    post = request.POST
    errores = {}
    username, err = validaciones.validar_username(
        post.get('username', editado.username), excluir_pk=editado.pk)
    if err:
        errores['username'] = err
    nombre, err = validaciones.validar_nombre_persona(
        post.get('first_name', editado.first_name), 'el nombre', obligatorio=False)
    if err:
        errores['first_name'] = err
    apellidos, err = validaciones.validar_nombre_persona(
        post.get('last_name', editado.last_name), 'los apellidos', obligatorio=False)
    if err:
        errores['last_name'] = err
    email, err = validaciones.validar_email(
        post.get('email', editado.email), excluir_pk=editado.pk)
    if err:
        errores['email'] = err

    rol = limpiar(post.get('rol')) or rol_actual
    if rol not in ROLES:
        errores['rol'] = "Seleccione un rol de la lista."
    elif rol != rol_actual:
        if es_propio:
            errores['rol'] = (
                "No puede quitarse a sí mismo el rol de administrador. "
                "Pídale a otro administrador que lo cambie."
            )
        elif es_tecnico(editado):
            pendientes = Incidencia.objects.filter(
                tecnico_asignado__trabajador=editado).exclude(estado='resuelto').count()
            if pendientes:
                errores['rol'] = (
                    f"Este técnico tiene {pendientes} incidencia(s) abiertas asignadas. "
                    "Reasígnelas antes de cambiarle el rol."
                )

    nueva = post.get('password', '')
    if nueva and nueva != editado.password:  # el hash reenviado no cuenta como cambio
        aspirante = User(username=username, first_name=nombre, last_name=apellidos, email=email)
        confirmacion = post.get('confirmPassword')
        if confirmacion is not None and nueva != confirmacion:
            errores['password'] = "Las contraseñas no coinciden. Escríbalas de nuevo."
        else:
            _, err = validaciones.validar_contrasena(nueva, usuario=aspirante)
            if err:
                errores['password'] = err
    else:
        nueva = ''

    activo = editado.is_active
    if 'is_active' in post:
        valor = limpiar(post.get('is_active')).lower()
        if valor in ('1', 'true', 'on', 'si', 'sí'):
            activo = True
        elif valor in ('0', 'false', 'off', 'no'):
            activo = False
        else:
            errores['is_active'] = "Indique si la cuenta está activa o inactiva."
        if not activo and editado.is_active:
            motivo = _motivo_no_desactivar(request.user, editado)
            if motivo:
                errores['is_active'] = motivo

    if errores:
        _mensajes_de_errores(request, errores)
        valores = {'username': username, 'first_name': nombre, 'last_name': apellidos,
                   'email': email, 'rol': rol, 'is_active': '1' if activo else '0'}
        return render(request, 'editar_usuario.html', contexto(errores, valores))

    with transaction.atomic():
        editado.username = username
        editado.first_name = nombre
        editado.last_name = apellidos
        editado.email = email
        editado.is_active = activo
        if nueva:
            editado.set_password(nueva)
        editado.save()
        if rol != rol_actual:
            editado.groups.set([_grupo(rol)])
        if rol == TECNICO:
            _asegurar_personal(editado)
    if nueva and es_propio:
        update_session_auth_hash(request, editado)
    messages.success(request, f"Se guardaron los cambios de «{editado.username}».")
    return redirect('usuarios')


@rol_requerido(ADMINISTRADOR)
@require_POST
def cambiar_activo_usuario(request, item_id):
    """Desactiva o reactiva una cuenta (conserva todo su historial).

    Campo POST: `is_active` = `1` (reactivar) o `0` (desactivar). Una cuenta
    desactivada no puede iniciar sesión y su sesión abierta deja de valer.
    """
    usuario = get_object_or_404(User, pk=item_id)
    valor = limpiar(request.POST.get('is_active')).lower()
    if valor in ('1', 'true', 'on', 'si', 'sí'):
        nuevo = True
    elif valor in ('0', 'false', 'off', 'no'):
        nuevo = False
    else:
        messages.error(
            request, "Indique si la cuenta debe quedar activa (1) o desactivada (0).")
        return redirigir_atras(request, 'usuarios')

    if nuevo == usuario.is_active:
        messages.info(
            request,
            f"La cuenta «{usuario.username}» ya estaba {'activa' if nuevo else 'desactivada'}.",
        )
    elif not nuevo and (motivo := _motivo_no_desactivar(request.user, usuario)):
        messages.error(request, motivo)
    else:
        usuario.is_active = nuevo
        usuario.save(update_fields=['is_active'])
        if nuevo:
            messages.success(
                request, f"La cuenta «{usuario.username}» fue reactivada. Ya puede iniciar sesión.")
        else:
            messages.success(
                request,
                f"La cuenta «{usuario.username}» fue desactivada. Ya no puede iniciar "
                "sesión y su historial se conserva.",
            )
    return redirigir_atras(request, 'usuarios')


# =========================================================== incidencias

def _incidencias_visibles(usuario):
    """Incidencias que el usuario puede ver, según su rol."""
    base = Incidencia.objects.select_related('usuario_reporte', 'tecnico_asignado__trabajador')
    if es_administrador(usuario) or es_almacenero(usuario):
        return base
    condicion = Q(usuario_reporte=usuario)
    if es_tecnico(usuario):
        condicion |= Q(tecnico_asignado__trabajador=usuario)
    return base.filter(condicion)


_ORDENES = {
    'recientes': ('-fecha', '-id'),
    'antiguas': ('fecha', 'id'),
    'prioridad': ('-prioridad', 'fecha', 'id'),
}


def _filtrar_incidencias(queryset, get):
    """Aplica búsqueda (q) y filtros exactos. Devuelve (queryset, filtros)."""
    consulta = limpiar(get.get('q'))
    filtros = {
        'q': consulta,
        'estado': limpiar(get.get('estado')),
        'tipo': limpiar(get.get('tipo')),
        'prioridad': limpiar(get.get('prioridad')),
        'tecnico': limpiar(get.get('tecnico')),
        'confirmada': limpiar(get.get('confirmada')),
        'orden': limpiar(get.get('orden')),
    }
    if consulta:
        condicion = (
            Q(ubicacion__icontains=consulta)
            | Q(descripcion__icontains=consulta)
            | Q(usuario_reporte__username__icontains=consulta)
            | Q(tecnico_asignado__trabajador__username__icontains=consulta)
            | Q(fecha__icontains=consulta)
        )
        for campo, choices, por_codigo in (
            ('tipo', Incidencia.TIPO_CHOICES, True),
            ('prioridad', Incidencia.PRIORIDAD_CHOICES, False),
            ('estado', Incidencia.ESTADO_CHOICES, True),
        ):
            codigos = _codigos_que_coinciden(choices, consulta, por_codigo)
            if codigos:
                condicion |= Q(**{f'{campo}__in': codigos})
        numero = validaciones.entero_positivo(consulta, maximo=2**31 - 1, minimo=1)
        if numero:
            condicion |= Q(pk=numero)
        queryset = queryset.filter(condicion)

    estado = filtros['estado']
    if estado == 'abiertas':
        queryset = queryset.exclude(estado='resuelto')
    elif estado in dict(Incidencia.ESTADO_CHOICES):
        queryset = queryset.filter(estado=estado)
    else:
        filtros['estado'] = ''
    if filtros['tipo'] in dict(Incidencia.TIPO_CHOICES):
        queryset = queryset.filter(tipo=filtros['tipo'])
    else:
        filtros['tipo'] = ''
    if filtros['prioridad'] in dict(Incidencia.PRIORIDAD_CHOICES):
        queryset = queryset.filter(prioridad=filtros['prioridad'])
    else:
        filtros['prioridad'] = ''
    if filtros['tecnico'] == 'sin':
        queryset = queryset.filter(tecnico_asignado__isnull=True)
    elif validaciones.entero_positivo(filtros['tecnico'], maximo=2**31 - 1, minimo=1):
        queryset = queryset.filter(tecnico_asignado_id=int(filtros['tecnico']))
    else:
        filtros['tecnico'] = ''
    if filtros['confirmada'] in ('0', '1'):
        queryset = queryset.filter(prioridad_confirmada=filtros['confirmada'] == '1')
    else:
        filtros['confirmada'] = ''
    if filtros['orden'] not in _ORDENES:
        filtros['orden'] = 'recientes'
    return queryset.order_by(*_ORDENES[filtros['orden']]), filtros


def _tecnicos_con_carga():
    """Todos los técnicos activos con ``abiertas`` = incidencias abiertas que
    atienden, de menor a mayor carga (un técnico puede tener varias a la vez;
    la interfaz muestra la carga para que el despachador decida)."""
    return list(
        Personal.objects.filter(
            trabajador__is_active=True, trabajador__groups__name=TECNICO
        )
        .select_related('trabajador')
        .annotate(abiertas=Count(
            'incidencias_asignadas',
            filter=~Q(incidencias_asignadas__estado='resuelto'),
            distinct=True,
        ))
        .distinct()
        .order_by('abiertas', 'trabajador__username', 'id')
    )


def _eliminar_incidencias(request):
    ids = ids_validos(request.POST.getlist('ids'))
    if not ids:
        messages.warning(request, "Seleccione al menos una incidencia para eliminar.")
        return redirigir_atras(request)

    candidatas = (
        Incidencia.objects.filter(pk__in=ids)
        .select_related('tecnico_asignado__trabajador')
        .annotate(n_materiales=Count('materialincidencia', distinct=True))
    )
    eliminables, sin_permiso, con_materiales = [], 0, []
    for incidencia in candidatas:
        if not puede_eliminar_incidencia(request.user, incidencia):
            sin_permiso += 1
        elif incidencia.n_materiales:
            con_materiales.append(incidencia.pk)
        else:
            eliminables.append(incidencia.pk)

    if eliminables:
        Incidencia.objects.filter(pk__in=eliminables).delete()
        messages.success(
            request,
            "Se eliminó 1 incidencia." if len(eliminables) == 1
            else f"Se eliminaron {len(eliminables)} incidencias.",
        )
    if sin_permiso:
        messages.warning(
            request,
            f"{sin_permiso} incidencia(s) no se eliminaron: solo puede eliminar las suyas "
            "mientras estén Pendientes.",
        )
    if con_materiales:
        numeros = ', '.join(f"n.º {pk}" for pk in con_materiales)
        messages.warning(
            request,
            f"No se eliminó la incidencia {numeros} porque tiene materiales asignados. "
            "Retire primero los materiales (su cantidad vuelve al inventario).",
        )
    return redirigir_atras(request)


@rol_requerido()
def incidencias(request):
    if request.method == 'POST':
        if request.POST.get('action') == 'eliminar':
            return _eliminar_incidencias(request)
        return redirect('incidencias')

    usuario = request.user
    visibles = _incidencias_visibles(usuario)
    tabla, filtros = _filtrar_incidencias(visibles, request.GET)
    tabla = tabla.prefetch_related('materialincidencia_set__material')

    page_obj = _paginar(request, tabla)
    page_obj.object_list = list(page_obj.object_list)
    for fila in page_obj.object_list:
        caps = capacidades_incidencia(usuario, fila)
        fila.puede_editar = caps['editar']
        fila.puede_eliminar = caps['eliminar']
        fila.puede_cambiar_estado = caps['cambiar_estado']
        fila.puede_asignar_tecnico = caps['asignar_tecnico']
        fila.puede_asignar_material = caps['asignar_material']
        fila.puede_gestionar_prioridad = caps['gestionar_prioridad']
        fila.es_mia = es_dueno(usuario, fila)
        fila.es_asignada_a_mi = es_tecnico_asignado(usuario, fila)

    administra = es_administrador(usuario)
    tecnicos = _tecnicos_con_carga() if administra else []
    materiales_disponibles = (
        Material.objects.filter(cantidad__gt=0).order_by('nombre', 'id')
        if puede_asignar_material(usuario) else []
    )

    return render(request, 'all_incidencias.html', {
        # Claves originales
        'tableIncidencia': tabla,
        'page_obj': page_obj,
        # Obsoleto: ya no se filtra por disponibilidad. Es la misma lista que
        # `tecnicos` y se conserva solo para la plantilla antigua.
        'tecnicos_disponibles': tecnicos,
        'tecnicos': tecnicos,
        'materiales_disponibles': materiales_disponibles,
        # Nuevas
        'q': filtros['q'],
        'qs': _qs(request),
        'filtros': filtros,
        'conteos': estadisticas.contar_por_estado(visibles),
        'total_filtrado': page_obj.paginator.count,
        'tipos': Incidencia.TIPO_CHOICES,
        'prioridades': Incidencia.PRIORIDAD_CHOICES,
        'estados': Incidencia.ESTADO_CHOICES,
        'ordenes': [('recientes', 'Más recientes'), ('antiguas', 'Más antiguas'),
                    ('prioridad', 'Prioridad (alta primero)')],
    })


def _contexto_reporte(errores=None, valores=None):
    return {
        'oc_b': True,
        'tipos': Incidencia.TIPO_CHOICES,
        'prioridades': Incidencia.PRIORIDAD_CHOICES,
        'prioridad_defecto': '2',
        'ubicacion_max': Incidencia.UBICACION_MAX,
        'descripcion_max': Incidencia.DESCRIPCION_MAX,
        'imagen_max_bytes': Incidencia.IMAGEN_MAX_BYTES,
        'imagen_max_mb': Incidencia.IMAGEN_MAX_BYTES // (1024 * 1024),
        'imagen_formatos': 'JPG, PNG, WEBP',
        'errores': errores or {},
        'valores': valores or {},
    }


@rol_requerido()
def reportar_incidencia(request):
    if request.method != 'POST':
        return render(request, 'reportar_incidencia.html', _contexto_reporte())

    post = request.POST
    errores = {}
    tipo, err = validaciones.validar_tipo_incidencia(
        post.get('tipo_incidencia', post.get('tipo')))
    if err:
        errores['tipo_incidencia'] = err
    prioridad, err = validaciones.validar_prioridad(post.get('prioridad'))
    if err:
        errores['prioridad'] = err
    ubicacion, err = validaciones.validar_ubicacion(post.get('ubicacion'))
    if err:
        errores['ubicacion'] = err
    descripcion, err = validaciones.validar_descripcion(post.get('descripcion'))
    if err:
        errores['descripcion'] = err
    imagen, err = validaciones.validar_imagen(request.FILES.get('imagen'))
    if err:
        errores['imagen'] = err

    if errores:
        _mensajes_de_errores(request, errores)
        valores = {'tipo_incidencia': tipo, 'prioridad': prioridad,
                   'ubicacion': ubicacion, 'descripcion': descripcion}
        return render(request, 'reportar_incidencia.html', _contexto_reporte(errores, valores))

    ahora = timezone.now()
    with transaction.atomic():
        incidencia = Incidencia.objects.create(
            tipo=tipo,
            # La prioridad que elige el solicitante es una propuesta; si quien
            # reporta es administrador, la que elige ya es la decisión.
            prioridad=prioridad or '2',
            prioridad_confirmada=es_administrador(request.user),
            ubicacion=ubicacion,
            descripcion=descripcion,
            fecha=ahora,
            usuario_reporte=request.user,
            imagen=imagen,
        )
        servicios.sincronizar_reporte(incidencia)
    messages.success(
        request,
        f"Su incidencia n.º {incidencia.pk} fue registrada. "
        "Puede seguir su estado en «Incidencias».",
    )
    return redirect('incidencias')


def _contexto_edicion(incidencia, caps, errores=None, valores=None):
    return {
        'incidencia': incidencia,
        'oc_b': True,
        'permisos': caps,
        'tipos': Incidencia.TIPO_CHOICES,
        'prioridades': Incidencia.PRIORIDAD_CHOICES,
        'estados': Incidencia.ESTADO_CHOICES,
        'ubicacion_max': Incidencia.UBICACION_MAX,
        'descripcion_max': Incidencia.DESCRIPCION_MAX,
        'materiales_asignados': incidencia.materialincidencia_set.select_related('material'),
        'errores': errores or {},
        'valores': valores or {},
    }


@rol_requerido()
def seleccionar_incidencia(request, item_id):
    """Edición de una incidencia; lo editable depende del rol y del estado."""
    incidencia = get_object_or_404(
        Incidencia.objects.select_related('usuario_reporte', 'tecnico_asignado__trabajador'),
        pk=item_id,
    )
    usuario = request.user
    caps = capacidades_incidencia(usuario, incidencia)
    if not caps['editar']:
        if es_dueno(usuario, incidencia):
            mensaje = (
                "Solo puede editar sus incidencias mientras estén Pendientes; "
                f"esta está en estado {incidencia.get_estado_display()}. "
                "Para un cambio, comuníquese con la Dirección de Mantenimiento."
            )
        elif caps['ver']:
            mensaje = "Su rol solo permite consultar esta incidencia, no modificarla."
        else:
            mensaje = "Esta incidencia pertenece a otra persona; usted no puede modificarla."
        return denegar(request, mensaje)

    if request.method != 'POST':
        return render(request, 'editar_incidencia.html', _contexto_edicion(incidencia, caps))

    post = request.POST
    errores, ignorados = {}, []
    nuevos = {}

    if caps['editar_datos']:
        if 'tipo' in post:
            nuevos['tipo'], err = validaciones.validar_tipo_incidencia(post.get('tipo'))
            if err:
                errores['tipo'] = err
        if 'ubicacion' in post:
            nuevos['ubicacion'], err = validaciones.validar_ubicacion(post.get('ubicacion'))
            if err:
                errores['ubicacion'] = err
        if 'descripcion' in post:
            nuevos['descripcion'], err = validaciones.validar_descripcion(post.get('descripcion'))
            if err:
                errores['descripcion'] = err
    else:
        for campo in ('tipo', 'ubicacion', 'descripcion'):
            if campo in post and limpiar(post.get(campo)) != limpiar(getattr(incidencia, campo)):
                ignorados.append(campo)

    if caps['gestionar_prioridad']:
        if 'prioridad' in post:
            nuevos['prioridad'], err = validaciones.validar_prioridad(
                post.get('prioridad'), obligatoria=True)
            if err:
                errores['prioridad'] = err
        if 'prioridad_confirmada' in post:
            marca = limpiar(post.getlist('prioridad_confirmada')[-1]).lower()
            nuevos['prioridad_confirmada'] = marca in ('1', 'true', 'on', 'si', 'sí')
        elif 'prioridad' in nuevos and nuevos['prioridad'] != incidencia.prioridad:
            # Corregir la prioridad equivale a confirmarla.
            nuevos['prioridad_confirmada'] = True
    else:
        if 'prioridad' in post and limpiar(post.get('prioridad')) != incidencia.prioridad:
            ignorados.append('prioridad')

    if caps['editar_fecha']:
        if 'fecha' in post:
            nuevos['fecha'], err = validaciones.validar_fecha_incidencia(
                post.get('fecha'), incidencia.fecha)
            if err:
                errores['fecha'] = err
    else:
        if 'fecha' in post:
            actual = timezone.localtime(incidencia.fecha).strftime('%Y-%m-%d %H:%M')
            if limpiar(post.get('fecha')) != actual:
                ignorados.append('fecha')

    if caps['cambiar_estado']:
        if 'estado' in post:
            if es_administrador(usuario):
                permitidos = None
            else:
                permitidos = {'en_proceso', 'resuelto', incidencia.estado}
            nuevos['estado'], err = validaciones.validar_estado_incidencia(
                post.get('estado'), permitidos)
            if err:
                errores['estado'] = err
    else:
        if 'estado' in post and limpiar(post.get('estado')) != incidencia.estado:
            ignorados.append('estado')

    if errores:
        _mensajes_de_errores(request, errores)
        valores = {campo: post.get(campo, '') for campo in
                   ('tipo', 'prioridad', 'fecha', 'ubicacion', 'descripcion', 'estado')}
        return render(request, 'editar_incidencia.html',
                      _contexto_edicion(incidencia, caps, errores, valores))

    with transaction.atomic():
        for campo in ('tipo', 'prioridad', 'prioridad_confirmada', 'fecha',
                      'ubicacion', 'descripcion'):
            if campo in nuevos:
                setattr(incidencia, campo, nuevos[campo])
        if 'estado' in nuevos:
            servicios.establecer_estado(incidencia, nuevos['estado'])
        servicios.guardar_incidencia(incidencia)

    if ignorados:
        etiquetas = {'tipo': 'tipo', 'ubicacion': 'ubicación', 'descripcion': 'descripción',
                     'prioridad': 'prioridad', 'fecha': 'fecha', 'estado': 'estado'}
        nombres = ', '.join(etiquetas[c] for c in ignorados)
        messages.warning(
            request,
            f"No se aplicaron los cambios en: {nombres}. Su rol no puede modificarlos "
            "(la prioridad la confirma el administrador).",
        )
    messages.success(request, f"Se guardaron los cambios de la incidencia n.º {incidencia.pk}.")
    return redirect('incidencias')


@rol_requerido(ADMINISTRADOR)
@require_POST
def confirmar_prioridad(request):
    """Confirma la prioridad propuesta (o la corrige y la confirma)."""
    pk = validaciones.entero_positivo(request.POST.get('incidencia_id'),
                                      maximo=2**31 - 1, minimo=1)
    incidencia = Incidencia.objects.filter(pk=pk).first() if pk else None
    if incidencia is None:
        messages.error(request, "No se encontró la incidencia. Actualice la página e inténtelo de nuevo.")
        return redirigir_atras(request)
    if 'prioridad' in request.POST:
        prioridad, err = validaciones.validar_prioridad(request.POST.get('prioridad'), obligatoria=True)
        if err:
            messages.error(request, err)
            return redirigir_atras(request)
        incidencia.prioridad = prioridad
    incidencia.prioridad_confirmada = True
    incidencia.save()
    messages.success(
        request,
        f"Prioridad {incidencia.get_prioridad_display()} confirmada para la incidencia n.º {incidencia.pk}.",
    )
    return redirigir_atras(request)


@rol_requerido(ADMINISTRADOR)
@require_POST
def asignar_tecnico(request):
    incidencia_id = validaciones.entero_positivo(
        request.POST.get('incidencia_id'), maximo=2**31 - 1, minimo=1)
    tecnico_id = validaciones.entero_positivo(
        request.POST.get('tecnico_id'), maximo=2**31 - 1, minimo=1)
    if not incidencia_id or not tecnico_id:
        messages.error(request, "Seleccione la incidencia y el técnico que la atenderá.")
        return redirigir_atras(request)
    incidencia = Incidencia.objects.select_related('tecnico_asignado__trabajador').filter(
        pk=incidencia_id).first()
    tecnico = Personal.objects.select_related('trabajador').filter(pk=tecnico_id).first()
    if incidencia is None or tecnico is None:
        messages.error(request, "La incidencia o el técnico ya no existen. Actualice la página.")
        return redirigir_atras(request)
    try:
        servicios.asignar_tecnico(incidencia, tecnico)
    except servicios.ErrorDeNegocio as exc:
        messages.error(request, str(exc))
    else:
        messages.success(
            request,
            f"Técnico {tecnico.trabajador.get_username()} asignado a la incidencia n.º {incidencia.pk}.",
        )
    return redirigir_atras(request)


@rol_requerido(ADMINISTRADOR)
@require_POST
def quitar_tecnico(request, incidencia_id):
    incidencia = get_object_or_404(
        Incidencia.objects.select_related('tecnico_asignado__trabajador'), pk=incidencia_id)
    try:
        anterior = servicios.quitar_tecnico(incidencia)
    except servicios.ErrorDeNegocio as exc:
        messages.error(request, str(exc))
    else:
        messages.success(
            request,
            f"Se quitó a {anterior.trabajador.get_username()} de la incidencia n.º "
            f"{incidencia.pk}, que vuelve a Pendiente.",
        )
    return redirigir_atras(request)


# ============================================================ materiales

def _contexto_material_lista(request, consulta, page_obj, tabla, errores=None, valores=None):
    return {
        'tableMaterial': tabla,
        'qs': _qs(request),
        'page_obj': page_obj,
        'q': consulta,
        'tipos': Incidencia.TIPO_CHOICES,
        'cantidad_max': MATERIAL_CANTIDAD_MAX,
        'errores': errores or {},
        'valores': valores or {},
        'abrir_registro': bool(errores),
    }


@rol_requerido(ADMINISTRADOR, ALMACENERO)
def materiales(request):
    if request.method == 'POST' and request.POST.get('action') == 'delete':
        return _eliminar_materiales(request)

    errores, valores = {}, {}
    if request.method == 'POST':
        post = request.POST
        nombre, err = validaciones.validar_material_nombre(
            post.get('username', post.get('nombre')))
        if err:
            errores['nombre'] = err
        tipo, err = validaciones.validar_material_tipo(
            post.get('tipo_material', post.get('tipo')))
        if err:
            errores['tipo'] = err
        cantidad, err = validaciones.validar_material_cantidad(post.get('cantidad'))
        if err:
            errores['cantidad'] = err
        if not errores:
            material = Material.objects.create(nombre=nombre, tipo=tipo, cantidad=cantidad)
            messages.success(
                request, f"Material «{material.nombre}» registrado con {material.cantidad} unidad(es).")
            return redirect('materiales')
        _mensajes_de_errores(request, errores)
        valores = {'nombre': nombre, 'tipo': tipo, 'cantidad': post.get('cantidad', '')}

    consulta = limpiar(request.GET.get('q'))
    tabla = Material.objects.order_by('nombre', 'id')
    if consulta:
        condicion = Q(nombre__icontains=consulta) | Q(tipo__icontains=consulta)
        codigos = _codigos_que_coinciden(Incidencia.TIPO_CHOICES, consulta)
        if codigos:
            condicion |= Q(tipo__in=codigos)
        tabla = tabla.filter(condicion)
    page_obj = _paginar(request, tabla)
    return render(request, 'all_materiales.html',
                  _contexto_material_lista(request, consulta, page_obj, tabla, errores, valores))


def _eliminar_materiales(request):
    ids = ids_validos(request.POST.getlist('ids'))
    if not ids:
        messages.warning(request, "Seleccione al menos un material para eliminar.")
        return redirect('materiales')
    candidatos = Material.objects.filter(pk__in=ids).annotate(
        n_usos=Count('materialincidencia', distinct=True))
    eliminables, bloqueados = [], []
    for material in candidatos:
        if material.n_usos:
            bloqueados.append(f"«{material.nombre}» ({material.n_usos} asignación/es)")
        else:
            eliminables.append(material.pk)
    if eliminables:
        Material.objects.filter(pk__in=eliminables).delete()
        messages.success(
            request,
            "Se eliminó 1 material." if len(eliminables) == 1
            else f"Se eliminaron {len(eliminables)} materiales.",
        )
    if bloqueados:
        messages.warning(
            request,
            "No se eliminó " + ', '.join(bloqueados) + ": está asignado a incidencias y "
            "borrarlo perdería el registro de lo consumido. Puede dejar su cantidad en 0.",
        )
    return redirect('materiales')


@rol_requerido(ADMINISTRADOR, ALMACENERO)
def seleccionar_material(request, item_id):
    material = get_object_or_404(Material, pk=item_id)

    def contexto(errores=None, valores=None):
        return {
            'material': material,
            'oc_b': True,
            'tipos': Incidencia.TIPO_CHOICES,
            'cantidad_max': MATERIAL_CANTIDAD_MAX,
            'errores': errores or {},
            'valores': valores or {},
        }

    if request.method != 'POST':
        return render(request, 'editar_material.html', contexto())

    post = request.POST
    errores = {}
    nombre, err = validaciones.validar_material_nombre(
        post.get('nombre', post.get('username', material.nombre)))
    if err:
        errores['nombre'] = err
    tipo, err = validaciones.validar_material_tipo(
        post.get('tipo', post.get('tipo_material', material.tipo)), actual=material.tipo)
    if err:
        errores['tipo'] = err
    cantidad, err = validaciones.validar_material_cantidad(
        post.get('cantidad', material.cantidad))
    if err:
        errores['cantidad'] = err
    if errores:
        _mensajes_de_errores(request, errores)
        valores = {'nombre': nombre, 'tipo': tipo, 'cantidad': post.get('cantidad', '')}
        return render(request, 'editar_material.html', contexto(errores, valores))

    with transaction.atomic():
        Material.objects.filter(pk=material.pk).update(
            nombre=nombre, tipo=tipo, cantidad=cantidad)
    messages.success(request, f"Se guardaron los cambios de «{nombre}».")
    return redirect('materiales')


@rol_requerido(ADMINISTRADOR, ALMACENERO)
@require_POST
def asignar_material(request):
    post = request.POST
    incidencia_id = validaciones.entero_positivo(
        post.get('incidencia_id'), maximo=2**31 - 1, minimo=1)
    material_id = validaciones.entero_positivo(
        post.get('material'), maximo=2**31 - 1, minimo=1)
    if not incidencia_id or not material_id:
        messages.error(request, "Seleccione la incidencia y el material que se va a usar.")
        return redirigir_atras(request)
    cantidad_txt = post.get('cantidad', '1')
    cantidad, err = validaciones.validar_material_cantidad(cantidad_txt, minimo=1)
    if err:
        messages.error(request, err)
        return redirigir_atras(request)
    incidencia = Incidencia.objects.filter(pk=incidencia_id).first()
    if incidencia is None:
        messages.error(request, "La incidencia ya no existe. Actualice la página.")
        return redirigir_atras(request)
    try:
        material = servicios.asignar_material(incidencia, material_id, cantidad)
    except servicios.ErrorDeNegocio as exc:
        messages.error(request, str(exc))
    else:
        messages.success(
            request,
            f"{cantidad} unidad(es) de «{material.nombre}» asignadas a la incidencia "
            f"n.º {incidencia.pk}; el inventario se actualizó.",
        )
    return redirigir_atras(request)


@rol_requerido(ADMINISTRADOR, ALMACENERO)
@require_POST
def quitar_material(request):
    registro_id = validaciones.entero_positivo(
        request.POST.get('material_incidencia_id'), maximo=2**31 - 1, minimo=1)
    if not registro_id:
        messages.error(request, "No se indicó qué material retirar. Actualice la página.")
        return redirigir_atras(request)
    try:
        nombre, cantidad = servicios.quitar_material(registro_id)
    except servicios.ErrorDeNegocio as exc:
        messages.warning(request, str(exc))
    else:
        messages.success(
            request,
            f"Se retiró «{nombre}»: {cantidad} unidad(es) volvieron al inventario.",
        )
    return redirigir_atras(request)


# ========================================================== estadísticas

@rol_requerido(ADMINISTRADOR, ALMACENERO)
def reportes(request):
    texto_periodo = limpiar(request.GET.get('mesAnio'))
    periodo = estadisticas.parsear_mes_anio(texto_periodo)
    if texto_periodo and periodo is None:
        messages.warning(
            request, "El mes indicado no es válido. Se muestran todos los periodos.")
        texto_periodo = ''

    incidencias_qs = Incidencia.objects.all()
    tabla = Reporte.objects.select_related('reporte_incidencia').order_by('-fecha', '-id')
    if periodo:
        anio_p, mes_p = periodo
        incidencias_qs = incidencias_qs.filter(fecha__year=anio_p, fecha__month=mes_p)
        tabla = tabla.filter(fecha__year=anio_p, fecha__month=mes_p)

    conteos = estadisticas.contar_por_estado(incidencias_qs)
    anio = estadisticas.anio_valido(request.GET.get('anio'))
    etiquetas_estado = dict(Incidencia.ESTADO_CHOICES)

    return render(request, 'all_reportes.html', {
        # Claves originales
        'tableReporte': tabla,
        'totalReportes': conteos['total'],
        'reporte_resuelto': conteos['resuelto'],
        'reporte_pendiente': conteos['pendiente'],
        'reporte_enProceso': conteos['en_proceso'],
        'incidencias_data': estadisticas.incidencias_por_mes(anio),
        'year': anio,
        'oc_b': True,
        'today': timezone.localdate(),
        # Nuevas
        'mesAnio': texto_periodo,
        'meses': estadisticas.MESES,
        'conteos': conteos,
        'por_estado': [
            {'codigo': codigo, 'etiqueta': etiquetas_estado[codigo], 'cantidad': conteos[codigo]}
            for codigo in ('pendiente', 'en_proceso', 'resuelto')
        ],
        'por_tipo': estadisticas.contar_por_tipo(incidencias_qs),
    })


def _texto_excel(valor):
    """Texto seguro para una celda: sin caracteres ilegales y sin fórmulas."""
    if valor is None:
        return ''
    return ILLEGAL_CHARACTERS_RE.sub('', str(valor))


def _escribir_fila(hoja, valores, textos=()):
    """Añade una fila; las columnas en ``textos`` se guardan siempre como texto
    (una descripción que empiece por «=» no debe ejecutarse como fórmula)."""
    hoja.append(valores)
    fila = hoja.max_row
    for indice in textos:
        celda = hoja.cell(row=fila, column=indice + 1)
        celda.data_type = 's'


@rol_requerido(ADMINISTRADOR, ALMACENERO)
def exportar_dashboard(request):
    anio = estadisticas.anio_valido(request.GET.get('anio'))
    data_meses = estadisticas.incidencias_por_mes(anio)
    conteos = estadisticas.contar_por_estado()

    libro = openpyxl.Workbook()

    # Hoja 1: estados
    ws_estados = libro.active
    ws_estados.title = 'Estados'
    ws_estados.append(['Estado', 'Total'])
    ws_estados['A1'].font = Font(bold=True)
    ws_estados['B1'].font = Font(bold=True)
    etiquetas_estado = dict(Incidencia.ESTADO_CHOICES)
    for codigo in ('pendiente', 'resuelto', 'en_proceso'):
        ws_estados.append([etiquetas_estado[codigo], conteos[codigo]])

    grafico_estado = PieChart()
    etiquetas = Reference(ws_estados, min_col=1, min_row=2, max_row=4)
    datos = Reference(ws_estados, min_col=2, min_row=1, max_row=4)
    grafico_estado.add_data(datos, titles_from_data=True)
    grafico_estado.set_categories(etiquetas)
    grafico_estado.title = "Incidencias por estado"
    grafico_estado.style = 10
    ws_estados.add_chart(grafico_estado, "D2")

    # Hoja 2: por mes (mismo cálculo que el dashboard)
    ws_meses = libro.create_sheet(title="Por Mes")
    ws_meses.append(['Mes', f'Incidencias {anio}'])
    ws_meses['A1'].font = Font(bold=True)
    ws_meses['B1'].font = Font(bold=True)
    for nombre_mes, valor in zip(estadisticas.MESES, data_meses):
        ws_meses.append([nombre_mes, valor])

    grafico_mes = BarChart()
    grafico_mes.type = "col"
    grafico_mes.title = f"Incidencias por mes ({anio})"
    grafico_mes.x_axis.title = "Mes"
    grafico_mes.y_axis.title = "Incidencias"
    datos_barras = Reference(ws_meses, min_col=2, min_row=1, max_row=13, max_col=2)
    categorias = Reference(ws_meses, min_col=1, min_row=2, max_row=13)
    grafico_mes.add_data(datos_barras, titles_from_data=True)
    grafico_mes.set_categories(categorias)
    ws_meses.add_chart(grafico_mes, "D2")

    # Hoja 3: por tipo
    ws_tipos = libro.create_sheet(title="Por Tipo")
    ws_tipos.append(['Tipo', 'Total'])
    ws_tipos['A1'].font = Font(bold=True)
    ws_tipos['B1'].font = Font(bold=True)
    for fila in estadisticas.contar_por_tipo():
        ws_tipos.append([fila['etiqueta'], fila['cantidad']])

    # Hoja 4: listado
    ws_listado = libro.create_sheet(title="Listado")
    encabezados = ['ID', 'Fecha', 'Tipo', 'Descripción', 'Estado', 'Prioridad',
                   'Prioridad confirmada', 'Ubicación', 'Solicitante', 'Técnico',
                   'Fecha de asignación', 'Fecha de resolución']
    ws_listado.append(encabezados)
    for celda in ws_listado[1]:
        celda.font = Font(bold=True)
        celda.alignment = Alignment(horizontal="center")

    def sin_zona(fecha):
        if fecha is not None and timezone.is_aware(fecha):
            return timezone.make_naive(fecha)
        return fecha

    lista = Incidencia.objects.select_related(
        'usuario_reporte', 'tecnico_asignado__trabajador').order_by('id')
    for inc in lista:
        _escribir_fila(ws_listado, [
            inc.pk,
            sin_zona(inc.fecha),
            _texto_excel(inc.get_tipo_display()),
            _texto_excel(inc.descripcion),
            _texto_excel(inc.get_estado_display()),
            _texto_excel(inc.get_prioridad_display()),
            'Sí' if inc.prioridad_confirmada else 'No',
            _texto_excel(inc.ubicacion),
            _texto_excel(inc.usuario_reporte.get_username()),
            _texto_excel(inc.tecnico_asignado.trabajador.get_username()
                         if inc.tecnico_asignado_id else ''),
            sin_zona(inc.fecha_asignacion),
            sin_zona(inc.fecha_resolucion),
        ], textos=(3, 7, 8, 9))

    respuesta = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    respuesta['Content-Disposition'] = 'attachment; filename=Dashboard_Incidencias.xlsx'
    libro.save(respuesta)
    return respuesta


# =============================================================== portada

def _recientes(queryset, limite=8):
    return list(
        queryset.select_related('usuario_reporte', 'tecnico_asignado__trabajador')
        .order_by('-fecha', '-id')[:limite]
    )


@rol_requerido()
def main(request):
    usuario = request.user
    notificaciones = Notification.objects.filter(user=usuario).order_by('-created_at', '-id')
    sin_leer = notificaciones.filter(is_read=False).count()

    administra = es_administrador(usuario)
    almacen = es_almacenero(usuario)
    tecnico = es_tecnico(usuario)

    visibles = _incidencias_visibles(usuario)
    conteos = estadisticas.contar_por_estado(visibles)
    abiertas = visibles.exclude(estado='resuelto')

    contexto = {
        # Claves originales
        'notifications': list(notificaciones[:10]),
        'unread_count': sin_leer,
        'oc_b': True,
        'is_admin': administra,
        'is_tecnico': tecnico,
        'is_almacenero': es_almacenero(usuario),
        'is_cliente': not (administra or tecnico or almacen),
        # Nuevas
        'rol_display': roles_texto(usuario),
        'conteos': conteos,
        'incidencias_recientes': _recientes(visibles),
        'incidencias_abiertas': _recientes(abiertas),
        'incidencias_sin_tecnico': [],
        'incidencias_sin_confirmar': [],
        'materiales_resumen': None,
        'soporte_pendientes': None,
    }
    if tecnico:
        contexto['incidencias_asignadas'] = _recientes(
            abiertas.filter(tecnico_asignado__trabajador=usuario))
    if administra or tecnico:
        contexto['soporte_pendientes'] = SolicitudSoporte.objects.filter(
            estado=SolicitudSoporte.ESTADO_PENDIENTE).count()
    if administra:
        sin_tecnico = abiertas.filter(tecnico_asignado__isnull=True)
        contexto['incidencias_sin_tecnico'] = list(
            sin_tecnico.select_related('usuario_reporte')
            .order_by('-prioridad', 'fecha', 'id')[:8]
        )
        contexto['incidencias_sin_confirmar'] = list(
            abiertas.filter(prioridad_confirmada=False)
            .select_related('usuario_reporte', 'tecnico_asignado__trabajador')
            .order_by('-prioridad', 'fecha', 'id')[:8]
        )
    if administra or almacen:
        contexto['materiales_resumen'] = Material.objects.aggregate(
            total=Count('id'),
            agotados=Count('id', filter=Q(cantidad=0)),
        )
    return render(request, 'main.html', contexto)


# ======================================================== notificaciones

def _respuesta_sin_sesion():
    return JsonResponse(
        {'status': 'error', 'message': 'Su sesión expiró. Vuelva a iniciar sesión.'},
        status=401,
    )


def get_notifications(request):
    """Últimas 50 notificaciones del usuario en sesión (JSON).

    ``notifications`` conserva la forma antigua (texto JSON serializado) y
    ``items`` es la lista limpia que debe usar la interfaz nueva.
    """
    if not request.user.is_authenticated:
        return _respuesta_sin_sesion()
    propias = Notification.objects.filter(user=request.user)
    recientes = list(propias.order_by('-created_at', '-id')[:50])
    antiguo = json.loads(serializers.serialize('json', recientes))
    for fila, notificacion in zip(antiguo, recientes):
        # La interfaz antigua antepone «/» a esta ruta.
        fila['fields']['urlAsociated'] = notificacion.url.lstrip('/')
    return JsonResponse({
        'notifications': json.dumps(antiguo),
        'items': [
            {
                'id': n.pk,
                'message': n.message,
                'is_read': n.is_read,
                'created_at': n.created_at.isoformat(),
                'url': n.url,
            }
            for n in recientes
        ],
        'unread_count': propias.filter(is_read=False).count(),
    }, safe=False)


@require_POST
def mark_as_read(request, notification_id):
    if not request.user.is_authenticated:
        return _respuesta_sin_sesion()
    actualizadas = Notification.objects.filter(
        pk=notification_id, user=request.user).update(is_read=True)
    if not actualizadas:
        return JsonResponse(
            {'status': 'error', 'message': 'Notificación no encontrada'}, status=404)
    return JsonResponse({'status': 'success'})


@require_POST
def delete_notification(request, notification_id):
    if not request.user.is_authenticated:
        return _respuesta_sin_sesion()
    borradas, _ = Notification.objects.filter(
        pk=notification_id, user=request.user).delete()
    if not borradas:
        return JsonResponse(
            {'status': 'error', 'message': 'Notificación no encontrada'}, status=404)
    return JsonResponse({'status': 'success'})


# ============================================================== personal

@rol_requerido(ADMINISTRADOR)
def personal(request):
    consulta = limpiar(request.GET.get('q'))
    tabla = (
        Personal.objects.select_related('trabajador', 'incidencia')
        .prefetch_related('trabajador__groups')
        .annotate(abiertas=Count(
            'incidencias_asignadas',
            filter=~Q(incidencias_asignadas__estado='resuelto'),
            distinct=True,
        ))
        .order_by('trabajador__username', 'id')
    )
    if consulta:
        tabla = tabla.filter(
            Q(trabajador__username__icontains=consulta)
            | Q(trabajador__first_name__icontains=consulta)
            | Q(trabajador__last_name__icontains=consulta)
            | Q(trabajador__email__icontains=consulta)
        )
    return render(request, 'all_personal.html', {
        'tablePersonal': tabla,
        'page_obj': _paginar(request, tabla),
        'q': consulta,
        'qs': _qs(request),
    })


# ============================================================== soporte

def _solicitudes_por_leer(solicitudes_qs, usuario, solo_del_solicitante=False):
    """Ids de solicitudes con respuestas ajenas sin leer.

    En la bandeja (`solo_del_solicitante`) solo cuentan los mensajes escritos
    por quien hizo la solicitud: son los que el personal de soporte debe atender.
    """
    pendientes = RespuestaSoporte.objects.filter(
        leido=False, solicitud__in=solicitudes_qs).exclude(autor=usuario)
    if solo_del_solicitante:
        pendientes = pendientes.filter(autor=F('solicitud__usuario'))
    return set(pendientes.values_list('solicitud_id', flat=True))


def _buscar_solicitudes(queryset, consulta, incluir_usuario):
    if not consulta:
        return queryset
    condicion = Q(descripcion__icontains=consulta)
    for campo, choices in (('tipo', SolicitudSoporte.TIPO_CHOICES),
                           ('estado', SolicitudSoporte.ESTADO_CHOICES)):
        codigos = _codigos_que_coinciden(choices, consulta)
        if codigos:
            condicion |= Q(**{f'{campo}__in': codigos})
    if incluir_usuario:
        condicion |= Q(usuario__username__icontains=consulta)
    return queryset.filter(condicion)


def _marcar_sin_leer(page_obj, ids_sin_leer):
    page_obj.object_list = list(page_obj.object_list)
    for solicitud in page_obj.object_list:
        solicitud.sin_leer = solicitud.pk in ids_sin_leer


@rol_requerido()
def solicitar_soporte(request):
    errores, valores = {}, {}
    if request.method == 'POST':
        post = request.POST
        if post.get('action') == 'delete':
            ids = ids_validos(post.getlist('ids'))
            if not ids:
                messages.warning(request, "Seleccione al menos una solicitud para eliminar.")
            else:
                borradas, _ = SolicitudSoporte.objects.filter(
                    pk__in=ids, usuario=request.user).delete()
                if borradas:
                    messages.success(request, "Solicitud(es) eliminada(s).")
                else:
                    messages.warning(
                        request, "Solo puede eliminar sus propias solicitudes de soporte.")
            return redirect('solicitar_soporte')

        tipo, err = validaciones.validar_tipo_soporte(post.get('tipo'))
        if err:
            errores['tipo'] = err
        descripcion, err = validaciones.validar_texto_soporte(
            post.get('descripcion'), SOPORTE_DESCRIPCION_MAX,
            "Describa el problema para que el equipo de soporte pueda ayudarle.")
        if err:
            errores['descripcion'] = err
        if not errores:
            SolicitudSoporte.objects.create(
                usuario=request.user, tipo=tipo, descripcion=descripcion)
            messages.success(request, "Su solicitud fue enviada. Recibirá la respuesta aquí y en sus notificaciones.")
            return redirect('solicitar_soporte')
        _mensajes_de_errores(request, errores)
        valores = {'tipo': tipo, 'descripcion': descripcion}

    consulta = limpiar(request.GET.get('q'))
    propias = SolicitudSoporte.objects.filter(usuario=request.user).order_by('-fecha_solicitud', '-id')
    tabla = _buscar_solicitudes(propias, consulta, incluir_usuario=False)
    page_obj = _paginar(request, tabla)
    sin_leer_ids = _solicitudes_por_leer(propias, request.user)
    _marcar_sin_leer(page_obj, sin_leer_ids)
    return render(request, 'soporte/solicitar_soporte.html', {
        'page_obj': page_obj,
        'solicitudes_por_leer': list(SolicitudSoporte.objects.filter(pk__in=sin_leer_ids)),
        'q': consulta,
        'qs': _qs(request),
        'tipos_soporte': SolicitudSoporte.TIPO_CHOICES,
        'descripcion_max': SOPORTE_DESCRIPCION_MAX,
        'errores': errores,
        'valores': valores,
    })


@rol_requerido(ADMINISTRADOR, TECNICO)
def bandeja_entrada_soporte(request):
    """Todas las solicitudes de soporte: las atienden administradores y técnicos;
    solo el administrador puede eliminarlas."""
    if request.method == 'POST':
        if request.POST.get('action') == 'delete':
            if not es_administrador(request.user):
                return denegar(
                    request,
                    "Solo un administrador puede eliminar solicitudes de soporte. "
                    "Usted puede verlas y responderlas.",
                )
            ids = ids_validos(request.POST.getlist('ids'))
            if not ids:
                messages.warning(request, "Seleccione al menos una solicitud para eliminar.")
            else:
                SolicitudSoporte.objects.filter(pk__in=ids).delete()
                messages.success(request, "Solicitud(es) eliminada(s).")
        return redirect('bandeja_entrada_soporte')

    consulta = limpiar(request.GET.get('q'))
    solicitudes = SolicitudSoporte.objects.select_related('usuario').order_by(
        '-fecha_solicitud', '-id')
    tabla = _buscar_solicitudes(solicitudes, consulta, incluir_usuario=True)
    page_obj = _paginar(request, tabla)
    sin_leer_ids = _solicitudes_por_leer(solicitudes, request.user, solo_del_solicitante=True)
    _marcar_sin_leer(page_obj, sin_leer_ids)
    return render(request, 'soporte/bandeja_entrada_soporte.html', {
        'solicitudes': tabla,
        'solicitudes_por_leer': list(SolicitudSoporte.objects.filter(pk__in=sin_leer_ids)),
        'page_obj': page_obj,
        'q': consulta,
        'qs': _qs(request),
        'puede_eliminar': es_administrador(request.user),
    })


@rol_requerido()
def detalle_solicitud(request, solicitud_id):
    solicitud = get_object_or_404(
        SolicitudSoporte.objects.select_related('usuario'), pk=solicitud_id)
    atiende = puede_atender_soporte(request.user)
    es_autor = solicitud.usuario_id == request.user.pk
    # Primero el permiso; recién después se marca nada como leído.
    if not (es_autor or atiende):
        return denegar(
            request,
            "Esta solicitud de soporte pertenece a otra persona. Solo su autor, "
            "los técnicos y los administradores pueden verla.",
        )

    if request.method == 'POST':
        mensaje, err = validaciones.validar_texto_soporte(
            request.POST.get('mensaje'), MENSAJE_SOPORTE_MAX,
            "Escriba el mensaje antes de enviarlo.")
        if err:
            messages.error(request, err)
        else:
            RespuestaSoporte.objects.create(
                solicitud=solicitud, autor=request.user, mensaje=mensaje)
        return redirect('detalle_solicitud', solicitud_id=solicitud.pk)

    RespuestaSoporte.objects.filter(solicitud=solicitud, leido=False).exclude(
        autor=request.user).update(leido=True)
    respuestas = list(solicitud.respuestas.select_related('autor').order_by('fecha', 'id'))
    return render(request, 'soporte/detalle_solicitud.html', {
        'solicitud': solicitud,
        'respuestas': respuestas,
        'es_autor': es_autor,
        'puede_responder': True,
        'puede_completar': (es_autor or atiende)
        and solicitud.estado != SolicitudSoporte.ESTADO_RESUELTO,
        'mensaje_max': MENSAJE_SOPORTE_MAX,
        'oc_b': True,
    })


@rol_requerido()
@require_POST
def completar_solicitud(request, solicitud_id):
    solicitud = get_object_or_404(SolicitudSoporte, pk=solicitud_id)
    if solicitud.usuario_id != request.user.pk and not puede_atender_soporte(request.user):
        return denegar(
            request,
            "Solo quien hizo la solicitud, un técnico o un administrador puede "
            "marcarla como completada.",
        )
    if solicitud.estado == SolicitudSoporte.ESTADO_RESUELTO:
        messages.info(request, "La solicitud ya estaba marcada como completada.")
    else:
        solicitud.estado = SolicitudSoporte.ESTADO_RESUELTO
        solicitud.save(update_fields=['estado'])
        messages.success(request, "La solicitud fue marcada como completada.")
    return redirect('detalle_solicitud', solicitud_id=solicitud.pk)
