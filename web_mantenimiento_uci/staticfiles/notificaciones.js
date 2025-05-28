function markAsRead(notificationId) {
    fetch(`/notifications/${notificationId}/read/`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': '{{ csrf_token }}',
        'Content-Type': 'application/json'
      }
    })
    .then(response => response.json())
    .then(data => {
      if (data.status === 'success') {
        const element = document.querySelector(`[data-id="${notificationId}"]`);
        if (element) element.remove();

        // Actualizar el contador
        const countSpan = document.getElementById("notificationCount");
        let count = parseInt(countSpan.textContent);
        if (!isNaN(count) && count > 0) {
          countSpan.textContent = count - 1;
        }
      }
    });
  }