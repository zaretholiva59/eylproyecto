// =========================
// purchase_order.js - CORREGIDO
// =========================

function formatCurrency(value) {
    return parseFloat(value || 0).toFixed(2);
}

// Actualiza índices del formset
function updateFormsetIndices(container, prefix) {
    container.find('.form-row').each(function (index) {
        $(this).find(':input').each(function () {
            let name = $(this).attr('name');
            let id = $(this).attr('id');
            if (name) {
                $(this).attr('name', name.replace(new RegExp(prefix + '-\\d+-'), prefix + '-' + index + '-'));
            }
            if (id) {
                $(this).attr('id', id.replace(new RegExp(prefix + '-\\d+-'), prefix + '-' + index + '-'));
            }
        });
    });
    $('#id_' + prefix + '-TOTAL_FORMS').val(container.find('.form-row').length);
}

// ====== Cálculos ======
function calculateProductRow(row) {
    let quantity = parseFloat(row.find('.quantity').val()) || 0;
    let price = parseFloat(row.find('.unit_price').val()) || 0;
    let subtotal = quantity * price;
    row.find('.total').val(formatCurrency(subtotal));
    calculateOrderTotal();
}

function calculateOrderTotal() {
    let total = 0;
    $('#productos-container .form-row').each(function () {
        total += parseFloat($(this).find('.total').val()) || 0;
    });
    $('#oc-total').text(formatCurrency(total));
}

// ====== Agregar filas ======
function addProductRow() {
    let container = $('#productos-container');
    let newRow = container.find('.form-row').last().clone(true);
    newRow.find('input').val('');
    container.append(newRow);
    updateFormsetIndices(container, 'podetailproduct');
}

function addSupplierRow() {
    let container = $('#proveedores-container');
    let newRow = container.find('.form-row').last().clone(true);
    newRow.find('input').val('');
    container.append(newRow);
    updateFormsetIndices(container, 'podetailsupplier');
}

// ====== DROPDOWN DE PROYECTOS ======
function initializeProjectDropdown() {
    const proyectoSelect = document.getElementById('proyectoSelect');
    
    if (proyectoSelect) {
        proyectoSelect.addEventListener('change', function() {
            const selectedValue = this.value;
            console.log('Proyecto seleccionado:', selectedValue);
            
            if (selectedValue === "") {
                // ✅ VACIAR EL GRID - Ir a página principal
                window.location.href = window.gridUrl;
            } else {
                // ✅ CARGAR PROYECTO SELECCIONADO
                const newUrl = window.gridCostosBaseUrl.replace('0', selectedValue);
                window.location.href = newUrl;
            }
        });
    }
}

// ====== Inicialización General ======
$(document).ready(function() {
    // ✅ Inicializar dropdown de proyectos
    initializeProjectDropdown();

    // ✅ Productos
    $(document).on('input', '.quantity, .unit_price', function () {
        calculateProductRow($(this).closest('.form-row'));
    });

    $(document).on('click', '.remove-product', function () {
        $(this).closest('.form-row').remove();
        calculateOrderTotal();
    });

    $('#add-producto').click(addProductRow);

    // ✅ Proveedores
    $(document).on('click', '.remove-supplier', function () {
        $(this).closest('.form-row').remove();
    });

    $('#add-proveedor').click(addSupplierRow);

    // ✅ Autocomplete de proveedores
    $(document).on("focus", ".supplier-autocomplete", function () {
        if (!$(this).data("ui-autocomplete")) {
            $(this).autocomplete({
                source: "/logis/autocomplete/supplier/",
                minLength: 2,
                select: function (event, ui) {
                    $(this).val(ui.item.label);
                    $(this).closest(".form-row").find("input[name$='supplier']").val(ui.item.id);
                    return false;
                }
            });
        }
    });

    // ✅ Autocomplete de productos
    $(document).on("focus", ".product-autocomplete", function () {
        if (!$(this).data("ui-autocomplete")) {
            $(this).autocomplete({
                source: "/logis/autocomplete/product/",
                minLength: 2,
                select: function (event, ui) {
                    $(this).val(ui.item.label);
                    $(this).closest(".form-row").find("input[name$='product']").val(ui.item.id);
                    return false;
                }
            });
        }
    });

    // ✅ Proyecto → Centro de costo
    const proyectoMap = window.proyectoMap || {};
    $('#id_presale').change(function () {
        $('#id_cost_center').val(proyectoMap[$(this).val()] || '');
    });
    if ($('#id_presale').val()) {
        $('#id_cost_center').val(proyectoMap[$('#id_presale').val()] || '');
    }

    // ✅ Inicializar total
    calculateOrderTotal();
});

// ====== Inicialización alternativa para carga dinámica ======
document.addEventListener('DOMContentLoaded', function() {
    // Solo inicializar si jQuery no está manejando ya el ready
    if (!window.jQuery || !window.jQuery.ready) {
        initializeProjectDropdown();
    }
});

// ==============================
// AJAX helpers para edición en grid
// ==============================
function getCSRFToken() {
    const name = 'csrftoken';
    const cookies = document.cookie ? document.cookie.split(';') : [];
    for (let i = 0; i < cookies.length; i++) {
        const c = cookies[i].trim();
        if (c.substring(0, name.length + 1) === (name + '=')) {
            return decodeURIComponent(c.substring(name.length + 1));
        }
    }
    return '';
}

async function updateSupplierStatus(selectEl) {
    const po = selectEl.getAttribute('data-po');
    const ruc = selectEl.getAttribute('data-ruc');
    const status = selectEl.value;

    try {
        const res = await fetch('/logis/ajax/update-supplier-status/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCSRFToken(),
            },
            body: new URLSearchParams({ po_number: po, supplier_ruc: ruc, status })
        });
        if (!res.ok) {
            const data = await res.json().catch(() => ({}));
            console.error('Error al actualizar supplier_status:', data.error || res.statusText);
        }
    } catch (e) {
        console.error('Error de red al actualizar supplier_status:', e);
    }
}

async function updateContabStatus(selectEl) {
    const po = selectEl.getAttribute('data-po');
    const ruc = selectEl.getAttribute('data-ruc');
    const status = selectEl.value;

    try {
        const res = await fetch('/logis/ajax/update-contabilidad-status/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCSRFToken(),
            },
            body: new URLSearchParams({ po_number: po, supplier_ruc: ruc, status })
        });
        if (!res.ok) {
            const data = await res.json().catch(() => ({}));
            console.error('Error al actualizar status_factura_contabilidad:', data.error || res.statusText);
        }
    } catch (e) {
        console.error('Error de red al actualizar status_factura_contabilidad:', e);
    }
}