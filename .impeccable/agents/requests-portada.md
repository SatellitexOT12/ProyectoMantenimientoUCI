# Peticiones de PORTADA, SOPORTE Y NOTIFICACIONES

Cada una tiene una solución local ya aplicada; la petición la mejora. Ninguna bloquea.

## Al backend (`views.py`, vista `main`)

1. **Almacenero: existencias bajas y últimas asignaciones.** El contrato solo da `materiales_resumen = {total, agotados}`. La portada del almacenero necesita las listas.
   - `materiales_bajos`: administrador y almacenero; `Material.objects.filter(cantidad__lte=UMBRAL).order_by('cantidad', 'nombre')[:8]`. Sugerencia: `UMBRAL = 5` (el modelo no guarda un mínimo por material; si se quiere uno por material hace falta un campo nuevo y migración). Vacío (`[]`) para los demás.
   - `asignaciones_recientes`: administrador y almacenero; `MaterialIncidencia.objects.select_related('material').order_by('-fecha_asignacion', '-id')[:8]`.
   - **Ya está preparado en `main.html`**: pinta `materiales_bajos` (tabla con «Actualizar existencia» → `editar_material`) y `asignaciones_recientes` en cuanto existan en el contexto. Mientras no lleguen, el almacenero ve un aviso con `materiales_resumen.agotados` y la lista de incidencias abiertas donde asignar materiales.
   - Esas dos ramas no se pudieron ver con datos reales (la vista no las envía); se probó solo que la plantilla no falla sin ellas.
2. **Técnico: orden por prioridad.** `incidencias_asignadas` sale ordenada por fecha (más reciente primero) y recortada a 8, así que una incidencia alta y antigua puede quedar fuera. Propuesta: `order_by('-prioridad', 'fecha', 'id')[:8]` (la plantilla ya reordena por prioridad lo que reciba).
3. **Soporte pendiente.** `soporte_pendientes` es solo un número (estado *pendiente*, no «sin responder»). Propuesta opcional: `soporte_recientes` con las 5 más antiguas pendientes (`select_related('usuario')`) para listarlas en la portada con «Responder» directo.

## Al backend (`incidencias`)

4. **Filtro exacto por número.** Los accesos directos de la portada («Asignar técnico», «Asignar materiales», «Ver») abren `/incidencias/?q=<n.º>`; `q` también busca en fechas y textos, así que un número corto (p. ej. 8) trae más de una fila. Propuesta: parámetro `?id=<n>` que filtra por `pk` exacto y que la portada usaría en su lugar. (Coordinar con quien mantenga la lista de incidencias.)

## Al backend (`detalle_solicitud`)

5. **Mensaje rechazado.** Ante un mensaje vacío o de más de 2000 caracteres, la vista responde con `messages.error` y **redirige**: el texto escrito se pierde. Solución local: `soporte.js` guarda el borrador en `sessionStorage` y lo recupera con un aviso. Propuesta: no redirigir cuando hay error; volver a renderizar (200) con `valores = {'mensaje': ...}` y `errores = {'mensaje': ...}` para que la plantilla pinte el error dentro de la celda.
6. **Confirmación de envío.** El envío correcto no emite mensaje. La plantilla lo compensa con un aviso «Mensaje enviado.» (por JS). Alternativa: `messages.success(request, "Su mensaje fue enviado.")`; habría que quitar entonces el aviso de `soporte.js`.

## A la fundación (`sgum.css`)

7. **Estilos de la lista de notificaciones.** `notificaciones.js` inyecta un `<style id="sgum-notif-css">` con las clases `nt-*` (enlace, línea de hora y botones de cada notificación), porque la campana está en todas las páginas y `sgum.css` no tiene esas reglas. Propuesta: mover ese bloque a la sección 15 de `sgum.css` y quitar la inyección.

## Contenido

8. **Documentación desactualizada** (`static/docs/*.pdf` y el ZIP). Hablan de «cliente» (ahora «Solicitante»), de recuperación de contraseña y de secciones que no existen. La portada los enlaza con una nota que avisa de posibles diferencias; conviene regenerarlos. Los tamaños (95, 92, 73 y 251 KB) están escritos a mano en `main.html`.
9. **Correo de soporte.** `soporte@uci.cu` sale solo del manual; la portada lo ofrece como enlace `mailto:` en la ayuda. Confirmar que sigue vigente.
