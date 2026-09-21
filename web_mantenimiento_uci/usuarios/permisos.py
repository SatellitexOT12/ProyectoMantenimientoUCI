"""Roles y permisos de SGUM-UCI.

Una sola fuente de verdad para «quién puede hacer qué». Las vistas, las
señales, el procesador de contexto y las etiquetas de plantilla usan estas
funciones; ninguna decide permisos por su cuenta.

Roles (grupos de Django): ``administrador``, ``tecnico``, ``almacenero`` y
``cliente`` (en la interfaz se muestra como «Solicitante»). El superusuario
cuenta siempre como administrador. Quien no pertenece a ningún grupo de
trabajo (administrador, técnico, almacenero) actúa como solicitante.
"""
from functools import wraps

from django.contrib.auth.models import User
from django.contrib.auth.views import redirect_to_login
from django.db.models import Q
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect, render
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.urls import reverse
from django.utils.html import escape
from django.utils.http import url_has_allowed_host_and_scheme

ADMINISTRADOR = 'administrador'
TECNICO = 'tecnico'
ALMACENERO = 'almacenero'
CLIENTE = 'cliente'

ROLES = (ADMINISTRADOR, TECNICO, ALMACENERO, CLIENTE)

# Nombre que ve el usuario. El grupo de Django sigue llamándose «cliente».
NOMBRES_ROL = {
    ADMINISTRADOR: 'Administrador',
    TECNICO: 'Técnico',
    ALMACENERO: 'Almacenero',
    CLIENTE: 'Solicitante',
}

ROLES_CHOICES = [(codigo, NOMBRES_ROL[codigo]) for codigo in ROLES]


# ---------------------------------------------------------------- roles

def roles_de(usuario):
    """Conjunto (inmutable) de roles efectivos del usuario.

    Se guarda en el propio objeto de usuario para no repetir la consulta
    dentro de una misma petición.
    """
    if not getattr(usuario, 'is_authenticated', False):
        return frozenset()
    en_cache = getattr(usuario, '_sgum_roles', None)
    if en_cache is not None:
        return en_cache
    # .all() aprovecha prefetch_related('groups') cuando existe.
    grupos = {grupo.name for grupo in usuario.groups.all()}
    trabajo = {rol for rol in (ADMINISTRADOR, TECNICO, ALMACENERO) if rol in grupos}
    if usuario.is_superuser:
        trabajo.add(ADMINISTRADOR)
    # «Solicitante» solo aparece cuando no hay ningún rol de trabajo; todos
    # los usuarios pueden reportar incidencias, esto no lo restringe.
    roles = frozenset(trabajo or {CLIENTE})
    usuario._sgum_roles = roles
    return roles


def es_administrador(usuario):
    return ADMINISTRADOR in roles_de(usuario)


def es_tecnico(usuario):
    return TECNICO in roles_de(usuario)


def es_almacenero(usuario):
    return ALMACENERO in roles_de(usuario)


def es_solicitante(usuario):
    return CLIENTE in roles_de(usuario)


def rol_principal(usuario):
    """Rol de mayor jerarquía (administrador > técnico > almacenero > solicitante)."""
    roles = roles_de(usuario)
    for rol in (ADMINISTRADOR, TECNICO, ALMACENERO, CLIENTE):
        if rol in roles:
            return rol
    return None


def nombre_rol(codigo):
    return NOMBRES_ROL.get(codigo, codigo)


def roles_texto(usuario):
    """«Administrador», «Técnico, Almacenero»… tal como se muestra."""
    roles = roles_de(usuario)
    return ', '.join(NOMBRES_ROL[rol] for rol in ROLES if rol in roles)


def usuarios_administradores():
    """Usuarios activos que actúan como administrador (grupo o superusuario)."""
    return User.objects.filter(is_active=True).filter(
        Q(groups__name=ADMINISTRADOR) | Q(is_superuser=True)
    ).distinct()


def usuarios_que_atienden_soporte():
    """Usuarios activos que responden solicitudes de soporte: administradores
    (grupo o superusuario) y técnicos."""
    return User.objects.filter(is_active=True).filter(
        Q(groups__name__in=[ADMINISTRADOR, TECNICO]) | Q(is_superuser=True)
    ).distinct()


def puede_atender_soporte(usuario):
    """Ver todas las solicitudes de soporte, responderlas y marcarlas completadas."""
    return es_administrador(usuario) or es_tecnico(usuario)


def puede_eliminar_soporte_ajeno(usuario):
    """Eliminar solicitudes de soporte de otras personas: solo el administrador."""
    return es_administrador(usuario)


# ---------------------------------------------------- capacidades globales

def capacidades(usuario):
    """Qué secciones y acciones generales tiene el usuario (para menús)."""
    admin = es_administrador(usuario)
    almacen = admin or es_almacenero(usuario)
    return {
        'reportar_incidencia': True,
        'ver_todas_las_incidencias': almacen,
        'usuarios': admin,
        'personal': admin,
        'materiales': almacen,
        'dashboard': almacen,
        'exportar': almacen,
        'bandeja_soporte': puede_atender_soporte(usuario),
        'eliminar_soporte_ajeno': puede_eliminar_soporte_ajeno(usuario),
        'asignar_tecnico': admin,
        'asignar_material': almacen,
        'gestionar_prioridad': admin,
    }


