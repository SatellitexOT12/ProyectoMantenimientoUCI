"""Inicio de sesión y gestión de usuarios y roles."""
import json

from django.contrib.auth.models import Group, User

from usuarios.models import Personal

from .base import CLAVE, SGUMTestCase


class LoginTest(SGUMTestCase):

    def entrar_con(self, usuario, clave=CLAVE, **extra):
        return self.client.post(
            self.url('login'), {'username': usuario, 'password': clave, **extra})

    def test_entra_y_va_a_la_portada(self):
        respuesta = self.entrar_con(self.solicitante.username)
        self.assertRedirects(respuesta, self.url('main'))
        self.assertEqual(respuesta.wsgi_request.user, self.solicitante)

    def test_redirige_a_next_si_es_del_mismo_sitio(self):
        respuesta = self.entrar_con(self.admin.username, next='/incidencias/?estado=abiertas')
        self.assertEqual(respuesta['Location'], '/incidencias/?estado=abiertas')

    def test_ignora_next_de_otro_sitio(self):
        for destino in ('https://malo.example/', '//malo.example/x', 'javascript:alert(1)'):
            with self.subTest(destino=destino):
                self.client.logout()
                respuesta = self.entrar_con(self.admin.username, next=destino)
                self.assertEqual(respuesta['Location'], self.url('main'))

    def test_next_por_get_se_conserva_en_el_formulario(self):
        respuesta = self.client.get(self.url('login'), {'next': '/materiales/'})
        self.assertEqual(respuesta.context['next'], '/materiales/')

    def test_usuario_ya_autenticado_va_a_la_portada(self):
        self.entrar(self.solicitante)
        self.assertRedirects(self.client.get(self.url('login')), self.url('main'))

    def test_el_error_no_dice_que_campo_fallo(self):
        malo_usuario = self.entrar_con('no_existe')
        mala_clave = self.entrar_con(self.solicitante.username, 'incorrecta')
        self.assertEqual(malo_usuario.status_code, 200)
        self.assertEqual(malo_usuario.context['error'], mala_clave.context['error'])
        self.assertIn('Usuario o contraseña', mala_clave.context['error'])
        self.assertNotIn(self.solicitante.username, mala_clave.context['error'])

    def test_campos_ausentes_no_dan_error_500(self):
        respuesta = self.client.post(self.url('login'), {})
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('error', respuesta.context)

    def test_cuenta_desactivada_no_entra_y_el_mensaje_no_filtra_datos(self):
        self.solicitante.is_active = False
        self.solicitante.save()
        # Con la contraseña correcta se le explica que la cuenta está desactivada.
        respuesta = self.entrar_con(self.solicitante.username)
        self.assertEqual(respuesta.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertTrue(respuesta.context['cuenta_desactivada'])
        self.assertIn('desactivada', respuesta.context['error'])
        # Con contraseña incorrecta (o usuario inexistente) el mensaje es el genérico:
        # nadie puede averiguar qué cuentas existen ni cuáles están desactivadas.
        generico = self.entrar_con('no_existe').context['error']
        mala_clave = self.entrar_con(self.solicitante.username, 'incorrecta')
        self.assertEqual(mala_clave.context['error'], generico)
        self.assertFalse(mala_clave.context['cuenta_desactivada'])

    def test_la_sesion_abierta_deja_de_valer_al_desactivar(self):
        self.entrar(self.solicitante)
        self.assertEqual(self.client.get(self.url('incidencias')).status_code, 200)
        self.solicitante.is_active = False
        self.solicitante.save()
        respuesta = self.client.get(self.url('incidencias'))
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(self.url('login'), respuesta['Location'])

    def test_la_pagina_protegida_lleva_a_login_con_next(self):
        respuesta = self.client.get(self.url('materiales'))
        self.assertEqual(respuesta['Location'], self.login_url('/materiales/').replace('%2F', '/'))


class CrearUsuarioTest(SGUMTestCase):

    def crear(self, **extra):
        datos = {'username': 'nuevo_usuario', 'name': 'Ana', 'lastname': 'Pérez Gómez',
                 'email': 'ana@uci.cu', 'password': 'Clave-Segura-77', 'confirmPassword': 'Clave-Segura-77'}
        datos.update(extra)
        self.entrar(self.admin)
        return self.client.post(self.url('usuarios'), datos)

    def test_crea_con_rol_solicitante_por_defecto(self):
        respuesta = self.crear()
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.json()['success'])
        usuario = User.objects.get(username='nuevo_usuario')
        self.assertEqual([g.name for g in usuario.groups.all()], ['cliente'])
        self.assertTrue(usuario.check_password('Clave-Segura-77'))

    def test_crear_tecnico_crea_su_ficha_de_personal(self):
        self.crear(rol='tecnico')
        self.assertTrue(Personal.objects.filter(trabajador__username='nuevo_usuario').exists())

    def test_errores_por_campo(self):
        casos = [
            ({'username': self.solicitante.username}, 'usuario'),
            ({'username': 'T_SOLICITANTE'}, 'usuario'),  # sin distinguir mayúsculas
            ({'username': 'con espacios'}, 'usuario'),
            ({'email': self.solicitante.email}, 'email'),
            ({'email': 'no-es-correo'}, 'email'),
            ({'name': ''}, 'nombre'),
            ({'lastname': ''}, 'apellidos'),
            ({'password': 'corta1', 'confirmPassword': 'corta1'}, 'password'),
            ({'password': '12345678', 'confirmPassword': '12345678'}, 'password'),
            ({'password': 'password', 'confirmPassword': 'password'}, 'password'),
            ({'password': 'Clave-Segura-77', 'confirmPassword': 'otra'}, 'confirmPassword'),
            ({'rol': 'superheroe'}, 'rol'),
        ]
        for extra, campo in casos:
            with self.subTest(extra=extra):
                respuesta = self.crear(**extra)
                self.assertEqual(respuesta.status_code, 400)
                cuerpo = respuesta.json()
                self.assertFalse(cuerpo['success'])
                self.assertIn(campo, cuerpo['errors'])
        self.assertFalse(User.objects.filter(username='nuevo_usuario').exists())

    def test_la_contrasena_no_puede_parecerse_al_usuario(self):
        respuesta = self.crear(username='juanperez', password='juanperez1', confirmPassword='juanperez1')
        self.assertIn('password', respuesta.json()['errors'])

    def test_solo_el_administrador(self):
        self.entrar(self.almacenero)
        respuesta = self.client.post(self.url('usuarios'), {'username': 'x'})
        self.assertEqual(respuesta.status_code, 403)


