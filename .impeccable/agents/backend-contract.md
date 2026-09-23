# Contrato del backend de SGUM-UCI

Lo escribe el agente BACKEND. Es la fuente de verdad de lo que las plantillas pueden esperar del servidor: permisos, URLs, campos POST, contexto y mensajes. Si una plantilla necesita algo que no está aquí, se pide al backend; no se inventa.

Convenciones que valen para todo el documento:

- Los nombres de URL y de campos POST de antes se conservan. Lo que cambia o se añade está marcado con **[CAMBIO]** (rompe la plantilla vieja) o **[NUEVO]** (se puede ignorar hasta necesitarlo).
- Toda acción que modifica datos exige `POST` y responde con **redirección** (POST-redirect-GET) y un mensaje de `django.contrib.messages`. Un `GET` a una de esas URLs devuelve **405**.
- Después de una acción la vista vuelve a la página de origen (cabecera `Referer`, o el campo POST `next` si viene) siempre que sea del mismo sitio; si no, a `incidencias`. Poner `<input type="hidden" name="next" value="{{ request.get_full_path }}">` en los formularios de acción conserva página y filtros.
- Rol `cliente` se muestra siempre «Solicitante» (`rol_display`, filtro `nombre_rol`).
- Nombre de la UCI y trato de usted: los mensajes ya vienen redactados así; no los reescriba en la plantilla, muéstrelos tal cual (`{{ message }}`).

---

## 1. Matriz de permisos

Superusuario cuenta como Administrador. Quien no tiene ningún rol de trabajo (ni grupo) actúa como Solicitante.

| Acción | Solicitante | Técnico | Almacenero | Administrador |
|---|---|---|---|---|
| Portada, notificaciones propias, reportar incidencia | sí | sí | sí | sí |
| Ver lista de incidencias | solo las suyas | las asignadas a él **y** las que él reportó | **todas** (solo lectura) | todas |
| Editar tipo, ubicación y descripción | las suyas, solo en *Pendiente* | las que él reportó, solo en *Pendiente* | las que él reportó, solo en *Pendiente* | cualquiera, en cualquier estado |
| Cambiar estado | no | solo las asignadas a él: *En proceso* o *Resuelto* (puede reabrir una resuelta) | no | cualquiera, cualquier estado |
| Proponer prioridad | al reportar | al reportar | al reportar | al reportar (queda ya *Confirmada*) |
| Cambiar / confirmar prioridad | no | no | no | **sí, solo él** |
| Corregir la fecha de la incidencia | no | no | no | sí (pasada, nunca futura) |
| Eliminar incidencia | las suyas en *Pendiente* | las que él reportó en *Pendiente* | las que él reportó en *Pendiente* | cualquiera |
| (nadie) eliminar una incidencia con materiales asignados | bloqueado: hay que retirar antes los materiales | | | |
| Asignar, cambiar o quitar técnico | no | no | no | sí |
| Asignar y quitar materiales | no | no | sí | sí |
| Materiales: registrar, editar, eliminar | no | no | sí | sí |
| Dashboard (`reportes`) y exportación a Excel | no | no | sí | sí |
| Personal | no | no | no | sí |
| Usuarios (alta, edición, roles, contraseña, baja) | no | no | no | sí |
| **Desactivar / reactivar cuentas** (`cambiar_activo_usuario`) | no | no | no | sí, **nunca la propia**; un administrador común no toca superusuarios; no se desactiva a un técnico con incidencias abiertas |
| Soporte: pedir, ver y responder **las propias**, marcarlas completadas, eliminarlas | sí | sí | sí | sí |
| Soporte: bandeja, **ver, responder y marcar completadas las de otros** | no | **sí** | no | sí |
| Soporte: **eliminar** solicitudes de otros | no | no | no | sí |

Decisiones que hay que conocer (marcadas como supuestos en el informe):

- **Soporte (decisión del usuario):** el técnico entra a la bandeja, ve **todas** las solicitudes y las responde junto con el administrador. Supuestos míos: puede también marcarlas como completadas; **eliminar solicitudes ajenas sigue siendo solo del administrador**; una solicitud propia del técnico funciona como la de cualquier usuario (la ve en «Solicitar soporte», puede eliminarla ahí y el resto del personal la atiende). La marca «sin leer» es compartida por el personal: si un técnico abre la solicitud, deja de figurar sin leer para los administradores.
- El almacenero ve todas las incidencias porque asigna materiales a incidencias que no son suyas.
- **Carga de técnicos (decisión del usuario):** un técnico puede tener varias incidencias abiertas a la vez. El servidor no limita la asignación; la interfaz debe mostrar `abiertas` junto a cada técnico para que el despachador decida. Ya **no** se filtra por «técnicos disponibles».
- **Asignar técnico ⇒ *En proceso*; quitarlo ⇒ *Pendiente*** (confirmado). No se puede asignar ni quitar en una incidencia resuelta.
- **Lo que tiene historial no se elimina (confirmado):** usuarios con incidencias registradas o atendidas (se desactivan), incidencias con materiales asignados (se retiran antes los materiales) y materiales con consumos (**la vía es dejar su cantidad en 0** con `editar_material`).

### Supuestos vigentes

Decididos por la coordinación en nombre del usuario; la interfaz debe respetarlos:

- (a) El almacenero ve **todas** las incidencias; el técnico ve las asignadas a él y las que él reportó.
- (b) Las incidencias existentes quedan como «Propuesta» (`prioridad_confirmada=False`); no se confirmaron en bloque.
- (c) Límite de imagen en el servidor: **8 MB** (`imagen_max_bytes`, `imagen_max_mb` en el contexto de `reportar_incidencia`). La interfaz reducirá la foto en el navegador antes de subirla; el servidor sigue rechazando lo que pase de 8 MB.
- (d) Si reporta un administrador, la prioridad queda **confirmada**.

