$(document).ready(function() {
    function cargarNotificaciones() {
        $.ajax({
            url: "/obtener_notificaciones/",  // Asegúrate de que esta URL sea correcta
            method: 'GET',
            success: function(data) {
                const dropdown = $('#notificationDropdown');
                dropdown.empty(); // Limpiar notificaciones anteriores

                if (data.length > 0) {
                    // Recorrer las notificaciones y agregarlas al dropdown
                    data.forEach(function(notificacion) {
                        dropdown.append(
                            `<li>
                                <a class="dropdown-item" href="#">${notificacion.mensaje} - ${new Date(notificacion.fecha_creacion).toLocaleString()}</a>
                                <button onclick="marcarComoLeida(${notificacion.id})" class="btn btn-sm btn-success">Marcar como leída</button>
                            </li>`
                        );
                    });
                    $('#notificationCount').text(data.length); // Actualizar contador
                } else {
                    dropdown.append('<li><a class="dropdown-item" href="#">No hay notificaciones nuevas.</a></li>');
                    $('#notificationCount').text('0');
                }
            },
            error: function() {
                $('#notificationDropdown').html('<li><a class="dropdown-item" href="#">Error al cargar notificaciones.</a></li>');
            }
        });
    }

    // Cargar notificaciones al abrir el dropdown
    $('#navbarDropdown').on('click', function() {
        cargarNotificaciones();
    });

    // Cargar notificaciones al cargar la página
    cargarNotificaciones();
});

// Función para marcar una notificación como leída
function marcarComoLeida(notificacionId) {
    $.ajax({
        url: `/marcar_leida/${notificacionId}/`,  // Asegúrate de que esta URL sea correcta
        method: 'POST',
        headers: {
            'X-CSRFToken': '{{ csrf_token }}'  // Necesitas incluir el token CSRF
        },
        success: function() {
            cargarNotificaciones(); // Recargar notificaciones después de marcar como leída
        },
        error: function() {
            alert('Error al marcar como leída.');
        }
    });
}