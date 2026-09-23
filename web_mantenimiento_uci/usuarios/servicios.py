"""Operaciones de negocio compartidas por las vistas (y las pruebas).

Mantienen coherentes los datos redundantes del modelo: el ``Reporte`` que
acompaña a cada incidencia y el reflejo ``Personal.incidencia`` del técnico.
"""
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .models import Incidencia, Material, MaterialIncidencia, Reporte

PENDIENTE = 'pendiente'
EN_PROCESO = 'en_proceso'
RESUELTO = 'resuelto'


class ErrorDeNegocio(Exception):
    """Regla de negocio incumplida; el mensaje ya está listo para el usuario."""


# ---------------------------------------------------- reporte y personal

def sincronizar_reporte(incidencia):
    """Deja el Reporte de la incidencia igual que ella (o lo crea si falta)."""
    actualizados = Reporte.objects.filter(reporte_incidencia=incidencia).update(
        estado=incidencia.estado,
        descripcion=incidencia.descripcion,
        fecha=incidencia.fecha,
    )
    if not actualizados:
        Reporte.objects.create(
            reporte_incidencia=incidencia,
            estado=incidencia.estado,
            descripcion=incidencia.descripcion,
            fecha=incidencia.fecha,
        )


def sincronizar_personal(personal):
    """Actualiza Personal.incidencia con la incidencia abierta más reciente."""
    if personal is None:
        return
    abierta = (
        Incidencia.objects.filter(tecnico_asignado=personal)
        .exclude(estado=RESUELTO)
        .order_by('-fecha')
        .first()
    )
    nuevo_id = abierta.pk if abierta else None
    if personal.incidencia_id != nuevo_id:
        personal.incidencia = abierta
        personal.save(update_fields=['incidencia'])


# ------------------------------------------------------------ estado

def establecer_estado(incidencia, nuevo, ahora=None):
    """Cambia el estado en memoria y ajusta la marca de resolución."""
    ahora = ahora or timezone.now()
    if nuevo == incidencia.estado:
        return
    incidencia.estado = nuevo
    if nuevo == RESUELTO:
        incidencia.fecha_resolucion = ahora
    else:
        incidencia.fecha_resolucion = None


def guardar_incidencia(incidencia, tecnicos_afectados=()):
    """Guarda la incidencia y propaga a Reporte y a los técnicos implicados."""
    incidencia.save()
    sincronizar_reporte(incidencia)
    afectados = list(tecnicos_afectados)
    if incidencia.tecnico_asignado_id:
        afectados.append(incidencia.tecnico_asignado)
    vistos = set()
    for personal in afectados:
        if personal is not None and personal.pk not in vistos:
            vistos.add(personal.pk)
            sincronizar_personal(personal)


# -------------------------------------------------------- técnico asignado

def es_tecnico_valido(personal):
    return (
        personal.trabajador.is_active
        and personal.trabajador.groups.filter(name='tecnico').exists()
    )


@transaction.atomic
def asignar_tecnico(incidencia, personal):
    """Asigna (o cambia) el técnico. Una incidencia asignada pasa a En proceso."""
    if incidencia.estado == RESUELTO:
        raise ErrorDeNegocio(
            "La incidencia ya está resuelta; no se le puede asignar un técnico."
        )
    if not es_tecnico_valido(personal):
        raise ErrorDeNegocio(
            "El usuario seleccionado no es un técnico activo. "
            "Elija otro técnico de la lista."
        )
    anterior = incidencia.tecnico_asignado
    if anterior is not None and anterior.pk == personal.pk:
        raise ErrorDeNegocio("Ese técnico ya está asignado a la incidencia.")
    ahora = timezone.now()
    incidencia.tecnico_asignado = personal
    incidencia.fecha_asignacion = ahora
    if incidencia.estado == PENDIENTE:
        establecer_estado(incidencia, EN_PROCESO, ahora)
    guardar_incidencia(incidencia, tecnicos_afectados=[anterior])


@transaction.atomic
def quitar_tecnico(incidencia):
    """Retira el técnico. Si estaba En proceso vuelve a Pendiente (sin técnico)."""
    anterior = incidencia.tecnico_asignado
    if anterior is None:
        raise ErrorDeNegocio("La incidencia no tiene un técnico asignado.")
    if incidencia.estado == RESUELTO:
        raise ErrorDeNegocio(
            "La incidencia ya está resuelta; el técnico que la atendió queda "
            "registrado en su historial."
        )
    incidencia.tecnico_asignado = None
    incidencia.fecha_asignacion = None
    if incidencia.estado == EN_PROCESO:
        establecer_estado(incidencia, PENDIENTE)
    guardar_incidencia(incidencia, tecnicos_afectados=[anterior])
    return anterior


# -------------------------------------------------------------- materiales

@transaction.atomic
def asignar_material(incidencia, material_id, cantidad):
    """Descuenta stock y registra el uso. Seguro ante peticiones simultáneas.

    El descuento es una sola sentencia condicional (``cantidad >= pedido``),
    de modo que dos peticiones a la vez nunca dejan el stock en negativo.
    """
    try:
        material = Material.objects.get(pk=material_id)
    except Material.DoesNotExist:
        raise ErrorDeNegocio("El material seleccionado ya no existe.")
    descontados = Material.objects.filter(
        pk=material.pk, cantidad__gte=cantidad
    ).update(cantidad=F('cantidad') - cantidad)
    if not descontados:
        material.refresh_from_db()
        raise ErrorDeNegocio(
            f"No hay suficiente existencia de «{material.nombre}»: quedan "
            f"{material.cantidad} y usted pidió {cantidad}."
        )
    MaterialIncidencia.objects.create(
        incidencia=incidencia, material=material, cantidad_usada=cantidad
    )
    return material


@transaction.atomic
def quitar_material(registro_id):
    """Elimina la asignación y devuelve la cantidad al inventario."""
    try:
        registro = MaterialIncidencia.objects.select_for_update().select_related(
            'material'
        ).get(pk=registro_id)
    except MaterialIncidencia.DoesNotExist:
        raise ErrorDeNegocio(
            "Esa asignación de material ya había sido retirada."
        )
    Material.objects.filter(pk=registro.material_id).update(
        cantidad=F('cantidad') + registro.cantidad_usada
    )
    nombre, cantidad = registro.material.nombre, registro.cantidad_usada
    registro.delete()
    return nombre, cantidad
