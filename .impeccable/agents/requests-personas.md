# Peticiones del agente PERSONAS

Todo lo de abajo tiene ya una solución local en las plantillas de personas; las peticiones mejoran o completan la pantalla.

## 1. BACKEND (urgente): quitar `'user': editado` del contexto de `seleccionar_usuario` (views.py, función `contexto()`)
- **Qué:** eliminar la clave `'user'` del diccionario que se pasa a `editar_usuario.html`.
- **Por qué:** `editar_usuario.html` ya usa `usuario_editado`, pero `navbar.html` sigue leyendo `user` (`user.username`, `user|has_groups`). Mientras `user` valga el usuario editado, la barra superior de esa página muestra el nombre, el rol y el menú del usuario EDITADO en lugar de los del administrador en sesión (comprobado: editando a `dev_tecnico`, la barra decía «dev_tecnico» y solo ofrecía Incidencias y Soporte). Desde plantilla no se puede corregir.
- **Comprobar:** `usuarios/tests/test_usuarios.py` (~línea 261) lee `.context`; revisar si aserta `user`.
- Alternativa equivalente en FUNDACIÓN: que `navbar.html` use `request.user` en lugar de `user`.

## 2. BACKEND: respetar `next` en `seleccionar_usuario` y en `_eliminar_usuarios`
- **Qué:** al guardar o eliminar, volver con `redirigir_atras(request, 'usuarios')` en lugar de `redirect('usuarios')`.
- **Por qué:** la lista y la edición conservan búsqueda, filtros y página en la URL (la edición se abre con `?q=…&rol=…&page=…` y «Cancelar»/«Volver» los respetan), pero tras «Guardar cambios» o «Eliminar cuenta» se pierde el filtro. `cambiar_activo_usuario` ya lo hace bien. La plantilla de edición no envía `next`; bastaría que el formulario lo enviara (puedo añadir `<input type="hidden" name="next" value="{% url 'usuarios' %}?{{ request.GET.urlencode }}">` en cuanto el backend lo respete).

## 3. BACKEND: mensaje de éxito en el alta por AJAX (`_crear_usuario`)
- **Qué:** además del JSON, `messages.success(request, "Se registró la cuenta «X». Ya puede iniciar sesión.")`.
- **Por qué:** hoy la plantilla guarda el nombre en `sessionStorage` y muestra un toast tras recargar. Con el mensaje del servidor, `master.html` lo pinta como el resto de acciones. Si se añade, retirar el bloque `CLAVE_CREADO` de `static/sgum/pages/personas.js` para no duplicar el aviso.

## 4. BACKEND: dato de historial por fila en la lista de usuarios
- **Qué:** anotar en cada fila de `usuarios` el número de incidencias registradas o atendidas (`Count('incidencia')` + `Count('personal__incidencias_asignadas')`, como ya hace `_eliminar_usuarios`), p. ej. `fila.n_historial`.
- **Por qué:** «Eliminar cuenta» hoy solo se entera del bloqueo tras confirmar. Con el dato, la plantilla mostraría «Eliminar» desactivado con el motivo («Tiene N incidencias: desactive la cuenta») en las cuentas con historial.

## 5. BACKEND: técnicos sin ficha `Personal`
- **Qué:** en la base de pruebas, el usuario `royciel` tiene el rol Técnico pero no tiene fila en `Personal`, así que no sale en la página Personal ni se le puede asignar una incidencia (la asignación usa el id de `Personal`).
- **Propuesta:** migración de datos que cree la ficha a todo usuario del grupo `tecnico` que no la tenga, o que `personal` y `_tecnicos_con_carga` las creen bajo demanda con `_asegurar_personal`.

## 6. BACKEND (mejora): incidencias abiertas por técnico en `personal`
- **Qué:** exponer por cada `Personal` las 3 primeras incidencias abiertas (`p.abiertas_lista`) en vez de solo el reflejo `p.incidencia`.
- **Por qué:** el despachador ve «3 abiertas» pero solo una referencia (a veces ninguna: `dev_tecnico` tiene 3 abiertas y `p.incidencia` es `None`, el reflejo no está sincronizado). La página muestra hoy el reflejo si existe y, si no, remite al enlace «Ver incidencias».

## 7. FUNDACIÓN: ícono `unlock` en `partials/icons_sprite.html`
- **Qué:** añadir `<symbol id="i-unlock">` con las mismas propiedades que `i-lock` (candado abierto): `<path d="M5 11h14v10H5zM8 11V7a4 4 0 0 1 7.5-1.9"/>`.
- **Por qué:** «Reactivar cuenta» lo necesita. Hoy lo define localmente `usuarios/templates/persona_iconos.html` (incluido en `all_usuarios.html`); al añadirlo al sprite, borrar ese archivo y su `include`.
