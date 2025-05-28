document.addEventListener('DOMContentLoaded', function() {
    // Configuración de campos a validar
    const camposValidacion = [
        {inputId: 'username', errorId: 'errorUsuario', tipo: 'texto'},
        {inputId: 'cantidad', errorId: 'errorCantidad', tipo: 'numero'}
    ];

    // Función de validación mejorada
    function validarCampo(inputId, errorId, tipo) {
        const input = document.getElementById(inputId);
        const errorElement = document.getElementById(errorId);
        const valor = input.value;
        
        if (tipo === 'numero') {
            // Validación para cantidad (números enteros positivos)
            const numero = parseInt(valor);
            const esValido = !isNaN(numero) && numero > 0;
            
            if (valor === '' || isNaN(numero)) {
                input.classList.add('is-invalid');
                errorElement.textContent = 'Este campo es obligatorio';
                return false;
            }
            
            if (!esValido) {
                input.classList.add('is-invalid');
                errorElement.textContent = 'Debe ser un número mayor a 0';
                return false;
            }
            
            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
            errorElement.textContent = '';
            return true;
        }
        else if (tipo === 'texto') {
            // Validación para username (letras, números y espacios)
            const valorTrimmed = valor.trim();
            const regex = /^[a-zA-ZÀ-ÿñÑ0-9\s]+$/;
            
            if (valorTrimmed === '') {
                input.classList.add('is-invalid');
                errorElement.textContent = 'Este campo es obligatorio';
                return false;
            }
            
            if (!regex.test(valorTrimmed)) {
                input.classList.add('is-invalid');
                errorElement.textContent = 'No se permiten caracteres especiales';
                return false;
            }
            
            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
            errorElement.textContent = '';
            return true;
        }
    }

    // Validación del formulario al enviar
    document.getElementById('registroForm').addEventListener('submit', function(e) {
        let formularioValido = true;
        
        // Validar campos específicos
        camposValidacion.forEach(campo => {
            if (!validarCampo(campo.inputId, campo.errorId, campo.tipo)) {
                formularioValido = false;
            }
        });
        
        // Validar el select (validación nativa de Bootstrap)
        const select = document.getElementById('tipo_material');
        if (select.value === '') {
            select.classList.add('is-invalid');
            formularioValido = false;
        } else {
            select.classList.remove('is-invalid');
            select.classList.add('is-valid');
        }
        
        if (!formularioValido) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        this.classList.add('was-validated');
    });

    // Validación en tiempo real para los campos
    camposValidacion.forEach(campo => {
        const input = document.getElementById(campo.inputId);
        
        input.addEventListener('input', function() {
            if (campo.tipo === 'numero') {
                // Limpiar cualquier caracter no numérico
                this.value = this.value.replace(/[^0-9]/g, '');
                // Asegurar que no sea negativo
                if (parseInt(this.value) < 0) {
                    this.value = '';
                }
            }
            validarCampo(campo.inputId, campo.errorId, campo.tipo);
        });
    });

    // Validación en tiempo real para el select
    document.getElementById('tipo_material').addEventListener('change', function() {
        if (this.value !== '') {
            this.classList.remove('is-invalid');
            this.classList.add('is-valid');
        }
    });
});



//Seleccionar todos los checkbox
function toggleCheckboxes(masterCheckbox) {
const checkboxes = document.querySelectorAll('.checkbox');
checkboxes.forEach((checkbox) => {
    checkbox.checked = masterCheckbox.checked;
});
}

//Funcion para abrir la imangen de la lista de incidencia 
function abrirImagen(url) {
    // Asignar la URL de la imagen al modal
    document.getElementById('imagenEnFoco').src = url;

    // Mostrar el modal
}


$(document).ready(function() {
    function cargarNotificaciones() {
        $.ajax({
            url: "{% url 'obtener_notificaciones' %}",
            method: 'GET',
            success: function(data) {
                const dropdown = $('#notificationDropdown');
                dropdown.empty(); // Limpiar notificaciones anteriores

                if (data.length > 0) {
                    data.forEach(function(notificacion) {
                        dropdown.append(
                            `<li><a class="dropdown-item" href="#">${notificacion.mensaje} - ${new Date(notificacion.fecha_creacion).toLocaleString()}</a></li>`
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


