# Encargo común: rediseño completo de SGUM-UCI

Lee este archivo entero antes de empezar. Es el contexto compartido de todos los agentes que trabajan en paralelo en este repositorio.

## Qué es el proyecto

SGUM-UCI: sistema de gestión de mantenimiento de la Universidad de las Ciencias Informáticas (La Habana, Cuba). Django + plantillas renderizadas en servidor + Bootstrap 5. Raíz del repo: `D:\Proyectos\ProyectoMantenimiento\ProyectoMantenimientoUCI`. La app Django (donde está `manage.py`) es `web_mantenimiento_uci\`; su única app es `usuarios\` (vistas, modelos, plantillas en `usuarios\templates\`). Estáticos propios en `web_mantenimiento_uci\static\`.

**No toques `web_mantenimiento_uci\staticfiles\`** (salida vieja de collectstatic), **`media\`**, **`db.sqlite3`** ni nada fuera de tu propiedad de archivos. **No hagas `git commit`, `git push` ni cambies de rama** (estás en la rama `rediseno-plano-uci`; otros agentes editan a la vez en el mismo árbol de trabajo).

## Fuentes de verdad (léelas primero)

1. `PRODUCT.md` (raíz): usuarios, propósito, restricciones, voz, decisiones. Manda sobre cualquier suposición tuya.
2. Contrato de dirección del login: `.impeccable\surfaces\imiento-uci-usuarios-templates-login-html-5acc7dae.md` (mundo visual «Plano de la UCI»).
3. Reglas de calidad de Impeccable (léelas antes de editar cualquier UI):
   - `C:\Users\Antivist\.claude\plugins\cache\impeccable\impeccable\4.3.1\skills\impeccable\reference\craft-floor.md`
   - `...\reference\operate.md` (la aplicación entera es modo **Operar**)
   - Según tu tarea, también los de comando en la misma carpeta: `layout.md`, `typeset.md`, `clarify.md`, `harden.md`, `adapt.md`, `polish.md`, `distill.md`, `onboard.md`.
4. Si ya existen: `DESIGN.md` y `.impeccable\agents\foundation-handoff.md` (catálogo de clases y parciales del sistema de diseño) y `.impeccable\agents\backend-contract.md` (contexto, permisos y campos de las vistas).

## El mundo visual: «Plano de la UCI» (elegido por el usuario)

La aplicación es un plano de ingeniería de la UCI. Hoja blanco azulada, tinta azul UCI, retícula fina, cajetines, esquinas rectas, sin degradados ni sombras decorativas, marco con zonas de referencia. Los colores de partida están en el contrato del login (tinta `#0b4a7f`, hoja `#f3f6f9`, cian del logo `#2a94d4` solo para marcas y estado activo, retícula `#9db3c6`/`#c9d3dc`). El boceto aprobado del login está en el lienzo de Design: https://claude.ai/code/artifact/d9d26710-3145-44d2-803d-07e79ce66799 (láminas «1 · Plano de la UCI» y «móvil»); su fuente está en `C:\Users\Antivist\AppData\Local\Temp\claude\D--Proyectos-ProyectoMantenimiento-ProyectoMantenimientoUCI\2b9b204d-c6bf-449b-bb22-7dd479d17f56\scratchpad\canvas\Main.dc.html` y `PlanoMovil.dc.html` (HTML con estilos en línea; úsalos como referencia visual y de medidas).

El mundo se aplica con criterio de **Operar**: escaneo rápido, densidad, consistencia de componentes, estados completos. La expresión nunca oculta la tarea. La marca vive en los detalles precisos (cajetines de formulario, celdas, numeración de filas, marcas de registro), no en decorado.

Interpretación para pantallas de trabajo (guía, no receta):
- Cada página es una lámina: encabezado tipo cajetín (título, acciones, búsqueda) y contenido dentro de un marco de línea fina.
- Tablas: primera columna con número de orden, cifras tabulares, encabezado fijo, filas con estado legible **con texto y patrón, nunca solo color**. Monoespaciada solo para códigos, fechas, cantidades y referencias (datos), no para botones ni etiquetas corrientes.
- Formularios: celdas de cajetín (etiqueta pequeña + valor), campos de 44 px o más, errores que dicen qué falló y cómo corregirlo.
- En móvil: las tablas pasan a lista compacta o desplazan horizontalmente dentro de su contenedor; nunca desbordan la página.

## Restricciones no negociables

