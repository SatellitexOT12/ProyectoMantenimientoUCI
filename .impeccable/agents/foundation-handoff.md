# Manual del sistema de diseño «Plano de la UCI» (entrega de FUNDACIÓN)

Para los agentes que aplican el sistema a cada pantalla. Todo está en español, trato de usted, solo intranet (nada remoto). Léalo entero una vez; después sirve de consulta.

**Idea en una línea:** cada página es una lámina de un plano de la UCI: hoja blanco azulada, tinta azul, esquinas rectas, celdas de cajetín, retícula fina. Sin degradados, sin sombras decorativas, sin tarjetas apiladas. Modo **Operar**: escanear rápido, densidad, estados completos.

## 1. Qué hay y dónde

| Archivo | Para qué |
|---|---|
| `static/vendor/` | Bootstrap 5.3.3 (CSS y JS con Popper), jQuery 3.7.1, Chart.js 4.4.7. Ver `README.md` de la carpeta. |
| `static/sgum/tokens.css` | Variables (`--sg-*`) y remapeo de las `--bs-*` de Bootstrap. |
| `static/sgum/sgum.css` | Componentes `sg-*` y aspecto de las clases de Bootstrap (`.btn`, `.table`, `.modal`, `.form-control`…). |
| `static/sgum/login.css` | Solo la pantalla de acceso. |
| `static/sgum/sgum.js` | Toasts, avisos que se cierran, botón «cargando», validación en celdas, limpiar búsqueda, selección de filas, contador de la campana. |
| `static/togglepassword.js` | Ojo de mostrar/ocultar contraseña y aviso de Bloq Mayús (todo en minúsculas, ya arreglado el nombre). |
| `static/js/scripts.js` | Heredado: `toggleCheckboxes`, `setIncidenciaId`, `abrirImagen`, `confirmarEliminacion` y la validación de `#registroForm`. Ya no falla si faltan los elementos. |
| `static/img/` | `portada-valla.jpg` (foto optimizada), `logo-marca.png` (hexágono). Ver su `README.md`. |
| `templates/master.html`, `navbar.html`, `footer.html`, `login.html`, `paginacion.html`, `403.html`, `404.html`, `500.html` | Armazón. |
| `templates/partials/` | Parciales (sección 4). |

Se retiraron `static/log.css` y `static/navbar.css` (sin uso).

## 2. Anatomía de una página

```django
{% extends "master.html" %}
{% load static %}
{% block title %}Incidencias{% endblock %}          {# la pestaña dice «Incidencias · SGUM-UCI» #}

{% block content %}
<div class="sg-sheet">                              {# lámina: marco de línea + marcas de registro #}
  {% include 'partials/page_head.html' with title='Incidencias' desc='…' count=page_obj.paginator.count action_url=url_reportar action_label='Registrar incidencia' action_icon='plus' %}
  {% include 'partials/toolbar.html' with placeholder='Buscar por ubicación o descripción' count=page_obj.paginator.count %}
  <div class="sg-table-wrap">
    <table class="sg-table sg-table--stack"> … </table>
  </div>
  {% include 'paginacion.html' %}                   {# igual que siempre: usa page_obj #}
</div>
{% endblock %}

{% block scripts %}<script src="{% static 'vendor/chart.umd.min.js' %}"></script>{% endblock %}  {# solo si la página lo necesita #}
```

Reglas del armazón (`master.html`):

- Carga en la cabecera Bootstrap CSS + `tokens.css` + `sgum.css`, y Bootstrap JS (con Popper) y jQuery sin `defer` (las páginas viejas con scripts en línea siguen funcionando). Bloques: `title`, `extra_head`, `messages`, `content`, `scripts`.
- **Los mensajes de Django ya los pinta `master.html`** (una sola vez, sobre el contenido). **Borre de cada página el bucle `{% for message in messages %}`**; si no, saldrán dos veces. Etiquetas: `success`, `info`, `warning`, `danger` (y `error`/`debug` por compatibilidad). Éxito e información se cierran solos a los 6 s; errores y advertencias esperan al usuario.
- Sigue definiendo `NOTIFICATIONS_URL`, `csrftoken` y carga `js/notificaciones.js`. `mostrarToast()` (global) sigue funcionando para las páginas viejas.
- Icons: el sprite se inyecta una sola vez en `master.html` y `login.html`. No incluya otro.
- `oc_b` queda sin efecto (la búsqueda ya no está en la barra superior; va en cada página con `toolbar.html`).
- Anchos: la lámina mide `min(100% − 40 px, 1440 px)`. `sg-sheet--narrow` (46 rem) para mensajes y errores, `sg-sheet--medium` (64 rem) para formularios. En móvil (<576 px) la lámina llena el ancho, sin marco lateral.
- `<main id="contenido" tabindex="-1">` y el enlace «Saltar al contenido» ya existen.

