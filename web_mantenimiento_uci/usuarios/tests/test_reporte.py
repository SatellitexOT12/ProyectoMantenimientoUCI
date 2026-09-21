"""Reporte de incidencias: el modelo es la fuente única y todo se valida."""
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile

from usuarios.models import Incidencia, Reporte

from .base import SGUMTestCase, imagen_png


class ReportarIncidenciaTest(SGUMTestCase):

    def datos(self, **extra):
        base = {'tipo_incidencia': 'plomeria', 'prioridad': '2',
                'ubicacion': 'Edificio 3, apto 204', 'descripcion': 'Salidero en el baño'}
        base.update(extra)
        return base

    def publicar(self, **extra):
        self.entrar(self.solicitante)
        return self.client.post(self.url('reportar_incidencia'), self.datos(**extra))

    def test_formulario_ofrece_los_diez_tipos_del_modelo(self):
        self.entrar(self.solicitante)
        contexto = self.client.get(self.url('reportar_incidencia')).context
        self.assertEqual(list(contexto['tipos']), list(Incidencia.TIPO_CHOICES))
        self.assertEqual(len(contexto['tipos']), 10)
        self.assertEqual(list(contexto['prioridades']), list(Incidencia.PRIORIDAD_CHOICES))
        self.assertEqual(contexto['ubicacion_max'], 50)
        self.assertEqual(contexto['descripcion_max'], 1000)
        self.assertNotIn('limpieza', dict(contexto['tipos']))

    def test_cada_tipo_del_modelo_se_acepta(self):
        for codigo, _ in Incidencia.TIPO_CHOICES:
            with self.subTest(tipo=codigo):
                respuesta = self.publicar(tipo_incidencia=codigo)
                self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(Incidencia.objects.count(), 10)

    def test_tipo_invalido_limpieza(self):
        respuesta = self.publicar(tipo_incidencia='limpieza')
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('tipo_incidencia', respuesta.context['errores'])
        self.assertEqual(Incidencia.objects.count(), 0)
        # Conserva lo escrito para no obligar a repetirlo.
        self.assertEqual(respuesta.context['valores']['descripcion'], 'Salidero en el baño')

    def test_prioridad_invalida(self):
        for valor in ('media', '4', '0', 'alta'):
            with self.subTest(prioridad=valor):
                respuesta = self.publicar(prioridad=valor)
                self.assertIn('prioridad', respuesta.context['errores'])
        self.assertEqual(Incidencia.objects.count(), 0)

    def test_longitud_de_la_ubicacion(self):
        self.assertEqual(self.publicar(ubicacion='u' * 50).status_code, 302)
        respuesta = self.publicar(ubicacion='u' * 51)
        self.assertIn('ubicacion', respuesta.context['errores'])
        self.assertIn('51', respuesta.context['errores']['ubicacion'])
        self.assertEqual(Incidencia.objects.count(), 1)

    def test_longitud_de_la_descripcion(self):
        self.assertEqual(self.publicar(descripcion='d' * 1000).status_code, 302)
        respuesta = self.publicar(descripcion='d' * 1001)
        self.assertIn('descripcion', respuesta.context['errores'])
        self.assertEqual(Incidencia.objects.count(), 1)

    def test_campos_vacios_o_solo_espacios(self):
        respuesta = self.publicar(ubicacion='   ', descripcion='\n\t ')
        self.assertEqual(set(respuesta.context['errores']), {'ubicacion', 'descripcion'})

    def test_los_errores_dicen_como_corregir(self):
        respuesta = self.publicar(ubicacion='u' * 60)
        self.assertIn('Abrevie', respuesta.context['errores']['ubicacion'])

    def test_el_reporte_lleva_la_descripcion_real(self):
        self.publicar(descripcion='  Tubería rota en el pasillo  ')
        incidencia = Incidencia.objects.get()
        reporte = Reporte.objects.get(reporte_incidencia=incidencia)
        self.assertEqual(reporte.descripcion, 'Tubería rota en el pasillo')
        self.assertNotIn('Servidor', reporte.descripcion)
        self.assertEqual(reporte.estado, 'pendiente')

    def test_caracteres_nul_se_eliminan(self):
        self.publicar(descripcion='hola\x00mundo')
        self.assertEqual(Incidencia.objects.get().descripcion, 'holamundo')

    def test_imagen_valida_se_guarda(self):
        self.entrar(self.solicitante)
        respuesta = self.client.post(
            self.url('reportar_incidencia'), {**self.datos(), 'imagen': imagen_png()})
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(Incidencia.objects.get().imagen.name.startswith('incidencias/'))

    def test_archivo_que_no_es_imagen_se_rechaza(self):
        falso = SimpleUploadedFile('foto.png', b'esto no es una imagen', content_type='image/png')
        self.entrar(self.solicitante)
        respuesta = self.client.post(
            self.url('reportar_incidencia'), {**self.datos(), 'imagen': falso})
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('no es una imagen válida', respuesta.context['errores']['imagen'])
        self.assertEqual(Incidencia.objects.count(), 0)

    def test_imagen_demasiado_grande(self):
        self.entrar(self.solicitante)
        with mock.patch.object(Incidencia, 'IMAGEN_MAX_BYTES', 50):
            respuesta = self.client.post(
                self.url('reportar_incidencia'), {**self.datos(), 'imagen': imagen_png(lado=64)})
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('imagen', respuesta.context['errores'])
        self.assertEqual(Incidencia.objects.count(), 0)

    def test_el_modelo_ya_no_tiene_prioridad_invalida_por_defecto(self):
        defecto = Incidencia._meta.get_field('prioridad').get_default()
        self.assertIn(defecto, dict(Incidencia.PRIORIDAD_CHOICES))
        self.assertFalse(Incidencia._meta.get_field('prioridad_confirmada').get_default())
