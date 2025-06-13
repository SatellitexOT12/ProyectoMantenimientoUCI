document.addEventListener('DOMContentLoaded', function () {
    

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


