"""Matriz de permisos por rol para las vistas sensibles."""
from django.contrib.auth.models import Group, User

from usuarios import permisos
from usuarios.models import Incidencia, Material, MaterialIncidencia

from .base import SGUMTestCase


class MatrizDePaginasTest(SGUMTestCase):
    """GET de cada página: anónimo, solicitante, técnico, almacenero, administrador."""

    ROLES = ('anonimo', 'solicitante', 'tecnico', 'almacenero', 'admin')

    # nombre de URL -> roles con acceso (200)
    PAGINAS = {
        'main': {'solicitante', 'tecnico', 'almacenero', 'admin'},
        'incidencias': {'solicitante', 'tecnico', 'almacenero', 'admin'},
        'reportar_incidencia': {'solicitante', 'tecnico', 'almacenero', 'admin'},
        'solicitar_soporte': {'solicitante', 'tecnico', 'almacenero', 'admin'},
        'usuarios': {'admin'},
        'personal': {'admin'},
        'materiales': {'almacenero', 'admin'},
        'reportes': {'almacenero', 'admin'},
        'exportar_dashboard': {'almacenero', 'admin'},
        'bandeja_entrada_soporte': {'tecnico', 'admin'},
    }

    def sesion(self, rol):
        self.salir()
        if rol != 'anonimo':
            self.entrar({
                'solicitante': self.solicitante, 'tecnico': self.tecnico,
                'almacenero': self.almacenero, 'admin': self.admin,
            }[rol])

    def test_paginas_por_rol(self):
        for nombre, permitidos in self.PAGINAS.items():
            url = self.url(nombre)
            for rol in self.ROLES:
                with self.subTest(pagina=nombre, rol=rol):
                    self.sesion(rol)
                    respuesta = self.client.get(url)
                    if rol == 'anonimo':
                        self.assertEqual(respuesta.status_code, 302)
                        self.assertIn(self.url('login'), respuesta['Location'])
                        self.assertIn('next=', respuesta['Location'])
                    elif rol in permitidos:
                        self.assertEqual(respuesta.status_code, 200)
                    else:
                        self.assertEqual(respuesta.status_code, 403)
                        self.assertIn('permiso', respuesta.content.decode())

    def test_superusuario_cuenta_como_administrador(self):
        self.entrar(self.superusuario)
        for nombre in ('usuarios', 'personal', 'materiales', 'reportes', 'bandeja_entrada_soporte'):
            with self.subTest(pagina=nombre):
                self.assertEqual(self.client.get(self.url(nombre)).status_code, 200)

    def test_usuario_sin_grupo_actua_como_solicitante(self):
        sin_grupo = User.objects.create_user('sin_grupo', 'sg@uci.cu', 'Sgum-Prueba-2025!')
        self.entrar(sin_grupo)
        self.assertEqual(self.client.get(self.url('incidencias')).status_code, 200)
        self.assertEqual(self.client.get(self.url('usuarios')).status_code, 403)
        self.assertEqual(permisos.roles_de(sin_grupo), frozenset({'cliente'}))

    def test_rol_cliente_se_muestra_como_solicitante(self):
        self.assertEqual(permisos.roles_texto(self.solicitante), 'Solicitante')
        self.assertEqual(permisos.nombre_rol('cliente'), 'Solicitante')