### Rechazos

- **Sin sesión**: `302` a `login` con `?next=<ruta>`.
- **Con sesión pero sin permiso**: `403`. Si existe la plantilla `403.html` (en `usuarios/templates/`) se renderiza con el contexto `mensaje` (texto en español que explica el motivo y la salida); si no, el servidor responde una página mínima propia. Peticiones AJAX (`X-Requested-With: XMLHttpRequest` o `Accept: application/json`): `{"status":"error","message":...}` con `403`. **Petición para el agente de interfaz: cree `403.html`** (hereda de `master.html`; muestra `{{ mensaje }}` y un enlace a `{% url 'main' %}`).
- Endpoints JSON de notificaciones sin sesión: `401` con `{"status":"error","message":"Su sesión expiró. Vuelva a iniciar sesión."}` (no redirigen).
- Acción `POST`-only por `GET`: `405`.

---

## 2. Contexto global (en todas las plantillas) [NUEVO]

Procesador de contexto `usuarios.context_processors.roles` (registrado en `settings.py`). Solo con sesión iniciada:

| Clave | Forma |
|---|---|
| `is_admin`, `is_tecnico`, `is_almacenero` | bool, independientes. Superusuario ⇒ `is_admin` |
| `is_cliente` | bool: `True` solo si **no** tiene ningún rol de trabajo (Solicitante puro) |
| `rol_display` | texto: «Administrador», «Técnico», «Almacenero», «Solicitante» o, si hay varios, «Técnico, Almacenero» |
| `puede` | dict de bool para decidir enlaces: `reportar_incidencia`, `ver_todas_las_incidencias`, `usuarios`, `personal`, `materiales`, `dashboard`, `exportar`, `bandeja_soporte` (administrador **y técnico**), `eliminar_soporte_ajeno` (solo administrador), `asignar_tecnico`, `asignar_material`, `gestionar_prioridad` |

Uso: `{% if puede.materiales %}…{% endif %}`. `messages` sigue disponible como siempre.

Filtros (`{% load auth_extras %}`):

- `user|has_groups:"administrador,almacenero"`: usa los roles efectivos (superusuario = administrador; `cliente` solo para Solicitante puro).
- `codigo|nombre_rol` → «Solicitante» para `cliente`.
- `usuario|roles_texto`.

### Clases de los mensajes [CAMBIO]

`MESSAGE_TAGS` (settings) hace que `message.level_tag` y `message.tags` valgan **`success`, `info`, `warning` y `danger`**. Django etiqueta por defecto los errores como `error`; aquí es **`danger`**. El parcial `partials/messages.html` comprueba `tag == 'error'` y con esto los errores saldrían como información: **debe comprobar `'danger'`** (recomiendo aceptar ambos). Niveles emitidos: `success` (operación hecha), `warning` (hecho a medias o aviso), `danger` (no se hizo), `info` (sin cambios).

### Fechas y zona horaria

`LANGUAGE_CODE='es'`, `TIME_ZONE='America/Havana'`. Con `USE_TZ`, `{{ x.fecha }}` se muestra en hora de La Habana y localizado; para un formato fijo use `|date:"d/m/Y H:i"`. El campo de fecha del formulario de edición se envía en hora local: `AAAA-MM-DD HH:MM` (también acepta `AAAA-MM-DDTHH:MM`, `DD/MM/AAAA HH:MM`, solo fecha).

---

## 3. Vistas

Notación: **Rol** = quién entra (los demás reciben 403; sin sesión, login). `errores` es siempre un dict `{nombre_de_campo_POST: texto}`; `valores` repite lo escrito para no obligar a repetirlo.

### 3.1 `login` — `GET|POST /`

- Si ya hay sesión: redirige a `next` (si es del mismo sitio) o a `main`.
- POST: `username`, `password`, `next` (opcional, campo oculto; solo rutas del propio sitio).
- Error: se vuelve a mostrar `login.html` (estado 200) con `error`, `next`, `username` (para rellenar el campo) y `cuenta_desactivada` (bool). Sin `messages`.
  - Credenciales incorrectas o usuario inexistente: siempre el mismo texto, «Usuario o contraseña incorrectos. Revise los datos e inténtelo de nuevo.» (no revela cuál falló).
  - **Cuenta desactivada:** solo si la contraseña es la correcta, `error` = «Su cuenta está desactivada. Comuníquese con la Dirección de Mantenimiento para que la reactiven.» y `cuenta_desactivada=True`. Con contraseña equivocada el mensaje es el genérico, de modo que nadie puede averiguar qué cuentas existen ni cuáles están desactivadas. Una sesión abierta de una cuenta que se desactiva deja de valer en la siguiente petición (302 a login).
- Contexto GET: `next`.

### 3.2 `logout` — `GET|POST /logout/`

Cierra sesión y va a `login`. (Enlace `GET` sigue valiendo.)

### 3.3 `main` — `GET /main/` — cualquier usuario con sesión

Claves antiguas conservadas: `notifications` (**lista de las 10 últimas**, antes todas), `unread_count`, `oc_b`, `is_admin`, `is_tecnico`, `is_almacenero`, `is_cliente` (mismas reglas de §2).

Claves [NUEVO]:

| Clave | Forma |
|---|---|
| `rol_display` | texto |
| `conteos` | `{pendiente, en_proceso, resuelto, total, abiertas, sin_tecnico, sin_confirmar}`. Alcance por rol: administrador y almacenero, todo el sistema; técnico, sus asignadas y las que reportó; solicitante, las suyas. `abiertas` = no resueltas; `sin_tecnico` y `sin_confirmar` (prioridad aún solo *propuesta*) cuentan sobre las abiertas |
| `incidencias_recientes` | lista de hasta 8 incidencias del alcance, las más nuevas primero (`usuario_reporte` y `tecnico_asignado.trabajador` ya cargados) |
| `incidencias_abiertas` | lista de hasta 8 no resueltas del alcance |
| `incidencias_sin_tecnico` | solo administrador (si no, `[]`): hasta 8 abiertas sin técnico, prioridad alta primero y más antiguas primero |
| `incidencias_sin_confirmar` | solo administrador (si no, `[]`): hasta 8 abiertas con prioridad solo propuesta |
| `incidencias_asignadas` | **solo existe si `is_tecnico`**: hasta 8 abiertas asignadas a él |
| `materiales_resumen` | administrador y almacenero: `{total, agotados}`; si no, `None` |
| `soporte_pendientes` | administrador y técnico: número de solicitudes de soporte *pendientes* (todas); si no, `None` |

### 3.4 `incidencias` — `GET|POST /incidencias/`

**Rol**: cualquiera con sesión (alcance según §1).

GET, parámetros de filtro (todos opcionales, combinables): `q` (busca en ubicación, descripción, solicitante, técnico, fecha, **y en el nombre visible de tipo, prioridad y estado sin distinguir acentos ni mayúsculas**: «plomería», «alta», «en proceso»; un número busca también por n.º de incidencia), `estado` (`pendiente`, `en_proceso`, `resuelto` o `abiertas`), `tipo`, `prioridad` (`1|2|3`), `tecnico` (`sin` o id de `Personal`), `confirmada` (`0|1`), `orden` (`recientes` por defecto, `antiguas`, `prioridad`), `page`.

Contexto:

| Clave | Forma |
|---|---|
| `page_obj` | páginas de 10. Cada fila trae **[NUEVO]** `puede_editar`, `puede_eliminar`, `puede_cambiar_estado`, `puede_asignar_tecnico`, `puede_asignar_material`, `puede_gestionar_prioridad`, `es_mia`, `es_asignada_a_mi` (bool) y los materiales precargados (`x.materialincidencia_set.all` sin consultas extra) |
| `tableIncidencia` | queryset completo filtrado (se conserva) |
| `tecnicos` | solo administrador (si no, `[]`): lista de **todos** los `Personal` de técnicos activos, de menor a mayor carga (luego por nombre), cada uno con `.trabajador` y **`.abiertas`** (n.º de incidencias abiertas que atiende; 0 si está libre) |
| `tecnicos_disponibles` | **[OBSOLETO]** ya no filtra: es la misma lista que `tecnicos`. Se conserva solo para que la plantilla antigua siga listando técnicos; la nueva debe usar `tecnicos` y mostrar `abiertas` |
| `materiales_disponibles` | administrador y almacenero: materiales con existencia > 0, por nombre; si no, `[]` |
| `q`, `filtros` | `filtros` = `{q, estado, tipo, prioridad, tecnico, confirmada, orden}` con lo aplicado (valores no válidos vienen vacíos) |
| `qs` | parámetros GET sin `page`, ya codificados (`?{{ qs }}&page=3`). `paginacion.html` ya conserva los filtros por sí mismo |
| `conteos` | igual que en `main` pero sobre **todo el alcance del usuario, sin filtros** (para pestañas o resumen) |
| `total_filtrado` | n.º de incidencias que cumplen el filtro |
| `tipos`, `prioridades`, `estados`, `ordenes` | listas de pares `(valor, etiqueta)` para selects |

Cada incidencia expone, además de los campos del modelo: `x.get_tipo_display`, `x.get_prioridad_display`, `x.get_estado_display`, `x.prioridad_confirmada` (bool), **`x.prioridad_situacion`** («Propuesta» / «Confirmada»), `x.fecha_asignacion`, `x.fecha_resolucion`, `x.esta_abierta`.

POST `action=eliminar` + `ids` (varios `ids`): elimina lo permitido y explica lo que no.

Mensajes: `warning` «Seleccione al menos una incidencia para eliminar.»; `success` «Se eliminó 1 incidencia.» / «Se eliminaron N incidencias.»; `warning` «N incidencia(s) no se eliminaron: solo puede eliminar las suyas mientras estén Pendientes.»; `warning` «No se eliminó la incidencia n.º X porque tiene materiales asignados. Retire primero los materiales…». Redirige de vuelta.

### 3.5 `reportar_incidencia` — `GET|POST /reportar_incidencia` (sin barra final)

**Rol**: cualquiera con sesión. Formulario `multipart/form-data`.

POST: `tipo_incidencia` (alias `tipo`), `prioridad` (`1|2|3`; **opcional**: si falta se toma `2`), `ubicacion`, `descripcion`, `imagen` (opcional).

Validación en servidor: tipo de la lista del modelo; prioridad válida; ubicación 1–50 caracteres; descripción 1–1000; imagen ≤ 8 MB y realmente JPG, PNG, WEBP o GIF. La prioridad enviada es una **propuesta** (`prioridad_confirmada=False`); si quien reporta es administrador queda ya confirmada.