# --------------------------------------------- capacidades por incidencia

def es_dueno(usuario, incidencia):
    return incidencia.usuario_reporte_id == usuario.pk


def es_tecnico_asignado(usuario, incidencia):
    if not incidencia.tecnico_asignado_id:
        return False
    return incidencia.tecnico_asignado.trabajador_id == usuario.pk


def puede_ver_incidencia(usuario, incidencia):
    if es_administrador(usuario) or es_almacenero(usuario):
        return True
    return es_dueno(usuario, incidencia) or es_tecnico_asignado(usuario, incidencia)


def puede_editar_datos(usuario, incidencia):
    """Tipo, ubicación y descripción."""
    if es_administrador(usuario):
        return True
    return es_dueno(usuario, incidencia) and incidencia.estado == 'pendiente'


def puede_gestionar_prioridad(usuario, incidencia=None):
    """Cambiar y confirmar la prioridad: solo el administrador."""
    return es_administrador(usuario)


def puede_editar_fecha(usuario, incidencia=None):
    return es_administrador(usuario)


def puede_cambiar_estado(usuario, incidencia):
    if es_administrador(usuario):
        return True
    return es_tecnico_asignado(usuario, incidencia)


def puede_editar_incidencia(usuario, incidencia):
    """¿Tiene algo que editar? (abre el formulario de edición)."""
    return (
        puede_editar_datos(usuario, incidencia)
        or puede_cambiar_estado(usuario, incidencia)
    )


def puede_eliminar_incidencia(usuario, incidencia):
    if es_administrador(usuario):
        return True
    return es_dueno(usuario, incidencia) and incidencia.estado == 'pendiente'


def puede_asignar_tecnico(usuario):
    return es_administrador(usuario)


def puede_asignar_material(usuario):
    return es_administrador(usuario) or es_almacenero(usuario)


def capacidades_incidencia(usuario, incidencia):
    """Diccionario con lo que el usuario puede hacer sobre una incidencia."""
    return {
        'ver': puede_ver_incidencia(usuario, incidencia),
        'editar': puede_editar_incidencia(usuario, incidencia),
        'editar_datos': puede_editar_datos(usuario, incidencia),
        'cambiar_estado': puede_cambiar_estado(usuario, incidencia),
        'gestionar_prioridad': puede_gestionar_prioridad(usuario, incidencia),
        'editar_fecha': puede_editar_fecha(usuario, incidencia),
        'eliminar': puede_eliminar_incidencia(usuario, incidencia),
        'asignar_tecnico': puede_asignar_tecnico(usuario),
        'asignar_material': puede_asignar_material(usuario),
    }


# --------------------------------------------------------- respuestas 403

MENSAJE_SIN_PERMISO = (
    "Su rol ({rol}) no tiene permiso para esta acción. Si cree que se trata "
    "de un error, comuníquese con la Dirección de Mantenimiento."
)


def _pide_json(request):
    return (
        request.headers.get('x-requested-with') == 'XMLHttpRequest'
        or 'application/json' in request.headers.get('accept', '')
    )


def denegar(request, mensaje=None, json=False):
    """Respuesta 403 clara y en español.

    Usa la plantilla ``403.html`` si existe; si no, una página mínima. Para
    peticiones AJAX responde JSON.
    """
    if mensaje is None:
        mensaje = MENSAJE_SIN_PERMISO.format(rol=roles_texto(request.user) or 'sin rol')
    if json or _pide_json(request):
        return JsonResponse({'status': 'error', 'message': mensaje}, status=403)
    try:
        get_template('403.html')
    except TemplateDoesNotExist:
        inicio = reverse('main')
        html = (
            '<!doctype html><html lang="es"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>Acceso denegado · SGUM-UCI</title></head><body>'
            f'<h1>Acceso denegado</h1><p>{escape(mensaje)}</p>'
            f'<p><a href="{inicio}">Volver al inicio</a></p></body></html>'
        )
        return HttpResponseForbidden(html)
    return render(request, '403.html', {'mensaje': mensaje}, status=403)


def rol_requerido(*roles, mensaje=None):
    """Exige sesión iniciada y pertenecer a alguno de los roles indicados.

    - Sin sesión: redirige al inicio de sesión (con ``next``).
    - Con sesión pero sin permiso: 403 con un texto claro.
    Sin roles, solo exige sesión.
    """
    permitidos = set(roles)

    def decorador(vista):
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if permitidos and not (roles_de(request.user) & permitidos):
                return denegar(request, mensaje)
            return vista(request, *args, **kwargs)
        return envoltura
    return decorador


# Nombre antiguo, conservado por compatibilidad.
grupo_requerido = rol_requerido


# ------------------------------------------------------------ redirección

def redirigir_atras(request, respaldo='incidencias'):
    """Vuelve a la página de origen si es del mismo sitio; si no, a ``respaldo``.

    Nunca falla por falta de ``Referer`` ni permite redirigir a otro dominio.
    """
    destino = request.POST.get('next') or request.META.get('HTTP_REFERER')
    if destino and url_has_allowed_host_and_scheme(
        destino,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(destino)
    return redirect(respaldo)