class AccionesSoloPostTest(SGUMTestCase):
    """Los cambios de estado exigen POST y respetan el rol."""

    def test_get_no_cambia_nada_y_da_405(self):
        incidencia = self.crear_incidencia(tecnico_asignado=self.personal, estado='en_proceso')
        material = self.crear_material()
        registro = MaterialIncidencia.objects.create(
            incidencia=incidencia, material=material, cantidad_usada=2)
        self.entrar(self.admin)
        peticiones = [
            self.url('quitar_tecnico', incidencia.pk),
            self.url('asignar_tecnico'),
            self.url('confirmar_prioridad'),
            self.url('asignar_material'),
            self.url('quitar_material'),
            self.url('completar_solicitud', self.crear_solicitud().pk),
        ]
        for url in peticiones:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 405)
        incidencia.refresh_from_db()
        self.assertEqual(incidencia.tecnico_asignado, self.personal)
        self.assertTrue(MaterialIncidencia.objects.filter(pk=registro.pk).exists())

    def test_acciones_de_gestion_por_rol(self):
        incidencia = self.crear_incidencia()
        material = self.crear_material()
        acciones = [
            ('asignar_tecnico', (), {'incidencia_id': incidencia.pk, 'tecnico_id': self.personal.pk},
             {'admin'}),
            ('confirmar_prioridad', (), {'incidencia_id': incidencia.pk}, {'admin'}),
            ('asignar_material', (), {'incidencia_id': incidencia.pk, 'material': material.pk,
                                       'cantidad': 1}, {'admin', 'almacenero'}),
        ]
        usuarios = {'solicitante': self.solicitante, 'tecnico': self.tecnico,
                    'almacenero': self.almacenero, 'admin': self.admin}
        for nombre, args, datos, permitidos in acciones:
            for rol, usuario in usuarios.items():
                with self.subTest(accion=nombre, rol=rol):
                    self.entrar(usuario)
                    respuesta = self.client.post(self.url(nombre, *args), datos)
                    if rol in permitidos:
                        self.assertEqual(respuesta.status_code, 302)
                    else:
                        self.assertEqual(respuesta.status_code, 403)
            # anónimo: a iniciar sesión
            self.salir()
            respuesta = self.client.post(self.url(nombre, *args), datos)
            self.assertEqual(respuesta.status_code, 302)
            self.assertIn(self.url('login'), respuesta['Location'])

    def test_anonimo_no_puede_quitar_material_ni_tecnico(self):
        incidencia = self.crear_incidencia(tecnico_asignado=self.personal, estado='en_proceso')
        material = self.crear_material()
        registro = MaterialIncidencia.objects.create(
            incidencia=incidencia, material=material, cantidad_usada=2)
        for url, datos in (
            (self.url('quitar_material'), {'material_incidencia_id': registro.pk}),
            (self.url('quitar_tecnico', incidencia.pk), {}),
        ):
            respuesta = self.client.post(url, datos)
            self.assertEqual(respuesta.status_code, 302)
            self.assertIn(self.url('login'), respuesta['Location'])
        incidencia.refresh_from_db()
        self.assertEqual(incidencia.tecnico_asignado, self.personal)
        self.assertTrue(MaterialIncidencia.objects.filter(pk=registro.pk).exists())

    def test_solicitante_y_tecnico_no_quitan_materiales(self):
        incidencia = self.crear_incidencia(tecnico_asignado=self.personal, estado='en_proceso')
        registro = MaterialIncidencia.objects.create(
            incidencia=incidencia, material=self.crear_material(), cantidad_usada=2)
        for usuario in (self.solicitante, self.tecnico):
            self.entrar(usuario)
            respuesta = self.client.post(
                self.url('quitar_material'), {'material_incidencia_id': registro.pk})
            self.assertEqual(respuesta.status_code, 403)
        self.assertTrue(MaterialIncidencia.objects.filter(pk=registro.pk).exists())


class EditarIncidenciaPermisosTest(SGUMTestCase):

    def test_matriz_de_edicion(self):
        propia_pendiente = self.crear_incidencia(self.solicitante)
        propia_en_proceso = self.crear_incidencia(
            self.solicitante, estado='en_proceso', tecnico_asignado=self.personal)
        propia_resuelta = self.crear_incidencia(
            self.solicitante, estado='resuelto', tecnico_asignado=self.personal)
        ajena = self.crear_incidencia(self.solicitante2)
        casos = [
            # (usuario, incidencia, ¿puede abrir la edición?)
            (self.solicitante, propia_pendiente, True),
            (self.solicitante, propia_en_proceso, False),
            (self.solicitante, propia_resuelta, False),
            (self.solicitante, ajena, False),
            (self.tecnico, propia_en_proceso, True),   # técnico asignado
            (self.tecnico, propia_resuelta, True),     # puede reabrir
            (self.tecnico, ajena, False),
            (self.tecnico2, propia_en_proceso, False),  # otro técnico
            (self.almacenero, ajena, False),
            (self.admin, ajena, True),
            (self.admin, propia_resuelta, True),
            (self.superusuario, propia_resuelta, True),
        ]
        for usuario, incidencia, esperado in casos:
            with self.subTest(usuario=usuario.username, incidencia=incidencia.pk,
                              estado=incidencia.estado):
                self.entrar(usuario)
                respuesta = self.client.get(self.url('editar_incidencia', incidencia.pk))
                self.assertEqual(respuesta.status_code, 200 if esperado else 403)

    def test_solicitante_no_edita_ajena_por_post(self):
        ajena = self.crear_incidencia(self.solicitante2, descripcion='Original')
        self.entrar(self.solicitante)
        respuesta = self.client.post(
            self.url('editar_incidencia', ajena.pk), {'descripcion': 'Manipulada'})
        self.assertEqual(respuesta.status_code, 403)
        ajena.refresh_from_db()
        self.assertEqual(ajena.descripcion, 'Original')

    def test_anonimo_redirige_a_login(self):
        incidencia = self.crear_incidencia()
        respuesta = self.client.get(self.url('editar_incidencia', incidencia.pk))
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(self.url('login'), respuesta['Location'])

    def test_mensaje_de_rechazo_explica_el_motivo(self):
        en_proceso = self.crear_incidencia(estado='en_proceso', tecnico_asignado=self.personal)
        self.entrar(self.solicitante)
        respuesta = self.client.get(self.url('editar_incidencia', en_proceso.pk))
        self.assertContains(respuesta, 'Pendientes', status_code=403)


