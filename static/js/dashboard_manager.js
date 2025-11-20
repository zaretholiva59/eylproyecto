// dashboard_manager.js - VERSIÓN COMPLETA FUNCIONAL

// FUNCIONES PARA CAMBIAR VISTAS
function showCurvaSView(view, event) {
    console.log('Cambiando a vista Curva S:', view);
    
    // Ocultar todas las vistas de Curva S
    var elementos = document.querySelectorAll('#curvaS-evm, #curvaS-cpi, #curvaS-progreso');
    for (var i = 0; i < elementos.length; i++) {
        elementos[i].style.display = 'none';
    }
    
    // Mostrar vista seleccionada
    var vistaSeleccionada = document.getElementById('curvaS-' + view);
    if (vistaSeleccionada) {
        vistaSeleccionada.style.display = 'block';
    }
    
    // Actualizar botones activos
    if (event && event.target) {
        var btnGroup = event.target.closest('.btn-group');
        var buttons = btnGroup.querySelectorAll('.btn');
        for (var j = 0; j < buttons.length; j++) {
            buttons[j].classList.remove('active');
        }
        event.target.classList.add('active');
    }
}

function showExcelView(view, event) {
    console.log('Cambiando a vista Excel:', view);
    
    // Ocultar todas las vistas de Excel
    var elementos = document.querySelectorAll('#excel-avance, #excel-costos, #excel-eficiencia');
    for (var i = 0; i < elementos.length; i++) {
        elementos[i].style.display = 'none';
    }
    
    // Mostrar vista seleccionada
    var vistaSeleccionada = document.getElementById('excel-' + view);
    if (vistaSeleccionada) {
        vistaSeleccionada.style.display = 'block';
    }
    
    // Actualizar botones activos
    if (event && event.target) {
        var btnGroup = event.target.closest('.btn-group');
        var buttons = btnGroup.querySelectorAll('.btn');
        for (var j = 0; j < buttons.length; j++) {
            buttons[j].classList.remove('active');
        }
        event.target.classList.add('active');
    }
}

// Utilidad: asegurar serie acumulada no decreciente
function enforceNonDecreasing(arr) {
    var out = [];
    var last = 0;
    for (var i = 0; i < (arr || []).length; i++) {
        var v = Number(arr[i] || 0);
        if (v < last) v = last;
        out.push(v);
        last = v;
    }
    return out;
}

