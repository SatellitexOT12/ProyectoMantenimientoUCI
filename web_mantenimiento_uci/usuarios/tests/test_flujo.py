"""Ciclo completo de una incidencia: reporte, asignación, materiales, resolución."""
from datetime import timedelta

from django.utils import timezone

from usuarios.models import Incidencia, Material, MaterialIncidencia, Notification, Reporte

from .base import SGUMTestCase


class CicloDeVidaTest(SGUMTestCase):

    def test_reporte_asignacion_materiales_resolucion(self):
        # 1. El solicitante reporta.
        self.entrar(self.solicitante)
        respuesta = self.client.post(self.url('reportar_incidencia'), {
            'tipo_incidencia': 'electricidad', 'prioridad': '3',
            'ubicacion': 'Edificio 5, cuarto 12',
            'descripcion': 'No hay corriente en el cuarto'})
        self.assertRedirects(respuesta, self.url('incidencias'))
        incidencia = Incidencia.objects.get()
        self.assertEqual(incidencia.estado, 'pendiente')
        self.assertIsNone(incidencia.tecnico_asignado)
        self.assertEqual(incidencia.usuario_reporte, self.solicitante)
        reporte = Reporte.objects.get(reporte_incidencia=incidencia)
        self.assertEqual(reporte.descripcion, 'No hay corriente en el cuarto')
        self.assertEqual(reporte.estado, 'pendiente')

        # 2. El administrador asigna un técnico: pasa a En proceso.
        self.entrar(self.admin)
        respuesta = self.client.post(self.url('asignar_tecnico'), {
            'incidencia_id': incidencia.pk, 'tecnico_id': self.personal.pk})
        self.assertEqual(respuesta.status_code, 302)
        incidencia.refresh_from_db()
        self.assertEqual(incidencia.tecnico_asignado, self.personal)
        self.assertEqual(incidencia.estado, 'en_proceso')
        self.assertIsNotNone(incidencia.fecha_asignacion)
        self.assertEqual(Reporte.objects.get(reporte_incidencia=incidencia).estado, 'en_proceso')
        self.personal.refresh_from_db()
        self.assertEqual(self.personal.incidencia, incidencia)

        # 3. El almacenero asigna materiales: el stock baja.
        material = self.crear_material(cantidad=10)
        self.entrar(self.almacenero)
        respuesta = self.client.post(self.url('asignar_material'), {
            'incidencia_id': incidencia.pk, 'material': material.pk, 'cantidad': '4'})
        self.assertEqual(respuesta.status_code, 302)
        material.refresh_from_db()
        self.assertEqual(material.cantidad, 6)
        self.assertEqual(MaterialIncidencia.objects.get().cantidad_usada, 4)

        # 4. El técnico cierra la incidencia.
        self.entrar(self.tecnico)
        respuesta = self.client.post(
            self.url('editar_incidencia', incidencia.pk), {'estado': 'resuelto'})
        self.assertRedirects(respuesta, self.url('incidencias'))
        incidencia.refresh_from_db()
        self.assertEqual(incidencia.estado, 'resuelto')
        self.assertIsNotNone(incidencia.fecha_resolucion)
        self.assertEqual(Reporte.objects.get(reporte_incidencia=incidencia).estado, 'resuelto')
        # Al resolverse, el técnico queda libre.
        self.personal.refresh_from_db()
        self.assertIsNone(self.personal.incidencia)

        # 5. El solicitante ve el resultado y ya no puede editarla.
        self.entrar(self.solicitante)
        self.assertEqual(
            self.client.get(self.url('editar_incidencia', incidencia.pk)).status_code, 403)

    def test_reabrir_borra_la_fecha_de_resolucion_y_ocupa_al_tecnico(self):
        incidencia = self.crear_incidencia(estado='resuelto', tecnico_asignado=self.personal,
                                           fecha_resolucion=timezone.now())
        self.entrar(self.tecnico)
        self.client.post(self.url('editar_incidencia', incidencia.pk), {'estado': 'en_proceso'})
        incidencia.refresh_from_db()
        self.assertEqual(incidencia.estado, 'en_proceso')
        self.assertIsNone(incidencia.fecha_resolucion)
        self.personal.refresh_from_db()
        self.assertEqual(self.personal.incidencia, incidencia)


