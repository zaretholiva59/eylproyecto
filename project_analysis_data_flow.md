# 🔄 DIAGRAMA DE FLUJO DE DATOS - PROYECTO EYL

## 🏗️ ARQUITECTURA DE FLUJO GENERAL

```mermaid
graph TB
    subgraph "ENTRADA DE DATOS"
        Cliente[👤 Cliente]
        Oportunidad[🎯 Oportunidad Comercial]
    end
    
    subgraph "MÓDULO COMERCIAL/PRESALE"
        Costumer[👤 Costumer]
        Chance[🎯 Chance]
        Presale[💼 Presale]
    end
    
    subgraph "MÓDULO PMI/PROYECTOS"
        Projects[🏗️ Projects]
        ProjectActivity[📋 ProjectActivity]
        ProjectBaseline[📊 ProjectBaseline]
        EarnedValue[💰 EarnedValue]
        ProjectProgress[📈 ProjectProgress]
    end
    
    subgraph "MÓDULO LOGÍSTICA"
        PurchaseOrder[📋 PurchaseOrder]
        PODetailProduct[📦 PODetailProduct]
        Supplier[🏭 Supplier]
        Product[📦 Product]
    end
    
    subgraph "MÓDULO CONTABILIDAD"
        Invoice[🧾 Invoice]
        ClientInvoice[💳 ClientInvoice]
        Billing[💰 Billing]
    end
    
    subgraph "SERVICIOS DE NEGOCIO"
        EVMCalculator[🧮 EarnedValueCalculator]
        BaselineService[📊 BaselineService]
        ActivityCalculator[📋 ActivityCalculator]
    end
    
    %% FLUJO PRINCIPAL
    Cliente --> Costumer
    Oportunidad --> Chance
    Costumer --> Chance
    Chance --> Presale
    Presale --> Projects
    
    %% FLUJO PMI
    Projects --> ProjectActivity
    Projects --> ProjectBaseline
    ProjectActivity --> ProjectProgress
    ProjectBaseline --> EarnedValue
    ProjectProgress --> EarnedValue
    
    %% FLUJO LOGÍSTICA
    Projects --> PurchaseOrder
    Supplier --> Product
    Product --> PODetailProduct
    PurchaseOrder --> PODetailProduct
    
    %% FLUJO CONTABILIDAD
    PurchaseOrder --> Invoice
    Projects --> ClientInvoice
    Invoice --> Billing
    
    %% SERVICIOS
    Projects --> EVMCalculator
    ProjectActivity --> ActivityCalculator
    Projects --> BaselineService
    EVMCalculator --> EarnedValue
    
    %% RETROALIMENTACIÓN
    PurchaseOrder -.-> EarnedValue
    Invoice -.-> EarnedValue
```

## 📊 FLUJOS DE DATOS DETALLADOS

### 1. **FLUJO COMERCIAL → PMI**

```mermaid
sequenceDiagram
    participant C as Cliente
    participant Ch as Chance
    participant P as Presale
    participant Pr as Projects
    participant PB as ProjectBaseline
    
    C->>Ch: Genera oportunidad
    Note over Ch: probability, estimated_value
    Ch->>P: Se convierte en preventa
    Note over P: estimated_budget, estimated_duration
    P->>Pr: Se aprueba como proyecto
    Note over Pr: budget (BAC), start_date, end_date
    Pr->>PB: Crea línea base
    Note over PB: planned_budget, planned_schedule
```

**Datos Transferidos:**
- `Chance.estimated_value` → `Presale.estimated_budget`
- `Presale.estimated_budget` → `Projects.budget` (BAC)
- `Presale.estimated_duration` → `Projects.estimated_duration`
- `Projects.budget` → `ProjectBaseline.planned_budget`

---

### 2. **FLUJO PMI → EVM CALCULATION**

