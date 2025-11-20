// Inicialización del Gantt
window.addEventListener('DOMContentLoaded', function() {
    gantt.config.scale_unit = "day";
    gantt.config.date_scale = "%d %M";
    gantt.config.date_format = "%Y-%m-%d %H:%i";
    gantt.config.readonly = false;
    gantt.plugins({
        grid_resize: true
    });
    
    // Configurar resize
    gantt.config.grid_resize = true;
    
    // Habilitar editor nativo (lightbox)
    gantt.config.details_on_dblclick = true;
    gantt.config.drag_create = true;
    
    // Configurar columnas
    gantt.config.columns = [
        {name: "text", label: "Tarea", width: "*", tree: true},
        {name: "start_date", label: "Inicio", align: "center", width: 80},
        {name: "duration", label: "Días", align: "center", width: 50},
        {name: "add", label: "", width: 44},
        {name: "buttons", label: "Acciones", width: 120, align: "center", template: function(task) {
            return `
                <button onclick="abrirModalEditar(${task.id}); event.stopPropagation();" 
                        class="px-2 py-1 text-xs bg-blue-100 text-blue-700 hover:bg-blue-200 rounded transition-colors mx-1" 
                        title="Editar">
                    ✏️
                </button>
                <button onclick="confirmarEliminar(${task.id}); event.stopPropagation();" 
                        class="px-2 py-1 text-xs bg-red-100 text-red-700 hover:bg-red-200 rounded transition-colors" 
                        title="Eliminar">
                    🗑️
                </button>
            `;
        }}
    ];
    
    // ✨ ORDEN CORRECTO: Primero init, luego parse
    gantt.init("gantt_here");
    gantt.parse({data: ganttData});
    
    // ✨ NUEVO: Interceptar cuando se crea una tarea desde el lightbox
    gantt.attachEvent("onAfterTaskAdd", function(id, item) {
        console.log('🆕 Nueva tarea detectada:', item);
        
        // Verificar si tiene ID temporal (generado por Gantt)
        if (typeof id === 'string' || id > 100000) {
            console.log('📝 Es una tarea nueva desde lightbox, guardando en BD...');
            guardarTareaEnBD(item);
        }
        
        return true;
    });
    
    // ✨ NUEVO: Interceptar cuando se actualiza una tarea desde el lightbox
    gantt.attachEvent("onAfterTaskUpdate", function(id, item) {
        console.log('✏️ Tarea actualizada:', item);
        return true;
    });
    
    // ✨ NUEVO: Modal elegante en doble clic (Estilo Taiwiland)
    gantt.attachEvent("onTaskDblClick", function(id, e) {
        const task = gantt.getTask(id);
        if (!task) return;
        
        // Extraer información del texto
        const title = task.text.split('|')[0].trim();
        const assignedMatch = task.text.match(/👤([^|]+)/);
        const unitsMatch = task.text.match(/📊([^|]+)/);
        
        const assignedTo = assignedMatch ? assignedMatch[1].trim() : 'No asignado';
        const units = unitsMatch ? unitsMatch[1].trim() : '0/0';
        const progress = Math.round(task.progress * 100);
        
        // Crear modal elegante
        const modalHTML = `
        <div id="taskModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div class="bg-white rounded-2xl shadow-2xl w-96 transform transition-all duration-300 scale-95 animate-fade-in">
                <!-- Header con gradiente -->
                <div class="bg-gradient-to-r from-blue-500 to-purple-600 rounded-t-2xl p-6 text-white">
                    <div class="flex justify-between items-center">
                        <h3 class="text-xl font-bold">📋 Detalles de Tarea</h3>
                        <button onclick="cerrarTaskModal()" class="text-white hover:text-gray-200 text-2xl transition-transform hover:scale-110">
                            ×
                        </button>
                    </div>
                </div>
                
                <!-- Contenido -->
                <div class="p-6 space-y-4">
                    <!-- Título -->
                    <div class="text-center">
                        <h4 class="text-lg font-semibold text-gray-800">${title}</h4>
                    </div>
                    
                    <!-- Información en tarjetas -->
                    <div class="grid grid-cols-2 gap-3">
                        <div class="bg-blue-50 rounded-lg p-3 text-center">
                            <div class="text-blue-600 text-sm">👤 Asignado</div>
                            <div class="font-semibold text-gray-800">${assignedTo}</div>
                        </div>
                        <div class="bg-green-50 rounded-lg p-3 text-center">
                            <div class="text-green-600 text-sm">📊 Unidades</div>
                            <div class="font-semibold text-gray-800">${units}</div>
                        </div>
                    </div>
                    
                    <!-- Barra de progreso -->
                    <div class="space-y-2">
                        <div class="flex justify-between text-sm">
                            <span class="text-gray-600">Progreso</span>
                            <span class="font-semibold">${progress}%</span>
                        </div>
                        <div class="w-full bg-gray-200 rounded-full h-2">
                            <div class="bg-gradient-to-r from-green-400 to-blue-500 h-2 rounded-full transition-all duration-500" 
                                 style="width: ${progress}%"></div>
                        </div>
                    </div>
                    
                    <!-- Fechas -->
                    <div class="space-y-2 text-sm">
                        <div class="flex justify-between">
                            <span class="text-gray-600">📅 Inicio:</span>
                            <span class="font-semibold">${gantt.date.date_to_str("%d/%m/%Y")(task.start_date)}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-600">📅 Fin:</span>
                            <span class="font-semibold">${gantt.date.date_to_str("%d/%m/%Y")(task.end_date)}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-600">⏱️ Duración:</span>
                            <span class="font-semibold">${task.duration} días</span>
                        </div>
                    </div>
                </div>
                
                <!-- Footer -->
                <div class="border-t border-gray-200 p-4 flex justify-end">
                    <button onclick="cerrarTaskModal()" 
                            class="px-6 py-2 bg-gradient-to-r from-gray-500 to-gray-600 text-white rounded-lg hover:from-gray-600 hover:to-gray-700 transition-all duration-300 transform hover:scale-105">
                        Cerrar
                    </button>
                </div>
            </div>
        </div>
        `;
        
        // Agregar modal al body
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Animación de entrada
        setTimeout(() => {
            const modal = document.getElementById('taskModal');
            modal.querySelector('.scale-95').classList.replace('scale-95', 'scale-100');
        }, 10);
        
        return false; // Evitar que se abra el lightbox
    });
}); // ← ESTE CIERRE FALTABA

