"""Solicitudes de soporte y su hilo de mensajes."""
from usuarios.models import Notification, RespuestaSoporte, SolicitudSoporte

from .base import SGUMTestCase


class SolicitarSoporteTest(SGUMTestCase):

    def test_crear_solicitud(self):
        self.entrar(self.solicitante)
        respuesta = self.client.post(
            self.url('solicitar_soporte'), {'tipo': 'hardware', 'descripcion': 'La PC no enciende'})
        self.assertRedirects(respuesta, self.url('solicitar_soporte'))
        solicitud = SolicitudSoporte.objects.get()
        self.assertEqual((solicitud.usuario, solicitud.tipo), (self.solicitante, 'hardware'))

    def test_validaciones(self):
        self.entrar(self.solicitante)
        for datos in ({'tipo': '', 'descripcion': 'x'}, {'tipo': 'magia', 'descripcion': 'x'},
                      {'tipo': 'otro', 'descripcion': '  '},
                      {'tipo': 'otro', 'descripcion': 'x' * 2001}):
            with self.subTest(datos=datos):
                respuesta = self.client.post(self.url('solicitar_soporte'), datos)
                self.assertEqual(respuesta.status_code, 200)
                self.assertTrue(respuesta.context['errores'])
        self.assertFalse(SolicitudSoporte.objects.exists())

    def test_solo_elimina_las_propias(self):
        propia = self.crear_solicitud(self.solicitante)
        ajena = self.crear_solicitud(self.solicitante2)
        self.entrar(self.solicitante)
        self.client.post(self.url('solicitar_soporte'),
                         {'action': 'delete', 'ids': [propia.pk, ajena.pk]})
        self.assertFalse(SolicitudSoporte.objects.filter(pk=propia.pk).exists())
        self.assertTrue(SolicitudSoporte.objects.filter(pk=ajena.pk).exists())

    def test_marca_sin_leer_solo_en_las_propias(self):
        propia = self.crear_solicitud(self.solicitante)
        ajena = self.crear_solicitud(self.solicitante2)
        RespuestaSoporte.objects.create(solicitud=propia, autor=self.admin, mensaje='Hola')
        RespuestaSoporte.objects.create(solicitud=ajena, autor=self.admin, mensaje='Hola')
        self.entrar(self.solicitante)
        contexto = self.client.get(self.url('solicitar_soporte')).context
        self.assertEqual([s.pk for s in contexto['solicitudes_por_leer']], [propia.pk])
        self.assertTrue(list(contexto['page_obj'])[0].sin_leer)


