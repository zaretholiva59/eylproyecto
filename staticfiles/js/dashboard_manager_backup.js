// dashboard_manager.js - Gestión del Dashboard Ejecutivo - VERSIÓN CORREGIDA

// Funciones para cambiar vistas
function showCurvaSView(view, event) {
    console.log('Cambiando a vista Curva S:', view);
    
    // Ocultar todas las vistas de Curva S
    document.querySelectorAll('#curvaS-evm, #curvaS-cpi, #curvaS-progreso').forEach(el => {
        el.style.display = 'none';
    });
    
    // Mostrar vista seleccionada
    const selectedView = document.getElementById(`curvaS-${view}`);
    if (selectedView) {
        selectedView.style.display = 'block';
    }
    
    // Actualizar botones activos
    const card = document.querySelector('#curvaS-evm').closest('.card');
    const buttons = card.querySelectorAll('.btn-group .btn');
    buttons.forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
}

function showExcelView(view, event) {
    console.log('Cambiando a vista Excel:', view);
    
    // Ocultar todas las vistas de Excel
    document.querySelectorAll('#excel-bac, #excel-costos, #excel-eficiencia').forEach(el => {
        el.style.display = 'none';
    });
    
    // Mostrar vista seleccionada
    const selectedView = document.getElementById(`excel-${view}`);
    if (selectedView) {
        selectedView.style.display = 'block';
    }
    
    // Actualizar botones activos
    const card = document.querySelector('#excel-bac').closest('.card');
    const buttons = card.querySelectorAll('.btn-group .btn');
    buttons.forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
}

// Inicializar gráficos cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
});

function initializeDashboard() {
    console.log('🚀 Inicializando Dashboard Ejecutivo...');
    
    // Verificar que los datos estén disponibles
    if (!window.dashboardData) {
        console.error('❌ No se encontraron datos del dashboard');
        return;
    }
    
    console.log('📊 Datos recibidos:', window.dashboardData);
    
    // Inicializar Curva S principal
    initializeCurvaSChart();
    
    // Inicializar gráficos adicionales si existen
    initializeAdditionalCharts();
}

function initializeCurvaSChart() {
    const ctx = document.getElementById('curvaSChart');
    if (!ctx) {
        console.log('❌ No se encontró el canvas de Curva S');
        return;
    }
    
    try {
        // ✅ CORREGIDO - Usar datos desde window.dashboardData
        const data = window.dashboardData;
        console.log('📈 Datos para gráfico:', data);
        
        // Verificar que los datos tengan longitud válida
        if (!data.meses || data.meses.length === 0) {
            console.error('❌ No hay datos para mostrar en el gráfico');
            return;
        }
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.meses,
                datasets: [
                    {
                        label: 'PV - Valor Planeado',
                        data: data.pv,
                        borderColor: '#0d6efd',
                        backgroundColor: 'rgba(13, 110, 253, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4
                    },
                    {
                        label: 'EV - Valor Ganado',
                        data: data.ev,
                        borderColor: '#198754',
                        backgroundColor: 'rgba(25, 135, 84, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4
                    },
                    {
                        label: 'AC - Costo Real',
                        data: data.ac,
                        borderColor: '#dc3545',
                        backgroundColor: 'rgba(220, 53, 69, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Curva S - Análisis de Valor Ganado'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: { display: true, text: 'Monto (S/)' }
                    },
                    x: {
                        title: { display: true, text: 'Meses' }
                    }
                }
            }
        });
        
        console.log('✅ Gráfico Curva S inicializado correctamente');
    } catch (error) {
        console.error('❌ Error inicializando Curva S:', error);
    }
}

function initializeAdditionalCharts() {
    // Inicializar gráfico CPI/SPI si existe
    initializeCPISPIChart();
    
    // Inicializar gráfico de progreso si existe
    initializeProgressChart();
}

function initializeCPISPIChart() {
    const ctx = document.getElementById('cpiSpiChart');
    if (!ctx) return;
    
    try {
        const data = window.dashboardData;
        
        // Datos de ejemplo para CPI/SPI - reemplazar con datos reales
        const cpiData = data.cpi || [1.0, 1.1, 1.05, 0.95, 0.98, 1.02];
        const spiData = data.spi || [0.9, 0.95, 1.0, 1.05, 1.1, 1.08];
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.meses || ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun'],
                datasets: [
                    {
                        label: 'CPI',
                        data: cpiData,
                        borderColor: '#36a2eb',
                        backgroundColor: 'rgba(54, 162, 235, 0.1)',
                        fill: true,
                        tension: 0.4
                    },
                    {
                        label: 'SPI',
                        data: spiData,
                        borderColor: '#ff6384',
                        backgroundColor: 'rgba(255, 99, 132, 0.1)',
                        fill: true,
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'CPI/SPI Trend'
                    }
                }
            }
        });
        
        console.log('✅ Gráfico CPI/SPI inicializado');
    } catch (error) {
        console.error('❌ Error inicializando CPI/SPI:', error);
    }
}

function initializeProgressChart() {
    const ctx = document.getElementById('progressChart');
    if (!ctx) return;
    
    try {
        const data = window.dashboardData;
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.meses || ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun'],
                datasets: [
                    {
                        label: 'Planificado',
                        data: data.pv || [10, 25, 45, 65, 80, 100],
                        backgroundColor: 'rgba(54, 162, 235, 0.8)'
                    },
                    {
                        label: 'Real',
                        data: data.ev || [8, 22, 40, 60, 75, 95],
                        backgroundColor: 'rgba(75, 192, 192, 0.8)'
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Progreso del Proyecto'
                    }
                }
            }
        });
        
        console.log('✅ Gráfico de Progreso inicializado');
    } catch (error) {
        console.error('❌ Error inicializando Progreso:', error);
    }
}

function exportDashboard() {
    console.log('📥 Exportando dashboard...');
    alert('📊 Función de exportación en desarrollo...');
}

// Función para recargar datos
function reloadDashboard() {
    console.log('🔄 Recargando dashboard...');
    location.reload();
}

// Manejo de errores global
window.addEventListener('error', function(e) {
    console.error('❌ Error global:', e.error);
});

// ✅ FUNCIÓN MEJORADA PARA CAMBIAR PROYECTO
function cambiarProyecto(projectId) {
    console.log('🔄 Cambiando a proyecto:', projectId);
    
    // Verificar que el projectId no esté vacío
    if (!projectId || projectId === '') {
        console.error('❌ Project ID vacío');
        return;
    }
    
    // Construir la nueva URL
    const nuevaUrl = `/dashboard/${projectId}/`;
    console.log('📍 Navegando a:', nuevaUrl);
    
    // Redirigir a la nueva URL
    window.location.href = nuevaUrl;
}

// Función para debug del dropdown
function debugDropdown() {
    console.log('🔍 Debug del dropdown:');
    const select = document.querySelector('select[onchange*="cambiarProyecto"]');
    if (select) {
        console.log('✅ Dropdown encontrado:', select);
        console.log('📋 Opciones disponibles:', 
            Array.from(select.options).map(opt => opt.value));
    } else {
        console.error('❌ Dropdown NO encontrado');
    }
}

// Ejecutar debug al cargar la página
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔍 Iniciando debug del dropdown...');
    setTimeout(debugDropdown, 1000); // Esperar 1 segundo para que cargue todo
});