class EliminarIncidenciasTest(SGUMTestCase):

    def eliminar(self, usuario, *incidencias):
        self.entrar(usuario)
        return self.client.post(self.url('incidencias'), {
            'action': 'eliminar', 'ids': [i.pk for i in incidencias]})

    def test_solicitante_solo_elimina_las_suyas_pendientes(self):
        propia = self.crear_incidencia(self.solicitante)
        en_proceso = self.crear_incidencia(
            self.solicitante, estado='en_proceso', tecnico_asignado=self.personal)
        ajena = self.crear_incidencia(self.solicitante2)
        respuesta = self.eliminar(self.solicitante, propia, en_proceso, ajena)
        self.assertEqual(respuesta.status_code, 302)
        self.assertFalse(Incidencia.objects.filter(pk=propia.pk).exists())
        self.assertTrue(Incidencia.objects.filter(pk=en_proceso.pk).exists())
        self.assertTrue(Incidencia.objects.filter(pk=ajena.pk).exists())
        self.assertIn('no se eliminaron', self.textos(respuesta))

    def test_tecnico_y_almacenero_no_eliminan_ajenas(self):
        asignada = self.crear_incidencia(tecnico_asignado=self.personal, estado='en_proceso')
        pendiente = self.crear_incidencia(self.solicitante2)
        self.eliminar(self.tecnico, asignada, pendiente)
        self.eliminar(self.almacenero, asignada, pendiente)
        self.assertEqual(Incidencia.objects.filter(pk__in=[asignada.pk, pendiente.pk]).count(), 2)

    def test_administrador_elimina_cualquiera(self):
        una = self.crear_incidencia(estado='en_proceso', tecnico_asignado=self.personal)
        otra = self.crear_incidencia(self.solicitante2)
        self.eliminar(self.admin, una, otra)
        self.assertEqual(Incidencia.objects.count(), 0)

    def test_eliminar_incidencia_no_borra_al_tecnico(self):
        una = self.crear_incidencia(estado='en_proceso', tecnico_asignado=self.personal)
        self.personal.incidencia = una
        self.personal.save()
        self.eliminar(self.admin, una)
        self.personal.refresh_from_db()
        self.assertIsNone(self.personal.incidencia)

    def test_no_elimina_incidencia_con_materiales(self):
        incidencia = self.crear_incidencia()
        MaterialIncidencia.objects.create(
            incidencia=incidencia, material=self.crear_material(), cantidad_usada=1)
        respuesta = self.eliminar(self.admin, incidencia)
        self.assertTrue(Incidencia.objects.filter(pk=incidencia.pk).exists())
        self.assertIn('materiales asignados', self.textos(respuesta))

    def test_ids_invalidos_no_rompen(self):
        self.entrar(self.admin)
        respuesta = self.client.post(
            self.url('incidencias'), {'action': 'eliminar', 'ids': ['abc', '', '-3']})
        self.assertEqual(respuesta.status_code, 302)
        respuesta = self.client.post(self.url('incidencias'), {'action': 'eliminar'})
        self.assertEqual(respuesta.status_code, 302)


