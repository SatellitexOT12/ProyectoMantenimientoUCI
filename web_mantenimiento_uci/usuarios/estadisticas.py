"""Conteos que comparten el dashboard, la exportación a Excel y la portada."""
import re

from django.db.models import Count, Q
from django.db.models.functions import ExtractMonth
from django.utils import timezone

from .models import Incidencia

MESES = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
]

_MES_ANIO = re.compile(r'^(\d{4})-(\d{1,2})$')


def contar_por_estado(queryset=None):
    """Conteos de un conjunto de incidencias, en una sola consulta.

    Claves: pendiente, en_proceso, resuelto, total; y sobre las abiertas
    (no resueltas): abiertas, sin_tecnico, sin_confirmar (prioridad aún
    solo propuesta).
    """
    if queryset is None:
        queryset = Incidencia.objects.all()
    abierta = ~Q(estado='resuelto')
    return queryset.aggregate(
        pendiente=Count('id', filter=Q(estado='pendiente')),
        en_proceso=Count('id', filter=Q(estado='en_proceso')),
        resuelto=Count('id', filter=Q(estado='resuelto')),
        total=Count('id'),
        abiertas=Count('id', filter=abierta),
        sin_tecnico=Count('id', filter=abierta & Q(tecnico_asignado__isnull=True)),
        sin_confirmar=Count('id', filter=abierta & Q(prioridad_confirmada=False)),
    )


def incidencias_por_mes(anio):
    """Lista de 12 enteros (enero..diciembre) con las incidencias de ``anio``.

    Agrupa por mes con un solo ``GROUP BY``. Es la única implementación:
    la usan tanto el dashboard como la exportación a Excel.
    """
    filas = (
        Incidencia.objects.filter(fecha__year=anio)
        .annotate(mes=ExtractMonth('fecha'))
        .values('mes')
        .annotate(cantidad=Count('id'))
        .order_by('mes')
    )
    datos = [0] * 12
    for fila in filas:
        mes = fila['mes']
        if mes and 1 <= mes <= 12:
            datos[mes - 1] = fila['cantidad']
    return datos


def contar_por_tipo(queryset=None):
    """Lista de dicts {'codigo', 'etiqueta', 'cantidad'} para los 10 tipos."""
    if queryset is None:
        queryset = Incidencia.objects.all()
    cuentas = {
        fila['tipo']: fila['cantidad']
        for fila in queryset.values('tipo').annotate(cantidad=Count('id'))
    }
    return [
        {'codigo': codigo, 'etiqueta': etiqueta, 'cantidad': cuentas.get(codigo, 0)}
        for codigo, etiqueta in Incidencia.TIPO_CHOICES
    ]


def parsear_mes_anio(valor):
    """'2025-06' -> (2025, 6); devuelve None si no es válido."""
    if not valor:
        return None
    coincide = _MES_ANIO.match(valor.strip())
    if not coincide:
        return None
    anio, mes = int(coincide.group(1)), int(coincide.group(2))
    if not (1 <= mes <= 12 and 2000 <= anio <= 2100):
        return None
    return anio, mes


def anio_valido(valor, por_defecto=None):
    """Año de un parámetro GET (por defecto el año actual)."""
    if por_defecto is None:
        por_defecto = timezone.localdate().year
    try:
        anio = int(valor)
    except (TypeError, ValueError):
        return por_defecto
    return anio if 2000 <= anio <= 2100 else por_defecto
