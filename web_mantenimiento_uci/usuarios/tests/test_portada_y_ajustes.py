"""Portada, ajustes del proyecto y datos iniciales."""
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.messages import constants, utils as msg_utils
from django.utils import timezone

from .base import SGUMTestCase


class PortadaTest(SGUMTestCase):

    def contexto(self, usuario):
        self.entrar(usuario)
        respuesta = self.client.get(self.url('main'))
        self.assertEqual(respuesta.status_code, 200)
        return respuesta.context

    def test_banderas_de_rol(self):
        esperado = {
            'solicitante': (self.solicitante, (False, False, False, True)),
            'tecnico': (self.tecnico, (False, True, False, False)),
            'almacenero': (self.almacenero, (False, False, True, False)),
            'admin': (self.admin, (True, False, False, False)),
            'super': (self.superusuario, (True, False, False, False)),
        }
        for nombre, (usuario, banderas) in esperado.items():
            with self.subTest(rol=nombre):
                c = self.contexto(usuario)
                self.assertEqual(
                    (c['is_admin'], c['is_tecnico'], c['is_almacenero'], c['is_cliente']), banderas)

    def test_administrador_ve_conteos_y_pendientes(self):
        sin_tecnico_alta = self.crear_incidencia(prioridad='3')
        sin_tecnico_baja = self.crear_incidencia(prioridad='1')
        self.crear_incidencia(estado='en_proceso', tecnico_asignado=self.personal)
        self.crear_incidencia(estado='resuelto')
        self.crear_solicitud(self.solicitante)
        c = self.contexto(self.admin)
        self.assertEqual(
            {k: c['conteos'][k] for k in ('pendiente', 'en_proceso', 'resuelto', 'total',
                                          'sin_tecnico', 'sin_confirmar')},
            {'pendiente': 2, 'en_proceso': 1, 'resuelto': 1, 'total': 4,
             'sin_tecnico': 2, 'sin_confirmar': 3})
        # Las de mayor prioridad primero.
        self.assertEqual([i.pk for i in c['incidencias_sin_tecnico']],
                         [sin_tecnico_alta.pk, sin_tecnico_baja.pk])
        self.assertEqual(len(c['incidencias_sin_confirmar']), 3)
        self.assertEqual(len(c['incidencias_recientes']), 4)
        self.assertEqual(c['soporte_pendientes'], 1)
        self.assertEqual(c['rol_display'], 'Administrador')

    def test_solicitante_solo_ve_sus_cifras(self):
        self.crear_incidencia(self.solicitante)
        self.crear_incidencia(self.solicitante2)
        c = self.contexto(self.solicitante)
        self.assertEqual(c['conteos']['total'], 1)
        self.assertEqual(len(c['incidencias_recientes']), 1)
        self.assertEqual(c['incidencias_sin_tecnico'], [])
        self.assertEqual(c['rol_display'], 'Solicitante')

    def test_tecnico_ve_sus_asignadas(self):
        propia = self.crear_incidencia(estado='en_proceso', tecnico_asignado=self.personal)
        self.crear_incidencia(estado='en_proceso', tecnico_asignado=self.personal2)
        c = self.contexto(self.tecnico)
        self.assertEqual([i.pk for i in c['incidencias_asignadas']], [propia.pk])
        self.assertEqual(c['conteos']['total'], 1)

    def test_tecnico_ve_las_solicitudes_de_soporte_pendientes(self):
        self.crear_solicitud(self.solicitante)
        self.assertEqual(self.contexto(self.tecnico)['soporte_pendientes'], 1)
        self.assertIsNone(self.contexto(self.almacenero)['soporte_pendientes'])
        self.assertIsNone(self.contexto(self.solicitante)['soporte_pendientes'])

    def test_almacenero_ve_resumen_de_inventario(self):
        self.crear_material(cantidad=0)
        self.crear_material('Otro', cantidad=4)
        c = self.contexto(self.almacenero)
        self.assertEqual(c['materiales_resumen'], {'total': 2, 'agotados': 1})
        self.assertEqual(c['conteos']['total'], 0)

    def test_procesador_de_contexto_en_todas_las_paginas(self):
        self.entrar(self.tecnico)
        c = self.client.get(self.url('incidencias')).context
        self.assertTrue(c['is_tecnico'])
        self.assertEqual(c['rol_display'], 'Técnico')
        self.assertFalse(c['puede']['usuarios'])
        self.assertTrue(c['puede']['bandeja_soporte'])       # el técnico atiende soporte
        self.assertFalse(c['puede']['eliminar_soporte_ajeno'])  # pero no elimina
        self.assertTrue(c['puede']['reportar_incidencia'])
        self.entrar(self.almacenero)
        c = self.client.get(self.url('incidencias')).context
        self.assertTrue(c['puede']['materiales'] and c['puede']['dashboard'])
        self.assertFalse(c['puede']['asignar_tecnico'])


