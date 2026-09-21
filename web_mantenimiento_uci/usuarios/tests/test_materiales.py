"""Inventario y asignación de materiales."""
from usuarios.models import Incidencia, Material, MaterialIncidencia

from .base import SGUMTestCase


class AsignarMaterialTest(SGUMTestCase):

    def setUp(self):
        self.incidencia = self.crear_incidencia(estado='en_proceso', tecnico_asignado=self.personal)
        self.material = self.crear_material(cantidad=5)
        self.entrar(self.almacenero)

    def asignar(self, **datos):
        base = {'incidencia_id': self.incidencia.pk, 'material': self.material.pk, 'cantidad': '2'}
        base.update(datos)
        return self.client.post(self.url('asignar_material'), base)

    def test_descuenta_el_stock(self):
        respuesta = self.asignar(cantidad='3')
        self.assertRedirects(respuesta, self.url('incidencias'), fetch_redirect_response=False)
        self.material.refresh_from_db()
        self.assertEqual(self.material.cantidad, 2)
        self.assertEqual(self.mensajes(respuesta)[0][0], 'success')

    def test_no_permite_pasar_del_stock(self):
        respuesta = self.asignar(cantidad='6')
        self.material.refresh_from_db()
        self.assertEqual(self.material.cantidad, 5)
        self.assertFalse(MaterialIncidencia.objects.exists())
        self.assertIn('quedan 5', self.textos(respuesta))

    def test_dos_peticiones_seguidas_no_dejan_stock_negativo(self):
        self.asignar(cantidad='3')
        self.asignar(cantidad='3')
        self.material.refresh_from_db()
        self.assertEqual(self.material.cantidad, 2)
        self.assertEqual(MaterialIncidencia.objects.count(), 1)

    def test_cantidades_invalidas(self):
        for valor in ('', 'abc', '-1', '0', '1.5', '1e3', ' ', '99999999'):
            with self.subTest(cantidad=valor):
                respuesta = self.asignar(cantidad=valor)
                self.assertEqual(respuesta.status_code, 302)
                self.assertEqual(self.mensajes(respuesta)[0][0], 'danger')
        self.material.refresh_from_db()
        self.assertEqual(self.material.cantidad, 5)
        self.assertFalse(MaterialIncidencia.objects.exists())

    def test_incidencia_o_material_inexistentes(self):
        for datos in ({'incidencia_id': '9999'}, {'material': '9999'},
                      {'incidencia_id': 'x'}, {'material': ''}):
            with self.subTest(datos=datos):
                respuesta = self.asignar(**datos)
                self.assertEqual(respuesta.status_code, 302)
                self.assertEqual(self.mensajes(respuesta)[0][0], 'danger')
        self.material.refresh_from_db()
        self.assertEqual(self.material.cantidad, 5)

    def test_redirige_a_la_lista_y_nunca_a_una_url_inexistente(self):
        respuesta = self.asignar(cantidad='999')
        self.assertEqual(respuesta['Location'], self.url('incidencias'))


class QuitarMaterialTest(SGUMTestCase):

    def setUp(self):
        self.incidencia = self.crear_incidencia()
        self.material = self.crear_material(cantidad=10)
        self.entrar(self.almacenero)
        self.client.post(self.url('asignar_material'), {
            'incidencia_id': self.incidencia.pk, 'material': self.material.pk, 'cantidad': '4'})
        self.registro = MaterialIncidencia.objects.get()

    def test_devuelve_la_cantidad_al_inventario(self):
        respuesta = self.client.post(
            self.url('quitar_material'), {'material_incidencia_id': self.registro.pk},
            HTTP_REFERER='http://testserver/incidencias/?page=3')
        self.assertRedirects(respuesta, 'http://testserver/incidencias/?page=3', fetch_redirect_response=False)
        self.material.refresh_from_db()
        self.assertEqual(self.material.cantidad, 10)
        self.assertFalse(MaterialIncidencia.objects.exists())

    def test_sin_referer_no_da_error(self):
        respuesta = self.client.post(
            self.url('quitar_material'), {'material_incidencia_id': self.registro.pk})
        self.assertEqual(respuesta['Location'], self.url('incidencias'))

    def test_quitar_dos_veces_no_devuelve_de_mas(self):
        for _ in range(2):
            self.client.post(self.url('quitar_material'),
                             {'material_incidencia_id': self.registro.pk})
        self.material.refresh_from_db()
        self.assertEqual(self.material.cantidad, 10)

    def test_id_invalido(self):
        respuesta = self.client.post(self.url('quitar_material'), {'material_incidencia_id': 'x'})
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(self.mensajes(respuesta)[-1][0], 'danger')
        self.material.refresh_from_db()
        self.assertEqual(self.material.cantidad, 6)


