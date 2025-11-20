# Documentación de Contabilidad: Flujo de Verificación Bancaria y Facturas de Cliente

Esta guía describe el modelo `ClientInvoice`, el flujo de estados de cobranza, las vistas, URLs y plantillas involucradas en la verificación bancaria y dashboards contables.

## Modelo `ClientInvoice`

Archivo: `projects/models/client_invoice.py`

- Estados (`INVOICE_STATUS`):
  - `BORRADOR`, `EMITIDA`, `PAGO_REPORTADO`, `PAGO_VERIFICADO`, `PAGADA`, `VENCIDA`, `PAGO_NO_RECIBIDO`, `CONTROVERSIA`.
- Campos clave:
  - `project`: relación con `Projects` (identificador `cod_projects_id`).
  - `invoice_number`, `invoice_date`, `amount`, `description`.
  - `status`: estado actual de la factura.
  - Fechas de flujo: `due_date`, `payment_reported_date`, `bank_verified_date`, `fully_paid_date`.
  - Montos: `paid_amount` (monto real recibido).
  - Banco: `bank_reference`, `bank_confirmation_code`.
  - Auditoría: `reported_by`, `verified_by`; notas `client_notes`, `internal_notes`, `verification_notes`.
  - Flags: `is_urgent`, `reminder_sent`.
- `save(...)` con automatización:
  - Si `status == 'PAGO_VERIFICADO'` → se cambia automáticamente a `PAGADA`, se asigna `fully_paid_date = hoy` y si `paid_amount` está vacío se iguala a `amount`.
  - Sincroniza estado legacy en `payment_status` (`PENDING`, `PAID`, `OVERDUE`, `PROBLEM`).
- Propiedades y helpers:
  - `is_overdue`: vencida si `due_date` pasó con `status in ['EMITIDA', 'PAGO_REPORTADO']`.
  - `days_since_reported`: días desde `payment_reported_date`.
  - `is_fully_paid`: `status == 'PAGADA'` y `paid_amount >= amount`.
  - `can_report_payment`: sólo si `status == 'EMITIDA'`.
  - `can_verify_payment`: sólo si `status == 'PAGO_REPORTADO'`.

## Diferenciación con `Invoice` (Proveedores)

- `projects/models/invoice.py` guarda facturas recibidas de proveedores (para costos reales `AC`).
- `ClientInvoice` son facturas emitidas al cliente (cobranza).
- AC en EVM usa `Invoice` proveedor; la eficiencia de cobranza y verificación bancaria usa `ClientInvoice`.

## Vistas y URLs

- Archivo de URLs: `projects/urls/contabilidad.py`.
  - `''` → `contabilidad_seleccion`.
  - `'jefe/'` → `contabilidad_jefe` (dashboard del jefe).
  - `'asistente/'` → `contabilidad_asistente`.
  - `'facturas-clientes/'` → `factura_cliente_list`.
  - `'facturas-clientes/crear/'` → `factura_cliente_crear`.
  - `'factura/<int:factura_id>/reportar-pago/'` → `factura_reportar_pago`.
  - `'factura/<int:factura_id>/verificar-pago/'` → `factura_verificar_pago`.
  - `'verificacion-bancaria/'` y `'verificacion-bancaria-simple/'` → `verificacion_bancaria_simple`.
  - `'pagos/'` → `pagos_status`, `'reportes/'` → `reportes_contables`.

- Archivo de vistas: `projects/views/contabilidad/contabilidad_views.py`.
  - `contabilidad_jefe`: agrega métricas de cobranza por proyecto (total, pagado, pendiente, eficiencia), pendientes de verificación, alertas; renderiza `contabilidad/jefe/dashboard.html`.
  - `verificacion_bancaria_simple`: motor para confirmar pagos por referencia bancaria.
  - `factura_verificar_pago`: pantalla para verificar un pago de una `ClientInvoice`.
  - `reportar_pago`: cambia estado a `PAGO_REPORTADO` y registra `payment_reported_date`.
  - `pagos_status`: estado global de pagos.

## Plantillas

- `projects/templates/contabilidad/verificacion_bancaria.html`:
  - Extiende `base_contabilidad.html`; navegación a `jefe_dashboard`, `verificacion_bancaria_simple`, `factura_cliente_list`, `reportes_contables`.
  - Botón para volver al dashboard.
- `projects/templates/contabilidad/jefe/dashboard.html`:
  - Resumen de cobranza con métricas por proyecto y acciones rápidas.
- `projects/templates/contabilidad/factura_verificar_pago.html`:
  - Muestra información de `ClientInvoice` y permite confirmar verificación.
- `projects/templates/contabilidad/dashboard.html`:
  - Panel general con accesos a facturas, pagos y reportes.

## Flujo End-to-End de Cobranza

1. Emisión: crear `ClientInvoice` → `status='EMITIDA'`, opcional `due_date`.
2. Reporte de pago: cliente reporta → `status='PAGO_REPORTADO'`, `payment_reported_date`.
3. Verificación bancaria: confirmar en `verificacion_bancaria_simple` → `status='PAGO_VERIFICADO'` → automáticamente `PAGADA` al guardar.
   - Se registra `fully_paid_date` y `paid_amount` si faltaba.
   - Se pueden registrar `bank_reference` y `bank_confirmation_code`.
4. Estado y métricas: dashboards muestran pendientes, problemas, eficiencia y alertas.

## Integración con PMI/EVM

- La verificación bancaria y cobranza (`ClientInvoice`) alimenta dashboards y métricas de facturación.
- Los costos reales EVM (`AC`) provienen de `Invoice` de proveedores asociadas a `PurchaseOrder`.
- El dashboard PMI (`projects/pmi_dashboard.html`) puede mostrar métricas financieras básicas junto a EVM, pero no usa `ClientInvoice` para `AC`.

## Buenas Prácticas

- Asociar cada `ClientInvoice` correctamente a `Projects`.
- Mantener `bank_reference` y `bank_confirmation_code` para trazabilidad.
- Usar `can_report_payment`/`can_verify_payment` para respetar el flujo.
- Revisar `is_overdue` para alertar vencidos y disparar recordatorios.