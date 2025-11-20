from datetime import date
from calendar import month_name
from decimal import Decimal

from django.utils import timezone

from projects.models import (
    Projects,
    ProjectBaseline,
    ProjectMonthlyBaseline,
)

class BaselineService:
    """Servicio para crear/leer baseline mensual persistente.
    - Si no existe, lo crea linealmente con base en Chance y duración del proyecto.
    - Devuelve arrays listos para Curva S, Ejecutivo y Eficiencia.
    """

    @staticmethod
    def _linear_series(total: Decimal, months: int):
        if months <= 0:
            return []
        total = Decimal(str(total or 0))
        step = (total / Decimal(months)) if months else Decimal(0)
        acc = Decimal(0)
        series = []
        for i in range(months):
            acc += step
            series.append(acc)
        # Ajuste final por redondeo
        if series:
            series[-1] = total
        return series

    @staticmethod
    def ensure_baseline(project_id: int):
        project = Projects.objects.get(cod_projects_id=project_id)
        # Crear/rescatar resumen
        baseline, _ = ProjectBaseline.objects.get_or_create(project=project)
        baseline.ensure_defaults()
        baseline.save()

        months = baseline.duration_months
        start_date = baseline.start_date or (project.start_date or timezone.now().date())
        bac = Decimal(str(baseline.bac_planned or 0))
        contract = Decimal(str(baseline.contract_planned or 0))

        # Series acumuladas
        pv_series = BaselineService._linear_series(bac, months)
        ac_series = BaselineService._linear_series(bac, months)
        billing_series = BaselineService._linear_series(contract, months)
        # EV planeado igual al PV acumulado cuando no hay avance real
        ev_series = list(pv_series)
        progress_series = []
        prog_step = (Decimal('100.0') / Decimal(months)) if months else Decimal(0)
        prog_acc = Decimal(0)
        for _ in range(months):
            prog_acc += prog_step
            progress_series.append(prog_acc)
        if progress_series:
            progress_series[-1] = Decimal('100.0')

        # Meses/etiquetas
        labels = []
        cur_year = start_date.year
        cur_month = start_date.month
        for i in range(months):
            labels.append(f"{month_name[cur_month]} {cur_year}")
            cur_month += 1
            if cur_month > 12:
                cur_month = 1
                cur_year += 1

        # Crear filas si no existen
        try:
            existing = set(
                ProjectMonthlyBaseline.objects.filter(project=project).values_list('month_index', flat=True)
            )
        except Exception:
            # Si la tabla no existe aún, salir sin intentar crear filas (migraciones pendientes)
            return baseline
        for idx in range(1, months + 1):
            if idx in existing:
                continue
            ProjectMonthlyBaseline.objects.create(
                project=project,
                baseline=baseline,
                month_index=idx,
                pv_planned=pv_series[idx-1],
                ev_planned=ev_series[idx-1],
                ac_planned=ac_series[idx-1],
                client_billing_planned=billing_series[idx-1],
                progress_planned=progress_series[idx-1],
                label=labels[idx-1]
            )

        return baseline

    @staticmethod
    def _build_ephemeral_arrays(project):
        months = project.estimated_duration or 12
        start_date = project.start_date or timezone.now().date()
        try:
            chance = project.cod_projects
            bac = Decimal(str(getattr(chance, 'total_costs', 0) or 0))
            contract = Decimal(str(getattr(chance, 'cost_aprox_chance', 0) or 0))
        except Exception:
            bac = Decimal('0')
            contract = Decimal('0')

        pv_series = BaselineService._linear_series(bac, months)
        ev_series = list(pv_series)
        ac_series = BaselineService._linear_series(bac, months)
        billing_series = BaselineService._linear_series(contract, months)
        
        progress_series = []
        prog_step = (Decimal('100.0') / Decimal(months)) if months else Decimal(0)
        prog_acc = Decimal(0)
        for _ in range(months):
            prog_acc += prog_step
            progress_series.append(prog_acc)
        if progress_series:
            progress_series[-1] = Decimal('100.0')

        labels = []
        cur_year = start_date.year
        cur_month = start_date.month
        for _ in range(months):
            labels.append(f"{month_name[cur_month]} {cur_year}")
            cur_month += 1
            if cur_month > 12:
                cur_month = 1
                cur_year += 1

        return {
            'months': list(range(1, months + 1)),
            'labels': labels,
            'pv': [float(x) for x in pv_series],
            'ev': [float(x) for x in ev_series],
            'ac': [float(x) for x in ac_series],
            'billing': [float(x) for x in billing_series],
            'progress': [float(x) for x in progress_series],
        }

    @staticmethod
    def get_monthly_arrays(project_id: int):
        """Devuelve arrays: months, pv, ev, ac, billing, progress.
        Pasa a modo efímero si las tablas aún no existen (migraciones pendientes).
        """
        project = Projects.objects.get(cod_projects_id=project_id)
        # Si las tablas aún no existen, generar arrays efímeros sin DB
        try:
            rows = ProjectMonthlyBaseline.objects.filter(project=project).order_by('month_index')
        except Exception:
            return BaselineService._build_ephemeral_arrays(project)
        
        # exists() ejecuta consulta; encapsular en try/except por tabla inexistente
        try:
            has_rows = rows.exists()
        except Exception:
            return BaselineService._build_ephemeral_arrays(project)
        
        if not has_rows:
            try:
                BaselineService.ensure_baseline(project_id)
                rows = ProjectMonthlyBaseline.objects.filter(project=project).order_by('month_index')
                try:
                    has_rows = rows.exists()
                except Exception:
                    return BaselineService._build_ephemeral_arrays(project)
                if not has_rows:
                    return BaselineService._build_ephemeral_arrays(project)
            except Exception:
                return BaselineService._build_ephemeral_arrays(project)
        
        # Iterar filas (evalúa queryset); encapsular
        try:
            months = [r.month_index for r in rows]
            # Si solo hay 1 mes, reforzar baseline para crear las filas faltantes
            if len(months) < 2:
                try:
                    BaselineService.ensure_baseline(project_id)
                    rows = ProjectMonthlyBaseline.objects.filter(project=project).order_by('month_index')
                    months = [r.month_index for r in rows]
                except Exception:
                    return BaselineService._build_ephemeral_arrays(project)
            labels = [r.label for r in rows]
            pv = [float(r.pv_planned or 0) for r in rows]
            ev = [float(r.ev_planned or 0) for r in rows]
            ac = [float(r.ac_planned or 0) for r in rows]
            billing = [float(r.client_billing_planned or 0) for r in rows]
            progress = [float(r.progress_planned or 0) for r in rows]
        except Exception:
            return BaselineService._build_ephemeral_arrays(project)

        return {
            'months': months,
            'labels': labels,
            'pv': pv,
            'ev': ev,
            'ac': ac,
            'billing': billing,
            'progress': progress,
        }

    @staticmethod
    def recalculate_pv_from_progress(project_id: int):
        """Recalcula PV/EV planeados usando % planificado mensual acumulado.
        - PV = BAC_planificado * (progress_planned / 100)
        - Aplica guardas de monotonía (0..100, no decreciente)
        - Ajusta el último valor a BAC para coherencia por redondeos
        """
        project = Projects.objects.get(cod_projects_id=project_id)
        try:
            baseline = ProjectBaseline.objects.get(project=project)
        except ProjectBaseline.DoesNotExist:
            baseline = BaselineService.ensure_baseline(project_id)
        bac = Decimal(str(baseline.bac_planned or 0))
        # Recuperar filas ordenadas
        try:
            rows = list(ProjectMonthlyBaseline.objects.filter(project=project).order_by('month_index'))
        except Exception:
            return 0
        if not rows:
            BaselineService.ensure_baseline(project_id)
            rows = list(ProjectMonthlyBaseline.objects.filter(project=project).order_by('month_index'))
        # Guardas y cálculo
        last_pct = Decimal('0')
        for r in rows:
            pct = Decimal(str(r.progress_planned or 0))
            if pct < last_pct:
                pct = last_pct
            if pct > Decimal('100'):
                pct = Decimal('100.0')
            last_pct = pct
            pv_value = (bac * pct / Decimal('100'))
            r.pv_planned = pv_value
            r.ev_planned = pv_value
        # Fuerza último = BAC para coherencia
        if rows:
            rows[-1].pv_planned = bac
            rows[-1].ev_planned = bac
        for r in rows:
            r.save()
        return len(rows)