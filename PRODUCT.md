# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Proyecto existente: Django 4.2 con plantillas renderizadas en servidor (app `usuarios`), Bootstrap 5 vía `django-bootstrap-v5`, JavaScript sin framework, jQuery, Chart.js para el dashboard y Font Awesome / Bootstrap Icons para íconos. Base de datos PostgreSQL en `settings.py` (el repo incluye además un `db.sqlite3` con datos de prueba). Hoy todas las librerías de interfaz (Bootstrap, jQuery, Chart.js, íconos) se cargan desde CDNs de internet.

Base CSS: **Bootstrap 5 local + capa de diseño propia** (decidido). Bootstrap, jQuery y Chart.js se sirven desde `static/vendor/` (sin CDN) y se conservan para modales, dropdowns y toasts; encima va una hoja de estilos propia de SGUM-UCI. Los íconos son SVG propios, sin Font Awesome ni Bootstrap Icons. Ningún recurso de interfaz puede depender de internet (ver Capacidades y restricciones).

## Users

**Usuario que más define el diseño: el administrador / despachador de la Dirección de Mantenimiento (o Servicios Generales) de la UCI.** Trabaja en una PC de escritorio durante toda la jornada: recibe las solicitudes, las prioriza, asigna técnicos y materiales y consulta el estado general. Si su pantalla no le permite escanear, filtrar y decidir rápido, el sistema no cumple su función.

Otros roles (grupos de Django: `administrador`, `tecnico`, `almacenero`, `cliente`):

- **Solicitantes**: residentes (estudiantes en las residencias) y trabajadores de la universidad. Reportan problemas y siguen su estado, sobre todo desde el móvil, a veces con una foto tomada en el momento. En la interfaz este rol se muestra siempre como "Solicitante"; el grupo de Django sigue llamándose `cliente`, y los manuales antiguos aún dicen "cliente".
- **Técnicos**: reciben las incidencias asignadas, las atienden en el lugar y las cierran, desde el móvil y con conexión irregular.
- **Almacenero**: controla el inventario y asigna materiales a las incidencias, desde una PC en el almacén.

## Product Purpose

SGUM-UCI centraliza en un solo sistema el ciclo completo del mantenimiento de la Universidad de las Ciencias Informáticas (La Habana, Cuba): reporte, asignación, atención, consumo de materiales y estadística. Reemplaza el registro en libros, papel o planillas y el aviso por llamada o en persona al despacho.

Se considera exitoso cuando:

1. Ninguna solicitud se pierde: todo lo reportado queda registrado con estado e historial.
2. Baja el tiempo de respuesta, desde el reporte hasta la asignación de un técnico y desde ahí hasta la resolución.
3. Los materiales están controlados: se sabe qué hay en almacén y qué se gastó en cada trabajo.
4. La dirección cuenta con estadísticas (por mes, tipo y estado, con exportación a Excel) para decidir e informar.

## Positioning

*Inferido del repositorio y de las respuestas; pendiente de confirmación explícita.* Un mismo registro sigue cada solicitud de mantenimiento del campus desde que un residente o trabajador la reporta hasta que se cierra, pasando por el técnico asignado y por los materiales realmente consumidos con su descuento de stock, y produce las estadísticas que la Dirección de Mantenimiento necesita. Está hecho para la UCI: sus residencias, sus locales docentes y administrativos y sus zonas exteriores, con la Dirección de Mantenimiento como despachadora y una intranet como entorno de funcionamiento.

## Operating Context

- **Despliegue: solo intranet de la UCI, sin salida a internet externo.** Fuentes, íconos, librerías y cualquier recurso deben empaquetarse localmente. Los usuarios entran desde móvil (residentes, técnicos) y desde PC (despachador, almacenero).
- **Ciclo de una incidencia**: el solicitante la reporta (tipo, prioridad, ubicación, descripción, imagen opcional) → estado *Pendiente* (aún sin técnico) → el administrador asigna un técnico → *En proceso* → el almacenero o el administrador asignan materiales y el stock se descuenta automáticamente → *Resuelto*. Se puede quitar un material asignado por error y su cantidad vuelve al inventario.
- **Tipos de incidencia** en el modelo: plomería, electricidad, infraestructura, mantenimiento de equipos, saneamiento, seguridad, jardinería, sistema de agua potable, sistema de gas y sistema de incendios.
- **Ubicaciones** que hay que poder nombrar: edificio + apartamento/cuarto (residencias); facultad/edificio + local (docencia y oficinas); zonas exteriores y servicios (viales, áreas verdes, comedores, redes de agua, luz y gas). Hoy es un texto libre de 50 caracteres. Se desconoce si la UCI tiene una nomenclatura oficial de edificios y locales.
- **Soporte**: solicitudes de soporte (software, hardware, otro) con hilo de mensajes entre el usuario y el administrador; notificaciones dentro del sistema.
- **Documentos de acompañamiento**: manual de usuario, guía rápida y preguntas frecuentes en PDF, más un ZIP con la documentación completa, todo en `web_mantenimiento_uci/static/docs/`. Contacto de soporte indicado en el manual: soporte@uci.cu.