// INICIALIZAR CURVA S
function initializeCurvaSChart() {
    console.log('Inicializando gráfico Curva S...');
    
    var ctx = document.getElementById('curvaSChart');
    if (!ctx) {
        console.log('No se encontró el canvas de Curva S');
        return;
    }

    try {
        var data = window.dashboardData;
        console.log('Datos para Curva S:', data);

        if (!data.meses || data.meses.length === 0) {
            console.error('No hay datos para mostrar en el gráfico');
            return;
        }

        // ✅ Guardia monotónica para prevenir caídas accidentales
        function ensureNonDecreasing(arr){
            var out = []; var last = 0;
            if (!arr) return out;
            for (var i = 0; i < arr.length; i++){
                var v = Number(arr[i] || 0);
                if (!isFinite(v) || v < 0) v = 0;
                if (v < last) v = last;
                out.push(v);
                last = v;
            }
            return out;
        }
        data.pv = ensureNonDecreasing(data.pv || []);
        data.ev = ensureNonDecreasing(data.ev || []);
        data.ac = ensureNonDecreasing(data.ac || []);
        data.ac_paid = ensureNonDecreasing(data.ac_paid || []);

        // Fallbacks para evitar líneas planas/casi cero
        try {
            var n = data.meses.length;
            // PV fallback: si todos son 0 o el máximo es muy pequeño
            var pvArr = (data.pv || []).map(function(x){ return Number(x||0); });
            var pvMax = pvArr.length ? Math.max.apply(null, pvArr) : 0;
            var pvAllZero = pvArr.length && pvArr.every(function(v){ return Math.abs(v) < 1e-6; });
            if (!pvArr.length || pvAllZero || pvMax < 1e-3) {
                var bacRef = Number(window.bacPlaneado || window.bacReal || (data.bac || 0));
                if (!bacRef || bacRef < 1e-6) {
                    // usar máximo de AC como referencia si BAC no disponible
                    var acArrRef = (data.ac || []).map(function(x){ return Number(x||0); });
                    bacRef = acArrRef.length ? Math.max.apply(null, acArrRef) : 0;
                }
                var pvFixed = [];
                for (var i = 1; i <= n; i++) {
                    pvFixed.push(Number(((bacRef * i) / n).toFixed(2)));
                }
                data.pv = pvFixed;
                console.log('🔧 PV corregido con rampa lineal hasta', bacRef);
            }

            // EV fallback: si es constante o todo cero
            var evArr = (data.ev || []).map(function(x){ return Number(x||0); });
            var uniqueEV = Array.from(new Set(evArr.map(function(v){ return Number(v.toFixed(2)); })));
            var evAllZero = evArr.length && evArr.every(function(v){ return Math.abs(v) < 1e-6; });
            if (!evArr.length || evAllZero || uniqueEV.length <= 1) {
                var evTarget = evArr.length ? evArr[evArr.length - 1] : 0;
                if (!evTarget || evTarget < 1e-6) {
                    // usar progreso físico si existiese o máximo AC
                    var acArr = (data.ac || []).map(function(x){ return Number(x||0); });
                    evTarget = acArr.length ? Math.max.apply(null, acArr) : 0;
                }
                var evFixed = [];
                for (var k = 1; k <= n; k++) {
                    evFixed.push(Number(((evTarget * k) / n).toFixed(2)));
                }
                data.ev = evFixed;
                console.log('🔧 EV corregido con rampa lineal hasta', evTarget);
            }
        } catch (fallbackErr) {
            console.warn('Fallback PV/EV no aplicado:', fallbackErr);
        }

        // Enforce cumulative monotonicity on all series before chart creation
        data.pv = enforceNonDecreasing((data.pv || []).map(function(x){ return Number(x || 0); }));
        data.ev = enforceNonDecreasing((data.ev || []).map(function(x){ return Number(x || 0); }));
        data.ac = enforceNonDecreasing((data.ac || []).map(function(x){ return Number(x || 0); }));
        data.ac_paid = enforceNonDecreasing((data.ac_paid || []).map(function(x){ return Number(x || 0); }));

        // Guardar instancia de Chart para actualizar según granularidad
        window.curvaSChart = new Chart(ctx, {
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
                    },
                    {
                        label: 'Cobros Verificados (Cliente)',
                        data: (data.ac_paid || []).map(function(x){ return Number(x || 0); }),
                        borderColor: '#6f42c1',
                        backgroundColor: 'rgba(111, 66, 193, 0.1)',
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
        console.error('Error inicializando Curva S:', error);
    }
}

// Cambiar granularidad de Curva S
function setCurvaSGranularity(gran) {
    try {
        var d = window.dashboardData;
        var chart = window.curvaSChart;
        if (!chart) return;

        var labels, pv, ev, ac, xTitle;
        if (gran === 'semanas' && d.semanas_labels && d.semanas_labels.length) {
            labels = d.semanas_labels; pv = d.semanas_pv; ev = d.semanas_ev; ac = d.semanas_ac; xTitle = 'Semanas';
        } else if (gran === 'dias' && d.dias_labels && d.dias_labels.length) {
            labels = d.dias_labels; pv = d.dias_pv; ev = d.dias_ev; ac = d.dias_ac; xTitle = 'Días';
        } else {
            labels = d.meses; pv = d.pv; ev = d.ev; ac = d.ac; xTitle = 'Meses';
        }

        // Enforce monotonicity for selected granularity series
        pv = enforceNonDecreasing((pv || []).map(function(x){ return Number(x || 0); }));
        ev = enforceNonDecreasing((ev || []).map(function(x){ return Number(x || 0); }));
        ac = enforceNonDecreasing((ac || []).map(function(x){ return Number(x || 0); }));

        chart.data.labels = labels;
        chart.data.datasets[0].data = pv;
        chart.data.datasets[1].data = ev;
        chart.data.datasets[2].data = ac;
        // Mostrar/Ocultar pagos verificados según granularidad disponible
        if (chart.data.datasets.length > 3) {
            if (xTitle !== 'Meses') {
                chart.data.datasets[3].hidden = true;
            } else {
                chart.data.datasets[3].hidden = false;
                var acPaidSeries = enforceNonDecreasing((d.ac_paid || []).map(function(x){ return Number(x || 0); }));
                chart.data.datasets[3].data = acPaidSeries;
            }
        }
        chart.options.scales.x.title.text = xTitle;
        chart.update();
        console.log('🔁 Curva S actualizada a', xTitle);
    } catch (e) {
        console.error('Error cambiando granularidad:', e);
    }
}

function initializeCPISPIChart() {
    var ctx = document.getElementById('cpiSpiChart');
    if (!ctx) return;
    
    try {
        var data = window.dashboardData;
        var labelsArr = data.meses || ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun'];
        var cpiData = Array.isArray(data.cpi) ? data.cpi : labelsArr.map(function(){ return Number(data.cpi || 1.0); });
        var spiData = Array.isArray(data.spi) ? data.spi : labelsArr.map(function(){ return Number(data.spi || 1.0); });
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labelsArr,
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
                    title: { display: true, text: 'CPI/SPI Trend' }
                }
            }
        });
        console.log('Gráfico CPI/SPI inicializado');
    } catch (error) {
        console.error('Error inicializando CPI/SPI:', error);
    }
}