class EliminarUsuariosTest(SGUMTestCase):

    def eliminar(self, *usuarios, como=None):
        self.entrar(como or self.admin)
        return self.client.post(self.url('usuarios'), {
            'action': 'delete', 'ids': [u.pk for u in usuarios]})

    def test_elimina_a_quien_no_tiene_historial(self):
        libre = self.crear_usuario('libre')
        self.eliminar(libre)
        self.assertFalse(User.objects.filter(pk=libre.pk).exists())

    def test_no_puede_eliminarse_a_si_mismo(self):
        respuesta = self.eliminar(self.admin)
        self.assertTrue(User.objects.filter(pk=self.admin.pk).exists())
        self.assertIn('su propia cuenta', self.textos(respuesta))

    def test_no_elimina_a_quien_tiene_incidencias(self):
        self.crear_incidencia(self.solicitante)
        respuesta = self.eliminar(self.solicitante)
        self.assertTrue(User.objects.filter(pk=self.solicitante.pk).exists())
        self.assertIn('desactive', self.textos(respuesta))

    def test_no_elimina_a_un_tecnico_con_historial(self):
        self.crear_incidencia(estado='resuelto', tecnico_asignado=self.personal)
        self.eliminar(self.tecnico)
        self.assertTrue(User.objects.filter(pk=self.tecnico.pk).exists())

    def test_un_administrador_comun_no_elimina_superusuarios(self):
        self.eliminar(self.superusuario)
        self.assertTrue(User.objects.filter(pk=self.superusuario.pk).exists())

    def test_ids_invalidos(self):
        self.entrar(self.admin)
        respuesta = self.client.post(self.url('usuarios'), {'action': 'delete', 'ids': ['a', '']})
        self.assertEqual(respuesta.status_code, 302)


