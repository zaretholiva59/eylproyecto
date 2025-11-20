# services/earned_value/calculator.py
from decimal import Decimal
from datetime import date
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from projects.models import Projects, PurchaseOrder, PODetailProduct, BudgetChange, ProjectActivity, Invoice, ClientInvoice
from .activity_calculator import ActivityCalculator  # ✅ Import limpio
from projects.services.baseline_service import BaselineService

class EarnedValueCalculator:
    """
    Servicio principal para Earned Value Management
    Usa ActivityCalculator para cálculos de avance físico
    """

    @staticmethod
    def calculate_earned_value(project_id):
        """
        Calcula datos EVM según estándar PMI - CON AVANCE FÍSICO REAL
        """
        project = Projects.objects.get(cod_projects_id=project_id)
        
        # 1. BAC desde Chance/Baseline
        bac = EarnedValueCalculator.get_bac_real(project)
        
        # 2. Duración del proyecto
        duration = project.estimated_duration or 12

        # 2.1 Fecha de inicio segura (corrige inconsistencias)
        start_date_safe = EarnedValueCalculator.get_safe_start_date(project)
        
        # 3. ✅ AVANCE FÍSICO desde ActivityCalculator
        physical_progress = ActivityCalculator.calculate_physical_progress(project)
        
        # 4. ✅ EV basado en avance físico real
        ev_total = bac * (physical_progress / Decimal('100.00'))
        
        # 5. AC desde OCs (costos reales)
        ac_data = EarnedValueCalculator.calculate_actual_cost_real(project, duration)
        # 5.1 Pagos verificados (cliente) como serie acumulada paralela
        ac_paid_data = EarnedValueCalculator.calculate_verified_payments_series(project, duration)
        
        # 6. PV acumulado lineal a lo largo de toda la duración (evita ceros iniciales)
        pv_data = EarnedValueCalculator.calculate_planned_value_pmi(bac, duration, start_date_safe)
        
        # 7. Métricas EVM (preliminar, se recalcula tras integrar baseline)
        metrics = EarnedValueCalculator.calculate_metrics(pv_data, [ev_total] * duration, ac_data, bac)
        
        # ➕ Datos por semanas y días (para filtros de visualización)
        weekly = EarnedValueCalculator._build_granular_curves(project, duration, bac, physical_progress, start_date_safe, interval_days=7)
        daily = EarnedValueCalculator._build_granular_curves(project, duration, bac, physical_progress, start_date_safe, interval_days=1)

        # EV mensual como acumulado progresivo lineal hasta el EV total
        ev_months = []
        for i in range(duration):
            frac = Decimal(str((i + 1) / duration))
            ev_months.append(ev_total * frac)

        # ==== Integración con Baseline persistente ====
        baseline_arrays = BaselineService.get_monthly_arrays(project_id)
        if baseline_arrays and baseline_arrays.get('months'):
            # Usar la longitud/meses del baseline para graficar
            duration = len(baseline_arrays['months'])
            # PV siempre desde baseline (plan)
            pv_data = [Decimal(str(x)) for x in baseline_arrays['pv']]

            # EV: solo usar baseline si no existe avance físico real
            try:
                has_progress = float(physical_progress or 0) > 0.0 and ev_total > Decimal('0')
            except Exception:
                has_progress = False
            if has_progress:
                # Recalcular rampa EV con la nueva duración
                ev_months = []
                for i in range(duration):
                    frac = Decimal(str((i + 1) / duration))
                    ev_months.append(ev_total * frac)
            else:
                ev_months = [Decimal(str(x)) for x in baseline_arrays['ev']]

            # Solo sobrescribir AC si la serie real está vacía/cero
            ac_is_zero = all(v == 0 for v in [float(x) for x in ac_data])
            if ac_is_zero:
                ac_data = [Decimal(str(x)) for x in baseline_arrays['ac']]

            # Recalcular series relacionadas con nueva duración
            ac_paid_data = EarnedValueCalculator.calculate_verified_payments_series(project, duration)
            weekly = EarnedValueCalculator._build_granular_curves(project, duration, bac, physical_progress, start_date_safe, interval_days=7)
            daily = EarnedValueCalculator._build_granular_curves(project, duration, bac, physical_progress, start_date_safe, interval_days=1)

            # Asegurar series no decrecientes
            pv_data = EarnedValueCalculator._ensure_non_decreasing(pv_data)
            ev_months = EarnedValueCalculator._ensure_non_decreasing(ev_months)
            ac_data = EarnedValueCalculator._ensure_non_decreasing(ac_data)
            ac_paid_data = EarnedValueCalculator._ensure_non_decreasing(ac_paid_data)

            # Recalcular métricas con las series finales
            metrics = EarnedValueCalculator.calculate_metrics(pv_data, ev_months, ac_data, bac)

        return {
            'curve_data': {
                'months': list(range(1, duration + 1)),
                'pv': [float(val) for val in pv_data],
                'ev': [float(val) for val in ev_months],
                'ac': [float(val) for val in ac_data],
                'ac_paid': [float(val) for val in ac_paid_data]
            },
            'curve_data_weekly': weekly,
            'curve_data_daily': daily,
            'metrics': metrics,
            'bac_calculated': float(bac),
            'physical_progress': float(physical_progress),
            'pmi_compliant': True
        }

    @staticmethod
    def calculate_verified_payments_series(project, duration):
        """
        Serie acumulada mensual de pagos verificados del cliente.
        Usa ClientInvoice con prioridad de fecha:
        fully_paid_date > bank_verified_date > payment_reported_date > invoice_date
        Monto: paid_amount si existe, caso contrario amount.
        """
        invoices = ClientInvoice.objects.filter(project=project, status__in=['PAGO_VERIFICADO', 'PAGADA']).order_by('invoice_date')
        if not invoices.exists():
            return [Decimal('0.00')] * duration

        # Fecha de referencia
        ref_date = project.start_date or timezone.now().date()
        # Construir mapa mes -> monto pagado verificado
        monthly = {}
        for inv in invoices:
            # Escoger la mejor fecha disponible
            inv_date = inv.fully_paid_date or inv.bank_verified_date or inv.payment_reported_date or inv.invoice_date
            if not inv_date:
                continue
            # Índice de mes relativo a ref_date
            try:
                idx = (inv_date.year - ref_date.year) * 12 + (inv_date.month - ref_date.month)
            except Exception:
                continue
            if idx < 0 or idx >= duration:
                continue
            amount = Decimal(str(getattr(inv, 'paid_amount', None) or inv.amount or 0))
            monthly[idx] = monthly.get(idx, Decimal('0')) + amount
        # Convertir a acumulado
        series = []
        acc = Decimal('0')
        for i in range(duration):
            acc += monthly.get(i, Decimal('0'))
            series.append(acc)
        return series

    @staticmethod
    def calculate_planned_value_pmi(bac, duration, start_date):
        """Genera una serie acumulada lineal de PV"""
        bac = Decimal(str(bac or 0))
        months = int(duration or 0)
        if months <= 0:
            return []
        step = bac / Decimal(months)
        acc = Decimal('0')
        out = []
        for i in range(months):
            acc += step
            out.append(acc)
        if out:
            out[-1] = bac
        return out

    @staticmethod
    def calculate_actual_cost_real(project, duration):
        invoices = Invoice.objects.filter(purchase_order__project_code=project).order_by('issue_date')
        if not invoices.exists():
            return [Decimal('0.00')] * duration
        acc = Decimal('0')
        series = []
        for i in range(duration):
            # Agrupar por mes desde start_date seguro
            series.append(acc)
        # Recalcular agrupando por fecha real
        monthly = {}
        for inv in invoices:
            if not inv.issue_date:
                continue
            idx_key = inv.issue_date.strftime('%Y-%m')
            monthly[idx_key] = monthly.get(idx_key, Decimal('0')) + Decimal(str(inv.total_amount or 0))
        # Ordenar claves y construir acumulado
        acc = Decimal('0')
        series = []
        for key in sorted(monthly.keys()):
            acc += monthly[key]
            series.append(acc)
        # Completar longitud a duration
        while len(series) < duration:
            series.append(acc)
        return series

    @staticmethod
    def calculate_metrics(pv, ev, ac, bac):
        """
        Calcula métricas básicas EVM
        """
        if not pv or not ev or not ac:
            return {
                'cpi': 1.0, 'spi': 1.0, 'cv': 0, 'sv': 0,
                'eac': float(bac), 'etc': float(bac)
            }

        current_pv = pv[-1]
        current_ev = ev[-1]
        current_ac = ac[-1]

        cpi = current_ev / current_ac if current_ac > 0 else Decimal('1.0')
        spi = current_ev / current_pv if current_pv > 0 else Decimal('1.0')
        cv = current_ev - current_ac
        sv = current_ev - current_pv
        eac = bac / cpi if cpi > 0 else bac
        etc = eac - current_ac

        return {
            'cpi': float(cpi),
            'spi': float(spi),
            'cv': float(cv),
            'sv': float(sv),
            'eac': float(eac),
            'vac': float(bac - eac),
            'etc': float(etc)
        }

    @staticmethod
    def _ensure_non_decreasing(series):
        """Asegura que la serie sea acumulada no decreciente (corrige caídas accidentales)."""
        cleaned = []
        last = Decimal('0')
        for val in series or []:
            try:
                v = Decimal(str(val or 0))
            except Exception:
                v = Decimal('0')
            if v < last:
                v = last
            cleaned.append(v)
            last = v
        return cleaned

    @staticmethod
    def get_safe_start_date(project):
        """
        Determina una fecha de inicio consistente para PV.
        Prioridad:
        1) project.start_date si es válida y <= hoy
        2) Primera OC (PurchaseOrder.issue_date)
        3) Primera actividad (ProjectActivity.created_at)
        4) last_progress_update si existe
        Si no hay datos, retorna project.start_date o None.
        """
        from datetime import date

        today = date.today()
        # 1) start_date válida
        if project.start_date and project.start_date <= today:
            return project.start_date

        # 2) primera OC
        try:
            po_first = PurchaseOrder.objects.filter(project_code=project).order_by('issue_date').values_list('issue_date', flat=True).first()
        except Exception:
            po_first = None

        # 3) primera actividad
        try:
            act_first_dt = ProjectActivity.objects.filter(project=project, is_active=True).order_by('created_at').values_list('created_at', flat=True).first()
            act_first = act_first_dt.date() if act_first_dt else None
        except Exception:
            act_first = None

        # 4) última actualización de progreso (como respaldo)
        lp = project.last_progress_update if project.last_progress_update else None

        candidates = [d for d in [po_first, act_first, lp] if d]
        # tomar la más antigua que no sea futura
        past_candidates = [d for d in candidates if d <= today]
        if past_candidates:
            return min(past_candidates)

        # si no hay candidatos en el pasado pero existe start_date, usarla
        return project.start_date or None

    @staticmethod
    def get_bac_real(project):
        """
        Calcula el BAC Real (presupuesto vigente):
        - Base: Chance.total_costs (preferido) o Chance.cost_aprox_chance
        - Ajuste: + suma de BudgetChange aprobados (re-baseline / órdenes de cambio)
        """
        bac_baseline = None

        # 1) Baseline desde Chance
        try:
            chance = project.cod_projects
            if getattr(chance, 'total_costs', None):
                bac_baseline = Decimal(str(chance.total_costs))
            elif getattr(chance, 'cost_aprox_chance', None):
                bac_baseline = Decimal(str(chance.cost_aprox_chance))
        except Exception as e:
            print(f"⚠️ Error obteniendo Chance: {e}")

        if bac_baseline is None:
            raise ValueError("No hay BAC disponible (necesita Chance con costos)")

        # 3) Ajuste por cambios aprobados
        try:
            changes_total = BudgetChange.objects.filter(project=project, status='Aprobado').aggregate(total=Sum('amount'))['total']
            changes_total = Decimal(str(changes_total)) if changes_total is not None else Decimal('0.00')
        except Exception as e:
            print(f"⚠️ Error obteniendo BudgetChange: {e}")
            changes_total = Decimal('0.00')

        # 4) BAC vigente (Real)
        return bac_baseline + changes_total

    @staticmethod
    def calculate_actual_cost_real(project, duration):
        """
        AC - Costo real preferentemente desde FACTURAS de proveedores.
        Fallback: usar detalles de OC cuando no existan facturas.
        """
        # 1) Intentar con FACTURAS (Invoice) vinculadas a OCs del proyecto
        invoices = Invoice.objects.filter(
            purchase_order__project_code=project
        ).select_related('purchase_order').order_by('issue_date')

        if invoices.exists():
            # Usar la primera fecha de factura como referencia
            first_invoice = next((inv for inv in invoices if inv.issue_date), None)
            if not first_invoice:
                return [Decimal('0.00')] * duration
            start_date = first_invoice.issue_date

            ac_by_month = [Decimal('0.00')] * duration
            for inv in invoices:
                if not inv.issue_date:
                    continue
                # Convertir a moneda local si es necesario
                exchange = Decimal(str(inv.exchange_rate or 1))
                amount_local = Decimal(str(inv.total_amount or 0)) * (exchange if inv.currency != 'PEN' else Decimal('1'))

                days = (inv.issue_date - start_date).days
                month_index = min(duration - 1, max(0, days // 30))
                ac_by_month[month_index] += amount_local

            # Acumular progresivamente
            cumulative = []
            running = Decimal('0.00')
            for m in ac_by_month:
                running += m
                cumulative.append(running)
            return cumulative

        # 2) Fallback: detalles de OC si no hay facturas
        detalles = PODetailProduct.objects.filter(
            purchase_order__project_code=project
        ).select_related('purchase_order').order_by('purchase_order__issue_date')

        if not detalles.exists():
            return [Decimal('0.00')] * duration

        first_detail = next((d for d in detalles if d.purchase_order and d.purchase_order.issue_date), None)
        if not first_detail:
            return [Decimal('0.00')] * duration
        start_date = first_detail.purchase_order.issue_date

        ac_by_month = [Decimal('0.00')] * duration
        for det in detalles:
            po = det.purchase_order
            if po and po.issue_date:
                days = (po.issue_date - start_date).days
                month_index = min(duration - 1, max(0, days // 30))
                valor = det.local_total if det.local_total is not None else det.total if det.total is not None else Decimal('0.00')
                ac_by_month[month_index] += Decimal(str(valor))

        cumulative = []
        running = Decimal('0.00')
        for m in ac_by_month:
            running += m
            cumulative.append(running)
        return cumulative

    # ===== NUEVO: Cálculos por granularidad =====
    @staticmethod
    def _build_granular_curves(project, duration_months, bac, physical_progress, start_date, interval_days=7):
        """
        Construye curvas PV/EV/AC por semanas (7) o días (1) para visualización.
        - PV: distribución lineal acumulada sobre la duración total.
        - EV: valor ganado constante acumulado (mismo enfoque que mensual).
        - AC: distribución por fecha de emisión de OCs usando interval_days.
        """
        units_count = max(1, duration_months * (30 // interval_days))

        # PV por intervalos como acumulado lineal hasta BAC
        pv_units = EarnedValueCalculator._calculate_pv_by_interval(bac, duration_months, start_date, interval_days, units_count)

        # EV por intervalos como acumulado lineal hasta EV total
        ev_total = bac * (physical_progress / Decimal('100.00'))
        ev_units_decimal = []
        for i in range(units_count):
            frac = Decimal(str((i + 1) / units_count))
            ev_units_decimal.append(ev_total * frac)
        ev_units = [float(x) for x in ev_units_decimal]

        # AC por intervalos
        ac_units = EarnedValueCalculator._calculate_ac_by_interval(project, duration_months, interval_days, units_count)

        # Etiquetas (semanas o días)
        labels = list(range(1, units_count + 1))
        return {
            'labels': labels,
            'pv': [float(x) for x in pv_units],
            'ev': [float(x) for x in ev_units],
            'ac': [float(x) for x in ac_units],
            'interval_days': interval_days,
        }

    @staticmethod
    def _calculate_pv_by_interval(bac, duration_months, start_date, interval_days, units_count):
        # PV acumulado distribuido linealmente en los intervalos (independiente de la fecha actual)
        if units_count <= 0:
            return []
        pv_data = []
        for i in range(units_count):
            frac = Decimal(str((i + 1) / units_count))
            pv_data.append(bac * frac)
        return pv_data

    @staticmethod
    def _calculate_ac_by_interval(project, duration_months, interval_days, units_count):
        # 1) Preferir FACTURAS
        invoices = Invoice.objects.filter(
            purchase_order__project_code=project
        ).select_related('purchase_order').order_by('issue_date')
        if invoices.exists():
            first_invoice = next((inv for inv in invoices if inv.issue_date), None)
            if not first_invoice:
                return [Decimal('0.00')] * units_count
            start_date = first_invoice.issue_date

            ac_units = [Decimal('0.00')] * units_count
            for inv in invoices:
                if not inv.issue_date:
                    continue
                exchange = Decimal(str(inv.exchange_rate or 1))
                amount_local = Decimal(str(inv.total_amount or 0)) * (exchange if inv.currency != 'PEN' else Decimal('1'))
                days = (inv.issue_date - start_date).days
                idx = min(units_count - 1, max(0, days // interval_days))
                ac_units[idx] += amount_local

            # Acumulado
            acc = Decimal('0.00')
            result = []
            for val in ac_units:
                acc += val
                result.append(acc)
            return result

        # 2) Fallback: detalles de OC
        detalles = PODetailProduct.objects.filter(
            purchase_order__project_code=project
        ).select_related('purchase_order').order_by('purchase_order__issue_date')
        if not detalles.exists():
            return [Decimal('0.00')] * units_count

        first_detail = next((d for d in detalles if d.purchase_order and d.purchase_order.issue_date), None)
        if not first_detail:
            return [Decimal('0.00')] * units_count
        start_date = first_detail.purchase_order.issue_date

        ac_units = [Decimal('0.00')] * units_count
        for det in detalles:
            po = det.purchase_order
            if po and po.issue_date:
                days = (po.issue_date - start_date).days
                idx = min(units_count - 1, max(0, days // interval_days))
                valor = det.local_total if det.local_total is not None else det.total if det.total is not None else Decimal('0.00')
                ac_units[idx] += Decimal(str(valor))

        acc = Decimal('0.00')
        result = []
        for val in ac_units:
            acc += val
            result.append(acc)
        return result

    @staticmethod
    def calculate_planned_value_pmi(bac, duration, start_date):
        """
        PV acumulado lineal por mes hasta BAC.
        Se evita depender de la fecha actual para que la serie completa
        represente el plan total y no muestre ceros iniciales.
        """
        if duration <= 0:
            return []
        pv_data = []
        for i in range(duration):
            frac = Decimal(str((i + 1) / duration))
            pv_data.append(bac * frac)
        return pv_data

    @staticmethod
    def calculate_metrics(pv, ev, ac, bac):
        """
        Calcula métricas básicas EVM
        """
        if not pv or not ev or not ac:
            return {
                'cpi': 1.0, 'spi': 1.0, 'cv': 0, 'sv': 0,
                'eac': float(bac), 'etc': float(bac)
            }

        current_pv = pv[-1]
        current_ev = ev[-1]
        current_ac = ac[-1]

        cpi = current_ev / current_ac if current_ac > 0 else Decimal('1.0')
        spi = current_ev / current_pv if current_pv > 0 else Decimal('1.0')
        cv = current_ev - current_ac
        sv = current_ev - current_pv
        eac = bac / cpi if cpi > 0 else bac
        etc = eac - current_ac

        return {
            'cpi': float(cpi),
            'spi': float(spi),
            'cv': float(cv),
            'sv': float(sv),
            'eac': float(eac),
            'vac': float(bac - eac),
            'etc': float(etc)
        }

    # ✅ MÉTODO DE CONVENIENCIA PARA EL DASHBOARD
    @staticmethod
    def get_pmi_dashboard_data(project_id):
        """
        Datos completos para el dashboard PMI
        """
        evm_data = EarnedValueCalculator.calculate_earned_value(project_id)
        
        # ✅ USAR ActivityCalculator para el detalle físico
        physical_detail = ActivityCalculator.get_physical_progress_detail(project_id)
        
        return {
            **evm_data,
            'physical_detail': physical_detail
        }