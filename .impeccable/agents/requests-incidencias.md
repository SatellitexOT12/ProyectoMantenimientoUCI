# Peticiones del agente INCIDENCIAS

## Fundación (sgum.css)

1. **Radios sin elegir se pintan como marcados.** En `sgum.css` (sección 7.2) la regla
   `.form-check-input:checked, .form-check-input:indeterminate { background-color: var(--sg-ink); … }`
   también alcanza a los `input[type="radio"]` de un grupo sin ninguna opción marcada, porque el navegador
   los considera `:indeterminate`. Resultado: todas las opciones se ven rellenas de tinta.
   Propuesta: limitar `:indeterminate` a casillas: `.form-check-input[type="checkbox"]:indeterminate`.
   Mientras tanto, `sgum/pages/incidencias.css` trae una corrección local (`.form-check-input[type="radio"]:indeterminate:not(:checked)`)
   que solo se carga en las páginas de incidencias.
2. **Tabla con cabecera fija y despliegue de detalle.** `sg-table-wrap` limita la altura y desplaza dentro; una lista con filas
   desplegables funciona mejor con el desplazamiento de la página. En `incidencias.css` se desactiva a partir de 1280 px
   (`overflow: visible` + `thead th { top: var(--sg-nav-h) }`). Si otras listas lo necesitan, valdría una variante
   `sg-table-wrap--page` en la fundación.

## Backend

Ninguna petición obligatoria. Sugerencias:

- `_eliminar_incidencias` redirige con `redirigir_atras`; desde la pantalla de edición se envía `next` explícito para no volver a una página inexistente.
- La lista podría exponer por fila `n_materiales` para no depender del prefetch en la plantilla (hoy se usa `x.materialincidencia_set.all`, que ya está precargado).