## Capabilities and Constraints

Existente:

- Login con usuario y contraseña; acceso por rol; el administrador gestiona usuarios y roles.
- Reporte de incidencias con imagen; lista con búsqueda, paginación, edición y eliminación por rol.
- Asignación y retiro de técnico; asignación y retiro de materiales con control de stock.
- Registro de personal técnico e inventario de materiales.
- Dashboard con estadísticas y exportación a Excel (estados, incidencias por mes, listado).
- Solicitudes de soporte con chat y marca de mensajes no leídos; notificaciones con contador.

Restricciones y decisiones tomadas:

- **Sin dependencias de internet externo** (intranet solamente).
- **Idioma: español.** La interfaz actual declara `lang="en"` y tiene textos en inglés ("Enter username"); eso es un defecto, no una decisión.
- **Prioridad**: el solicitante puede proponerla, pero el despachador la confirma o la corrige. Hoy el código deja que la elija quien reporta; se está implementando la decisión.
- **Nomenclatura**: SGUM = "Sistema de Gestión Universitaria de Mantenimiento". Nombre oficial de la universidad: "Universidad de las Ciencias Informáticas".
- **Rol "cliente"**: en la interfaz se llama "Solicitante".
- **Tipos de incidencia**: el modelo (10 tipos) es la fuente única; el formulario de reporte los toma de él en vez de mantener su propia lista de 5.
- **Alcance del rediseño (aprobado por el usuario)**: interfaz y experiencia completas más corrección de la lógica de vistas y modelos (con migraciones si hacen falta).

Decisiones abiertas:
- Si existe una nomenclatura oficial de edificios y locales que el sistema deba respetar.
- Quién opera concretamente el rol de administrador en la Dirección de Mantenimiento, y si hay una política de plazos de respuesta.

## Brand Commitments

- **Nombre: SGUM-UCI.** Es el nombre del producto. "Mantenimiento UCI" (portada) y "MainPage" (pestaña) son restos que se alinean con este nombre.
- **Logo y lema**: `web_mantenimiento_uci/static/logoSGUM.png`, con el lema "Gestión inteligente, comunidad conectada." Ya existe y se respeta.
- **Voz: institucional y de usted.** Español formal de universidad, por ejemplo "Registre la incidencia" y "Su solicitud fue recibida". Aplica a botones, mensajes, errores y notificaciones.
- **Foto de la pantalla de login**: `web_mantenimiento_uci/static/portada_fidel_2.jpeg`, una valla de la UCI con la imagen de Fidel Castro. El usuario la declaró parte de la identidad y se mantiene; el diseño debe convivir con ella.

## Evidence on Hand

- Código de la aplicación y datos de prueba en `web_mantenimiento_uci/db.sqlite3` (12 usuarios, 8 incidencias, 3 materiales, 4 técnicos, 5 solicitudes de soporte). Son datos de prueba, no de operación.
- Manual de usuario, guía rápida y FAQ en `web_mantenimiento_uci/static/docs/`. Describen cosas que el sistema todavía no hace (recuperación de contraseña, una sección "Documentación" propia) y el enlace del video tutorial es un marcador de posición.
- Logo y foto de login (rutas arriba).
- No hay datos reales de uso, tiempos de respuesta, volúmenes, testimonios ni cifras de la UCI. Trabajo futuro no debe inventarlos.

## Product Principles

1. **El despachador manda.** La interfaz se diseña primero para su jornada: escanear, priorizar y asignar sin fricción. Los demás roles se ordenan a partir de ahí.
2. **Nada se pierde.** Toda solicitud tiene un estado, un responsable y un historial visibles para quienes intervienen.
3. **Reportar es fácil y ocurre en el móvil.** El solicitante no es técnico ni administrador; describir un problema y adjuntar una foto debe resolverse en un momento y con conexión modesta.
4. **Funciona dentro de la UCI.** Nada de lo que la interfaz necesita para cargar o funcionar depende de internet.
5. **Lo que se gasta se registra.** Los materiales quedan ligados a la incidencia y el inventario siempre refleja lo real; de ahí salen los datos para decidir e informar.