class EditarUsuarioTest(SGUMTestCase):

    def editar(self, usuario, como=None, **extra):
        datos = {'username': usuario.username, 'first_name': 'Nombre', 'last_name': 'Apellido',
                 'email': usuario.email, 'rol': 'cliente'}
        datos.update(extra)
        self.entrar(como or self.admin)
        return self.client.post(self.url('editar_usuario', usuario.pk), datos)

    def test_cambia_el_rol_y_crea_personal_para_tecnicos(self):
        libre = self.crear_usuario('libre', 'cliente')
        respuesta = self.editar(libre, rol='tecnico')
        self.assertRedirects(respuesta, self.url('usuarios'), fetch_redirect_response=False)
        self.assertEqual([g.name for g in libre.groups.all()], ['tecnico'])
        self.assertTrue(Personal.objects.filter(trabajador=libre).exists())

    def test_rol_inexistente_en_la_base_no_provoca_error(self):
        Group.objects.filter(name='almacenero').delete()
        libre = self.crear_usuario('libre')
        respuesta = self.editar(libre, rol='almacenero')
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual([g.name for g in libre.groups.all()], ['almacenero'])

    def test_rol_desconocido_se_rechaza(self):
        libre = self.crear_usuario('libre', 'cliente')
        respuesta = self.editar(libre, rol='superheroe')
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('rol', respuesta.context['errores'])

    def test_un_administrador_no_se_quita_su_propio_rol(self):
        respuesta = self.editar(self.admin, rol='cliente')
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('rol', respuesta.context['errores'])
        self.assertTrue(self.admin.groups.filter(name='administrador').exists())

    def test_un_administrador_puede_editar_sus_otros_datos(self):
        respuesta = self.editar(self.admin, rol='administrador', first_name='Otro')
        self.assertEqual(respuesta.status_code, 302)
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.first_name, 'Otro')

    def test_no_se_desactiva_a_si_mismo_pero_si_a_otros(self):
        respuesta = self.editar(self.admin, rol='administrador', is_active='0')
        self.assertIn('is_active', respuesta.context['errores'])
        libre = self.crear_usuario('libre', 'cliente')
        self.editar(libre, is_active='0')
        libre.refresh_from_db()
        self.assertFalse(libre.is_active)

    def test_no_se_quita_el_rol_a_un_tecnico_con_incidencias_abiertas(self):
        self.crear_incidencia(estado='en_proceso', tecnico_asignado=self.personal)
        respuesta = self.editar(self.tecnico, rol='cliente')
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('Reasígnelas', respuesta.context['errores']['rol'])

    def test_usuario_y_correo_duplicados(self):
        respuesta = self.editar(self.solicitante, username=self.solicitante2.username)
        self.assertIn('username', respuesta.context['errores'])
        respuesta = self.editar(self.solicitante, email=self.solicitante2.email)
        self.assertIn('email', respuesta.context['errores'])

    def test_contrasena_nueva_se_valida(self):
        libre = self.crear_usuario('libre', 'cliente')
        respuesta = self.editar(libre, password='123')
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('password', respuesta.context['errores'])
        libre.refresh_from_db()
        self.assertTrue(libre.check_password(CLAVE))
        respuesta = self.editar(libre, password='Otra-Clave-Larga-9')
        self.assertEqual(respuesta.status_code, 302)
        libre.refresh_from_db()
        self.assertTrue(libre.check_password('Otra-Clave-Larga-9'))

    def test_contrasena_vacia_no_cambia_nada_y_el_hash_reenviado_tampoco(self):
        libre = self.crear_usuario('libre', 'cliente')
        antes = libre.password
        self.editar(libre, password='')
        self.editar(libre, password=antes)
        libre.refresh_from_db()
        self.assertEqual(libre.password, antes)

    def test_contexto_incluye_usuario_editado_sin_pisar_al_de_la_sesion(self):
        libre = self.crear_usuario('libre', 'tecnico')
        self.entrar(self.admin)
        contexto = self.client.get(self.url('editar_usuario', libre.pk)).context
        self.assertEqual(contexto['usuario_editado'], libre)
        self.assertEqual(contexto['rol_actual'], 'tecnico')
        self.assertFalse(contexto['es_propio'])

    def test_solo_el_administrador_edita(self):
        for usuario in (self.solicitante, self.tecnico, self.almacenero):
            self.entrar(usuario)
            self.assertEqual(
                self.client.get(self.url('editar_usuario', self.solicitante2.pk)).status_code, 403)