function initializeProgressChart() {
    var ctx = document.getElementById('progressChart');
    if (!ctx) return;
    
    try {
        var data = window.dashboardData;
        
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
                    title: { display: true, text: 'Progreso del Proyecto' }
                }
            }
        });
        console.log('Gráfico de Progreso inicializado');
    } catch (error) {
        console.error('Error inicializando Progreso:', error);
    }
}

// INICIALIZAR GRÁFICOS EXCEL EJECUTIVO
function initializeExcelCharts() {
    console.log('Inicializando gráficos Excel Ejecutivo...');
    
    // Reemplazo: Gráfico de Avance (acumulado) basado en GRID
    var ctxAvance = document.getElementById('avanceChart');
    if (ctxAvance) {
        var fm = window.facturacionMensual || [];
        var labelsAv = fm.map(function(x){ return x.mes; });
        var factMensual = fm.map(function(x){ return Number(x.total || 0); });
        var factAcum = [];
        var accF = 0;
        for (var iA = 0; iA < factMensual.length; iA++) { accF += factMensual[iA]; factAcum.push(Number(accF.toFixed(2))); }

        // Costos acumulados desde AC (ya es acumulado)
        var acAcum = (window.dashboardData && window.dashboardData.ac) ? window.dashboardData.ac.map(function(x){return Number(x||0);}) : [];
        // Alinear longitudes
        if (labelsAv.length && acAcum.length > labelsAv.length) acAcum = acAcum.slice(0, labelsAv.length);

        var bacReal = Number(window.bacReal || 0);
        var avancePct = [];
        for (var jA = 0; jA < factAcum.length; jA++) {
            var pct = (bacReal && bacReal > 0) ? (factAcum[jA] / bacReal) * 100 : (acAcum[jA] ? (factAcum[jA] / acAcum[jA]) * 100 : 0);
            avancePct.push(Number(pct.toFixed(1)));
        }
        // Fallback si no hay datos del GRID
        if (!labelsAv.length) {
            labelsAv = (window.dashboardData && window.dashboardData.meses) ? window.dashboardData.meses.map(function(m){ return 'Mes ' + m; }) : ['Mes 1','Mes 2','Mes 3'];
            factAcum = labelsAv.map(function(){ return 0; });
            acAcum = (window.dashboardData && window.dashboardData.ac) ? window.dashboardData.ac.slice(0, labelsAv.length) : labelsAv.map(function(){ return 0; });
            avancePct = labelsAv.map(function(){ return 0; });
        }

        new Chart(ctxAvance, {
            type: 'line',
            data: {
                labels: labelsAv,
                datasets: [
                    {
                        label: 'Facturación acumulada (GRID)',
                        data: factAcum,
                        borderColor: '#198754',
                        backgroundColor: 'rgba(25, 135, 84, 0.1)',
                        fill: true,
                        tension: 0.4
                    },
                    {
                        label: 'Costos acumulados (AC)',
                        data: acAcum,
                        borderColor: '#dc3545',
                        backgroundColor: 'rgba(220, 53, 69, 0.1)',
                        fill: true,
                        tension: 0.4
                    },
                    {
                        label: 'Avance (%)',
                        data: avancePct,
                        borderColor: '#0d6efd',
                        backgroundColor: 'rgba(13, 110, 253, 0.1)',
                        fill: false,
                        tension: 0.3,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 1.2,
                plugins: {
                    title: { display: true, text: 'Avance del Proyecto (Acumulado)', font: { size: 14 } },
                    legend: { position: 'bottom', labels: { boxWidth: 20, font: { size: 12 } } }
                },
                scales: {
                    y: { beginAtZero: true, title: { display: true, text: 'Monto (S/)' } },
                    y1: { beginAtZero: true, position: 'right', title: { display: true, text: '% Avance' }, min: 0, max: 100 }
                }
            }
        });
        console.log('✅ Gráfico de Avance creado');
    }
    
    var ctxCostos = document.getElementById('costosChart');
    if (ctxCostos) {
        // Construir gráfico mensual Facturación vs Costos según GRID
        var fm = window.facturacionMensual || [];
        var labels = fm.map(function(x){ return x.mes; });
        var factValues = fm.map(function(x){ return Number(x.total || 0); });
        // AC acumulado desde Curva S; convertir a mensual (delta)
        var acSeries = (window.dashboardData && window.dashboardData.ac) ? window.dashboardData.ac.map(function(x){return Number(x||0);}) : [];
        var acDelta = [];
        for (var i = 0; i < acSeries.length; i++) {
            var prev = i > 0 ? acSeries[i-1] : 0;
            acDelta.push(acSeries[i] - prev);
        }
        // Alinear longitudes con fm
        var costValues = [];
        for (var j = 0; j < fm.length; j++) {
            costValues.push(Number(acDelta[j] || 0));
        }
        // Si no hay fm, crear etiquetas básicas
        if (!labels.length) {
            labels = (window.dashboardData && window.dashboardData.meses) ? window.dashboardData.meses.map(function(m){ return 'Mes ' + m; }) : ['Mes 1','Mes 2','Mes 3'];
            factValues = labels.map(function(){ return 0; });
            costValues = acDelta.slice(0, labels.length);
        }
        new Chart(ctxCostos, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Facturación (Cliente Verificada)',
                        data: factValues,
                        backgroundColor: 'rgba(25, 135, 84, 0.7)'
                    },
                    {
                        label: 'Costos (AC mensual)',
                        data: costValues,
                        backgroundColor: 'rgba(220, 53, 69, 0.7)'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 1.4,
                plugins: {
                    title: { display: true, text: 'Facturación vs Costos (Mensual - GRID)', font: { size: 14 } },
                    legend: { position: 'bottom', labels: { boxWidth: 20, font: { size: 12 } } }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
        console.log('✅ Gráfico mensual Facturación vs Costos creado');
    }
    
    var ctxEficiencia = document.getElementById('eficienciaChart');
    if (ctxEficiencia) {
        // Eficiencia mensual basada en GRID: (Facturación / Costos) * 100
        var fm = window.facturacionMensual || [];
        var labels = fm.map(function(x){ return x.mes; });
        var factValues = fm.map(function(x){ return Number(x.total || 0); });
        var acSeries = (window.dashboardData && window.dashboardData.ac) ? window.dashboardData.ac.map(function(x){return Number(x||0);}) : [];
        var acDelta = [];
        for (var i = 0; i < acSeries.length; i++) {
            var prev = i > 0 ? acSeries[i-1] : 0;
            acDelta.push(acSeries[i] - prev);
        }
        var effValues = [];
        for (var j = 0; j < fm.length; j++) {
            var cost = Number(acDelta[j] || 0);
            var fact = Number(factValues[j] || 0);
            var eff = cost > 0 ? (fact / cost) * 100 : 100;
            effValues.push(Number(eff.toFixed(1)));
        }
        // Fallback si no hay datos
        if (!labels.length) {
            labels = (window.dashboardData && window.dashboardData.meses) ? window.dashboardData.meses.map(function(m){ return 'Mes ' + m; }) : ['Mes 1','Mes 2','Mes 3'];
            effValues = labels.map(function(){ return 100; });
        }
        new Chart(ctxEficiencia, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Eficiencia Mensual (Facturación/Costos)',
                    data: effValues,
                    borderColor: '#ff6384',
                    backgroundColor: 'rgba(255, 99, 132, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 1.2,
                plugins: {
                    title: { display: true, text: 'Tendencia de Eficiencia (GRID)', font: { size: 14 } },
                    legend: { position: 'bottom', labels: { boxWidth: 20, font: { size: 12 } } }
                },
                scales: {
                    y: { min: 0, max: 200 }
                }
            }
        });
        console.log('✅ Gráfico Eficiencia (GRID) creado');
    }
}

// INICIALIZAR TODO EL DASHBOARD
function initializeDashboard() {
    console.log('🔄 Inicializando Dashboard Ejecutivo...');
    
    // Verificar que los datos estén disponibles
    if (!window.dashboardData) {
        console.error('❌ No se encontraron datos del dashboard');
        return;
    }

    console.log('📊 Datos recibidos:', window.dashboardData);

    // Inicializar Curva S principal
    initializeCurvaSChart();
    initializeCPISPIChart();
    initializeProgressChart();

    // Inicializar gráficos Excel
    initializeExcelCharts();
    // Poblar resumen de fórmulas con valores actuales
    try { populateResumenFormulas(); } catch(e){ console.warn('No se pudo poblar el resumen de fórmulas:', e); }
}

// EJECUTAR AL CARGAR LA PÁGINA
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Iniciando dashboard...');
    // Si Chart aún no está disponible, espera al load completo
    if (typeof Chart === 'undefined') {
        window.addEventListener('load', initializeDashboard, { once: true });
        return;
    }
    initializeDashboard();
});