class InventarioTest(SGUMTestCase):

    def registrar(self, **extra):
        datos = {'username': 'Cable', 'tipo_material': 'electricidad', 'cantidad': '8'}
        datos.update(extra)
        self.entrar(self.almacenero)
        return self.client.post(self.url('materiales'), datos)

    def test_registrar(self):
        respuesta = self.registrar()
        self.assertRedirects(respuesta, self.url('materiales'), fetch_redirect_response=False)
        material = Material.objects.get()
        self.assertEqual((material.nombre, material.tipo, material.cantidad),
                         ('Cable', 'electricidad', 8))

    def test_acepta_los_nombres_de_campo_nuevos(self):
        self.entrar(self.almacenero)
        respuesta = self.client.post(self.url('materiales'), {
            'nombre': 'Interruptor', 'tipo': 'electricidad', 'cantidad': '3'})
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(Material.objects.get().nombre, 'Interruptor')

    def test_registro_invalido_no_crea_y_conserva_lo_escrito(self):
        for extra in ({'cantidad': '-5'}, {'cantidad': 'abc'}, {'cantidad': ''},
                      {'cantidad': '1.5'}, {'username': '  '},
                      {'tipo_material': 'limpieza'}, {'tipo_material': ''},
                      {'username': 'n' * 101}):
            with self.subTest(extra=extra):
                respuesta = self.registrar(**extra)
                self.assertEqual(respuesta.status_code, 200)
                self.assertTrue(respuesta.context['errores'])
                self.assertTrue(respuesta.context['abrir_registro'])
        self.assertEqual(Material.objects.count(), 0)

    def test_cantidad_cero_es_valida(self):
        self.registrar(cantidad='0')
        self.assertEqual(Material.objects.get().cantidad, 0)

    def test_editar_con_los_campos_de_la_plantilla_actual(self):
        material = self.crear_material()
        self.entrar(self.almacenero)
        respuesta = self.client.post(self.url('editar_material', material.pk), {
            'nombre': 'Llave nueva', 'tipo': 'plomeria', 'cantidad': '12'})
        self.assertRedirects(respuesta, self.url('materiales'), fetch_redirect_response=False)
        material.refresh_from_db()
        self.assertEqual((material.nombre, material.cantidad), ('Llave nueva', 12))

    def test_editar_invalido(self):
        material = self.crear_material(cantidad=7)
        self.entrar(self.almacenero)
        for datos in ({'nombre': '', 'tipo': 'plomeria', 'cantidad': '1'},
                      {'nombre': 'x', 'tipo': 'plomeria', 'cantidad': '-1'},
                      {'nombre': 'x', 'tipo': 'plomeria', 'cantidad': 'mucho'},
                      {'nombre': 'x', 'tipo': 'inventado', 'cantidad': '1'}):
            with self.subTest(datos=datos):
                respuesta = self.client.post(self.url('editar_material', material.pk), datos)
                self.assertEqual(respuesta.status_code, 200)
                self.assertTrue(respuesta.context['errores'])
        material.refresh_from_db()
        self.assertEqual(material.cantidad, 7)

    def test_conserva_un_tipo_antiguo_al_editar(self):
        material = self.crear_material(tipo='Construccion', cantidad=3)
        self.entrar(self.almacenero)
        respuesta = self.client.post(self.url('editar_material', material.pk), {
            'nombre': material.nombre, 'tipo': 'Construccion', 'cantidad': '4'})
        self.assertEqual(respuesta.status_code, 302)

    def test_editar_material_exige_sesion_y_rol(self):
        material = self.crear_material()
        self.salir()
        respuesta = self.client.get(self.url('editar_material', material.pk))
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(self.url('login'), respuesta['Location'])
        self.entrar(self.solicitante)
        self.assertEqual(self.client.get(self.url('editar_material', material.pk)).status_code, 403)
        self.assertEqual(
            self.client.post(self.url('editar_material', material.pk),
                             {'nombre': 'x', 'tipo': 'plomeria', 'cantidad': '1'}).status_code, 403)

    def test_busqueda_sin_duplicar_filtros(self):
        self.crear_material('Cable', 'electricidad', 5)
        self.crear_material('Llave', 'plomeria', 5)
        self.entrar(self.almacenero)
        respuesta = self.client.get(self.url('materiales'), {'q': 'plomería'})
        self.assertEqual([m.nombre for m in respuesta.context['page_obj']], ['Llave'])
        respuesta = self.client.get(self.url('materiales'), {'q': 'cab'})
        self.assertEqual([m.nombre for m in respuesta.context['page_obj']], ['Cable'])

    def test_no_se_elimina_material_con_asignaciones(self):
        usado, libre = self.crear_material('Usado'), self.crear_material('Libre')
        MaterialIncidencia.objects.create(
            incidencia=self.crear_incidencia(), material=usado, cantidad_usada=1)
        self.entrar(self.almacenero)
        respuesta = self.client.post(self.url('materiales'), {
            'action': 'delete', 'ids': [usado.pk, libre.pk]})
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(Material.objects.filter(pk=usado.pk).exists())
        self.assertFalse(Material.objects.filter(pk=libre.pk).exists())
        self.assertIn('Usado', self.textos(respuesta))
        self.assertTrue(Incidencia.objects.exists())