```mermaid
sequenceDiagram
    participant PA as ProjectActivity
    participant PP as ProjectProgress
    participant PB as ProjectBaseline
    participant EVC as EarnedValueCalculator
    participant EV as EarnedValue
    participant PO as PurchaseOrder
    
    PA->>PP: Actualiza progreso físico
    Note over PP: physical_progress %
    PB->>EVC: Proporciona PV (Planned Value)
    PP->>EVC: Proporciona progreso para EV
    PO->>EVC: Proporciona AC (Actual Cost)
    EVC->>EV: Calcula métricas EVM
    Note over EV: PV, EV, AC, CPI, SPI, BAC
```

**Fórmulas EVM Aplicadas:**
- `PV = ProjectBaseline.planned_budget * % tiempo transcurrido`
- `EV = Projects.budget * ProjectActivity.physical_progress`
- `AC = Σ(PurchaseOrder.total_amount)`
- `CPI = EV / AC`
- `SPI = EV / PV`

---

### 3. **FLUJO LOGÍSTICA → CONTABILIDAD**

```mermaid
sequenceDiagram
    participant Pr as Projects
    participant PO as PurchaseOrder
    participant POD as PODetailProduct
    participant Inv as Invoice
    participant CI as ClientInvoice
    participant B as Billing
    
    Pr->>PO: Genera orden de compra
    Note over PO: po_number, total_amount
    PO->>POD: Detalla productos
    Note over POD: quantity, unit_price, total_price
    PO->>Inv: Genera factura de proveedor
    Note over Inv: invoice_number, amount
    Pr->>CI: Genera factura a cliente
    Note over CI: invoice_amount, status
    Inv->>B: Registra facturación
    Note over B: billing_amount, payment_status
```

**Datos de Control Financiero:**
- `PODetailProduct.total_price` → `PurchaseOrder.total_amount`
- `PurchaseOrder.total_amount` → `Invoice.amount`
- `Projects.budget` → `ClientInvoice.invoice_amount`
- `Invoice.amount` → `Billing.billing_amount`

---

### 4. **FLUJO DE ACTUALIZACIÓN DE PROGRESO**

```mermaid
flowchart TD
    A[Usuario actualiza actividad] --> B[ProjectActivity.physical_progress]
    B --> C[ActivityCalculator.recalculate_weights]
    C --> D[Projects.physical_progress]
    D --> E[EarnedValueCalculator.calculate]
    E --> F[EarnedValue.earned_value]
    F --> G[Dashboard actualizado]
    
    H[Nueva Purchase Order] --> I[PurchaseOrder.total_amount]
    I --> J[EarnedValueCalculator.calculate]
    J --> K[EarnedValue.actual_cost]
    K --> G
```

---

## 🔄 CICLOS DE RETROALIMENTACIÓN

### **Ciclo EVM (Earned Value Management)**
```mermaid
graph LR
    A[Planificación<br/>ProjectBaseline] --> B[Ejecución<br/>ProjectActivity]
    B --> C[Medición<br/>ProjectProgress]
    C --> D[Análisis<br/>EarnedValue]
    D --> E[Control<br/>BudgetChange]
    E --> A
```

### **Ciclo Financiero**
```mermaid
graph LR
    A[Presupuesto<br/>Projects.budget] --> B[Compras<br/>PurchaseOrder]
    B --> C[Facturas<br/>Invoice]
    C --> D[Pagos<br/>Billing]
    D --> E[Facturación Cliente<br/>ClientInvoice]
    E --> A
```

---

## 📈 MÉTRICAS Y KPIS CALCULADOS

### **Métricas EVM Principales**
```python
# Calculadas por EarnedValueCalculator
PV = planned_value          # Valor Planificado
EV = earned_value          # Valor Ganado  
AC = actual_cost           # Costo Real
BAC = budget_at_completion # Presupuesto al Completar

# Índices de Performance
CPI = EV / AC             # Cost Performance Index
SPI = EV / PV             # Schedule Performance Index

# Proyecciones
EAC = BAC / CPI           # Estimate at Completion
ETC = EAC - AC            # Estimate to Complete
VAC = BAC - EAC           # Variance at Completion
```