Contexto (GET y POST con errores): `tipos` (10 pares del modelo; **use esto, no una lista propia**), `prioridades` (`('3','Alta'),('2','Media'),('1','Baja')`), `prioridad_defecto` (`'2'`), `ubicacion_max` (50), `descripcion_max` (1000), `imagen_max_bytes`, `imagen_max_mb` (8), `imagen_formatos` («JPG, PNG, WEBP»), `errores` (claves `tipo_incidencia`, `prioridad`, `ubicacion`, `descripcion`, `imagen`), `valores` (`tipo_incidencia`, `prioridad`, `ubicacion`, `descripcion`), `oc_b`.

Éxito: `success` «Su incidencia n.º N fue registrada. Puede seguir su estado en «Incidencias».» y redirige a `incidencias`. Error: se re-renderiza `reportar_incidencia.html` con estado 200, `errores` y un `danger` «Revise los campos marcados: no se guardó nada.». Además se crea el `Reporte` con la descripción real (el texto fijo «Reporte de Incidencia en el Servidor» ya no existe).

### 3.6 `editar_incidencia` — `GET|POST /incidencia/editar/<item_id>/`

**Rol**: quien pueda editar esa incidencia (§1); si no, 403 con un motivo concreto («Solo puede editar sus incidencias mientras estén Pendientes…»). Sin sesión, login.

Contexto: `incidencia`, `oc_b`, `permisos` (dict: `ver`, `editar`, `editar_datos`, `cambiar_estado`, `gestionar_prioridad`, `editar_fecha`, `eliminar`, `asignar_tecnico`, `asignar_material`; **muestre solo los campos con permiso**), `tipos`, `prioridades`, `estados`, `ubicacion_max`, `descripcion_max`, `materiales_asignados` (queryset de `MaterialIncidencia` con `.material`), `errores`, `valores`.

POST (solo se procesan los campos que llegan; los que el rol no puede cambiar se ignoran con aviso):

| Campo | Quién lo aplica | Nota |
|---|---|---|
| `tipo`, `ubicacion`, `descripcion` | `permisos.editar_datos` | mismas validaciones que al reportar |
| `prioridad` | administrador | `1|2|3` |
| `prioridad_confirmada` | administrador | `1` o `0`. Para una casilla envíe primero `<input type="hidden" name="prioridad_confirmada" value="0">` y luego la casilla `value="1"`. Si el administrador **cambia** la prioridad sin enviar este campo, queda confirmada |
| `fecha` | administrador | `AAAA-MM-DD HH:MM`, no futura. Si no se toca, se conserva con sus segundos |
| `estado` | administrador (los 3) y técnico asignado (`en_proceso`, `resuelto`) | ya **no** se reinicia a *pendiente* si no llega |

Efectos: `Reporte` (estado, descripción, fecha) y el reflejo del técnico se sincronizan; `fecha_resolucion` se fija al resolver y se borra al reabrir; se notifica al solicitante si cambia el estado.

Mensajes: éxito `success` «Se guardaron los cambios de la incidencia n.º N.» y redirige a `incidencias`; `warning` «No se aplicaron los cambios en: prioridad, … Su rol no puede modificarlos…»; con errores: `danger` «Revise los campos marcados…» y se re-renderiza (200) con `errores`.

### 3.7 `confirmar_prioridad` — `POST /incidencia/confirmar-prioridad/` [NUEVO]

**Rol**: administrador. Campos: `incidencia_id`, `prioridad` (opcional: corrige y confirma). Es la acción de un clic de la lista: botón «Confirmar prioridad». Mensajes: `success` «Prioridad Alta confirmada para la incidencia n.º N.»; `danger` si el id o la prioridad no son válidos.

### 3.8 `asignar_tecnico` — `POST /asignar-tecnico/`

**Rol**: administrador. Campos: `incidencia_id`, `tecnico_id` (id de **`Personal`**, no de usuario). Sirve también para cambiar de técnico.

Efectos: la incidencia queda `tecnico_asignado`, `fecha_asignacion`; si estaba *Pendiente* pasa a *En proceso*; se notifica al técnico y al solicitante. Rechazos con `danger`: incidencia resuelta, técnico inexistente o que ya no es técnico activo, mismo técnico. Éxito: «Técnico X asignado a la incidencia n.º N.» (`success`). Un técnico puede acumular varias incidencias.

### 3.9 `quitar_tecnico` — `POST /quitar-tecnico/<incidencia_id>/` **[CAMBIO]**

**Rol**: administrador. **Antes era un enlace `GET`; ahora hay que enviar un formulario `POST` con `{% csrf_token %}`** (con confirmación). Sin técnico asignado ya no falla: `danger` «La incidencia no tiene un técnico asignado.». Si estaba *En proceso* vuelve a *Pendiente*. No se puede quitar el técnico de una incidencia resuelta. Éxito: «Se quitó a X de la incidencia n.º N, que vuelve a Pendiente.»

### 3.10 `asignar_material` — `POST /incidencia/asignar-material/`

**Rol**: almacenero, administrador. Campos: `incidencia_id`, `material` (id), `cantidad` (entero 1–1 000 000; solo dígitos). El descuento de existencias es atómico: dos peticiones simultáneas nunca dejan el inventario en negativo. Mensajes: `success` «N unidad(es) de «X» asignadas a la incidencia n.º N; el inventario se actualizó.»; `danger` «No hay suficiente existencia de «X»: quedan A y usted pidió B.» o «La cantidad debe ser un número entero…». Vuelve a la página de origen (antes redirigía a una URL inexistente en un caso).

### 3.11 `quitar_material` — `POST /quitar-material/` **[CAMBIO]** (sin Referer ya no falla)

**Rol**: almacenero, administrador (**antes no tenía ninguna comprobación**). Campo: `material_incidencia_id`. Devuelve la cantidad al inventario. Mensajes: `success` «Se retiró «X»: N unidad(es) volvieron al inventario.»; `warning` si ya estaba retirado.