// CAMBIAR PROYECTO
function cambiarProyecto(projectId) {
    if (projectId && projectId !== '') {
        console.log('🔄 Cambiando a proyecto:', projectId);
        window.location.href = '/dashboard/' + projectId + '/';
    }
}

console.log('✅ Dashboard Manager - VERSIÓN COMPLETA - Cargado correctamente');


// ==================== FUNCIONES PARA TABLAS ====================

function mostrarTablaCurvaS() {
    console.log('Mostrando tabla Curva S...');
    // Aquí irá el modal con la tabla de Curva S
    alert('📊 Tabla Curva S - En desarrollo');
}

function mostrarTablaExcel() {
    console.log('Mostrando Grid ejecutivo...');
    try {
        var modalEl = document.getElementById('excelInfoModal');
        if (!modalEl) {
            alert('No se encontró el modal de Grid ejecutivo');
            return;
        }

        // Helpers
        function formatCurrency(val){ try { return new Intl.NumberFormat('es-PE', {style:'currency', currency:'PEN'}).format(Number(val||0)); } catch(e){ return (Number(val||0)).toFixed(2); } }
        function formatPercent(val){ try { return (Number(val||0)).toFixed(1) + '%'; } catch(e){ return '0.0%'; } }

        // Datos base
        var acSeries = (window.dashboardData && window.dashboardData.ac) ? window.dashboardData.ac.map(function(x){return Number(x||0);}) : [];
        var bacReal = Number(window.bacReal || 0);

        // Construir grid ejecutivo (tabla única)
        var tbody = document.getElementById('corporativo_grid_body');
        if (tbody) {
            while (tbody.firstChild) tbody.removeChild(tbody.firstChild);
            var fm = window.facturacionMensual || [];
            // Costos mensuales desde AC acumulado (delta)
            var acDelta = [];
            for (var j = 0; j < acSeries.length; j++) {
                var prev = j > 0 ? acSeries[j-1] : 0;
                acDelta.push(acSeries[j] - prev);
            }
            // Mostrar solo los meses reales de facturación para evitar "Mes 1, Mes 2..."
            var maxRows = fm.length;
            var quarterSum = 0;
            var factAcum = 0;
            for (var r = 0; r < maxRows; r++) {
                var tr = document.createElement('tr');
                var mesLabel = (fm[r] && fm[r].mes) ? fm[r].mes : ('Mes ' + (r+1));
                var factVal = (fm[r] && fm[r].total) ? Number(fm[r].total || 0) : 0;
                var costVal = Number(acDelta[r] || 0);
                quarterSum += factVal + costVal;
                factAcum += factVal;

                // Porcentajes
                var avancePct = bacReal > 0 ? (factAcum / bacReal * 100) : 0;
                var eficienciaPct = 0;
                if (costVal > 0) {
                    eficienciaPct = (factVal / costVal) * 100;
                } else {
                    eficienciaPct = factVal > 0 ? 100 : 0;
                }
                // celdas
                var tdMes = document.createElement('td'); tdMes.textContent = mesLabel;
                var tdFact = document.createElement('td'); tdFact.className = 'text-end'; tdFact.textContent = formatCurrency(factVal);
                var tdCost = document.createElement('td'); tdCost.className = 'text-end'; tdCost.textContent = formatCurrency(costVal);
                var tdAvance = document.createElement('td'); tdAvance.className = 'text-end'; tdAvance.textContent = formatPercent(avancePct);
                var tdEfic = document.createElement('td'); tdEfic.className = 'text-end'; tdEfic.textContent = formatPercent(eficienciaPct);
                var tdTrim = document.createElement('td'); tdTrim.className = 'text-end'; tdTrim.textContent = formatCurrency(quarterSum);
                tr.appendChild(tdMes); tr.appendChild(tdFact); tr.appendChild(tdCost); tr.appendChild(tdAvance); tr.appendChild(tdEfic); tr.appendChild(tdTrim);
                tbody.appendChild(tr);
                // reset acumulado al final de cada trimestre
                if ((r+1) % 3 === 0) quarterSum = 0;
            }
        }

        var modal = new bootstrap.Modal(modalEl);
        modal.show();
    } catch (error) {
        console.error('Error mostrando Grid ejecutivo:', error);
        alert('Ocurrió un error al mostrar el Grid ejecutivo');
    }
}