class AsignarTecnicoTest(SGUMTestCase):

    def asignar(self, incidencia, personal):
        self.entrar(self.admin)
        return self.client.post(self.url('asignar_tecnico'), {
            'incidencia_id': incidencia.pk, 'tecnico_id': personal.pk})

    def test_cambiar_de_tecnico_libera_al_anterior(self):
        incidencia = self.crear_incidencia()
        self.asignar(incidencia, self.personal)
        self.asignar(incidencia, self.personal2)
        incidencia.refresh_from_db()
        self.assertEqual(incidencia.tecnico_asignado, self.personal2)
        self.personal.refresh_from_db()
        self.personal2.refresh_from_db()
        self.assertIsNone(self.personal.incidencia)
        self.assertEqual(self.personal2.incidencia, incidencia)

    def test_un_tecnico_puede_tener_varias_incidencias(self):
        una, otra = self.crear_incidencia(), self.crear_incidencia()
        self.asignar(una, self.personal)
        self.asignar(otra, self.personal)
        self.assertEqual(Incidencia.objects.filter(tecnico_asignado=self.personal).count(), 2)
        # Ambas siguen atribuidas a él y su carga se ve en la lista.
        self.entrar(self.admin)
        contexto = self.client.get(self.url('incidencias')).context
        carga = {t.pk: t.abiertas for t in contexto['tecnicos']}
        self.assertEqual(carga[self.personal.pk], 2)
        self.assertEqual(carga[self.personal2.pk], 0)
        # Ya no se filtra por disponibilidad: están todos, del menos cargado al más cargado.
        self.assertEqual([t.pk for t in contexto['tecnicos']], [self.personal2.pk, self.personal.pk])
        self.assertEqual([t.pk for t in contexto['tecnicos_disponibles']],
                         [t.pk for t in contexto['tecnicos']])
        self.assertEqual(len(list(contexto['tecnicos'])), 2)

    def test_usuario_que_no_es_tecnico_se_rechaza(self):
        from usuarios.models import Personal
        falso = Personal.objects.create(trabajador=self.solicitante)
        incidencia = self.crear_incidencia()
        respuesta = self.asignar(incidencia, falso)
        incidencia.refresh_from_db()
        self.assertIsNone(incidencia.tecnico_asignado)
        self.assertIn('no es un técnico', self.textos(respuesta))

    def test_no_se_asigna_a_incidencia_resuelta(self):
        incidencia = self.crear_incidencia(estado='resuelto')
        respuesta = self.asignar(incidencia, self.personal)
        incidencia.refresh_from_db()
        self.assertIsNone(incidencia.tecnico_asignado)
        self.assertIn('resuelta', self.textos(respuesta))

    def test_datos_invalidos_no_rompen(self):
        self.entrar(self.admin)
        for datos in ({}, {'incidencia_id': 'x', 'tecnico_id': '1'},
                      {'incidencia_id': '99999', 'tecnico_id': '99999'}):
            respuesta = self.client.post(self.url('asignar_tecnico'), datos)
            self.assertEqual(respuesta.status_code, 302)
            self.assertEqual(self.mensajes(respuesta)[0][0], 'danger')

    def test_quitar_tecnico_vuelve_a_pendiente(self):
        incidencia = self.crear_incidencia()
        self.asignar(incidencia, self.personal)
        respuesta = self.client.post(self.url('quitar_tecnico', incidencia.pk),
                                     HTTP_REFERER='http://testserver/incidencias/?page=2')
        self.assertRedirects(respuesta, 'http://testserver/incidencias/?page=2', fetch_redirect_response=False)
        incidencia.refresh_from_db()
        self.assertIsNone(incidencia.tecnico_asignado)
        self.assertEqual(incidencia.estado, 'pendiente')
        self.personal.refresh_from_db()
        self.assertIsNone(self.personal.incidencia)

    def test_quitar_tecnico_sin_tecnico_no_falla_ni_necesita_referer(self):
        incidencia = self.crear_incidencia()
        self.entrar(self.admin)
        respuesta = self.client.post(self.url('quitar_tecnico', incidencia.pk))
        self.assertRedirects(respuesta, self.url('incidencias'), fetch_redirect_response=False)
        self.assertIn('no tiene un técnico', self.textos(respuesta))

    def test_redireccion_ignora_referer_de_otro_sitio(self):
        incidencia = self.crear_incidencia()
        self.entrar(self.admin)
        respuesta = self.client.post(self.url('quitar_tecnico', incidencia.pk),
                                     HTTP_REFERER='http://sitio-malicioso.example/robar')
        self.assertEqual(respuesta['Location'], self.url('incidencias'))