### 3.12 `materiales` — `GET|POST /materiales/`

**Rol**: almacenero, administrador.

GET: `q` (busca por nombre y tipo, también por nombre visible del tipo), `page`. Contexto: `page_obj` (10, orden por nombre), `tableMaterial`, `q`, `qs`, `tipos` (10 pares del modelo), `cantidad_max`, `errores`, `valores`, `abrir_registro` (bool: `True` cuando el alta falló y el modal/panel de registro debe abrirse mostrando `errores`).

POST alta: `username` (alias `nombre`), `tipo_material` (alias `tipo`), `cantidad` (0–1 000 000; entero, sin signos ni decimales). Éxito: `success` «Material «X» registrado con N unidad(es).» y redirige. Error: 200 con `errores` (`nombre`, `tipo`, `cantidad`), `valores` (`nombre`, `tipo`, `cantidad`), `abrir_registro=True`, más `danger` general.

POST baja: `action=delete` + `ids`. **Los materiales asignados a alguna incidencia no se eliminan** (se perdería el registro de lo consumido; la vía para un material con consumos es **dejar su cantidad en 0** con `editar_material`): `warning` «No se eliminó «X» (N asignación/es): … Puede dejar su cantidad en 0.»

### 3.13 `editar_material` — `GET|POST /material/editar/<item_id>/`

**Rol**: almacenero, administrador (**antes sin `login_required`**). POST: `nombre` (alias `username`), `tipo` (alias `tipo_material`), `cantidad`. Contexto: `material`, `oc_b`, `tipos`, `cantidad_max`, `errores` (`nombre`, `tipo`, `cantidad`), `valores`. Se acepta conservar un `tipo` antiguo que no esté en la lista. Éxito: `success` «Se guardaron los cambios de «X».» y redirige a `materiales`. **Antes esta vista leía `username` y por eso fallaba con la plantilla que envía `nombre`.**

### 3.14 `reportes` (dashboard) — `GET /reportes/`

**Rol**: almacenero, administrador. Parámetros: `mesAnio` (`AAAA-MM`; inválido ⇒ `warning` y se ignora), `anio` (año del gráfico mensual; por defecto el actual).

Claves conservadas con los mismos nombres: `tableReporte` (`Reporte` con `reporte_incidencia` ya cargada, más nuevos primero), `totalReportes`, `reporte_resuelto`, `reporte_pendiente`, `reporte_enProceso`, `incidencias_data` (lista de 12 enteros, enero..diciembre), `year`, `oc_b`, `today`. **[CAMBIO de fondo, mismas claves]** los conteos salen ahora de las incidencias (fuente de verdad) y el conteo por mes **ya agrupa bien** (`usuarios.estadisticas.incidencias_por_mes`, la misma función que usa la exportación).

[NUEVO]: `mesAnio` (eco), `meses` (12 nombres), `conteos` (mismo dict que `main`), `por_estado` (`[{codigo, etiqueta, cantidad}]` en orden pendiente, en_proceso, resuelto), `por_tipo` (`[{codigo, etiqueta, cantidad}]` con los 10 tipos, incluso en cero).

### 3.15 `exportar_dashboard` — `GET /dashboard/exportar/?anio=`

**Rol**: almacenero, administrador. Devuelve `Dashboard_Incidencias.xlsx` con hojas `Estados`, `Por Mes`, `Por Tipo` [NUEVO] y `Listado`. El listado ahora usa etiquetas legibles y añade columnas (Prioridad, Prioridad confirmada, Ubicación, Solicitante, Técnico, fechas de asignación y resolución). Las descripciones se guardan como texto (no se ejecutan como fórmulas de Excel).

### 3.16 `usuarios` — `GET|POST /usuarios/`

**Rol**: administrador.

GET: `q` (usuario, correo, nombre, apellidos), `rol` (`administrador|tecnico|almacenero|cliente`), `activo` (`1` activas, `0` desactivadas), `page`. Contexto: `page_obj` (cada fila trae **[NUEVO]** `rol_codigo`, `rol_display`, `es_propio` y `puede_cambiar_activo`: bool, falso para la propia cuenta y, si quien mira no es superusuario, para superusuarios; más `is_active` del modelo), `tableUsuario`, `q`, `qs`, `rol_filtro`, `activo_filtro`, `roles` (pares `(código, nombre visible)`: `cliente` ⇒ «Solicitante»), `password_ayuda` (lista de textos de los validadores de contraseña, para mostrar los requisitos).

POST alta (**responde JSON**, la interfaz usa `fetch`): `username`, `name` (alias `first_name`), `lastname` (alias `last_name`), `email`, `password`, `confirmPassword`, `rol` (opcional, por defecto `cliente`). Éxito: `{"success": true, "mensaje": "Usuario creado correctamente", "id": N}`. Error (estado 400): `{"success": false, "errors": {...}}` con claves posibles `usuario`, `nombre`, `apellidos`, `email`, `password` (incluye los requisitos de los validadores de Django), `confirmPassword`, `rol` y `general` (resumen de todo lo que no sea `usuario` ni `email`, para interfaces antiguas; la nueva puede ignorarlo). El usuario y el correo se comparan sin distinguir mayúsculas.

POST baja: `action=delete` + `ids`. No se eliminan: la propia cuenta, superusuarios (salvo por otro superusuario) y cuentas con incidencias registradas o atendidas: `warning` con el motivo y la sugerencia de **desactivar** la cuenta (ver 3.16b). Éxito: `success` «Se eliminó 1 usuario.» / «Se eliminaron N usuarios.»

