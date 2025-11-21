// Crear nueva tarea

function guardarNuevaTarea() {
    const form = document.getElementById('formNuevaTarea');
    const formData = new FormData(form);
    
    // Validar que las unidades planificadas sean mayor a 0
    const unitsPlanned = parseFloat(formData.get('units_planned') || 0);
    if (unitsPlanned <= 0) {
        alert('⚠️ Las unidades planificadas deben ser mayores a 0');
        return;
    }
    
    // Validar que se haya seleccionado un proyecto
    const project = formData.get('project');
    if (!project) {
        alert('⚠️ Por favor selecciona un proyecto');
        return;
    }
    
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
            // Mostrar errores específicos
            let errorMsg = data.error || 'Error al guardar la tarea';
            
            if (data.error_messages && data.error_messages.length > 0) {
                errorMsg = 'Errores de validación:\n\n' + data.error_messages.join('\n');
            } else if (data.error_details) {
                const details = [];
                for (const [field, errors] of Object.entries(data.error_details)) {
                    details.push(`${field}: ${errors.join(', ')}`);
                }
                if (details.length > 0) {
                    errorMsg = 'Errores de validación:\n\n' + details.join('\n');
                }
            }
            
            alert(errorMsg);
            console.error('Errores del formulario:', data);
        }
    })
    .catch(error => {
        console.error('Error de red:', error);
        alert('Error de conexión al guardar la tarea');
    });
}