### Barra superior (`navbar.html`)

Orden pensado para el despachador: **Incidencias**, Materiales, Personal, Usuarios, Estadísticas, Soporte, y a la derecha «Registrar incidencia» (siempre a mano), campana y menú de usuario (rol legible: Administrador, Técnico, Almacenero, Solicitante; usa `rol_display` si el contexto lo trae). Permisos con `has_groups` (3 consultas por página). Administrador y técnico ven **Soporte** como menú (Bandeja de soporte y Solicitar soporte); los demás, un enlace. Solicitante ve «Mis incidencias». Página actual: `aria-current="page"` + fondo y barra cian según `request.resolver_match.url_name` (si crea una URL nueva relacionada con una sección, añádala a la condición de esa sección en `navbar.html`). Entre 992 y 1439 px «Registrar incidencia» se reduce a un botón con `+` (nombre accesible intacto). Menos de 992 px: menú desplegable con la campana y el usuario siempre visibles.

**Para quien reescriba `notificaciones.js`:** `#notificationCount` es el contador (sin leer; `hidden` en cero: `sgum.js` lo oculta solo cuando el texto es 0 y actualiza el `aria-label` de la campana). `#notificationDropdown` es la **lista `<ul class="sg-notif__list">`**, no el menú; su cabecera «Notificaciones» es aparte, así que puede vaciar y rellenar el `<ul>` sin perderla. Cada elemento: `<li class="notification">` (añada `read` cuando esté leída: cuadro hueco y texto atenuado; sin `read`: cuadro de tinta y fondo azul claro). Para «sin notificaciones»: `<li class="text-muted">No hay notificaciones</li>` (sin marcador). Use `textContent`, no `innerHTML`.

## 3. Tokens (`tokens.css`)

**Color** (todos ≥4.5:1 como texto sobre su fondo, salvo los marcados «línea»)

| Token | Valor | Uso |
|---|---|---|
| `--sg-ink` | `#0b4a7f` | tinta: líneas fuertes, títulos, acción primaria |
| `--sg-ink-deep` / `--sg-ink-press` | `#083a66` / `#062d50` | hover / active de la tinta |
| `--sg-text` | `#0b2a44` | cuerpo y valores (13,5:1) |
| `--sg-text-2` | `#33536b` | texto secundario (7,5:1) |
| `--sg-text-3` | `#46667f` | etiquetas, ayudas, placeholder (5,6:1) |
| `--sg-sheet` | `#f3f6f9` | hoja (fondo de la aplicación, con retícula) |
| `--sg-panel` | `#f9fbfd` | segunda capa: barras, cabeceras de tabla, pie |
| `--sg-paper` | `#ffffff` | celdas, tablas, modales |
| `--sg-hover` / `--sg-selected` | `#e4eef6` / `#d7e8f5` | fila u opción bajo el puntero / seleccionada |
| `--sg-grid` / `--sg-grid-strong` | `#c9d3dc` / `#9db3c6` | divisiones finas (línea, decorativas) |
| `--sg-line-control` | `#5d7d97` | borde de controles sueltos (4:1) |
| `--sg-cyan` | `#2a94d4` | **solo** marcas de registro y estado activo (barra de la pestaña actual). Nunca como texto ni fondo |
| `--sg-focus` | `#1a7fbd` | anillo de foco de teclado |
| `--sg-warn-*`, `--sg-ok-*`, `--sg-danger-*`, `--sg-info-*`, `--sg-neutral-*` | `-bg`, `-fg`, `-line` | estados (advertencia/pendiente, correcto/resuelto, error/alta, información/en proceso, neutro) |
| `--sg-danger` (+ `-deep`, `-press`), `--sg-ok` (+ `-deep`) | | botones peligro y éxito |