- **Solo intranet.** Prohibido cargar nada de internet (CDN, Google Fonts, etc.). Bootstrap/jQuery/Chart.js van locales en `static\vendor\`. Íconos: SVG propios (sprite), nada de Font Awesome ni Bootstrap Icons, nada de emoji ni glifos Unicode como íconos.
- **Español, trato de usted.** Botones nombran su acción («Registrar incidencia», no «Enviar»). Errores nombran el problema y la salida. El rol `cliente` se muestra siempre como **«Solicitante»**; el grupo de Django sigue llamándose `cliente`.
- **Nombre:** «SGUM-UCI». Universidad: «Universidad de las Ciencias Informáticas». Nada de «MainPage» ni «Mantenimiento UCI» como nombre.
- **Prohibiciones de la craft-floor** (resumen): sin kicker/eyebrow sobre encabezados, sin cards de icono+título+texto como estructura de página, sin cards anidadas, sin degradado en texto, sin `border-left`/`border-right` de color mayor a 1px, sin sombras duras de bloque, sin glass decorativo, sin métricas «hero», sin numerar secciones (salvo cuando el orden sea información, como el Nº de fila), sin modal para tareas que no exigen interrupción (los modales de confirmación destructiva sí son legítimos).
- Contraste mínimo 4.5:1 (texto) y 3:1 (texto grande y controles); foco de teclado visible; objetivos táctiles de 44 px.
- Movimiento: 150–250 ms, solo para comunicar estado, respetar `prefers-reduced-motion`.
- Django objetivo real: **4.2.19** (requirements.txt) con **PostgreSQL** en producción. El entorno de pruebas usa Django 5.2 + SQLite; escribe código compatible con 4.2 y portable entre motores.

## Entorno de pruebas (ya montado, fuera del repo)

Carpeta: `C:\Users\Antivist\AppData\Local\Temp\claude\D--Proyectos-ProyectoMantenimiento-ProyectoMantenimientoUCI\2b9b204d-c6bf-449b-bb22-7dd479d17f56\scratchpad\run\` (en bash: `/c/Users/Antivist/AppData/Local/Temp/claude/D--Proyectos-ProyectoMantenimiento-ProyectoMantenimientoUCI/2b9b204d-c6bf-449b-bb22-7dd479d17f56/scratchpad/run`). Llámala `$RUN`.

- Servidor: `nohup "$RUN/serve.sh" <PUERTO> > "$RUN/server-<PUERTO>.log" 2>&1 &` (usa TU puerto, indicado en tu encargo; con autorecarga de plantillas y Python). Detén el tuyo al terminar (PowerShell: `Get-CimInstance Win32_Process -Filter "Name='python.exe'" | ? { $_.CommandLine -match 'runserver 127.0.0.1:<PUERTO>' } | % { Stop-Process -Id $_.ProcessId -Force }`).
- Base SQLite de pruebas (copia, ya migrada, con datos de ejemplo): `$RUN\dev.sqlite3`. Ajustes de pruebas: `$RUN\sgum_dev.py` (importa los de la app y sustituye la base). **Es compartida entre agentes: no la borres ni la resetees**; tus datos de prueba añádelos con prudencia. Si cambias modelos, las migraciones se aplican con `manage.py migrate` bajo esos ajustes (variables `PYTHONPATH="$RUN;<ruta>\web_mantenimiento_uci"` y `DJANGO_SETTINGS_MODULE=sgum_dev`, intérprete `$RUN\venv\Scripts\python.exe`, ver `serve.sh`).
- Usuarios de prueba, contraseña `sgum1234`: `dev_admin` (administrador/despachador), `dev_tecnico`, `dev_almacen`, `dev_solicitante`. Para ver una página interna sin iniciar sesión añade `?as=<usuario>` a la URL (solo existe en los ajustes de pruebas).
- Capturas: `"$RUN/shot.sh" "http://127.0.0.1:<PUERTO>/incidencias/?as=dev_admin" salida.png 1440 900` (Edge sin cabeza) y otra a `390 844` para móvil. Guarda tus capturas en `$RUN\shots\<tu-agente>\`. Lee cada PNG con la herramienta Read para revisarla.
- Tests: `cd web_mantenimiento_uci` y `manage.py test` con las mismas variables de entorno.

## Cómo trabajar (pasadas acotadas)

Construye completo, inspecciona **una vez** con una ronda de capturas por lotes (escritorio y móvil juntos, y los estados clave: vacío, error, con datos), corrige todo lo que muestre en un solo lote, confirma con **como máximo una ronda más** y termina. Nada de bucles abiertos de pulido. Al final, ejecuta **una vez** el detector mecánico sobre lo que cambiaste:
`"C:\Users\Antivist\.claude\plugins\cache\impeccable\impeccable\4.3.1\skills\impeccable\scripts\impeccable.cmd" detect --json <archivos html/css cambiados>` y corrige lo mecánico.

No puedes preguntar al usuario. Ante una duda de producto, elige la opción más segura y conservadora, márcala como supuesto y déjala en «PREGUNTAS PARA EL USUARIO» de tu informe; la lanzadera se la traslada al usuario.

## Informe final (máximo ~350 palabras, en español)

1. Qué cambiaste (archivos por grupo) y qué decisiones tomaste.
2. Qué verificaste y cómo (puertos, capturas, tests) y qué quedó sin verificar.
3. Deuda o pendientes que otro agente debe recoger (peticiones al backend, parciales que faltan).
4. PREGUNTAS PARA EL USUARIO.