class AjustesTest(SGUMTestCase):

    def test_idioma_y_zona_horaria(self):
        self.assertEqual(settings.LANGUAGE_CODE, 'es')
        self.assertEqual(settings.TIME_ZONE, 'America/Havana')
        self.assertEqual(str(timezone.get_current_timezone()), 'America/Havana')

    def test_las_alertas_usan_clases_del_sistema_de_diseno(self):
        etiquetas = msg_utils.get_level_tags()
        self.assertEqual(etiquetas[constants.ERROR], 'danger')
        self.assertEqual(etiquetas[constants.SUCCESS], 'success')
        self.assertEqual(etiquetas[constants.WARNING], 'warning')
        self.assertEqual(etiquetas[constants.INFO], 'info')

    def test_los_cuatro_grupos_existen(self):
        nombres = set(Group.objects.values_list('name', flat=True))
        self.assertLessEqual({'administrador', 'tecnico', 'almacenero', 'cliente'}, nombres)

    def test_mensajes_de_django_en_espanol(self):
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError) as ctx:
            validate_password('123')
        self.assertIn('caracteres', ' '.join(ctx.exception.messages))

    def test_configuracion_por_variables_de_entorno(self):
        import importlib
        import os
        from unittest import mock
        modulo = importlib.import_module('web_mantenimiento_uci.settings')
        entorno = {'DJANGO_SECRET_KEY': 'otra-clave', 'DJANGO_DEBUG': '0',
                   'DJANGO_ALLOWED_HOSTS': 'a.uci.cu, b.uci.cu', 'DB_NAME': 'otra_base',
                   'DB_PASSWORD': 'secreta', 'DB_HOST': 'db.interno', 'DB_PORT': '6543'}
        with mock.patch.dict(os.environ, entorno):
            recargado = importlib.reload(modulo)
            self.assertEqual(recargado.SECRET_KEY, 'otra-clave')
            self.assertFalse(recargado.DEBUG)
            self.assertEqual(recargado.ALLOWED_HOSTS, ['a.uci.cu', 'b.uci.cu'])
            base = recargado.DATABASES['default']
            self.assertEqual((base['NAME'], base['PASSWORD'], base['HOST'], base['PORT']),
                             ('otra_base', 'secreta', 'db.interno', '6543'))
        # Con el entorno limpio se recuperan los valores de siempre.
        limpio = {k: v for k, v in os.environ.items()
                  if not k.startswith(('DJANGO_SECRET', 'DJANGO_DEBUG', 'DJANGO_ALLOWED', 'DB_'))}
        with mock.patch.dict(os.environ, limpio, clear=True):
            por_defecto = importlib.reload(modulo)
            self.assertTrue(por_defecto.DEBUG)
            self.assertEqual(por_defecto.ALLOWED_HOSTS, [])
            base = por_defecto.DATABASES['default']
            self.assertEqual(base['ENGINE'], 'django.db.backends.postgresql')
            self.assertEqual((base['NAME'], base['USER'], base['PASSWORD'], base['HOST'], base['PORT']),
                             ('mantenimientouci', 'postgres', 'root', 'localhost', '5432'))
            self.assertTrue(por_defecto.SECRET_KEY.startswith('django-insecure-'))
        importlib.reload(modulo)


class SoloUnaSuiteDePruebasTest(SGUMTestCase):

    def test_no_existe_tests_py_junto_al_paquete(self):
        import pathlib
        import usuarios
        raiz = pathlib.Path(usuarios.__file__).parent
        self.assertFalse((raiz / 'tests.py').exists())
        self.assertTrue((raiz / 'tests' / '__init__.py').exists())