### 3.16b `cambiar_activo_usuario` — `POST /usuarios/activo/<item_id>/` [NUEVO]

**Rol**: administrador. Desactiva o reactiva una cuenta sin perder nada de su historial. Un botón por fila de la lista (formulario POST con `{% csrf_token %}`, con confirmación al desactivar).

- Campo POST: **`is_active`** = `0` (desactivar) o `1` (reactivar). Opcional `next` para volver a la lista con sus filtros; sin él, vuelve al `Referer` o a `usuarios`.
- Reglas (todas con `danger` y motivo): no se desactiva la propia cuenta; solo un superusuario desactiva a otro superusuario; no se desactiva a un técnico con incidencias abiertas asignadas («Reasígnelas antes de desactivar la cuenta.»). Valor distinto de `0`/`1`: `danger`. Si ya estaba en ese estado: `info`. Usuario inexistente: 404. `GET`: 405; sin sesión: login; otros roles: 403.
- Éxito (`success`): «La cuenta «X» fue desactivada. Ya no puede iniciar sesión y su historial se conserva.» / «La cuenta «X» fue reactivada. Ya puede iniciar sesión.»
- Efecto: la cuenta desactivada no puede iniciar sesión (mensaje en el login, §3.1) y su sesión abierta deja de valer. Sus incidencias, solicitudes y notificaciones se conservan. El formulario de `editar_usuario` sigue aceptando `is_active` con las mismas reglas.

### 3.17 `editar_usuario` — `GET|POST /usuarios/editar/<item_id>/`

**Rol**: administrador. Contexto: `usuario_editado` **[NUEVO, úselo]**, `user` (**[CAMBIO recomendado]** se conserva por compatibilidad, pero **tapa al usuario en sesión** en esa página: la barra superior mostraría el nombre del usuario editado; hay que migrar la plantilla a `usuario_editado`), `oc_b`, `roles`, `rol_actual` (código; el `<select>` debe marcar ese `selected`, la plantilla vieja no marcaba ninguno y al guardar dejaba a todos como Solicitante), `es_propio` (bool), `password_ayuda`, `errores`, `valores`.

POST: `username`, `first_name`, `last_name`, `email`, `rol`, y opcionales `password` + `confirmPassword` (vacío = no cambia; se valida con los validadores de Django), `is_active` (`1`/`0`; ausente = no cambia; mismas reglas que 3.16b). Reglas: un administrador **no puede quitarse a sí mismo el rol de administrador ni desactivarse**; no se cambia el rol a un técnico con incidencias abiertas asignadas (hay que reasignarlas); usuario y correo únicos; el rol se crea si el grupo no existe (ya no hay error 500). Errores: 200 con `errores` (`username`, `first_name`, `last_name`, `email`, `rol`, `password`, `is_active`). Éxito: `success` «Se guardaron los cambios de «X».» y redirige a `usuarios`. Un rol `tecnico` crea su ficha en `Personal`.

### 3.18 `personal` — `GET /personal/`

**Rol**: administrador. `q` (usuario, nombre, apellidos, correo), `page`. Contexto: `tablePersonal`, `page_obj`, `q`, `qs`. Cada `Personal` trae `.trabajador`, `.incidencia` (reflejo de su incidencia abierta más reciente, o `None`) y **[NUEVO]** `.abiertas` (n.º de incidencias abiertas). En la plantilla, `p.incidencia.tipo` muestra el código: use `p.incidencia.get_tipo_display`. Para el nombre del rol use `p.trabajador|roles_texto`.

### 3.19 Soporte

- **`solicitar_soporte`** — `GET|POST /soporte/`. **Rol**: cualquiera. POST alta: `tipo` (`software|hardware|otro`), `descripcion` (1–2000). POST baja: `action=delete` + `ids` (**solo las propias**). Contexto: `page_obj` (cada fila trae **[NUEVO]** `sin_leer`: bool), `solicitudes_por_leer` (se conserva: lista de solicitudes con respuestas ajenas sin leer, **ya limitada a las propias**), `q`, `qs`, `tipos_soporte`, `descripcion_max`, `errores` (`tipo`, `descripcion`), `valores`. Éxito: `success` «Su solicitud fue enviada…».
- **`bandeja_entrada_soporte`** — `GET|POST /soporte/admin/`. **Rol**: **administrador y técnico** (ven todas las solicitudes). Baja: `action=delete` + `ids`, **solo administrador** (un técnico recibe 403). Contexto: `page_obj` (con `sin_leer`), `solicitudes`, `solicitudes_por_leer`, `q`, `qs`, **[NUEVO]** `puede_eliminar` (bool: mostrar u ocultar el botón/casillas de eliminar). Aquí «sin leer» = mensajes escritos por quien hizo la solicitud que el personal aún no ha abierto. Se puede buscar por usuario, tipo (incluye el nombre visible) y estado.
- **`detalle_solicitud`** — `GET|POST /soporte/detalle/<solicitud_id>/`. **Rol**: el autor de la solicitud, un técnico o un administrador (el personal las ve todas); cualquier otro recibe 403 (**el permiso se comprueba antes de marcar nada como leído**; antes se redirigía a una URL inexistente). POST: `mensaje` (1–2000; vacío ⇒ `danger` y vuelve). Contexto: `solicitud`, `respuestas` (lista ordenada, `autor` cargado), `es_autor`, `puede_responder`, `puede_completar` (autor, técnico o administrador, mientras no esté resuelta), `mensaje_max`, `oc_b`. Al abrirla se marcan como leídas las respuestas ajenas.
- **`completar_solicitud`** — `POST /soporte/completar/<solicitud_id>/` **[CAMBIO]** (antes aceptaba GET). **Rol**: el autor, un técnico o un administrador. `success` «La solicitud fue marcada como completada.» o `info` si ya lo estaba.