// ==================== RESUMEN DE FÓRMULAS (VALORES) ====================

// Helpers globales para formato
function formatCurrency(val){
    try { return new Intl.NumberFormat('es-PE', {style:'currency', currency:'PEN'}).format(Number(val||0)); }
    catch(e){ return 'S/ ' + (Number(val||0)).toFixed(2); }
}
function formatPercent(val){
    try { return (Number(val||0)).toFixed(1) + '%'; }
    catch(e){ return '0.0%'; }
}

function populateResumenFormulas(){
    // Datos base desde window
    var acSeries = (window.dashboardData && window.dashboardData.ac) ? window.dashboardData.ac.map(function(x){return Number(x||0);}) : [];
    var acJtd = acSeries.length ? Number(acSeries[acSeries.length-1] || 0) : 0;
    var bacPlaneado = Number(window.bacPlaneado || 0);
    var contractAmount = Number(window.contractAmount || 0);
    var facturadoCliente = Number(window.facturadoClienteTotal || 0);
    if ((!facturadoCliente || facturadoCliente === 0) && window.facturacionMensual){
        try {
            var fm = Array.isArray(window.facturacionMensual) ? window.facturacionMensual : [];
            facturadoCliente = fm.reduce(function(acc, d){ return acc + Number(d.amount || 0); }, 0);
        } catch(_e){}
    }
    var horasData = Array.isArray(window.horasData) ? window.horasData : [];
    var costData = window.costData || {};

    // Distribución componentes
    var mat = Number(costData.materiales || 0);
    var serv = Number(costData.servicios || 0);
    var subc = Number(costData.subcontratado || 0);
    var gast = Number(costData.gastos || 0);
    var totalComp = mat + serv + subc + gast;
    var totalDeclarado = Number(costData.total || bacPlaneado || 0);
    var diff = (totalComp - totalDeclarado);
    var status = Math.abs(diff) < 0.5 ? 'OK' : 'VERIFICAR';

    // Porcentajes
    var pctCompletado = bacPlaneado > 0 ? (acJtd / bacPlaneado * 100) : 0;
    var pctAvanceFact = contractAmount > 0 ? (facturadoCliente / contractAmount * 100) : 0;
    var eficienciaGlobal = acJtd > 0 ? (facturadoCliente / acJtd * 100) : (facturadoCliente > 0 ? 100 : 0);
    var totalHoras = horasData.reduce(function(acc, h){ return acc + Number(h.hours || 0); }, 0);

    // Escribir en el panel (si existe)
    var el;
    el = document.getElementById('valMontoContractual'); if (el) el.textContent = formatCurrency(contractAmount);
    el = document.getElementById('valBacPlaneado'); if (el) el.textContent = formatCurrency(bacPlaneado);
    el = document.getElementById('valAcJtd'); if (el) el.textContent = formatCurrency(acJtd);
    el = document.getElementById('valFacturadoCliente'); if (el) el.textContent = formatCurrency(facturadoCliente);
    el = document.getElementById('valPctCompletado'); if (el) el.textContent = formatPercent(pctCompletado);
    el = document.getElementById('valPctAvanceFact'); if (el) el.textContent = formatPercent(pctAvanceFact);
    el = document.getElementById('valEficienciaGlobal'); if (el) el.textContent = formatPercent(eficienciaGlobal);
    el = document.getElementById('valTotalHoras'); if (el) el.textContent = totalHoras.toFixed(2);
    el = document.getElementById('valCostoMateriales'); if (el) el.textContent = formatCurrency(mat);
    el = document.getElementById('valCostoServicios'); if (el) el.textContent = formatCurrency(serv);
    el = document.getElementById('valCostoSubcontratado'); if (el) el.textContent = formatCurrency(subc);
    el = document.getElementById('valCostoGastos'); if (el) el.textContent = formatCurrency(gast);
    el = document.getElementById('valStatusComponentes'); if (el) el.textContent = status;
    el = document.getElementById('valDiferenciaComponentes'); if (el) el.textContent = '(Dif: ' + formatCurrency(diff) + ')';

    // Refrescar al abrir el collapse
    var col = document.getElementById('resumenFormulasExec');
    if (col && typeof bootstrap !== 'undefined'){
        col.addEventListener('shown.bs.collapse', function(){
            populateResumenFormulas();
        }, { once: true });
    }
}

