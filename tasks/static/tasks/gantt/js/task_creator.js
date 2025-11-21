// ACTUALIZAR la función guardarNuevaTarea existente
async function guardarNuevaTarea() {
    const form = document.getElementById('formNuevaTarea');
    const formData = new FormData(form);
    
    console.log('📤 Enviando formulario Django...');
    
    // 🎯 NUEVO: El Form Django ya valida automáticamente, podemos quitar validaciones manuales
    // (O mantenerlas como doble verificación)
    
    try {
        const response = await fetch('/tasks/crear/', {  // ← USA TU URL ACTUAL
            method: 'POST',
            body: formData,
            headers: { 
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log('✅ Tarea creada:', data);
            alert(data.message || '✅ Tarea creada exitosamente');
            cerrarModal();
            location.reload();
            
        } else {
            console.error('❌ Errores del Form Django:', data);
            
            // 🎯 MEJORADO: Mostrar errores específicos del Form Django
            let errorMsg = 'Errores de validación:\n\n';
            
            if (data.error_details) {
                // Errores por campo del Form Django
                for (const [field, errors] of Object.entries(data.error_details)) {
                    errorMsg += `• ${field}: ${errors.join(', ')}\n`;
                }
            } else if (data.error_messages && data.error_messages.length > 0) {
                // Mensajes de error legibles
                errorMsg += data.error_messages.join('\n');
            } else {
                errorMsg = data.error || 'Error desconocido al guardar la tarea';
            }
            
            alert(errorMsg);
        }
        
    } catch (error) {
        console.error('🚨 Error de red:', error);
        alert('Error de conexión al guardar la tarea: ' + error.message);
    }
}