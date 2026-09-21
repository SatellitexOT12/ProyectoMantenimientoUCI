"""Notificaciones: destinatario correcto y URL accesible para ese destinatario."""
import json

from django.urls import resolve

from usuarios.models import Incidencia, Notification, RespuestaSoporte

from .base import SGUMTestCase


class UrlsAccesiblesMixin:

    def comprobar_urls_accesibles(self):
        """Toda notificación lleva una ruta absoluta y su destinatario puede abrirla."""
        self.assertTrue(Notification.objects.exists())
        for noti in Notification.objects.select_related('user'):
            with self.subTest(destinatario=noti.user.username, mensaje=noti.message[:40]):
                self.assertTrue(noti.urlAsociated.startswith('/'), noti.urlAsociated)
                resolve(noti.urlAsociated)  # existe en las URLs del proyecto
                self.entrar(noti.user)
                self.assertEqual(self.client.get(noti.urlAsociated).status_code, 200)


class NotificacionesDeIncidenciasTest(UrlsAccesiblesMixin, SGUMTestCase):

    def test_al_reportar_se_avisa_al_solicitante_y_a_los_administradores(self):
        self.entrar(self.solicitante)
        self.client.post(self.url('reportar_incidencia'), {
            'tipo_incidencia': 'gas', 'prioridad': '3',
            'ubicacion': 'Comedor', 'descripcion': 'Olor a gas'})
        destinatarios = set(Notification.objects.values_list('user__username', flat=True))
        self.assertEqual(destinatarios, {'t_solicitante', 't_admin', 't_super'})
        propia = Notification.objects.get(user=self.solicitante)
        self.assertIn('Su incidencia', propia.message)
        self.comprobar_urls_accesibles()

    def test_al_asignar_se_avisa_al_tecnico(self):
        incidencia = self.crear_incidencia()
        Notification.objects.all().delete()
        self.entrar(self.admin)
        self.client.post(self.url('asignar_tecnico'), {
            'incidencia_id': incidencia.pk, 'tecnico_id': self.personal.pk})
        para_tecnico = Notification.objects.filter(user=self.tecnico)
        self.assertEqual(para_tecnico.count(), 1)
        self.assertIn('Se le asignó', para_tecnico.get().message)
        self.assertEqual(para_tecnico.get().urlAsociated, self.url('incidencias'))
        self.comprobar_urls_accesibles()

    def test_reasignar_avisa_solo_al_nuevo_y_no_repite(self):
        incidencia = self.crear_incidencia()
        self.entrar(self.admin)
        self.client.post(self.url('asignar_tecnico'), {
            'incidencia_id': incidencia.pk, 'tecnico_id': self.personal.pk})
        self.client.post(self.url('asignar_tecnico'), {
            'incidencia_id': incidencia.pk, 'tecnico_id': self.personal2.pk})
        self.assertEqual(Notification.objects.filter(user=self.tecnico).count(), 1)
        self.assertEqual(Notification.objects.filter(user=self.tecnico2).count(), 1)

    def test_un_cambio_de_estado_avisa_al_solicitante(self):
        incidencia = self.crear_incidencia(estado='en_proceso', tecnico_asignado=self.personal)
        Notification.objects.all().delete()
        self.entrar(self.tecnico)
        self.client.post(self.url('editar_incidencia', incidencia.pk), {'estado': 'resuelto'})
        aviso = Notification.objects.get(user=self.solicitante)
        self.assertIn('Resuelto', aviso.message)
        self.assertIn('En proceso', aviso.message)
        self.comprobar_urls_accesibles()

    def test_guardar_sin_cambiar_estado_ni_tecnico_no_notifica(self):
        incidencia = self.crear_incidencia(estado='en_proceso', tecnico_asignado=self.personal)
        Notification.objects.all().delete()
        self.entrar(self.admin)
        self.client.post(self.url('editar_incidencia', incidencia.pk), {'descripcion': 'Ajuste'})
        self.client.post(self.url('confirmar_prioridad'), {'incidencia_id': incidencia.pk})
        self.assertFalse(Notification.objects.exists())

    def test_asignar_avisa_al_solicitante_del_paso_a_en_proceso(self):
        incidencia = self.crear_incidencia()
        Notification.objects.all().delete()
        self.entrar(self.admin)
        self.client.post(self.url('asignar_tecnico'), {
            'incidencia_id': incidencia.pk, 'tecnico_id': self.personal.pk})
        self.assertTrue(Notification.objects.filter(
            user=self.solicitante, message__contains='En proceso').exists())


