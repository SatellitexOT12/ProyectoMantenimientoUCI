function markAsRead(notificationId) {
  console.log("Marcando como leída:", notificationId);
  console.log("CSRF Token:", csrftoken);

  fetch(`/notifications/${notificationId}/read/`, {
    method: 'POST',
    headers: {
  'X-CSRFToken': csrftoken,
  'Content-Type': 'application/json'
}
  })
  .then(response => response.json())
  .then(data => {
    if (data.status === 'success') {
      const element = document.querySelector(`[data-id="${notificationId}"]`);
      if (element) {
          element.classList.add("read"); // Puedes usar esto para cambiar color, opacidad, etc.
        }

      const countSpan = document.getElementById("notificationCount");
      let count = parseInt(countSpan.textContent);
      if (!isNaN(count) && count > 0) {
        countSpan.textContent = count - 1;
      }
    }
  });
}

  function loadNotifications() {
    fetch(NOTIFICATIONS_URL)
      .then(response => response.json())
      .then(data => {
        const notifications = JSON.parse(data.notifications);
        const dropdown = document.getElementById("notificationDropdown");
        const countSpan = document.getElementById("notificationCount");

        let unreadCount = 0;
        dropdown.innerHTML = ''; // Limpiar contenido anterior

        if (notifications.length === 0) {
          dropdown.innerHTML = '<li class="dropdown-item text-muted">No hay notificaciones</li>';
          countSpan.textContent = 0;
          return;
        }

        notifications.forEach(noti => {
          const fields = noti.fields;

          if (!fields.is_read) unreadCount++;

          const item = document.createElement('li');
          item.className = 'dropdown-item notification' + (fields.is_read ? ' read' : '');
          item.setAttribute('data-id', noti.pk);

          item.innerHTML = `
          <a href="/${fields.urlAsociated}" id="irahi"> ir ahí </a>
            <div class="d-flex justify-content-between align-items-center">
              <span>${fields.message}</span>
              <button class="btn btn-sm btn-outline-primary" onclick="markAsRead(${noti.pk})">Marcar como leída</button>
              <button class="btn btn-sm btn-outline-danger ms-2 delete-notification" title="Eliminar">×</button>
            </div>
          `;
          const deleteButton = item.querySelector(".delete-notification");
          const irahi =  item.querySelector("#irahi");
          //Eliminar desde ir -ahi
          irahi.onclick= function deletefromA (){
            const notificationId = item.getAttribute("data-id");
          // Eliminar del DOM
          item.remove();
          deleteNotification(notificationId);
          }
          //Eliminar desde el boton eliminar
        deleteButton.addEventListener("click", function () {
          const notificationId = item.getAttribute("data-id");

          // Eliminar del DOM
          item.remove();

          
          deleteNotification(notificationId);
        });
    
          dropdown.appendChild(item);
        });
        

        countSpan.textContent = unreadCount;
      });
  }
  
  // Carga inicial y refresco automático cada X segundos (ej: 30 seg)
  document.addEventListener("DOMContentLoaded", () => {
    loadNotifications();
    setInterval(loadNotifications, 30000); // cada 30 segundos
  });

  function deleteNotification(notificationId) {
  

  fetch(`/notifications/${notificationId}/delete/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": csrftoken,
      "Content-Type": "application/json"
    }
  })
  .then(response => response.json())
  .then(data => {
    if (data.status === "success") {
      console.log("Notificación eliminada del servidor");
    } else {
      console.error("Error al eliminar del servidor");
    }
  });
}