class AlcanceDeLaListaTest(SGUMTestCase):

    def ids(self, usuario, **params):
        self.entrar(usuario)
        respuesta = self.client.get(self.url('incidencias'), params)
        self.assertEqual(respuesta.status_code, 200)
        return {i.pk for i in respuesta.context['page_obj']}

    def test_lista_segun_rol(self):
        de_uno = self.crear_incidencia(self.solicitante)
        de_dos = self.crear_incidencia(self.solicitante2)
        asignada = self.crear_incidencia(
            self.solicitante2, estado='en_proceso', tecnico_asignado=self.personal)
        reportada_por_tecnico = self.crear_incidencia(self.tecnico)
        todas = {de_uno.pk, de_dos.pk, asignada.pk, reportada_por_tecnico.pk}
        self.assertEqual(self.ids(self.solicitante), {de_uno.pk})
        self.assertEqual(self.ids(self.tecnico), {asignada.pk, reportada_por_tecnico.pk})
        self.assertEqual(self.ids(self.tecnico2), set())
        self.assertEqual(self.ids(self.almacenero), todas)
        self.assertEqual(self.ids(self.admin), todas)  # sin ser superusuario
        self.assertEqual(self.ids(self.superusuario), todas)

    def test_tecnico_sin_fila_de_personal_no_rompe(self):
        huerfano = User.objects.create_user('sin_personal', 'sp@uci.cu', 'Sgum-Prueba-2025!')
        huerfano.groups.add(Group.objects.get(name='tecnico'))
        self.entrar(huerfano)
        self.assertEqual(self.client.get(self.url('incidencias')).status_code, 200)

    def test_busqueda_por_etiqueta_sin_acentos_y_por_estado(self):
        plomeria = self.crear_incidencia(tipo='plomeria', ubicacion='Edificio 1')
        equipos = self.crear_incidencia(tipo='mantenimiento_equipos', ubicacion='Edificio 2',
                                        estado='resuelto')
        self.assertEqual(self.ids(self.admin, q='plomería'), {plomeria.pk})
        self.assertEqual(self.ids(self.admin, q='Mantenimiento de equipos'), {equipos.pk})
        self.assertEqual(self.ids(self.admin, q='resuelto'), {equipos.pk})
        self.assertIn(plomeria.pk, self.ids(self.admin, q=str(plomeria.pk)))

    def test_filtros_exactos(self):
        libre = self.crear_incidencia(prioridad='3')
        asignada = self.crear_incidencia(prioridad='1', estado='en_proceso',
                                         tecnico_asignado=self.personal)
        self.assertEqual(self.ids(self.admin, tecnico='sin'), {libre.pk})
        self.assertEqual(self.ids(self.admin, tecnico=str(self.personal.pk)), {asignada.pk})
        self.assertEqual(self.ids(self.admin, prioridad='3'), {libre.pk})
        self.assertEqual(self.ids(self.admin, estado='abiertas'), {libre.pk, asignada.pk})
        self.assertEqual(self.ids(self.admin, confirmada='0'), {libre.pk, asignada.pk})

    def test_qs_conserva_los_filtros_sin_la_pagina(self):
        self.entrar(self.admin)
        contexto = self.client.get(
            self.url('incidencias'), {'estado': 'abiertas', 'page': '1', 'q': 'x y'}).context
        self.assertEqual(sorted(contexto['qs'].split('&')), ['estado=abiertas', 'q=x+y'])

    def test_banderas_por_fila(self):
        propia = self.crear_incidencia(self.solicitante)
        en_proceso = self.crear_incidencia(
            self.solicitante, estado='en_proceso', tecnico_asignado=self.personal)
        self.entrar(self.solicitante)
        filas = {i.pk: i for i in self.client.get(self.url('incidencias')).context['page_obj']}
        self.assertTrue(filas[propia.pk].puede_editar)
        self.assertTrue(filas[propia.pk].puede_eliminar)
        self.assertFalse(filas[en_proceso.pk].puede_editar)
        self.assertFalse(filas[en_proceso.pk].puede_eliminar)
        self.assertFalse(filas[propia.pk].puede_asignar_tecnico)


class DesactivarYCuentasTest(SGUMTestCase):

    def test_usuario_inactivo_no_entra(self):
        self.solicitante.is_active = False
        self.solicitante.save()
        respuesta = self.client.post(
            self.url('login'), {'username': self.solicitante.username, 'password': 'Sgum-Prueba-2025!'})
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('error', respuesta.context)

    def test_filtro_has_groups_usa_roles_efectivos(self):
        from usuarios.templatetags.auth_extras import has_groups
        self.assertTrue(has_groups(self.superusuario, 'administrador'))
        self.assertTrue(has_groups(self.solicitante, 'cliente'))
        self.assertFalse(has_groups(self.solicitante, 'administrador,tecnico'))
        self.assertTrue(has_groups(self.almacenero, 'almacenero,administrador'))