class NotificacionesDeSoporteTest(UrlsAccesiblesMixin, SGUMTestCase):

    def test_solicitud_nueva(self):
        solicitud = self.crear_solicitud(self.solicitante)
        # El autor, los administradores y los técnicos (que también atienden el soporte).
        destinatarios = set(Notification.objects.values_list('user__username', flat=True))
        self.assertEqual(destinatarios, {'t_solicitante', 't_admin', 't_super', 't_tecnico', 't_tecnico2'})
        for noti in Notification.objects.all():
            self.assertEqual(noti.urlAsociated, self.url('detalle_solicitud', solicitud.pk))
        self.comprobar_urls_accesibles()

    def test_la_url_del_solicitante_no_lleva_a_la_bandeja_de_administradores(self):
        self.crear_solicitud(self.solicitante)
        RespuestaSoporte.objects.create(
            solicitud=self.crear_solicitud(self.solicitante), autor=self.admin, mensaje='Hola')
        for noti in Notification.objects.filter(user=self.solicitante):
            self.assertNotIn('/admin/', noti.urlAsociated)

    def test_respuesta_del_administrador_avisa_al_solicitante(self):
        solicitud = self.crear_solicitud(self.solicitante)
        Notification.objects.all().delete()
        RespuestaSoporte.objects.create(solicitud=solicitud, autor=self.admin, mensaje='Ya lo vemos')
        self.assertEqual(list(Notification.objects.values_list('user__username', flat=True)),
                         ['t_solicitante'])
        self.comprobar_urls_accesibles()

    def test_respuesta_del_solicitante_avisa_a_los_administradores(self):
        solicitud = self.crear_solicitud(self.solicitante)
        Notification.objects.all().delete()
        RespuestaSoporte.objects.create(solicitud=solicitud, autor=self.solicitante, mensaje='¿Novedades?')
        self.assertEqual(set(Notification.objects.values_list('user__username', flat=True)),
                         {'t_admin', 't_super', 't_tecnico', 't_tecnico2'})
        self.comprobar_urls_accesibles()

    def test_respuesta_de_un_tecnico_avisa_solo_al_autor(self):
        solicitud = self.crear_solicitud(self.solicitante)
        Notification.objects.all().delete()
        RespuestaSoporte.objects.create(solicitud=solicitud, autor=self.tecnico, mensaje='Voy para allá')
        self.assertEqual(list(Notification.objects.values_list('user__username', flat=True)),
                         ['t_solicitante'])
        self.comprobar_urls_accesibles()

    def test_solicitud_de_un_tecnico_avisa_al_resto_del_personal_y_no_a_el(self):
        solicitud = self.crear_solicitud(self.tecnico)
        destinatarios = set(Notification.objects.values_list('user__username', flat=True))
        self.assertEqual(destinatarios, {'t_tecnico', 't_admin', 't_super', 't_tecnico2'})
        self.assertEqual(Notification.objects.filter(user=self.tecnico).count(), 1)  # solo su acuse
        self.assertTrue(solicitud.pk)
        self.comprobar_urls_accesibles()

    def test_marcar_como_completada_no_notifica_de_nuevo_por_el_campo_respuesta(self):
        solicitud = self.crear_solicitud(self.solicitante)
        Notification.objects.all().delete()
        solicitud.estado = 'resuelto'
        solicitud.save()
        self.assertFalse(Notification.objects.exists())


