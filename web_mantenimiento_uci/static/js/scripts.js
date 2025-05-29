document.addEventListener('DOMContentLoaded', function() {
    // Configuración de campos a validar
    const camposValidacion = [
        {inputId: 'username', errorId: 'errorUsuario'},
        {inputId: 'name', errorId: 'errorNombre'},
        {inputId: 'lastname', errorId: 'errorApellido'},
        
    ];

    // Función de validación para campos de texto
    function validarCampoTexto(inputId, errorId) {
        const input = document.getElementById(inputId);
        const errorElement = document.getElementById(errorId);
        const valor = input.value.trim();
        
        // Expresión regular que permite letras, números (solo para username), espacios, acentos y ñ/Ñ
        const regex = inputId === 'username' 
            ? /^[a-zA-ZÀ-ÿ\u00f1\u00d1\s0-9]+$/  // Permite números solo en username
            : /^[a-zA-ZÀ-ÿ\u00f1\u00d1\s]+$/;   // No permite números en name y lastname
        
        if (valor === '') {
            input.classList.add('is-invalid');
            input.classList.remove('is-valid');
            errorElement.textContent = 'Este campo es obligatorio';
            return false;
        }
        
        if (!regex.test(valor)) {
            input.classList.add('is-invalid');
            input.classList.remove('is-valid');
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
        
        // Validar campos de texto
        camposValidacion.forEach(campo => {
            if (!validarCampoTexto(campo.inputId, campo.errorId)) {
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
        document.getElementById(campo.inputId).addEventListener('input', function() {
            validarCampoTexto(campo.inputId, campo.errorId);
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


    // Función para setear el ID de la incidencia antes de abrir el modal
    function setIncidenciaId(id) {
        document.getElementById('incidencia_id').value = id;
    }

    // Abrir imagen en modal
    function abrirImagen(url) {
        document.getElementById('imagenEnFoco').src = url;
    }

    
    function confirmarEliminacion() {

        console.log("La función confirmarEliminacion() se ha ejecutado"); // <--- Añadimos esto

        // Obtener todos los checkboxes marcados
        const checkboxes = document.querySelectorAll('input[name="ids"]:checked');
        const form = document.getElementById('eliminar_incidencia');
        const contenedor = document.getElementById('checkboxes-seleccionados');

        // Limpiar campos anteriores
        contenedor.innerHTML = '';

        // Si no hay ninguno seleccionado, mostrar alerta
        if (checkboxes.length === 0) {
            alert("Por favor, selecciona al menos una incidencia para eliminar.");
            return;
        }

        // Crear inputs ocultos por cada checkbox seleccionado
        checkboxes.forEach(cb => {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'ids';
            input.value = cb.value;
            contenedor.appendChild(input);
        });

        // Enviar formulario
        form.submit();
    }