class BandejaTest(SGUMTestCase):
    """Decisión del usuario: administradores y técnicos atienden el soporte;
    solo el administrador elimina solicitudes."""

    def test_almacenero_y_solicitante_no_entran_pero_si_piden_soporte(self):
        for usuario in (self.solicitante, self.almacenero):
            self.entrar(usuario)
            self.assertEqual(self.client.get(self.url('bandeja_entrada_soporte')).status_code, 403)
            self.assertEqual(self.client.get(self.url('solicitar_soporte')).status_code, 200)

    def test_tecnico_y_administrador_ven_todas_y_las_sin_leer(self):
        una = self.crear_solicitud(self.solicitante)
        otra = self.crear_solicitud(self.solicitante2)
        RespuestaSoporte.objects.create(solicitud=una, autor=self.solicitante, mensaje='¿Hay novedades?')
        # Un mensaje de otro miembro del personal no cuenta como pendiente de atender.
        RespuestaSoporte.objects.create(solicitud=otra, autor=self.admin, mensaje='Lo vemos')
        for usuario in (self.tecnico, self.admin):
            self.entrar(usuario)
            contexto = self.client.get(self.url('bandeja_entrada_soporte')).context
            self.assertEqual({s.pk for s in contexto['page_obj']}, {una.pk, otra.pk})
            self.assertEqual([s.pk for s in contexto['solicitudes_por_leer']], [una.pk])

    def test_solo_el_administrador_elimina(self):
        una, otra = self.crear_solicitud(self.solicitante), self.crear_solicitud(self.solicitante2)
        self.entrar(self.tecnico)
        respuesta = self.client.post(self.url('bandeja_entrada_soporte'),
                                     {'action': 'delete', 'ids': [una.pk]})
        self.assertEqual(respuesta.status_code, 403)
        self.assertTrue(SolicitudSoporte.objects.filter(pk=una.pk).exists())
        contexto = self.client.get(self.url('bandeja_entrada_soporte')).context
        self.assertFalse(contexto['puede_eliminar'])
        self.entrar(self.admin)
        self.assertTrue(self.client.get(self.url('bandeja_entrada_soporte')).context['puede_eliminar'])
        self.client.post(self.url('bandeja_entrada_soporte'), {'action': 'delete', 'ids': [una.pk]})
        self.assertFalse(SolicitudSoporte.objects.filter(pk=una.pk).exists())
        self.assertTrue(SolicitudSoporte.objects.filter(pk=otra.pk).exists())

    def test_la_solicitud_propia_de_un_tecnico_es_como_la_de_cualquiera(self):
        propia = self.crear_solicitud(self.tecnico)
        self.entrar(self.tecnico)
        respuesta = self.client.post(self.url('solicitar_soporte'),
                                     {'tipo': 'hardware', 'descripcion': 'Mi teclado falla'})
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(SolicitudSoporte.objects.filter(usuario=self.tecnico).count(), 2)
        # Puede eliminar las suyas desde «solicitar soporte», no las ajenas.
        ajena = self.crear_solicitud(self.solicitante)
        self.client.post(self.url('solicitar_soporte'),
                         {'action': 'delete', 'ids': [propia.pk, ajena.pk]})
        self.assertFalse(SolicitudSoporte.objects.filter(pk=propia.pk).exists())
        self.assertTrue(SolicitudSoporte.objects.filter(pk=ajena.pk).exists())
        # Sus solicitudes le llegan al resto del personal (otros técnicos y administradores).
        self.assertTrue(Notification.objects.filter(user=self.tecnico2).exists())

    def test_buscar_por_usuario_y_por_tipo(self):
        self.crear_solicitud(self.solicitante, tipo='software')
        self.crear_solicitud(self.solicitante2, tipo='hardware')
        self.entrar(self.admin)
        respuesta = self.client.get(self.url('bandeja_entrada_soporte'), {'q': 'solicitante2'})
        self.assertEqual([s.usuario for s in respuesta.context['page_obj']], [self.solicitante2])
        respuesta = self.client.get(self.url('bandeja_entrada_soporte'), {'q': 'soft'})
        self.assertEqual([s.usuario for s in respuesta.context['page_obj']], [self.solicitante])