**Tipografía:** `--sg-font` (Segoe UI → system-ui → Noto/Liberation/Arial, sin fuentes remotas) y `--sg-font-mono` (ui-monospace → Cascadia/Consolas → DejaVu/Liberation). Escala fija de razón ≈1,125 sobre 15 px: `--sg-fs-2xs` 11, `xs` 12, `sm` 13, `md` 15 (cuerpo), `lg` 17, `xl` 19, `2xl` 22, `3xl` 25 (h1), `4xl` 28. Pesos `--sg-fw-regular/medium/semi/bold`. Interlínea `--sg-lh-tight/snug/body`. Prosa: `--sg-measure` 68ch.
**Espaciado (módulo de 8, con medio paso):** `--sg-s-1` 4, `s-2` 8, `s-3` 12, `s-4` 16, `s-5` 24, `s-6` 32, `s-7` 48, `s-8` 64. Otros: `--sg-gutter` 20, `--sg-sheet-max` 1440, `--sg-nav-h` 64, `--sg-touch` y `--sg-control-h` 44.
**Formas y líneas:** `--sg-radius: 0` (todo recto; el único círculo es el botón de radio). Líneas `--sg-line` 1px, `--sg-line-strong` 1,5px (cajetín), `--sg-frame` 2px (marco, modal, nav).
**Sombra:** solo `--sg-shadow-pop` (menús y toasts, que flotan sobre contenido). Nada más lleva sombra.
**Movimiento:** `--sg-ease`, `--sg-dur-fast` 150ms, `--sg-dur` 200ms. `prefers-reduced-motion` desactiva todo.
**Capas:** `--sg-z-sticky`, `-nav`, `-dropdown`, `-backdrop`, `-modal`, `-toast`.
**Marcas:** `--sg-registro` (cruz cian, SVG) y `--sg-reticula` (retícula de 32 px) como `url()`.

Chart.js: lea los colores con `getComputedStyle(document.documentElement).getPropertyValue('--sg-ink')`. Serie principal `--sg-ink`; secundarias `--sg-cyan`, `--sg-warn-line`, `--sg-ok-line`, `--sg-danger-line`, `--sg-neutral-line`. No dependa solo del color: etiquetas de datos o leyenda con texto; texto de ejes `--sg-text-2`; cuadrícula `--sg-grid`. Sin sombras ni degradados en las barras.

## 4. Parciales (`templates/partials/`)

Todos reciben parámetros con `{% include '…' with a=b %}` (añada `only` si quiere aislar el contexto). Cada archivo trae su documentación en la cabecera.