class DesactivarUsuariosTest(SGUMTestCase):
    """Acción POST `cambiar_activo_usuario`: desactivar y reactivar cuentas."""

    def cambiar(self, usuario, valor, como=None, **extra):
        self.entrar(como or self.admin)
        return self.client.post(
            self.url('cambiar_activo_usuario', usuario.pk), {'is_active': valor, **extra})

    def test_desactivar_y_reactivar(self):
        libre = self.crear_usuario('libre', 'cliente')
        respuesta = self.cambiar(libre, '0')
        self.assertEqual(respuesta.status_code, 302)
        libre.refresh_from_db()
        self.assertFalse(libre.is_active)
        self.assertIn('desactivada', self.textos(respuesta))
        self.cambiar(libre, '1')
        libre.refresh_from_db()
        self.assertTrue(libre.is_active)

    def test_conserva_el_historial(self):
        self.crear_incidencia(self.solicitante)
        self.cambiar(self.solicitante, '0')
        self.solicitante.refresh_from_db()
        self.assertFalse(self.solicitante.is_active)
        self.assertEqual(self.solicitante.incidencia_set.count(), 1)

    def test_no_a_si_mismo(self):
        respuesta = self.cambiar(self.admin, '0')
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)
        self.assertEqual(self.mensajes(respuesta)[-1][0], 'danger')
        self.assertIn('propia cuenta', self.textos(respuesta))

    def test_solo_el_administrador(self):
        libre = self.crear_usuario('libre', 'cliente')
        for usuario in (self.solicitante, self.tecnico, self.almacenero):
            respuesta = self.cambiar(libre, '0', como=usuario)
            self.assertEqual(respuesta.status_code, 403)
        libre.refresh_from_db()
        self.assertTrue(libre.is_active)
        self.salir()
        respuesta = self.client.post(self.url('cambiar_activo_usuario', libre.pk), {'is_active': '0'})
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(self.url('login'), respuesta['Location'])

    def test_exige_post(self):
        libre = self.crear_usuario('libre')
        self.entrar(self.admin)
        self.assertEqual(self.client.get(self.url('cambiar_activo_usuario', libre.pk)).status_code, 405)

    def test_no_desactiva_a_un_tecnico_con_incidencias_abiertas(self):
        self.crear_incidencia(estado='en_proceso', tecnico_asignado=self.personal)
        respuesta = self.cambiar(self.tecnico, '0')
        self.tecnico.refresh_from_db()
        self.assertTrue(self.tecnico.is_active)
        self.assertIn('Reasígnelas', self.textos(respuesta))

    def test_un_administrador_comun_no_desactiva_superusuarios(self):
        self.cambiar(self.superusuario, '0')
        self.superusuario.refresh_from_db()
        self.assertTrue(self.superusuario.is_active)
        self.cambiar(self.admin, '0', como=self.superusuario)
        self.admin.refresh_from_db()
        self.assertFalse(self.admin.is_active)

    def test_valor_invalido_y_usuario_inexistente(self):
        libre = self.crear_usuario('libre')
        respuesta = self.cambiar(libre, 'quizas')
        self.assertEqual(self.mensajes(respuesta)[-1][0], 'danger')
        libre.refresh_from_db()
        self.assertTrue(libre.is_active)
        self.entrar(self.admin)
        self.assertEqual(self.client.post(
            self.url('cambiar_activo_usuario', 99999), {'is_active': '0'}).status_code, 404)

    def test_repetir_la_accion_solo_informa(self):
        libre = self.crear_usuario('libre')
        respuesta = self.cambiar(libre, '1')
        self.assertEqual(self.mensajes(respuesta)[-1][0], 'info')

    def test_vuelve_a_la_pagina_de_origen(self):
        libre = self.crear_usuario('libre')
        self.entrar(self.admin)
        respuesta = self.client.post(
            self.url('cambiar_activo_usuario', libre.pk), {'is_active': '0'},
            HTTP_REFERER='http://testserver/usuarios/?rol=cliente&page=2')
        self.assertEqual(respuesta['Location'], 'http://testserver/usuarios/?rol=cliente&page=2')
        respuesta = self.client.post(self.url('cambiar_activo_usuario', libre.pk), {'is_active': '1'})
        self.assertEqual(respuesta['Location'], self.url('usuarios'))

    def test_la_lista_permite_filtrar_por_estado_y_marca_quien_se_puede_cambiar(self):
        libre = self.crear_usuario('libre', 'cliente')
        libre.is_active = False
        libre.save()
        self.entrar(self.admin)
        respuesta = self.client.get(self.url('usuarios'), {'activo': '0'})
        self.assertEqual([u.username for u in respuesta.context['page_obj']], ['libre'])
        self.assertEqual(respuesta.context['activo_filtro'], '0')
        filas = {u.username: u for u in self.client.get(self.url('usuarios')).context['page_obj']}
        self.assertTrue(filas['libre'].puede_cambiar_activo)
        self.assertFalse(filas['t_admin'].puede_cambiar_activo)   # ella misma
        self.assertFalse(filas['t_super'].puede_cambiar_activo)   # superusuario

    def test_editar_con_is_active_aplica_las_mismas_reglas(self):
        self.crear_incidencia(estado='en_proceso', tecnico_asignado=self.personal)
        self.entrar(self.admin)
        respuesta = self.client.post(self.url('editar_usuario', self.tecnico.pk), {
            'username': self.tecnico.username, 'email': self.tecnico.email,
            'rol': 'tecnico', 'is_active': '0'})
        self.assertIn('is_active', respuesta.context['errores'])


class ListaDeUsuariosTest(SGUMTestCase):

    def test_busqueda_con_q(self):
        self.entrar(self.admin)
        respuesta = self.client.get(self.url('usuarios'), {'q': 'solicitante2'})
        self.assertEqual([u.username for u in respuesta.context['page_obj']], ['t_solicitante2'])
        # Buscar algo que no tiene sentido para esos campos ya no rompe ni devuelve todo.
        respuesta = self.client.get(self.url('usuarios'), {'q': 'True'})
        self.assertEqual(list(respuesta.context['page_obj']), [])

    def test_filtro_por_rol_y_rol_visible(self):
        self.entrar(self.admin)
        respuesta = self.client.get(self.url('usuarios'), {'rol': 'cliente'})
        nombres = {u.username for u in respuesta.context['page_obj']}
        self.assertEqual(nombres, {'t_solicitante', 't_solicitante2'})
        fila = list(respuesta.context['page_obj'])[0]
        self.assertEqual(fila.rol_display, 'Solicitante')
        respuesta = self.client.get(self.url('usuarios'), {'rol': 'administrador'})
        self.assertEqual({u.username for u in respuesta.context['page_obj']}, {'t_admin', 't_super'})