### **Métricas de Progreso**
```python
# Calculadas por ActivityCalculator
physical_progress = Σ(activity.physical_progress * activity.weight)
schedule_variance = EV - PV
cost_variance = EV - AC
```

---

## 🎯 PUNTOS DE INTEGRACIÓN CRÍTICOS

### **1. Sincronización Presale → Projects**
- **Trigger**: Aprobación de preventa
- **Datos**: `estimated_budget`, `estimated_duration`, `description`
- **Validación**: Budget > 0, fechas válidas

### **2. Actualización Projects → EVM**
- **Trigger**: Cambio en `physical_progress` o nueva `PurchaseOrder`
- **Proceso**: Recálculo automático de métricas EVM
- **Persistencia**: `EarnedValue` model

### **3. Control PurchaseOrder → AC**
- **Trigger**: Creación/modificación de OC
- **Impacto**: Actualización de `actual_cost` en EVM
- **Validación**: Verificación de presupuesto disponible

### **4. Facturación Projects → ClientInvoice**
- **Trigger**: Hito de facturación o % completado
- **Datos**: Monto basado en `earned_value`
- **Control**: Estado de pagos y cobranza

---

## ⚡ EVENTOS Y TRIGGERS DEL SISTEMA

### **Eventos Automáticos**
```python
# Cuando se actualiza physical_progress
ProjectActivity.save() → ActivityCalculator.recalculate() → EarnedValue.update()

# Cuando se crea/modifica PurchaseOrder  
PurchaseOrder.save() → EarnedValueCalculator.update_ac() → EarnedValue.update()

# Cuando se cambia estado de Invoice
Invoice.save() → Billing.update_status() → Cash_flow.update()
```

### **Eventos Manuales**
```python
# Dashboard refresh
User.click_refresh() → EarnedValueCalculator.calculate_all() → Dashboard.update()

# Baseline recalculation
User.recalculate_baseline() → BaselineService.update() → ProjectBaseline.save()

# Activity weight redistribution
User.recalculate_weights() → ActivityCalculator.redistribute() → ProjectActivity.save()
```

---

## 🔍 ANÁLISIS DE DEPENDENCIAS

### **Dependencias Fuertes (Críticas)**
- `Presale` ↔ `Projects` (OneToOne)
- `Projects` → `EarnedValue` (Cálculos EVM)
- `PurchaseOrder` → `PODetailProduct` (Integridad financiera)

### **Dependencias Débiles (Opcionales)**
- `Projects` → `ClientInvoice` (Facturación)
- `Invoice` → `Billing` (Control contable)
- `ProjectActivity` → `Hoursrecord` (Seguimiento tiempo)

### **Dependencias Calculadas (Derivadas)**
- `ProjectActivity.physical_progress` → `Projects.physical_progress`
- `PODetailProduct.total_price` → `PurchaseOrder.total_amount`
- `PurchaseOrder.total_amount` → `EarnedValue.actual_cost`

---

## 🚨 PUNTOS DE ATENCIÓN

### **Consistencia de Datos**
- ✅ Verificar que `Projects.budget` = `ProjectBaseline.planned_budget`
- ✅ Validar que `Σ(PODetailProduct.total_price)` = `PurchaseOrder.total_amount`
- ✅ Confirmar que `physical_progress` esté entre 0-100%

### **Performance**
- ⚡ Cálculos EVM pueden ser costosos con muchas actividades
- ⚡ Considerar cache para métricas frecuentemente consultadas
- ⚡ Optimizar queries N+1 en dashboard

### **Integridad Referencial**
- 🔒 `Projects` no debe eliminarse si tiene `PurchaseOrder` asociadas
- 🔒 `Supplier` no debe eliminarse si tiene `Product` activos
- 🔒 `ProjectActivity` debe mantener consistencia de pesos (suma = 100%)