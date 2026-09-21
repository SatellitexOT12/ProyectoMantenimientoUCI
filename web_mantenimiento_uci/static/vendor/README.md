# Librerías de terceros (locales)

SGUM-UCI funciona solo dentro de la intranet de la UCI: ninguna librería se carga desde internet. Todo lo de esta carpeta se descargó una vez (jsDelivr) y se sirve desde el propio sistema.

| Archivo | Librería | Versión | Licencia |
|---|---|---|---|
| `bootstrap.min.css` | Bootstrap | 5.3.3 | MIT |
| `bootstrap.bundle.min.js` | Bootstrap (incluye Popper) | 5.3.3 | MIT |
| `jquery.min.js` | jQuery | 3.7.1 | MIT |
| `chart.umd.min.js` | Chart.js (build UMD, ya minificado) | 4.4.7 | MIT |

Cambios respecto a los originales: solo se eliminó la línea final `sourceMappingURL` (evita peticiones 404 al abrir las herramientas de desarrollo). Los avisos de copyright y licencia de cada archivo se conservan.

El aspecto de Bootstrap se sustituye en `static/sgum/` (`tokens.css` y `sgum.css`); no se edita nada aquí. Para actualizar una librería, descargue la nueva versión con el mismo nombre de archivo y compruebe las pantallas con modales, menús desplegables y gráficos.
