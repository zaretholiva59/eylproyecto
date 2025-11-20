// Crear nueva tarea

function guardarNuevaTarea() {
    const form = document.getElementById('formNuevaTarea');
    const formData = new FormData(form);
    
    fetch('/tasks/crear/', {
        method: 'POST',
        body: formData,
        headers: { 'X-CSRFToken': csrfToken }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            cerrarModal();
            location.reload();
        } else {
            alert('Error: ' + data.error);
        }
    });
}