### 3.20 Notificaciones

- **`get_notifications`** — `GET /notifications/`. Sin sesión: 401 JSON. Con sesión: 
  ```json
  {
    "items": [{"id": 12, "message": "…", "is_read": false, "created_at": "2026-09-20T15:04:05-04:00", "url": "/incidencias/"}],
    "unread_count": 3,
    "notifications": "<texto JSON con la forma antigua>"
  }
  ```
  `items` son las 50 últimas, más recientes primero. **`url` es una ruta absoluta que empieza con `/`** y siempre lleva a una página que el destinatario puede abrir. **Use `items` y `href = item.url`.** `notifications` (texto JSON serializado por Django, forma antigua) se mantiene solo para que el `notificaciones.js` viejo siga funcionando: en esa forma `fields.urlAsociated` va **sin** barra inicial para que `/${fields.urlAsociated}` siga dando la ruta correcta. Cuando el JS nuevo use `items`, dejaré de enviar `notifications`.
- **`mark_as_read`** — `POST /notifications/<id>/read/` y **`delete_notification`** — `POST /notifications/<id>/delete/`: `{"status":"success"}`, o `404` `{"status":"error","message":"Notificación no encontrada"}` (también para las de otro usuario), o `401` sin sesión. Envían `X-CSRFToken` como hasta ahora.
- Los textos de las notificaciones son **texto plano sin `<` ni `>`**; aun así, en el JS asigne con `textContent`, no con `innerHTML`.

Qué notifica el sistema y a dónde lleva (`urlAsociated`, calculado con `reverse`):

| Evento | Destinatarios | URL |
|---|---|---|
| Incidencia reportada | el solicitante; todos los administradores (salvo quien reporta) | `/incidencias/` |
| Técnico asignado o cambiado | el técnico nuevo | `/incidencias/` |
| Cambio de estado de la incidencia (incluye el paso a *En proceso* al asignar) | el solicitante | `/incidencias/` |
| Solicitud de soporte creada | el autor; **todo el personal de soporte (administradores y técnicos)**, salvo el propio autor si lo es | `/soporte/detalle/<id>/` |
| Mensaje en una solicitud | si escribe el autor: administradores y técnicos (menos él); si escribe un administrador o un técnico: solo el autor | `/soporte/detalle/<id>/` |

---

## 4. Cambios incompatibles con las plantillas viejas (resumen)

1. **Errores de `messages` ahora son `danger`** (no `error`). Afecta a `partials/messages.html` (usa `'error'`). Las plantillas viejas con `alert-{{ message.tags }}` mejoran (`alert-danger`).
2. **`quitar_tecnico` ya no acepta GET**: `all_incidencias.html` lo enlaza con `<a href>`; debe ser un `<form method="post">` con `{% csrf_token %}` (con confirmación previa). `completar_solicitud`, `asignar_tecnico`, `asignar_material`, `quitar_material` y `confirmar_prioridad` también son solo POST (las viejas ya los enviaban por POST, salvo `completar_solicitud` si alguien lo enlazara).
3. **Lista de tipos**: `limpieza` ya **no es un valor válido**. Las plantillas que dibujan sus propias 5 opciones (`reportar_incidencia.html`, `editar_incidencia.html`, `modalRegistrarMaterial.html`, `editar_material.html`) enviarían un tipo rechazado al elegir «Saneamiento». Hay que generar los `<option>` con `tipos` (10 pares). Los datos antiguos con `limpieza` se migraron a `saneamiento`.
4. **Etiquetas del modelo con ortografía correcta**: «Plomería», «Jardinería», «Mantenimiento de equipos», «Sistema de agua potable», «Sistema de gas», «Sistema de incendios», **«En proceso»** (antes «En Proceso»). Si alguna plantilla compara textos en lugar de códigos, se rompe; compare siempre `x.estado == 'en_proceso'`.
5. **`editar_usuario.html`**: `user` en el contexto tapa al usuario en sesión (la barra muestra al editado). Migrar a `usuario_editado`. El `<select name="rol">` necesita marcar `rol_actual`; sin eso, guardar cambia el rol a Solicitante (y a un administrador que se edita a sí mismo se le rechaza el cambio, con error visible solo si la plantilla muestra `errores.rol`). Además el campo contraseña de esa plantilla tiene un atributo roto (`id="password name="password"`).
6. **Notificaciones**: `urlAsociated` guarda ahora rutas absolutas. El `notificaciones.js` actual usa `href="/${fields.urlAsociated}"`; sigue funcionando por la forma antigua que conservo, pero el JS nuevo debe usar `data.items[i].url` tal cual (con `/` inicial) para no producir `//ruta`.
7. **`get_notifications`** ahora responde 401 JSON sin sesión (antes redirigía a login y el `fetch` fallaba al parsear HTML).
8. **Alcance de la lista de incidencias**: el administrador (no superusuario) y el almacenero ahora ven **todas** las incidencias; antes solo veían las suyas. El técnico ve, además de las asignadas, las que él reportó.
9. **`has_groups`**: usa roles efectivos. `has_groups:"cliente"` solo es verdadero para el Solicitante puro; el superusuario es `administrador`.
10. **`main`**: `notifications` trae 10, no todas.
11. **Contexto de la lista de incidencias**: `tecnicos` y `tecnicos_disponibles` son listas (no querysets), vacías salvo para el administrador, y **`tecnicos_disponibles` ya no filtra** (es igual a `tecnicos`); use `tecnicos` con `.abiertas`. `materiales_disponibles` vacío para quien no asigna materiales.
11b. **Soporte para técnicos**: `bandeja_entrada_soporte` deja de dar 403 al técnico; la navegación del técnico debe ofrecerle «Bandeja de soporte» (`puede.bandeja_soporte`) además de «Solicitar soporte», sin botón de eliminar (`puede_eliminar`). `detalle_solicitud` y `completar_solicitud` admiten al técnico.
11c. **Cuentas desactivadas**: `login` recibe `cuenta_desactivada`; la lista de usuarios necesita, por fila, un botón POST hacia `cambiar_activo_usuario` (§3.16b).
12. **Textos de `messages`**: ahora casi toda acción emite un mensaje (antes casi ninguna). `master.html` debe pintarlos una sola vez.
13. **Login**: para conservar `next` el formulario debe reenviarlo en un campo oculto `next` (la plantilla nueva ya lo hace). Error en `error`, sin `messages`.
14. **`reportar_incidencia.html`**: el JS de la plantilla vieja busca `#registroForm` y `#modalIncidencia` que no existen en ella (se rompe al enviar). Es un defecto de plantilla, no del servidor.
15. **Seguridad de plantilla**: `all_incidencias.html` pasa la descripción a JavaScript con `onclick="mostrarDescripcion('{{x.descripcion}}')"`; una comilla en el texto rompe el script y permite inyección. Use `data-descripcion="{{ x.descripcion }}"` (o `json_script`) y léalo desde JS.
16. **Paginación**: `qs` viene en el contexto de todas las listas, pero `paginacion.html` nueva ya conserva los parámetros por sí sola (`partials/_qs.html`); no hace falta usarlo.