| Parcial | Ejemplo |
|---|---|
| `icon.html` | `{% include 'partials/icon.html' with name='bell' %}` · opcional `class='sg-icon--lg'` (`--sm` 16, defecto 20, `--lg` 24, `--xl` 40) y `title='Notificaciones'` (si lleva title, el ícono se anuncia; si no, es decorativo). |
| `page_head.html` | `with title='Materiales' desc='Inventario de almacén.' count=page_obj.paginator.count count_label='materiales' action_url=… action_label='Registrar material' action_icon='plus'`. Páginas de detalle: `back_url=… back_label='Volver a incidencias'`. Segunda acción: `action2_*`. |
| `toolbar.html` | `with placeholder='Buscar por nombre o tipo' count=page_obj.paginator.count`. GET `q`, conserva los demás parámetros de la URL, quita `page`, botón × «Limpiar búsqueda» si hay búsqueda. Con filtros: arme `<div class="sg-toolbar">` + `partials/search_form.html` + `<div class="sg-toolbar__filters">` con `select.sg-select` (auto-envío con `onchange="this.form.requestSubmit()"` o un botón «Aplicar»). |
| `field.html` | Modo Django: `with field=form.ubicacion span='6'`. Modo manual: `with id='nombre' label='Nombre' required=True autocomplete='off' maxlength=50 hint='Como aparece en el almacén.'`; `as='textarea' rows=4`; `password=True`; `error='…'`; `optional=True`. |
| `badge_estado.html` | `with estado=x.estado` (`pendiente`, `en_proceso`, `resuelto`; sirve también para soporte). |
| `badge_prioridad.html` | `with prioridad=x.prioridad` (`'3'` alta, `'2'` media, `'1'` baja). |
| `empty.html` | `with title='Aún no hay materiales' text='Registre el primero para poder asignarlo a incidencias.' action_url=… action_label='Registrar material' action_icon='plus' icon='box'` |
| `modal_confirm.html` | `with id='eliminarIncidencias' title='¿Eliminar las incidencias seleccionadas?' text='Se borrarán y sus materiales volverán al inventario.' confirm_label='Eliminar incidencias' form='eliminar_incidencia'` (o `action_url=` + `hidden_name`/`hidden_value`, o `onclick=`). Se abre con `data-bs-toggle="modal" data-bs-target="#eliminarIncidencias"`. `safe=True` para confirmaciones no destructivas. |
| `messages.html` | Ya incluido en `master.html`. No lo vuelva a incluir. |
| `toast.html` | `with id='avisoSeleccion' kind='warn' message='Seleccione al menos una incidencia.'` y `SGUM.showToast('avisoSeleccion')`. Para textos calculados: `SGUM.toast('Texto', { kind: 'warn' })` (`info`, `ok`, `warn`, `danger`). |
| `search_form.html` | Solo el formulario de búsqueda (lo usa `toolbar.html`). |
| `paginacion.html` (raíz) | `{% include 'paginacion.html' %}` con `page_obj`. «Registros 1 a 10 de 24», anterior/siguiente y ventana de páginas; móvil: «Página 2 de 5». Conserva **todos** los parámetros GET (filtros, orden). No dibuja nada con una sola página. |

## 5. Clases `sg-*` (resumen)

**Armazón:** `sg-sheet` (`--narrow`, `--medium`), `sg-sheet__body`, `sg-section`, `sg-panel` (`__head`, `__body`; úselo solo para agrupar dentro de una lámina, **nunca anidado**), `sg-page-head` (`__main`, `__title`, `__desc`, `__count`, `__actions`, `__back`), `sg-backlink`, `sg-toolbar` (`__filters`, `__count`), `sg-search`, `sg-messages`, `sg-foot`.
**Botones:** `sg-btn` + `--primary` (una por pantalla), `--secondary`, `--danger` (solo destructivas), `--danger-outline`, `--ghost`, `--sm`, `--lg`, `--block`, `--icon` (cuadrado 44 px; exige `aria-label`). Estados: `:hover`, `:focus-visible`, `:active`, `:disabled`/`aria-disabled`, `.is-loading` (barra de avance inferior, conserva el color). Para enviar formularios con «cargando»: `<form data-sg-loading>` y `data-loading-label="Guardando…"` en el botón.
**Campos:** cajetín `sg-fields` (rejilla de 12) > `sg-field` (`--8/--6/--4/--3`; `is-error`, `is-disabled`, `--static` para solo lectura) con `sg-field__label` (+ `sg-field__opt` «opcional»), `sg-field__control` o cualquier `input/select/textarea` dentro, `sg-field__row` + `sg-field__btn` (botón dentro de la celda), `sg-field__hint`, `sg-field__msg`, `sg-field__value` (dato de solo lectura). Controles sueltos (toolbars, filtros): `sg-input`, `sg-select`, `sg-textarea`, `sg-label`, `sg-help`. Opciones: `sg-check` con `input.form-check-input` + `label`. Pie de formulario: `sg-form-actions`; resumen de error del formulario: `sg-form-error`.
**Tablas:** `sg-table-wrap` (contenedor con desplazamiento y cabecera fija) > `sg-table` (`--dense`, `--stack`). Columnas: `sg-col-n` (Nº), `sg-col-check`, `sg-col-actions` (+ `sg-actions`), `sg-num` (cifras a la derecha), `sg-data` (fecha/código en monoespaciada), `sg-truncate`. Ordenación: `<th aria-sort="ascending|descending"><a class="sg-sort" href="?orden=…">Fecha {icon chevron-down}</a></th>`. Fila seleccionada: `tr.is-selected` (lo pone `sgum.js` al marcar la casilla; la casilla de cabecera lleva `data-sg-select-all`).
**Estados:** `sg-badge` (`--pendiente`, `--proceso`, `--resuelto`, `--alta`, `--media`, `--baja`, `--neutro`; use los parciales), `sg-alert` (`--danger`, `--warn`, `--ok`, `--info`; `__body`, `__title`, `__close`), `sg-toast`, `sg-empty` (`__mark`, `__title`, `__text`, `__actions`), `sg-skeleton` (`--title`, `--text`, `--short`, `--block`), `sg-skeleton-row`, `sg-count` (contador de la campana).
**Utilidades:** `sg-mono` (datos), `sg-num` (cifras tabulares), `sg-muted`, `sg-nowrap`, `sg-stack`, `sg-cluster`, `sg-prose`, `sg-visually-hidden`, `sg-label-caps`.
**Atributos de comportamiento (`sgum.js`):** `data-sg-dismiss`, `data-sg-autodismiss="ms"`, `data-sg-loading`, `data-loading-label`, `data-sg-validate` (valida `required` y pone el error dentro de la celda: «Escriba su usuario.»; personalice con `data-msg-required`), `data-sg-clear`, `data-sg-select-all`, `data-sg-selected-count`, `data-sg-toggle-password` (+ `aria-controls`), `data-sg-caps-for`.