function cambiarEscala(escala) {
    if (!gantt.ext.zoom.levels) {
        gantt.ext.zoom.init({
            levels: [
                {
                    name: "day",
                    scale_height: 60,
                    min_column_width: 80,
                    scales: [
                        {unit: "day", step: 1, format: "%d %M"}
                    ]
                },
                {
                    name: "week",
                    scale_height: 60,
                    min_column_width: 100,
                    scales: [
                        {unit: "week", step: 1, format: "Semana %W"}
                    ]
                },
                {
                    name: "month",
                    scale_height: 60,
                    min_column_width: 120,
                    scales: [
                        {unit: "month", step: 1, format: "%M %Y"}
                    ]
                }
            ]
        });
    }
    gantt.ext.zoom.setLevel(escala);
}

function filtrarPorProyecto(projectId) {
    if (projectId === '' || projectId === undefined) {
        window.location.href = '/gantt/';
    } else {
        window.location.href = '/gantt/' + projectId + '/';
    }
}

// Función para cerrar el modal de tarea
function cerrarTaskModal() {
    const modal = document.getElementById('taskModal');
    if (modal) {
        modal.querySelector('.scale-100').classList.replace('scale-100', 'scale-95');
        setTimeout(() => {
            modal.remove();
        }, 300);
    }
}