class TextoPlanoTest(SGUMTestCase):
    """Los avisos son texto plano: lo que escribe el usuario no puede llevar marcado."""

    def test_sin_marcado_en_los_avisos(self):
        self.crear_incidencia(ubicacion='<img src=x onerror=alert(1) ')
        self.crear_solicitud(descripcion='<script>alert(1)</script> hola <b onmouseover=x ')
        for noti in Notification.objects.all():
            self.assertNotIn('<', noti.message)
            self.assertNotIn('>', noti.message)


class ApiDeNotificacionesTest(SGUMTestCase):

    def test_anonimo_recibe_401_json(self):
        respuesta = self.client.get(self.url('get_notifications'))
        self.assertEqual(respuesta.status_code, 401)
        self.assertEqual(respuesta.json()['status'], 'error')

    def test_forma_de_la_respuesta(self):
        incidencia = self.crear_incidencia()
        self.entrar(self.solicitante)
        datos = self.client.get(self.url('get_notifications')).json()
        self.assertEqual(datos['unread_count'], 1)
        item = datos['items'][0]
        self.assertEqual(set(item), {'id', 'message', 'is_read', 'created_at', 'url'})
        self.assertEqual(item['url'], '/incidencias/')
        # Forma antigua: texto JSON con «urlAsociated» sin barra inicial.
        antiguo = json.loads(datos['notifications'])
        self.assertEqual(antiguo[0]['fields']['urlAsociated'], 'incidencias/')
        self.assertTrue(incidencia.pk)

    def test_notificaciones_antiguas_sin_url_apuntan_a_la_portada(self):
        Notification.objects.create(user=self.solicitante, message='vieja')
        Notification.objects.create(user=self.solicitante, message='vieja 2', urlAsociated='soporte')
        self.entrar(self.solicitante)
        urls = {i['message']: i['url'] for i in self.client.get(self.url('get_notifications')).json()['items']}
        self.assertEqual(urls['vieja'], '/main/')
        self.assertEqual(urls['vieja 2'], '/soporte')

    def test_solo_ve_las_suyas(self):
        Notification.objects.create(user=self.solicitante2, message='ajena')
        self.entrar(self.solicitante)
        self.assertEqual(self.client.get(self.url('get_notifications')).json()['items'], [])

    def test_marcar_como_leida_y_eliminar(self):
        propia = Notification.objects.create(user=self.solicitante, message='mía', urlAsociated='/main/')
        ajena = Notification.objects.create(user=self.solicitante2, message='ajena', urlAsociated='/main/')
        self.entrar(self.solicitante)
        self.assertEqual(self.client.post(self.url('mark_as_read', propia.pk)).json()['status'], 'success')
        propia.refresh_from_db()
        self.assertTrue(propia.is_read)
        self.assertEqual(self.client.post(self.url('mark_as_read', ajena.pk)).status_code, 404)
        self.assertEqual(self.client.post(self.url('delete_notification', ajena.pk)).status_code, 404)
        self.assertEqual(self.client.post(self.url('delete_notification', propia.pk)).status_code, 200)
        self.assertEqual(self.client.get(self.url('mark_as_read', propia.pk)).status_code, 405)

    def test_marcar_como_leida_exige_sesion(self):
        noti = Notification.objects.create(user=self.solicitante, message='x')
        self.assertEqual(self.client.post(self.url('mark_as_read', noti.pk)).status_code, 401)
        self.assertFalse(Notification.objects.get(pk=noti.pk).is_read)

    def test_modelo_normaliza_la_url(self):
        noti = Notification(user=self.solicitante, message='x', urlAsociated='incidencias/')
        self.assertEqual(noti.url, '/incidencias/')
        self.assertEqual(Incidencia.objects.count(), 0)
