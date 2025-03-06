
const togglePassword = document.querySelector('#togglePassword');
const password = document.querySelector('#password');

togglePassword.addEventListener('click', function () {
      // Cambiar el tipo de input entre "password" y "text"
    const type = password.getAttribute('type') === 'password' ? 'text' : 'password';
    password.setAttribute('type', type);

      // Cambiar el ícono del ojo
    this.querySelector('i').classList.toggle('bi-eye');
    this.querySelector('i').classList.toggle('bi-eye-slash');
});




//Verificar contraseñas
document.getElementById("registroForm").addEventListener("submit", function(event) {
    const password = document.getElementById("password").value;
    const confirmPassword = document.getElementById("confirmPassword").value;
    const errorMessage = document.getElementById("error-message");

    if (password !== confirmPassword) {
        errorMessage.style.display = "block"; // Muestra el mensaje de error
        event.preventDefault(); // Detiene el envío del formulario
    } else {
        errorMessage.style.display = "none"; // Oculta el mensaje si todo está correcto
        alert("¡Registro exitoso!");
    }
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