## 6. Convertir una página de Bootstrap a este sistema

| Hoy (Bootstrap) | Sistema |
|---|---|
| `<div class="container… mt-3"><h1>Título</h1> … botones` | `<div class="sg-sheet">` + `page_head.html`. |
| `<form class="d-flex"><input class="form-control" name="q">` o buscador con `oc_b` | `toolbar.html`. |
| `btn btn-primary` / `btn-danger` / `btn-secondary` | `sg-btn sg-btn--primary` / `--danger` / `--secondary`. (Las clases `btn-*` de Bootstrap ya se ven igual; migre igualmente, así hay un solo vocabulario.) |
| `btn btn-warning` / `btn-success` / `btn-info` para asignar/cambiar | `sg-btn sg-btn--secondary sg-btn--sm` (el color no es una jerarquía; la primaria es solo la acción principal). |
| `<table class="table table-hover">` con `<tr class="table-dark">` | `sg-table-wrap` > `sg-table`; `<thead><tr>` sin clases; columna **Nº** primero: `<th class="sg-col-n">Nº</th>` / `<td class="sg-col-n" data-label="Nº">{{ page_obj.start_index|add:forloop.counter0 }}</td>`; `data-label="…"` en cada `td` si usa `sg-table--stack`. |
| `<span class="badge bg-warning text-dark">` | `badge_estado.html` / `badge_prioridad.html`. |
| `<div class="mb-3"><label class="form-label">…<input class="form-control">` | `field.html` dentro de `sg-fields`. |
| `<select class="form-select">` | Dentro de formulario: celda con `<select>` (ver `field.html`, modo Django o markup a mano). Suelto: `class="sg-select"`. |
| `<input class="form-check-input">` | igual (`form-check-input` ya se dibuja como casilla cuadrada de tinta) dentro de `<div class="sg-check">` + `<label>`. |
| `<div class="modal fade">` de confirmar eliminación | `modal_confirm.html`. |
| Modal de formulario para registrar algo | Considere una página o un panel en la lámina (los modales solo para confirmar). Si lo conserva, use `.modal` estándar: ya se ve cuadrado, con línea de tinta. |
| `<div class="alert alert-…">` y bucle de `messages` | Bórrelo (lo hace `master.html`). Avisos propios de la página: `sg-alert sg-alert--danger` con ícono. |
| `<div class="toast … id="toastSeleccionar">` + `mostrarToast()` | `SGUM.toast('…', {kind:'warn'})`. |
| `<i class="fas fa-…">` / `bi bi-…` / emoji / glifos | `{% include 'partials/icon.html' with name='…' %}`. |
| `<div class="card">` como estructura | Quítelo: la lámina ya es el contenedor. Agrupe con `sg-section` o `sg-panel` (uno por nivel). |
| `onclick="return confirm('…')"` | `modal_confirm.html` (formulario POST con `{% csrf_token %}` cuando la acción modifica datos; el backend exige POST). |
| `text-white bg-dark rounded` en banners | Quítelos; el encabezado de lámina hace ese papel. |

