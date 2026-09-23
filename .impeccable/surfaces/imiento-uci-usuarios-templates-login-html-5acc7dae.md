---
version: 1
slug: "imiento-uci-usuarios-templates-login-html-5acc7dae"
primary_target: "web_mantenimiento_uci/usuarios/templates/login.html"
related_targets: []
---

## Scope

Superficie: pantalla de acceso (`login.html`) y, desde ella, el mundo visual de toda la aplicación. Modo: Operar (la tarea es autenticarse rápido; es además la primera lámina de la identidad SGUM-UCI). Fidelidad: pantalla lista para producción, sustituye `login.html` y `log.css`. Redesign: se reemplaza el mundo visual anterior (Bootstrap sin personalizar sobre foto oscurecida); se conservan nombre, logo, lema, foto de la valla, voz de usted y restricción de solo intranet.

Elección del usuario: opción 1, «Plano de la UCI» (lienzo de Design, artboard `Main` y `PlanoMovil`).

## Direction contract

THESIS: El acceso es la primera lámina de un plano de la UCI. La foto de la valla es la vista principal, sin nada encima, y el formulario es el cajetín de la lámina. Rechaza la tarjeta flotante sobre una foto oscurecida.

OWN-WORLD: Hoja blanco azulada (#f3f6f9), tinta azul UCI (#0b4a7f) para líneas y texto, cian del logo (#2a94d4) solo para marcas de registro y estado activo, gris de retícula (#9db3c6 / #c9d3dc). Marco de doble línea con zonas de referencia A–H y 1–6, celdas de cajetín con etiqueta pequeña y valor, esquinas rectas, sin degradados ni sombras decorativas. Tipografía del sistema; monoespaciada solo para referencias, códigos y datos; cifras tabulares. Sin CDN: todo local.

STORY: Quien llega entiende en un segundo que es el sistema de mantenimiento de la UCI (SGUM-UCI), escribe usuario y contraseña y accede. Si no tiene acceso sabe a quién pedirlo. Si falla, el mensaje dice qué falló y qué hacer.

FIRST VIEWPORT: Escritorio 1440×900: marco de plano a 20 px del borde; la vista con la foto ocupa unos dos tercios a la izquierda; a la derecha un cajetín de 380 px con logo, nombre del sistema, celda Usuario, celda Contraseña con ojo, botón ACCEDER a todo el ancho, ayuda de acceso y pie. Móvil 390×844: la foto llena el viewport y el cajetín queda anclado abajo, con campos de 44 px o más.

FORM: Plano de la UCI (cajetín de lámina de ingeniería), candidato 4 de la lista propia, asignado por el sorteo, seed key 1a38519b.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Decisiones abiertas

- El texto de ayuda de acceso («Solicite su cuenta a la Dirección de Mantenimiento») es un marcador: no está confirmado cómo se obtienen las cuentas (la respuesta fue «con su cuenta institucional de la UCI», pero hoy el sistema crea cuentas locales).
- No hay recuperación de contraseña en el sistema; el login no la promete.
- «Lámina 01» del pie del cajetín es parte del boceto aprobado; en el resto de la aplicación no se numeran las páginas.
