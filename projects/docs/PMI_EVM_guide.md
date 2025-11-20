# Guía técnica de Earned Value Management (PMI) en el sistema

Esta guía documenta las fórmulas, fuentes de datos, servicios y vistas que implementan el dashboard PMI/EVM en el proyecto. Incluye cómo se calcula cada métrica y cómo se integran en la plantilla de visualización.

## Fuentes de Datos

- Presupuesto base (BAC): `Presale.total_cost` del proyecto.
- Costos reales (AC): `Invoice.total_amount` vinculadas a `PurchaseOrder` del proyecto, agregadas por mes según `issue_date`.
- Avance físico y pesos: `ProjectActivity` (complejidad, esfuerzo, impacto, % completado), calculados con `ActivityCalculator`.
- Proyecto: `Projects` (clave `cod_projects_id`).

## Archivos Clave

- Servicios EVM:
  - `projects/services/earned_value/calculator.py` → `EarnedValueCalculator`
  - `projects/services/earned_value/activity_calculator.py` → `ActivityCalculator`
  - `projects/services/earned_value/metrics.py` → `ProjectMetrics`
- Vistas y URLs:
  - `projects/views/project/dashboard_view.py` → `pmi_dashboard`
  - `projects/urls/pmi.py` → ruta `project/<str:project_id>/pmi-dashboard/`
- Plantilla:
  - `projects/templates/projects/pmi_dashboard.html`

## Fórmulas EVM

Las métricas se calculan en `EarnedValueCalculator.calculate_metrics(...)` y se alimentan con datos de `calculate_earned_value(...)`:

- EV (Earned Value):
  - `EV = BAC × (progreso_físico / 100)`
  - Progreso físico agregando pesos y % completados de actividades.
- AC (Actual Cost):
  - Suma de `Invoice.total_amount` relacionadas con el proyecto a través de `PurchaseOrder`.
  - Se construye una curva mensual acumulada usando `issue_date`.
- PV (Planned Value):
  - Distribución lineal del `BAC` sobre la duración del proyecto.
  - `PV(t) = BAC × (tiempo_transcurrido / duración_total)`.
- Métricas principales:
  - `CPI = EV / AC` (eficiencia de costo; ≥ 1 es bueno).
  - `SPI = EV / PV` (eficiencia de cronograma; ≥ 1 adelantado).
  - `CV = EV - AC` (variación de costo; positivo indica ahorro).
  - `SV = EV - PV` (variación de cronograma; positivo indica adelanto).
  - `EAC = BAC / CPI` (Estimación al completar, suponiendo desempeño constante).
  - `ETC = EAC - AC` (costo restante para completar).

### Índices avanzados (`ProjectMetrics`)

- `TCPI = (BAC - EV) / (BAC - AC)` (para objetivo BAC), o variantes contra `EAC`.
- `VAC = BAC - EAC`.
- Ratios de costo/cronograma y análisis de tendencia (basados en `CPI` y `SPI`).
- Métricas de riesgo: niveles de costo, cronograma y global con alertas.
- Forecast: escenarios `EAC/ETC` actual, optimista y pesimista, días estimados a conclusión.
- Calidad: consistencia y confiabilidad del avance físico.

## Avance Físico y Pesos (`ActivityCalculator`)

- Peso de actividad: `peso_i = (complejidad + esfuerzo + impacto) / Σ(puntos) × 100`.
- Validación: la suma de pesos debe ser ≈ 100% (tolerancia pequeña).
- Progreso físico total: `Σ(peso_i × %_completado_i) / 100`.
- Detalle físico: `get_physical_progress_detail(project_id)` retorna aporte por actividad, progreso total y validez de pesos.

## Orquestación (`EarnedValueCalculator.calculate_earned_value`)

1. Obtiene `BAC` desde `Presale.total_cost` (`get_bac_real`).
2. Calcula avance físico con `ActivityCalculator.calculate_physical_progress`.
3. Calcula `EV` proporcional a avance físico.
4. Calcula `AC` agregando facturas (`Invoice`) por mes.
5. Calcula `PV` con distribución lineal.
6. Calcula métricas `CPI`, `SPI`, `CV`, `SV`, `EAC`, `ETC`.
7. Genera `curve_data` con `months`, `pv`, `ev`, `ac` y `metrics`.

## Vistas y Uso

- URL: `project/<project_id>/pmi-dashboard/` mapea a `projects.views.project.dashboard_view.pmi_dashboard`.
- La vista:
  - Busca el `Projects` por `cod_projects_id`.
  - Llama `EarnedValueCalculator.calculate_earned_value(project_id)`.
  - Llama `EarnedValueCalculator.get_physical_progress_detail(project_id)`.
  - Integra métricas financieras y análisis (`analyze_performance`).
  - Renderiza `projects/pmi_dashboard.html`.

### Ejemplo de uso en código

```python
from projects.services.earned_value.calculator import EarnedValueCalculator

project_id = "PRJ-001"
evm = EarnedValueCalculator.calculate_earned_value(project_id)

bac = evm['bac_calculated']
cpi = evm['metrics']['cpi']
spi = evm['metrics']['spi']
ev_last = evm['curve_data']['ev'][-1]
pv_last = evm['curve_data']['pv'][-1]
ac_last = evm['curve_data']['ac'][-1]
```

## Plantilla

- `projects/templates/projects/pmi_dashboard.html` muestra:
  - KPI: `CPI`, `SPI`, `EAC`, `physical_progress`, `BAC`, `AC`, `EV`, `PV`.
  - Métricas financieras básicas (monto del contrato, total facturado).
  - Indicador de cumplimiento PMI (`pmi_compliant`) basado en umbrales.

## Supuestos y Consideraciones

- Protección ante división por cero: si `AC` o `PV` son 0, revisar manejo para `CPI` y `SPI`.
- Pesos de actividades deben sumar ≈ 100%; usar `validate_weights_sum`.
- Duración del proyecto: si falta, la distribución lineal de `PV` necesita valores por defecto.
- `AC` se basa en facturas (`Invoice`) de proveedores asociadas a órdenes del proyecto; no en facturas a cliente.

## Mapa Rápido

- BAC → `Presale.total_cost`.
- Avance físico → `ActivityCalculator` sobre `ProjectActivity`.
- EV → proporcional al avance físico.
- AC → `Invoice.total_amount` (curva mensual por `issue_date`).
- PV → distribución lineal del BAC.
- Dashboard → `pmi_dashboard` + `pmi_dashboard.html`.