// ✨ NUEVA FUNCIÓN: Guardar tarea en BD (para sub-tareas desde lightbox)
function guardarTareaEnBD(task) {
    // Obtener el proyecto actual desde el URL
    const urlPath = window.location.pathname;
    const projectMatch = urlPath.match(/\/gantt\/([^\/]+)\/?$/);
    const projectId = projectMatch ? projectMatch[1] : null;
    
    if (!projectId) {
        console.error('❌ No se pudo obtener el proyecto actual del URL');
        return;
    }
    
    console.log('📤 Guardando tarea en BD:', task);
    console.log('📂 Proyecto:', projectId);
    
    // Preparar datos
    const formData = new FormData();
    formData.append('project', projectId);
    formData.append('title', task.text);
    formData.append('units_planned', 10); // Valor por defecto
    formData.append('planned_start', gantt.date.date_to_str("%Y-%m-%d %H:%i")(task.start_date));
    formData.append('planned_end', gantt.date.date_to_str("%Y-%m-%d %H:%i")(task.end_date));
    
    // ✨ Si tiene parent, incluirlo
    if (task.parent) {
        formData.append('parent', task.parent);
        console.log('👶 Sub-tarea de:', task.parent);
    }
    
    // Enviar a backend
    fetch('/tasks/crear/', {
        method: 'POST',
        body: formData,
        headers: { 'X-CSRFToken': csrfToken }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('✅ Tarea guardada en BD con ID:', data.task_id);
            
            // ✨ CRÍTICO: Actualizar el ID temporal con el ID real de la BD
            const tempId = task.id;
            gantt.changeTaskId(tempId, data.task_id);
            
            console.log(`🔄 ID actualizado: ${tempId} → ${data.task_id}`);
        } else {
            console.error('❌ Error guardando tarea:', data.error);
            alert('Error al guardar: ' + data.error);
            // Eliminar la tarea temporal del Gantt
            gantt.deleteTask(task.id);
        }
    })
    .catch(error => {
        console.error('❌ Error de red:', error);
        alert('Error de conexión');
        gantt.deleteTask(task.id);
    });
}