// Mostrar/Ocultar la tabla de resumen ejecutivo
function toggleTablaResumen(){
    var tablaBody = document.getElementById('tablaResumenBody');
    if (!tablaBody) return;

    var visible = tablaBody.style.display !== 'none';
    tablaBody.style.display = visible ? 'none' : 'block';

    // Cargar valores si se muestra
    if (!visible){
        var contractAmount = Number(window.contractAmount || 0);
        var bacPlaneado = Number(window.bacPlaneado || 0);
        var facturadoCliente = Number(window.facturadoClienteTotal || 0);

        var costoTotal = Number((window.costData && window.costData.total) || bacPlaneado || 0);
        var margen = contractAmount - costoTotal;

        // Porcentajes
        var costoPorcentaje = contractAmount > 0 ? (costoTotal / contractAmount * 100) : 0;
        var margenPorcentaje = contractAmount > 0 ? (margen / contractAmount * 100) : 0;
        var facturacionPorcentaje = contractAmount > 0 ? (facturadoCliente / contractAmount * 100) : 0;

        // Escribir
        var el;
        el = document.getElementById('montoContractual'); if (el) el.textContent = formatCurrency(contractAmount);
        el = document.getElementById('costoTotal'); if (el) el.textContent = formatCurrency(costoTotal);
        el = document.getElementById('margen'); if (el) el.textContent = formatCurrency(margen);
        el = document.getElementById('facturacion'); if (el) el.textContent = formatCurrency(facturadoCliente);
        el = document.getElementById('costoPorcentaje'); if (el) el.textContent = formatPercent(costoPorcentaje);
        el = document.getElementById('margenPorcentaje'); if (el) el.textContent = formatPercent(margenPorcentaje);
        el = document.getElementById('facturacionPorcentaje'); if (el) el.textContent = formatPercent(facturacionPorcentaje);

        // Construir el grid ejecutivo dentro de la Tabla Resumen
        try {
            var tbody = document.getElementById('corporativo_grid_body_page');
            if (tbody) {
                while (tbody.firstChild) tbody.removeChild(tbody.firstChild);
                var fm = window.facturacionMensual || [];
                var acSeries = (window.dashboardData && window.dashboardData.ac) ? window.dashboardData.ac.map(function(x){return Number(x||0);}) : [];
                var bacReal = Number(window.bacReal || 0);

                // Costos mensuales desde AC acumulado (delta)
                var acDelta = [];
                for (var j = 0; j < acSeries.length; j++) {
                    var prev = j > 0 ? acSeries[j-1] : 0;
                    acDelta.push(acSeries[j] - prev);
                }

                var maxRows = fm.length;
                var quarterSum = 0;
                var factAcum = 0;
                for (var r = 0; r < maxRows; r++) {
                    var tr = document.createElement('tr');
                    var mesLabel = (fm[r] && fm[r].mes) ? fm[r].mes : ('Mes ' + (r+1));
                    var factVal = (fm[r] && fm[r].total) ? Number(fm[r].total || 0) : 0;
                    var costVal = Number(acDelta[r] || 0);
                    quarterSum += factVal + costVal;
                    factAcum += factVal;

                    // Porcentajes
                    var avancePct = bacReal > 0 ? (factAcum / bacReal * 100) : 0;
                    var eficienciaPct = 0;
                    if (costVal > 0) {
                        eficienciaPct = (factVal / costVal) * 100;
                    } else {
                        eficienciaPct = factVal > 0 ? 100 : 0;
                    }

                    // celdas
                    var tdMes = document.createElement('td'); tdMes.textContent = mesLabel;
                    var tdFact = document.createElement('td'); tdFact.className = 'text-end'; tdFact.textContent = formatCurrency(factVal);
                    var tdCost = document.createElement('td'); tdCost.className = 'text-end'; tdCost.textContent = formatCurrency(costVal);
                    var tdAvance = document.createElement('td'); tdAvance.className = 'text-end'; tdAvance.textContent = formatPercent(avancePct);
                    var tdEfic = document.createElement('td'); tdEfic.className = 'text-end'; tdEfic.textContent = formatPercent(eficienciaPct);
                    var tdTrim = document.createElement('td'); tdTrim.className = 'text-end'; tdTrim.textContent = formatCurrency(quarterSum);
                    tr.appendChild(tdMes); tr.appendChild(tdFact); tr.appendChild(tdCost); tr.appendChild(tdAvance); tr.appendChild(tdEfic); tr.appendChild(tdTrim);
                    tbody.appendChild(tr);

                    // reset acumulado al final de cada trimestre
                    if ((r+1) % 3 === 0) quarterSum = 0;
                }
            }
        } catch(err){ console.warn('No se pudo construir el grid ejecutivo en Tabla Resumen:', err); }
    }
}