class DetalleSolicitudTest(SGUMTestCase):

    def setUp(self):
        self.solicitud = self.crear_solicitud(self.solicitante)
        self.respuesta_admin = RespuestaSoporte.objects.create(
            solicitud=self.solicitud, autor=self.admin, mensaje='Revisaremos su caso')

    def test_ajeno_recibe_403_y_no_marca_nada_como_leido(self):
        self.entrar(self.solicitante2)
        respuesta = self.client.get(self.url('detalle_solicitud', self.solicitud.pk))
        self.assertEqual(respuesta.status_code, 403)
        self.respuesta_admin.refresh_from_db()
        self.assertFalse(self.respuesta_admin.leido)

    def test_el_autor_marca_como_leidas_las_ajenas(self):
        self.entrar(self.solicitante)
        respuesta = self.client.get(self.url('detalle_solicitud', self.solicitud.pk))
        self.assertEqual(respuesta.status_code, 200)
        self.respuesta_admin.refresh_from_db()
        self.assertTrue(self.respuesta_admin.leido)
        self.assertEqual([r.pk for r in respuesta.context['respuestas']], [self.respuesta_admin.pk])

    def test_no_marca_como_leidas_las_propias(self):
        propia = RespuestaSoporte.objects.create(
            solicitud=self.solicitud, autor=self.solicitante, mensaje='Gracias')
        self.entrar(self.solicitante)
        self.client.get(self.url('detalle_solicitud', self.solicitud.pk))
        propia.refresh_from_db()
        self.assertFalse(propia.leido)

    def test_responder(self):
        self.entrar(self.solicitante)
        respuesta = self.client.post(
            self.url('detalle_solicitud', self.solicitud.pk), {'mensaje': '  Sigue sin funcionar  '})
        self.assertRedirects(respuesta, self.url('detalle_solicitud', self.solicitud.pk))
        self.assertEqual(self.solicitud.respuestas.latest('id').mensaje, 'Sigue sin funcionar')

    def test_mensaje_vacio_da_aviso(self):
        self.entrar(self.solicitante)
        respuesta = self.client.post(
            self.url('detalle_solicitud', self.solicitud.pk), {'mensaje': '   '})
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(self.solicitud.respuestas.count(), 1)
        self.assertEqual(self.mensajes(respuesta)[0][0], 'danger')

    def test_ajeno_no_puede_responder(self):
        self.entrar(self.solicitante2)
        respuesta = self.client.post(
            self.url('detalle_solicitud', self.solicitud.pk), {'mensaje': 'intruso'})
        self.assertEqual(respuesta.status_code, 403)
        self.assertEqual(self.solicitud.respuestas.count(), 1)

    def test_el_tecnico_ve_y_responde_solicitudes_ajenas(self):
        self.entrar(self.tecnico)
        self.assertEqual(
            self.client.get(self.url('detalle_solicitud', self.solicitud.pk)).status_code, 200)
        respuesta = self.client.post(
            self.url('detalle_solicitud', self.solicitud.pk), {'mensaje': 'Pase por el laboratorio'})
        self.assertEqual(respuesta.status_code, 302)
        ultimo = self.solicitud.respuestas.latest('id')
        self.assertEqual((ultimo.autor, ultimo.mensaje), (self.tecnico, 'Pase por el laboratorio'))

    def test_almacenero_no_ve_solicitudes_ajenas(self):
        self.entrar(self.almacenero)
        self.assertEqual(
            self.client.get(self.url('detalle_solicitud', self.solicitud.pk)).status_code, 403)
        self.assertEqual(
            self.client.post(self.url('detalle_solicitud', self.solicitud.pk),
                             {'mensaje': 'intruso'}).status_code, 403)
        self.assertEqual(self.solicitud.respuestas.count(), 1)

    def test_el_tecnico_marca_como_leidas_las_del_solicitante(self):
        del_usuario = RespuestaSoporte.objects.create(
            solicitud=self.solicitud, autor=self.solicitante, mensaje='¿Novedades?')
        self.entrar(self.tecnico)
        self.client.get(self.url('detalle_solicitud', self.solicitud.pk))
        del_usuario.refresh_from_db()
        self.assertTrue(del_usuario.leido)

    def test_administrador_lee_y_marca_las_del_usuario(self):
        del_usuario = RespuestaSoporte.objects.create(
            solicitud=self.solicitud, autor=self.solicitante, mensaje='¿Novedades?')
        self.entrar(self.admin)
        self.assertEqual(
            self.client.get(self.url('detalle_solicitud', self.solicitud.pk)).status_code, 200)
        del_usuario.refresh_from_db()
        self.assertTrue(del_usuario.leido)

    def test_completar_solo_por_post_y_solo_autor_tecnico_o_admin(self):
        url = self.url('completar_solicitud', self.solicitud.pk)
        self.entrar(self.solicitante)
        self.assertEqual(self.client.get(url).status_code, 405)
        for sin_permiso in (self.solicitante2, self.almacenero):
            self.entrar(sin_permiso)
            self.assertEqual(self.client.post(url).status_code, 403)
        self.solicitud.refresh_from_db()
        self.assertEqual(self.solicitud.estado, 'pendiente')
        self.entrar(self.solicitante)
        respuesta = self.client.post(url)
        self.assertRedirects(respuesta, self.url('detalle_solicitud', self.solicitud.pk))
        self.solicitud.refresh_from_db()
        self.assertEqual(self.solicitud.estado, 'resuelto')
        # Repetirlo no falla.
        self.assertEqual(self.client.post(url).status_code, 302)
