document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('registroForm');
    const fechaInicio = document.getElementById('fechaInicio');
    const fechaFin = document.getElementById('fechaFin');
    const errorInicio = document.getElementById('errorFechaInicio');
    const errorFin = document.getElementById('errorFechaFin');

    // Validación en tiempo real
    fechaInicio.addEventListener('change', validarFechas);
    fechaFin.addEventListener('change', validarFechas);

    // Validación al enviar el formulario
    form.addEventListener('submit', function(e) {
        if (!validarFechas()) {
            e.preventDefault();
            e.stopPropagation();
        }
        form.classList.add('was-validated');
    });

    function validarFechas() {
        let valido = true;
        
        // Resetear estados
        fechaInicio.classList.remove('is-invalid');
        fechaFin.classList.remove('is-invalid');
        errorInicio.textContent = '';
        errorFin.textContent = '';

        // Validar que ambas fechas tengan valor
        if (!fechaInicio.value) {
            fechaInicio.classList.add('is-invalid');
            errorInicio.textContent = 'Por favor ingrese la fecha de inicio';
            valido = false;
        }

        if (!fechaFin.value) {
            fechaFin.classList.add('is-invalid');
            errorFin.textContent = 'Por favor ingrese la fecha de fin';
            valido = false;
        }

        // Si ambas tienen valor, compararlas
        if (fechaInicio.value && fechaFin.value) {
            const inicio = new Date(fechaInicio.value);
            const fin = new Date(fechaFin.value);
            
            if (inicio > fin) {
                fechaInicio.classList.add('is-invalid');
                fechaFin.classList.add('is-invalid');
                errorInicio.textContent = 'La fecha de inicio no puede ser mayor que la de fin';
                errorFin.textContent = 'La fecha de fin no puede ser menor que la de inicio';
                valido = false;
            }
        }

        // Marcar como válidos si todo está correcto
        if (valido) {
            fechaInicio.classList.remove('is-invalid');
            fechaFin.classList.remove('is-invalid');
            fechaInicio.classList.add('is-valid');
            fechaFin.classList.add('is-valid');
        }

        return valido;
    }
});