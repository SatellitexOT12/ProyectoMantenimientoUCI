/* SGUM-UCI · funciones heredadas que aún usan algunas páginas (validación del registro de usuario,
   selección múltiple, imagen en modal y borrado de incidencias).
   Se mantiene compatible con las páginas actuales y NO falla si la página no tiene esos elementos.
   Los comportamientos nuevos (toasts, «cargando», validación en celdas, contraseña) viven en sgum/sgum.js y togglepassword.js. */

/* ---------- Funciones globales que llaman las plantillas ---------- */

// Marcar / desmarcar todas las casillas .checkbox
function toggleCheckboxes(masterCheckbox) {
    document.querySelectorAll('.checkbox').forEach(function (checkbox) {
        checkbox.checked = masterCheckbox.checked;
        var tr = checkbox.closest ? checkbox.closest('tr') : null;
        if (tr) { tr.classList.toggle('is-selected', checkbox.checked); }
    });
}

// Guardar el id de la incidencia antes de abrir el modal
function setIncidenciaId(id) {
    var el = document.getElementById('incidencia_id');
    if (el) { el.value = id; }
}

// Abrir imagen en modal
function abrirImagen(url) {
    var img = document.getElementById('imagenEnFoco');
    if (img) { img.src = url; }
}

// Borrar las incidencias marcadas: crea un campo oculto por casilla y envía el formulario
function confirmarEliminacion() {
    var checkboxes = document.querySelectorAll('input[name="ids"]:checked');
    var form = document.getElementById('eliminar_incidencia');
    var contenedor = document.getElementById('checkboxes-seleccionados');
    if (!form || !contenedor) { return; }

    contenedor.innerHTML = '';

    if (checkboxes.length === 0) {
        var msg = 'Seleccione al menos una incidencia para eliminar.';
        if (window.SGUM) { window.SGUM.toast(msg, { kind: 'warn' }); } else { alert(msg); }
        return;
    }

    checkboxes.forEach(function (cb) {
        var input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'ids';
        input.value = cb.value;
        contenedor.appendChild(input);
    });

    form.submit();
}

/* ---------- Validación del formulario de registro de usuario (#registroForm) ---------- */
(function () {
    'use strict';
    if (window.__sgumLegacyScripts) { return; } // la página puede cargar este archivo dos veces
    window.__sgumLegacyScripts = true;

    document.addEventListener('DOMContentLoaded', function () {
        var camposValidacion = [
            { inputId: 'username', errorId: 'errorUsuario' },
            { inputId: 'name', errorId: 'errorNombre' },
            { inputId: 'lastname', errorId: 'errorApellido' }
        ];

        function validarCampoTexto(inputId, errorId) {
            var input = document.getElementById(inputId);
            var errorElement = document.getElementById(errorId);
            if (!input) { return true; }
            var valor = input.value.trim();

            // Letras, acentos, ñ y espacios; números solo en el usuario
            var regex = inputId === 'username'
                ? /^[a-zA-ZÀ-ÿñÑ\s0-9]+$/
                : /^[a-zA-ZÀ-ÿñÑ\s]+$/;

            function fallo(texto) {
                input.classList.add('is-invalid');
                input.classList.remove('is-valid');
                if (errorElement) { errorElement.textContent = texto; }
                return false;
            }

            if (valor === '') { return fallo('Este campo es obligatorio.'); }
            if (!regex.test(valor)) {
                return fallo(inputId === 'username'
                    ? 'Use solo letras y números, sin símbolos.'
                    : 'Use solo letras, sin números ni símbolos.');
            }

            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
            if (errorElement) { errorElement.textContent = ''; }
            return true;
        }

        var registro = document.getElementById('registroForm');
        if (registro) {
            registro.addEventListener('submit', function (e) {
                var formularioValido = true;

                camposValidacion.forEach(function (campo) {
                    if (!validarCampoTexto(campo.inputId, campo.errorId)) { formularioValido = false; }
                });

                var password = document.getElementById('password');
                var confirmPassword = document.getElementById('confirmPassword');
                var errorMessage = document.getElementById('error-message');
                if (password && confirmPassword) {
                    if (password.value !== confirmPassword.value) {
                        confirmPassword.classList.add('is-invalid');
                        confirmPassword.classList.remove('is-valid');
                        if (errorMessage) { errorMessage.style.display = 'block'; }
                        formularioValido = false;
                    } else {
                        confirmPassword.classList.remove('is-invalid');
                        confirmPassword.classList.add('is-valid');
                        if (errorMessage) { errorMessage.style.display = 'none'; }
                    }
                }

                if (!formularioValido) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                registro.classList.add('was-validated');
            });

            camposValidacion.forEach(function (campo) {
                var input = document.getElementById(campo.inputId);
                if (input) {
                    input.addEventListener('input', function () { validarCampoTexto(campo.inputId, campo.errorId); });
                }
            });
        }
    });
}());