Iconos disponibles: `bell user users logout menu plus edit trash search eye eye-off check x alert info clock chevron-down chevron-up chevron-left chevron-right arrow-left download upload filter image paperclip send map-pin wrench box chart inbox book help lock calendar file home refresh dots list`. Trazo de 1,75 sobre rejilla de 24, terminación cuadrada, uniones en inglete, sin relleno. ¿Necesita otro? Añada un `<symbol id="i-nombre">` a `partials/icons_sprite.html` con las mismas propiedades (no cambie las existentes) y anótelo aquí.

## 7. Reglas de contenido y de interfaz

**Tablas**
- Primera columna **Nº** (orden en pantalla; en listas paginadas continúe la numeración con `page_obj.start_index`). No es el id de base de datos.
- Estado y prioridad siempre con los parciales (texto + patrón). Nunca solo color.
- Fechas, cantidades, códigos y referencias van en monoespaciada (`sg-data`, `sg-mono`) y con cifras tabulares. Nombres, ubicaciones y descripciones, en la fuente normal.
- Cabecera fija por defecto (`sg-table-wrap` limita la altura y desplaza dentro). Para tablas cortas (<8 filas) use `sg-table-wrap--free`.
- Acciones de fila: máximo una visible («Editar» o «Asignar técnico»); el resto, botones de ícono con `aria-label` que nombre la fila («Eliminar incidencia 12»).
- Móvil: `sg-table--stack` si la tabla tiene ≤7 columnas y todas tienen `data-label`; si no, deje el desplazamiento horizontal dentro del contenedor. Nunca desborde la página.
- Lista vacía: `empty.html` con el siguiente paso; sin resultados de búsqueda: dígalo y ofrezca «Quitar búsqueda».

**Formularios**
- Celdas de cajetín (`sg-fields`), etiqueta corta en la celda, un campo por celda; 44 px o más de alto. Marque lo **opcional** (`optional=True`), no lo obligatorio.
- Un error por campo, dentro de la celda: qué falló y cómo corregirlo. Encima, si hay varios, un `sg-form-error` con el conteo («Corrija los 2 campos marcados»). Los `errores` y `valores` del backend (`backend-contract.md`) se pintan con `field.html` (`error=errores.ubicacion value=valores.ubicacion`).
- Botones al pie en `sg-form-actions`: primaria a la derecha con el verbo de la acción («Registrar incidencia», «Guardar cambios»), «Cancelar» como secundaria. Nada de «Enviar» ni «Aceptar».
- Contraseñas: `autocomplete="current-password"` / `new-password`, con ojo (`password=True`).

**Modales:** solo confirmaciones destructivas o irreversibles (`modal_confirm.html`), con título en forma de pregunta, consecuencia y botón que nombra la acción. El botón de peligro va a la derecha y «Cancelar» a la izquierda.

**Estados de todo control interactivo:** default, hover, focus (anillo de 2 px `--sg-focus`), active, disabled, loading, error. Los componentes `sg-*` ya los traen; si crea uno nuevo, defina los siete.

**Copy:** trato de usted, español, botones con verbo («Asignar técnico», «Retirar material»). Errores: problema + salida. `cliente` se muestra «Solicitante». Nombre: «SGUM-UCI».

## 8. Lo que NO se debe hacer

