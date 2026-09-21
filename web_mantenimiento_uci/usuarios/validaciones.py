"""Validación en el servidor de todo lo que llega por formulario.

Cada función devuelve ``(valor_limpio, error)``; ``error`` es ``None`` si el
dato es válido, o un texto en español (trato de usted) que dice qué falló y
cómo corregirlo. Las claves de error usan los nombres de los campos POST.
"""
import re
from datetime import datetime

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.template.defaultfilters import filesizeformat
from django.utils import timezone

from .models import Incidencia, SolicitudSoporte

MATERIAL_NOMBRE_MAX = 100
MATERIAL_TIPO_MAX = 100
MATERIAL_CANTIDAD_MAX = 1_000_000
SOPORTE_DESCRIPCION_MAX = 2000
MENSAJE_SOPORTE_MAX = 2000
USUARIO_NOMBRE_MAX = 150

FORMATOS_IMAGEN = {'JPEG': 'JPG', 'PNG': 'PNG', 'WEBP': 'WEBP', 'GIF': 'GIF'}

_FORMATOS_FECHA = (
    '%Y-%m-%d %H:%M',
    '%Y-%m-%dT%H:%M',
    '%Y-%m-%d %H:%M:%S',
    '%Y-%m-%dT%H:%M:%S',
    '%d/%m/%Y %H:%M',
    '%Y-%m-%d',
    '%d/%m/%Y',
)

_SOLO_DIGITOS = re.compile(r'^[0-9]+$')


def limpiar(valor):
    """Recorta espacios y elimina caracteres NUL (PostgreSQL los rechaza)."""
    if valor is None:
        return ''
    return str(valor).replace('\x00', '').strip()


def entero_positivo(valor, maximo=MATERIAL_CANTIDAD_MAX, minimo=0):
    """Convierte un texto a entero estricto (solo dígitos ASCII) o devuelve None."""
    texto = limpiar(valor)
    if not _SOLO_DIGITOS.match(texto) or len(texto) > 12:
        return None
    numero = int(texto)
    if numero < minimo or numero > maximo:
        return None
    return numero


def ids_validos(valores):
    """Lista de ids enteros sin repetir, ignorando lo que no sea un número."""
    vistos = []
    for valor in valores:
        numero = entero_positivo(valor, maximo=2**31 - 1, minimo=1)
        if numero is not None and numero not in vistos:
            vistos.append(numero)
    return vistos


# ------------------------------------------------------------ incidencias

def validar_tipo_incidencia(valor):
    valor = limpiar(valor)
    if valor not in dict(Incidencia.TIPO_CHOICES):
        return valor, "Seleccione un tipo de incidencia de la lista."
    return valor, None


def validar_prioridad(valor, obligatoria=False):
    valor = limpiar(valor)
    if not valor:
        if obligatoria:
            return valor, "Seleccione una prioridad: Alta, Media o Baja."
        return valor, None
    if valor not in dict(Incidencia.PRIORIDAD_CHOICES):
        return valor, "Seleccione una prioridad válida: Alta, Media o Baja."
    return valor, None


def validar_ubicacion(valor):
    valor = limpiar(valor)
    maximo = Incidencia.UBICACION_MAX
    if not valor:
        return valor, "Indique la ubicación, por ejemplo «Edificio 3, apartamento 204»."
    if len(valor) > maximo:
        return valor, (
            f"La ubicación admite hasta {maximo} caracteres y usted escribió "
            f"{len(valor)}. Abrevie el texto."
        )
    return valor, None


def validar_descripcion(valor):
    valor = limpiar(valor)
    maximo = Incidencia.DESCRIPCION_MAX
    if not valor:
        return valor, "Describa el problema para que el técnico sepa qué va a encontrar."
    if len(valor) > maximo:
        return valor, (
            f"La descripción admite hasta {maximo} caracteres y usted escribió "
            f"{len(valor)}. Resuma el texto."
        )
    return valor, None


def validar_imagen(archivo):
    """Imagen opcional: tamaño máximo y formato real (no solo la extensión)."""
    if not archivo:
        return None, None
    maximo = Incidencia.IMAGEN_MAX_BYTES
    if archivo.size > maximo:
        return None, (
            f"La imagen pesa {filesizeformat(archivo.size)} y el máximo es "
            f"{filesizeformat(maximo)}. Tome la foto con menor resolución o "
            "adjunte otra."
        )
    mensaje_formato = (
        "El archivo adjunto no es una imagen válida. Adjunte una foto en "
        "formato JPG, PNG o WEBP."
    )
    try:
        # ImageField de formularios abre el archivo con Pillow y lo verifica.
        forms.ImageField().clean(archivo)
    except ValidationError:
        return None, mensaje_formato
    formato = getattr(getattr(archivo, 'image', None), 'format', None)
    if formato not in FORMATOS_IMAGEN:
        return None, mensaje_formato
    archivo.seek(0)
    return archivo, None


def parsear_fecha(valor):
    """Interpreta la fecha escrita por el usuario en la zona horaria local."""
    texto = limpiar(valor)
    for formato in _FORMATOS_FECHA:
        try:
            naive = datetime.strptime(texto, formato)
        except ValueError:
            continue
        return timezone.make_aware(naive, timezone.get_current_timezone())
    return None


