# Imágenes derivadas

| Archivo | Origen | Tratamiento |
|---|---|---|
| `portada-valla.jpg` | `static/portada_fidel_2.jpeg` (2560×1920, 1,1 MB; el original se conserva) | Reducida a 1600×1200, JPEG calidad 78 (unos 350 KB). Sin recortes, filtros ni capas. Es la foto de la valla de la pantalla de acceso. |
| `logo-marca.png` | `static/logoSGUM.png` (500×500) | Recorte 194×194 del hexágono del logo, sin retoque. Se usa como marca en la barra superior y como ícono de pestaña. El logo completo (`logoSGUM.png`) sigue siendo el de la pantalla de acceso. |

Ambas se generaron con PowerShell y `System.Drawing` (interpolación bicúbica de alta calidad).
