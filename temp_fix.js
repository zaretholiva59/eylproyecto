// SOLUCIÓN: Reemplazar la función showExcelView 
function showExcelView(view, event) { 
    console.log('Cambiando a vista Excel:', view); 
 
    // Ocultar todas las vistas de Excel 
    document.querySelectorAll('#excel-bac, #excel-costos, #excel-eficiencia').forEach(el =
        el.style.display = 'none'; 
    }); 
 
    // Mostrar vista seleccionada 
    const selectedView = document.getElementById('excel-' + view); 
    if (selectedView) { 
        selectedView.style.display = 'block'; 
    } 
 
    // SOLUCIÓN: Buscar el card de forma segura 
    const card = document.querySelector('.card .card-header:contains("Excel Ejecutivo")')?.closest('.card'); 
        const buttons = card.querySelectorAll('.btn-group .btn'); 
        buttons.forEach(btn =
        event.target.classList.add('active'); 
    } 
} 