- Cargar nada de internet (CDN, Google Fonts, Font Awesome, Bootstrap Icons) ni usar emoji o glifos Unicode como íconos.
- Kicker o «eyebrow» sobre un título; numerar secciones (el Nº de fila sí); métricas «hero»; tarjetas de ícono + título + texto como estructura; tarjetas anidadas.
- `border-left`/`border-right` de color mayores a 1 px; degradados en texto; sombras de bloque o «glass»; sombras que no sean `--sg-shadow-pop`.
- Color como único portador de significado (estado, prioridad, error).
- Cian `--sg-cyan` como color de texto, botón o relleno (solo marcas de registro y estado activo).
- Monoespaciada en botones, etiquetas y textos corrientes.
- Modales para tareas que no exigen interrupción; `alert()` y `confirm()` del navegador.
- Poner scripts de otra página en `master.html`; duplicar el bucle de `messages`.
- Editar `static/vendor/**` o `static/sgum/**` desde una página (si falta algo del sistema, pídalo a FUNDACIÓN o extienda con una clase nueva en la propia plantilla con `<style>` mínimo, y anótelo).
- Pasar datos a JavaScript con `onclick="f('{{ texto }}')"`: use `data-*` y léalos desde JS.

## 9. Decisiones y supuestos tomados

- **Monoespaciada:** el boceto aprobado usaba monoespaciada en las etiquetas de celda y en el botón ACCEDER; COMMON.md la reserva para datos. Se aplicó COMMON.md: etiquetas y botones en la fuente del sistema (mayúsculas pequeñas con espaciado), monoespaciada solo en marcas de zona (A–H, 1–6), «VISTA 01 · ACCESO», «LÁMINA 01», Nº, fechas, cantidades y códigos.
- **Rótulo «SISTEMA»** sobre el nombre del sistema en el cajetín del boceto: retirado (es un «eyebrow» prohibido por craft-floor). El nombre es ahora el `h1` de la pantalla de acceso.
- **Zonas A–H / 1–6** solo en el acceso (según el boceto). En las pantallas de trabajo el marco se resuelve con la lámina y sus marcas de registro cian, sin regla de zonas (decorado sin función en una herramienta).
- **Pie de la aplicación:** cajetín de tres celdas (sistema, universidad y año, enlaces Inicio y Soporte). No se incluyó el correo `soporte@uci.cu` (sale del manual, sin confirmar que siga vigente).
- **Textos de 403/404/500** y su indicación «comuníquelo a la Dirección de Mantenimiento» son supuestos, igual que el marcador «¿Sin acceso? Solicite su cuenta a la Dirección de Mantenimiento.» del acceso.
- No hay tema oscuro: la hoja clara es la decisión (oficina y luz de día). `color-scheme: light` fijo.

## 10. Pendiente y deuda conocida

- Todas las pantallas salvo acceso, armazón y páginas de error siguen con su markup de Bootstrap (se ven coherentes, pero sin Nº de fila, celdas de cajetín, parciales ni modales de confirmar). Es el trabajo de la siguiente oleada.
- `static/js/notificaciones.js` sin tocar (lo hace otro agente); hoy pinta botones Bootstrap dentro de un `<a>` y usa `innerHTML`.
- `static/js/scripts.js` conserva la validación de `#registroForm` en su forma antigua (clases `is-invalid` de Bootstrap, que sí están vestidas). Al migrar el alta de usuarios a `data-sg-validate` + respuesta JSON del backend, elimine ese bloque.
- `field.html` en modo Django no añade `aria-describedby` ni `aria-invalid` al control (Django no lo permite desde la plantilla). Si un formulario lo necesita, hágalo en el `Form` (`widget.attrs`) o use el modo manual.
- Las pruebas de navegador opcionales `usuarios/tests/test_login_page.py` (Selenium, `SGUM_SELENIUM=1`) comprueban el markup **antiguo** del acceso (título «Login», `.text-prest`, `#togglePassword`, «Por favor llena este campo»). El nuevo: título «Acceso · SGUM-UCI», `h1.lg-name`, `#username`, `#password`, `[data-sg-toggle-password]`, error de credenciales en `.lg-alert`, errores de campo `.sg-field__msg` («Escriba su usuario.»).
- Ordenación de columnas: el sistema define cómo se ve (`aria-sort`, `sg-sort`); la lógica (parámetro `orden` del backend o JS de página) es de cada pantalla.
- Bootstrap sigue cargado completo (232 KB) por los modales, menús y toasts de las páginas sin migrar. Cuando todas estén migradas se puede valorar un Bootstrap reducido.
- Sin `collectstatic` ejecutado: `staticfiles/` no se tocó. Producción debe ejecutar `collectstatic` para publicar `vendor/`, `sgum/` e `img/`.