class EdicionDeIncidenciaTest(SGUMTestCase):

    def test_tecnico_solo_cambia_el_estado(self):
        incidencia = self.crear_incidencia(tecnico_asignado=self.personal, estado='en_proceso',
                                           descripcion='Original', prioridad='2')
        self.entrar(self.tecnico)
        respuesta = self.client.post(self.url('editar_incidencia', incidencia.pk), {
            'estado': 'resuelto', 'descripcion': 'Reescrita', 'prioridad': '3',
            'tipo': 'gas', 'ubicacion': 'Otro sitio'})
        self.assertEqual(respuesta.status_code, 302)
        incidencia.refresh_from_db()
        self.assertEqual(incidencia.estado, 'resuelto')
        self.assertEqual(incidencia.descripcion, 'Original')
        self.assertEqual(incidencia.prioridad, '2')
        self.assertEqual(incidencia.tipo, 'plomeria')
        self.assertIn('No se aplicaron', self.textos(respuesta))

    def test_tecnico_no_puede_volver_a_pendiente(self):
        incidencia = self.crear_incidencia(tecnico_asignado=self.personal, estado='en_proceso')
        self.entrar(self.tecnico)
        respuesta = self.client.post(
            self.url('editar_incidencia', incidencia.pk), {'estado': 'pendiente'})
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('estado', respuesta.context['errores'])
        incidencia.refresh_from_db()
        self.assertEqual(incidencia.estado, 'en_proceso')

    def test_estado_ausente_o_invalido_no_reinicia_a_pendiente(self):
        incidencia = self.crear_incidencia(estado='en_proceso', tecnico_asignado=self.personal)
        self.entrar(self.admin)
        self.client.post(self.url('editar_incidencia', incidencia.pk),
                         {'descripcion': 'Nueva descripción'})
        incidencia.refresh_from_db()
        self.assertEqual(incidencia.estado, 'en_proceso')
        self.assertEqual(incidencia.descripcion, 'Nueva descripción')
        respuesta = self.client.post(
            self.url('editar_incidencia', incidencia.pk), {'estado': 'inventado'})
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('estado', respuesta.context['errores'])

    def test_solicitante_edita_su_incidencia_pendiente(self):
        incidencia = self.crear_incidencia(self.solicitante)
        self.entrar(self.solicitante)
        respuesta = self.client.post(self.url('editar_incidencia', incidencia.pk), {
            'tipo': 'seguridad', 'ubicacion': 'Portería', 'descripcion': 'Cerradura rota',
            'prioridad': incidencia.prioridad, 'estado': 'resuelto'})
        self.assertEqual(respuesta.status_code, 302)
        incidencia.refresh_from_db()
        self.assertEqual(incidencia.tipo, 'seguridad')
        self.assertEqual(incidencia.ubicacion, 'Portería')
        self.assertEqual(incidencia.estado, 'pendiente')  # el estado no lo cambia el solicitante
        self.assertEqual(Reporte.objects.get(reporte_incidencia=incidencia).descripcion,
                         'Cerradura rota')

    def test_validaciones_al_editar(self):
        incidencia = self.crear_incidencia(self.solicitante)
        self.entrar(self.solicitante)
        respuesta = self.client.post(self.url('editar_incidencia', incidencia.pk), {
            'tipo': 'limpieza', 'ubicacion': 'x' * 51, 'descripcion': '   '})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(set(respuesta.context['errores']), {'tipo', 'ubicacion', 'descripcion'})
        incidencia.refresh_from_db()
        self.assertEqual(incidencia.tipo, 'plomeria')

    def test_fecha_solo_la_corrige_el_administrador_y_se_valida(self):
        incidencia = self.crear_incidencia()
        original = incidencia.fecha
        self.entrar(self.solicitante)
        self.client.post(self.url('editar_incidencia', incidencia.pk),
                         {'fecha': '2020-01-01 10:00', 'descripcion': 'x'})
        incidencia.refresh_from_db()
        self.assertEqual(incidencia.fecha, original)

        self.entrar(self.admin)
        futura = (timezone.localtime() + timedelta(days=2)).strftime('%Y-%m-%d %H:%M')
        respuesta = self.client.post(self.url('editar_incidencia', incidencia.pk), {'fecha': futura})
        self.assertIn('fecha', respuesta.context['errores'])
        respuesta = self.client.post(self.url('editar_incidencia', incidencia.pk), {'fecha': 'ayer'})
        self.assertIn('fecha', respuesta.context['errores'])
        respuesta = self.client.post(
            self.url('editar_incidencia', incidencia.pk), {'fecha': '2025-06-04 14:30'})
        self.assertEqual(respuesta.status_code, 302)
        incidencia.refresh_from_db()
        local = timezone.localtime(incidencia.fecha)
        self.assertEqual((local.year, local.month, local.day, local.hour, local.minute),
                         (2025, 6, 4, 14, 30))
        self.assertEqual(Reporte.objects.get(reporte_incidencia=incidencia).fecha, incidencia.fecha)

    def test_fecha_sin_cambios_conserva_los_segundos(self):
        incidencia = self.crear_incidencia()
        original = incidencia.fecha
        minuto = timezone.localtime(original).strftime('%Y-%m-%d %H:%M')
        self.entrar(self.admin)
        self.client.post(self.url('editar_incidencia', incidencia.pk), {'fecha': minuto})
        incidencia.refresh_from_db()
        self.assertEqual(incidencia.fecha, original)