---

## 5. Modelo y migraciones

Migraciones nuevas (todas idempotentes y portables entre PostgreSQL y SQLite; ya aplicadas a la base compartida de pruebas):

- **`0033_prioridad_confirmada_y_fechas`** (esquema):
  - `Incidencia.prioridad_confirmada` `BooleanField(default=False)`. Las incidencias existentes quedan como «Propuesta».
  - `Incidencia.fecha_asignacion` y `Incidencia.fecha_resolucion` (`DateTimeField`, nulos) para medir tiempos de respuesta.
  - `Incidencia.prioridad`: el valor por defecto era `'media'` (inválido); ahora `'2'`.
  - `Personal.incidencia`: `on_delete` pasa de `CASCADE` a `SET_NULL` (antes, eliminar una incidencia borraba la ficha del técnico asignado).
- **`0034_datos_iniciales`** (datos): asegura los grupos `administrador`, `tecnico`, `almacenero`, `cliente`; pasa `tipo='limpieza'` a `saneamiento`; crea el `Reporte` que falte a cada incidencia y reemplaza el texto fijo de los reportes antiguos por la descripción real; normaliza las `urlAsociated` antiguas a rutas absolutas (y las de `soporte/admin/` de quien no es administrador a `/soporte/`). Sin operación inversa.
- **`0035_etiquetas_en_espanol`** (choices, sin cambio en la base): ortografía de las etiquetas de tipo y estado.

Propiedades y métodos nuevos del modelo (úselos en plantillas): `Incidencia.prioridad_situacion` («Propuesta»/«Confirmada»), `Incidencia.esta_abierta`, `Notification.url`, `Personal.incidencias_abiertas`, `__str__` en `Incidencia` y `Personal`. Constantes: `Incidencia.UBICACION_MAX=50`, `DESCRIPCION_MAX=1000`, `IMAGEN_MAX_BYTES=8 MiB`.

`Personal.incidencia` sigue existiendo y se mantiene sincronizado, pero la fuente de verdad de la asignación es `Incidencia.tecnico_asignado`.

Esta ronda **no añade migraciones** (solo lógica). Módulos nuevos de Python: `usuarios/permisos.py` (roles y permisos, único lugar donde se decide quién puede qué), `validaciones.py`, `servicios.py` (asignar técnico, estados, materiales con stock atómico), `estadisticas.py`, `context_processors.py`.

## 6. Ajustes y entorno

- `settings.py` lee de variables de entorno, con los **mismos valores de antes por defecto**: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG` (por defecto verdadero), `DJANGO_ALLOWED_HOSTS` (coma), `DJANGO_CSRF_TRUSTED_ORIGINS`, `DB_ENGINE` (por defecto PostgreSQL), `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`. En producción defina al menos clave, `DJANGO_DEBUG=0`, hosts y contraseña de base.
- `LANGUAGE_CODE='es'` (Django no trae `es-cu`), `TIME_ZONE='America/Havana'`, `LOGIN_REDIRECT_URL='main'`.
- Con `DEBUG` falso, `/media/` (imágenes de incidencias) no lo sirve Django: lo debe servir el servidor web.
- `requirements.txt`: se añade `openpyxl==3.1.5` y `et_xmlfile==2.0.0`.
- CI (`.github/workflows/django.yml`): rama `master`, `working-directory: web_mantenimiento_uci`, servicio PostgreSQL, comprueba migraciones al día y corre `manage.py test`.
- Pruebas: `usuarios/tests/` (el antiguo `tests.py` se eliminó porque impedía descubrir el paquete). Las de navegador (`test_login_page.py`, Selenium + Firefox) son opcionales: `SGUM_SELENIUM=1`. Comprueban el marcado de `login.html` (título «Login», textos «Bienvenido», clases `text-prest`/`text-sub`, `#togglePassword`, `.err`), que el rediseño cambia: quien mantenga el login debe actualizarlas.
