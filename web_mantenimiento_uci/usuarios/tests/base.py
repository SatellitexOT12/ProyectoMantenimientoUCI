"""Utilidades comunes para las pruebas de SGUM-UCI."""
import io
import shutil
import tempfile

from django.contrib.auth.models import Group, User
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from usuarios import servicios
from usuarios.models import Incidencia, Material, Personal, SolicitudSoporte

CLAVE = 'Sgum-Prueba-2025!'

_MEDIA = tempfile.mkdtemp(prefix='sgum-media-')


def imagen_png(nombre='foto.png', lado=8):
    buffer = io.BytesIO()
    Image.new('RGB', (lado, lado), (11, 74, 127)).save(buffer, format='PNG')
    return SimpleUploadedFile(nombre, buffer.getvalue(), content_type='image/png')


@override_settings(
    MEDIA_ROOT=_MEDIA,
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],  # pruebas más rápidas
)
class SGUMTestCase(TestCase):
    """Crea un usuario de cada rol y ofrece ayudas para armar datos."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(_MEDIA, ignore_errors=True)

    @classmethod
    def setUpTestData(cls):
        for nombre in ('administrador', 'tecnico', 'almacenero', 'cliente'):
            Group.objects.get_or_create(name=nombre)
        cls.admin = cls.crear_usuario('t_admin', 'administrador')
        cls.tecnico = cls.crear_usuario('t_tecnico', 'tecnico')
        cls.tecnico2 = cls.crear_usuario('t_tecnico2', 'tecnico')
        cls.almacenero = cls.crear_usuario('t_almacen', 'almacenero')
        cls.solicitante = cls.crear_usuario('t_solicitante', 'cliente')
        cls.solicitante2 = cls.crear_usuario('t_solicitante2', 'cliente')
        cls.superusuario = User.objects.create_superuser(
            't_super', 't_super@uci.cu', CLAVE)
        cls.personal = Personal.objects.get(trabajador=cls.tecnico)
        cls.personal2 = Personal.objects.get(trabajador=cls.tecnico2)

    @classmethod
    def crear_usuario(cls, username, rol=None):
        usuario = User.objects.create_user(
            username, f'{username}@uci.cu', CLAVE,
            first_name=username.title(), last_name='Prueba')
        if rol:
            usuario.groups.add(Group.objects.get(name=rol))
        if rol == 'tecnico':
            Personal.objects.create(trabajador=usuario)
        return usuario

    # ---------------------------------------------------------- datos

    def crear_incidencia(self, solicitante=None, **extra):
        datos = dict(
            tipo='plomeria', prioridad='2', ubicacion='Edificio 3, apto 204',
            descripcion='Salidero en el baño', fecha=timezone.now(),
            usuario_reporte=solicitante or self.solicitante,
        )
        datos.update(extra)
        incidencia = Incidencia.objects.create(**datos)
        servicios.sincronizar_reporte(incidencia)
        return incidencia

    def crear_material(self, nombre='Llave de agua', tipo='plomeria', cantidad=10):
        return Material.objects.create(nombre=nombre, tipo=tipo, cantidad=cantidad)

    def crear_solicitud(self, usuario=None, **extra):
        datos = dict(usuario=usuario or self.solicitante, tipo='software',
                     descripcion='No abre el sistema')
        datos.update(extra)
        return SolicitudSoporte.objects.create(**datos)

    # -------------------------------------------------------- sesiones

    def entrar(self, usuario):
        self.client.force_login(usuario)
        return self.client

    def salir(self):
        self.client.logout()

    def mensajes(self, respuesta):
        return [(m.level_tag, str(m)) for m in get_messages(respuesta.wsgi_request)]

    def textos(self, respuesta):
        return ' | '.join(texto for _, texto in self.mensajes(respuesta))

    # ----------------------------------------------------------- URLs

    def url(self, nombre, *args):
        return reverse(nombre, args=args)

    def login_url(self, destino):
        return f"{reverse('login')}?next={destino}"