def validar_fecha_incidencia(valor, actual=None):
    """Fecha corregida por el administrador: válida y no futura.

    Si el valor coincide con la fecha actual mostrada (al minuto) se conserva
    la original, con sus segundos.
    """
    texto = limpiar(valor)
    if not texto:
        return actual, None
    fecha = parsear_fecha(texto)
    if fecha is None:
        return actual, (
            "Escriba la fecha con el formato AAAA-MM-DD HH:MM, por ejemplo "
            "2025-06-04 14:30."
        )
    if actual is not None:
        local = timezone.localtime(actual).replace(second=0, microsecond=0)
        if fecha == local:
            return actual, None
    ahora = timezone.now()
    if fecha > ahora:
        return actual, "La fecha no puede ser posterior a hoy. Indique una fecha pasada."
    if fecha.year < 2000:
        return actual, "La fecha es demasiado antigua. Revise el año."
    return fecha, None


def validar_estado_incidencia(valor, permitidos=None):
    valor = limpiar(valor)
    validos = dict(Incidencia.ESTADO_CHOICES)
    if permitidos is not None:
        validos = {k: v for k, v in validos.items() if k in permitidos}
    if valor not in validos:
        nombres = ', '.join(validos.values())
        return valor, f"Seleccione un estado válido ({nombres})."
    return valor, None


# -------------------------------------------------------------- materiales

def validar_material_nombre(valor):
    valor = limpiar(valor)
    if not valor:
        return valor, "Escriba el nombre del material."
    if len(valor) > MATERIAL_NOMBRE_MAX:
        return valor, (
            f"El nombre admite hasta {MATERIAL_NOMBRE_MAX} caracteres y usted "
            f"escribió {len(valor)}."
        )
    return valor, None


def validar_material_tipo(valor, actual=None):
    """El tipo debe ser uno de los tipos de incidencia (fuente única: el modelo).

    En una edición se admite conservar el valor que ya tenía el material,
    aunque sea uno antiguo.
    """
    valor = limpiar(valor)
    if not valor:
        return valor, "Seleccione el tipo de material."
    if valor in dict(Incidencia.TIPO_CHOICES):
        return valor, None
    if actual is not None and valor == actual:
        return valor, None
    return valor, "Seleccione un tipo de material de la lista."


def validar_material_cantidad(valor, minimo=0):
    numero = entero_positivo(valor, maximo=MATERIAL_CANTIDAD_MAX, minimo=minimo)
    if numero is None:
        return None, (
            f"La cantidad debe ser un número entero entre {minimo} y "
            f"{MATERIAL_CANTIDAD_MAX:,}".replace(',', '.') + ", sin signos ni decimales."
        )
    return numero, None


# ---------------------------------------------------------------- usuarios

def validar_username(valor, excluir_pk=None):
    valor = limpiar(valor)
    if not valor:
        return valor, "Escriba el nombre de usuario."
    if len(valor) > USUARIO_NOMBRE_MAX:
        return valor, f"El usuario admite hasta {USUARIO_NOMBRE_MAX} caracteres."
    try:
        User._meta.get_field('username').run_validators(valor)
    except ValidationError:
        return valor, (
            "El nombre de usuario solo puede tener letras, números y los "
            "signos @ . + - _ (sin espacios)."
        )
    existentes = User.objects.filter(username__iexact=valor)
    if excluir_pk:
        existentes = existentes.exclude(pk=excluir_pk)
    if existentes.exists():
        return valor, f"El nombre de usuario «{valor}» ya está ocupado. Elija otro."
    return valor, None


def validar_email(valor, excluir_pk=None):
    valor = limpiar(valor)
    if not valor:
        return valor, "Escriba el correo electrónico."
    try:
        validate_email(valor)
    except ValidationError:
        return valor, "El correo no es válido. Escríbalo así: nombre@uci.cu."
    existentes = User.objects.filter(email__iexact=valor)
    if excluir_pk:
        existentes = existentes.exclude(pk=excluir_pk)
    if existentes.exists():
        return valor, f"El correo «{valor}» ya está registrado en otra cuenta."
    return valor, None


def validar_nombre_persona(valor, etiqueta, obligatorio):
    valor = limpiar(valor)
    if not valor:
        if obligatorio:
            return valor, f"Escriba {etiqueta}."
        return valor, None
    if len(valor) > USUARIO_NOMBRE_MAX:
        return valor, f"Se admiten hasta {USUARIO_NOMBRE_MAX} caracteres."
    return valor, None


def validar_contrasena(contrasena, confirmacion=None, usuario=None):
    """Aplica los AUTH_PASSWORD_VALIDATORS y la confirmación (si llega)."""
    if not contrasena:
        return contrasena, "Escriba la contraseña."
    if confirmacion is not None and contrasena != confirmacion:
        return contrasena, "Las contraseñas no coinciden. Escríbalas de nuevo."
    try:
        validate_password(contrasena, user=usuario)
    except ValidationError as exc:
        return contrasena, ' '.join(exc.messages)
    return contrasena, None


# ----------------------------------------------------------------- soporte

def validar_tipo_soporte(valor):
    valor = limpiar(valor)
    if valor not in dict(SolicitudSoporte.TIPO_CHOICES):
        return valor, "Seleccione el tipo de soporte: Software, Hardware u Otro."
    return valor, None


def validar_texto_soporte(valor, maximo, vacio):
    valor = limpiar(valor)
    if not valor:
        return valor, vacio
    if len(valor) > maximo:
        return valor, (
            f"El texto admite hasta {maximo} caracteres y usted escribió "
            f"{len(valor)}. Resúmalo."
        )
    return valor, None
