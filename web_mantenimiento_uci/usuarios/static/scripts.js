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

function toggleCheckboxes(masterCheckbox) {
const checkboxes = document.querySelectorAll('.checkbox');
checkboxes.forEach((checkbox) => {
    checkbox.checked = masterCheckbox.checked;
});

}
