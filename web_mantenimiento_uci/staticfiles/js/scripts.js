document.addEventListener('DOMContentLoaded', function() {
    // Configuración de campos a validar
    const camposValidacion = [
        {inputId: 'username', errorId: 'errorUsuario'},
        {inputId: 'name', errorId: 'errorNombre'},
        {inputId: 'lastname', errorId: 'errorApellido'},
        {inputId: 'cantidad', errorId: 'errorCantidad', tipo: 'numero'}
    ];
    function validarCampo(inputId, errorId, tipo = 'texto') {
        const input = document.getElementById(inputId);
        const errorElement = document.getElementById(errorId);
        const valor = input.value.trim();
        
        if (tipo === 'numero') {
            // Validación para cantidad (números enteros positivos)
            const esNumero = /^[0-9]+$/.test(valor) && parseInt(valor) > 0;
            
            if (valor === '') {
                input.classList.add('is-invalid');
                errorElement.textContent = 'Este campo es obligatorio';
                return false;
            }
            
            if (!esNumero) {
                input.classList.add('is-invalid');
                errorElement.textContent = 'Solo se permiten números enteros positivos';
                return false;
            }
            
            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
            errorElement.textContent = '';
            return true;
        }
        
        // Resto de tu validación original para texto...
        const regex = inputId === 'username' 
            ? /^[a-zA-ZÀ-ÿ\u00f1\u00d1\s0-9]+$/
            : /^[a-zA-ZÀ-ÿ\u00f1\u00d1\s]+$/;
        
        if (valor === '') {
            input.classList.add('is-invalid');
            errorElement.textContent = 'Este campo es obligatorio';
            return false;
        }
        
        if (!regex.test(valor)) {
            input.classList.add('is-invalid');
            errorElement.textContent = inputId === 'username' 
                ? 'No se permiten caracteres especiales' 
                : 'No se permiten caracteres especiales ni números';
            return false;
        }
        
        input.classList.remove('is-invalid');
        input.classList.add('is-valid');
        errorElement.textContent = '';
        return true;
    }

    // Validación del formulario al enviar
    document.getElementById('registroForm').addEventListener('submit', function(e) {
        let formularioValido = true;
        
        camposValidacion.forEach(campo => {
            if (!validarCampo(campo.inputId, campo.errorId, campo.tipo)) {
                formularioValido = false;
            }
        });
        
        // Validar contraseñas (añadiendo esta funcionalidad extra)
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        const errorMessage = document.getElementById('error-message');
        
        if (password !== confirmPassword) {
            document.getElementById('confirmPassword').classList.add('is-invalid');
            document.getElementById('confirmPassword').classList.remove('is-valid');
            errorMessage.style.display = 'block';
            formularioValido = false;
        } else {
            document.getElementById('confirmPassword').classList.remove('is-invalid');
            document.getElementById('confirmPassword').classList.add('is-valid');
            errorMessage.style.display = 'none';
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
            // Para el campo cantidad, limpia caracteres no numéricos
            if (campo.tipo === 'numero') {
                this.value = this.value.replace(/[^0-9]/g, '');
            }
            validarCampo(campo.inputId, campo.errorId, campo.tipo);
        });
    });

    // Función para mostrar/ocultar contraseña
    document.getElementById('togglePassword').addEventListener('click', function() {
        const passwordInput = document.getElementById('password');
        const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordInput.setAttribute('type', type);
        this.querySelector('i').classList.toggle('bi-eye-slash');
    });

    document.getElementById('togglePassword2').addEventListener('click', function() {
        const confirmPasswordInput = document.getElementById('confirmPassword');
        const type = confirmPasswordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        confirmPasswordInput.setAttribute('type', type);
        this.querySelector('i').classList.toggle('bi-eye-slash');
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