class PrioridadTest(SGUMTestCase):
    """El solicitante propone; el administrador confirma o corrige."""

    def test_al_reportar_queda_propuesta(self):
        self.entrar(self.solicitante)
        self.client.post(self.url('reportar_incidencia'), {
            'tipo_incidencia': 'plomeria', 'prioridad': '3',
            'ubicacion': 'Edificio 1', 'descripcion': 'Urgente'})
        incidencia = Incidencia.objects.get()
        self.assertEqual(incidencia.prioridad, '3')
        self.assertFalse(incidencia.prioridad_confirmada)
        self.assertEqual(incidencia.prioridad_situacion, 'Propuesta')

    def test_si_reporta_un_administrador_ya_esta_confirmada(self):
        self.entrar(self.admin)
        self.client.post(self.url('reportar_incidencia'), {
            'tipo_incidencia': 'plomeria', 'prioridad': '1',
            'ubicacion': 'Edificio 1', 'descripcion': 'Llamada de un profesor'})
        self.assertTrue(Incidencia.objects.get().prioridad_confirmada)

    def test_prioridad_omitida_toma_media(self):
        self.entrar(self.solicitante)
        self.client.post(self.url('reportar_incidencia'), {
            'tipo_incidencia': 'plomeria', 'ubicacion': 'Edificio 1', 'descripcion': 'Algo'})
        self.assertEqual(Incidencia.objects.get().prioridad, '2')

    def test_administrador_confirma_con_un_clic(self):
        incidencia = self.crear_incidencia(prioridad='3')
        self.entrar(self.admin)
        respuesta = self.client.post(
            self.url('confirmar_prioridad'), {'incidencia_id': incidencia.pk})
        self.assertEqual(respuesta.status_code, 302)
        incidencia.refresh_from_db()
        self.assertTrue(incidencia.prioridad_confirmada)
        self.assertEqual(incidencia.prioridad, '3')
        self.assertEqual(incidencia.prioridad_situacion, 'Confirmada')

    def test_administrador_corrige_y_confirma(self):
        incidencia = self.crear_incidencia(prioridad='3')
        self.entrar(self.admin)
        self.client.post(self.url('confirmar_prioridad'),
                         {'incidencia_id': incidencia.pk, 'prioridad': '1'})
        incidencia.refresh_from_db()
        self.assertEqual((incidencia.prioridad, incidencia.prioridad_confirmada), ('1', True))

    def test_confirmar_con_prioridad_invalida_no_cambia_nada(self):
        incidencia = self.crear_incidencia(prioridad='3')
        self.entrar(self.admin)
        respuesta = self.client.post(self.url('confirmar_prioridad'),
                                     {'incidencia_id': incidencia.pk, 'prioridad': 'media'})
        incidencia.refresh_from_db()
        self.assertEqual((incidencia.prioridad, incidencia.prioridad_confirmada), ('3', False))
        self.assertEqual(self.mensajes(respuesta)[0][0], 'danger')

    def test_corregir_al_editar_equivale_a_confirmar(self):
        incidencia = self.crear_incidencia(prioridad='2')
        self.entrar(self.admin)
        self.client.post(self.url('editar_incidencia', incidencia.pk), {'prioridad': '3'})
        incidencia.refresh_from_db()
        self.assertEqual((incidencia.prioridad, incidencia.prioridad_confirmada), ('3', True))

    def test_confirmacion_explicita_al_editar(self):
        incidencia = self.crear_incidencia(prioridad='2')
        self.entrar(self.admin)
        # Patrón de casilla: campo oculto «0» y casilla «1».
        self.client.post(self.url('editar_incidencia', incidencia.pk),
                         {'prioridad': '2', 'prioridad_confirmada': ['0', '1']})
        incidencia.refresh_from_db()
        self.assertTrue(incidencia.prioridad_confirmada)
        self.client.post(self.url('editar_incidencia', incidencia.pk),
                         {'prioridad': '2', 'prioridad_confirmada': ['0']})
        incidencia.refresh_from_db()
        self.assertFalse(incidencia.prioridad_confirmada)

    def test_solicitante_no_cambia_ni_confirma_la_prioridad(self):
        incidencia = self.crear_incidencia(self.solicitante, prioridad='1')
        self.entrar(self.solicitante)
        respuesta = self.client.post(self.url('editar_incidencia', incidencia.pk), {
            'descripcion': 'Igual', 'prioridad': '3', 'prioridad_confirmada': '1'})
        self.assertEqual(respuesta.status_code, 302)
        incidencia.refresh_from_db()
        self.assertEqual((incidencia.prioridad, incidencia.prioridad_confirmada), ('1', False))
        self.assertIn('prioridad', self.textos(respuesta))

    def test_expuesta_en_la_lista(self):
        self.crear_incidencia(prioridad='3')
        self.entrar(self.admin)
        contexto = self.client.get(self.url('incidencias')).context
        self.assertEqual(contexto['conteos']['sin_confirmar'], 1)
        self.assertFalse(list(contexto['page_obj'])[0].prioridad_confirmada)
