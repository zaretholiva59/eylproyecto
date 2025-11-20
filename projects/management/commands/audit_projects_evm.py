import os
import csv
from django.conf import settings
from django.core.management.base import BaseCommand

from projects.models.projects import Projects
from projects.models.oc import PurchaseOrder
from projects.services.earned_value.calculator import EarnedValueCalculator
from projects.services.earned_value.activity_calculator import ActivityCalculator


class Command(BaseCommand):
    help = (
        "Genera un análisis EVM para TODOS los proyectos, "
        "detecta datos faltantes y exporta CSVs (resumen y series)."
    )

    def handle(self, *args, **options):
        reports_dir = os.path.join(settings.BASE_DIR, 'projects', 'reports')
        os.makedirs(reports_dir, exist_ok=True)

        summary_path = os.path.join(reports_dir, 'evm_audit_summary.csv')
        series_path = os.path.join(reports_dir, 'evm_graph_data.csv')

        summary_fields = [
            'project_id', 'cost_center', 'state', 'start_date', 'duration_months',
            'bac', 'bac_source', 'physical_progress_percent', 'activities_count', 'weights_valid_100',
            'po_count', 'pv_last', 'ev_last', 'ac_last', 'cpi', 'spi', 'eac', 'etc', 'vac',
            'pmi_compliant', 'missing_data'
        ]
        series_fields = ['project_id', 'month_index', 'pv', 'ev', 'ac']

        projects_qs = Projects.objects.select_related('cod_projects').all().order_by('cod_projects_id')

        with open(summary_path, 'w', newline='', encoding='utf-8') as fsum, \
             open(series_path, 'w', newline='', encoding='utf-8') as fser:
            summary_writer = csv.DictWriter(fsum, fieldnames=summary_fields)
            series_writer = csv.DictWriter(fser, fieldnames=series_fields)
            summary_writer.writeheader()
            series_writer.writeheader()

            for p in projects_qs:
                project_id = p.cod_projects_id

                # BAC
                missing_bac = False
                bac_source = 'Missing'
                bac_val = 0.0
                try:
                    bac_real = EarnedValueCalculator.get_bac_real(p)
                    bac_val = float(bac_real)
                    if hasattr(p.cod_projects, 'presale'):
                        bac_source = 'Presale.total_cost'
                    elif getattr(p.cod_projects, 'cost_aprox_chance', None):
                        bac_source = 'Chance.cost_aprox_chance'
                    else:
                        bac_source = 'Unknown'
                except Exception:
                    missing_bac = True

                duration = p.estimated_duration or 0
                start_date_iso = p.start_date.isoformat() if p.start_date else ''
                missing_start_date = p.start_date is None

                po_count = PurchaseOrder.objects.filter(project_code=p).count()
                missing_purchase_orders = po_count == 0

                # Avance físico y validaciones de actividades
                try:
                    phys = ActivityCalculator.get_physical_progress_detail(project_id)
                    activities_count = phys.get('activities_count', 0)
                    weights_valid = bool(phys.get('weights_valid', False))
                    physical_progress = float(phys.get('total_physical_progress', 0.0))
                except Exception:
                    activities_count = 0
                    weights_valid = False
                    physical_progress = 0.0

                missing_activities = activities_count == 0
                invalid_weights = not weights_valid

                # Métricas EVM y curvas
                try:
                    evm = EarnedValueCalculator.calculate_earned_value(project_id)
                    metrics = evm.get('metrics', {})
                    curve = evm.get('curve_data', {'months': [], 'pv': [], 'ev': [], 'ac': []})
                    pmi_compliant = bool(evm.get('pmi_compliant', False))
                except Exception:
                    metrics = {
                        'cpi': 1.0, 'spi': 1.0, 'cv': 0.0, 'sv': 0.0,
                        'eac': bac_val, 'vac': bac_val - bac_val, 'etc': bac_val
                    }
                    curve = {
                        'months': list(range(1, (duration or 0) + 1)),
                        'pv': [0.0] * (duration or 0),
                        'ev': [0.0] * (duration or 0),
                        'ac': [0.0] * (duration or 0)
                    }
                    pmi_compliant = False

                pv_last = float(curve['pv'][-1]) if curve['pv'] else 0.0
                ev_last = float(curve['ev'][-1]) if curve['ev'] else 0.0
                ac_last = float(curve['ac'][-1]) if curve['ac'] else 0.0

                missing_data_flags = []
                if missing_bac:
                    missing_data_flags.append('Falta BAC (Presale/Chance)')
                if missing_start_date:
                    missing_data_flags.append('Falta start_date')
                if missing_purchase_orders:
                    missing_data_flags.append('Sin OC/AC')
                if missing_activities:
                    missing_data_flags.append('Sin actividades')
                if invalid_weights:
                    missing_data_flags.append('Pesos != 100%')

                summary_writer.writerow({
                    'project_id': project_id,
                    'cost_center': p.cost_center,
                    'state': p.state_projects,
                    'start_date': start_date_iso,
                    'duration_months': duration,
                    'bac': round(bac_val, 2),
                    'bac_source': bac_source,
                    'physical_progress_percent': round(physical_progress, 2),
                    'activities_count': activities_count,
                    'weights_valid_100': 1 if weights_valid else 0,
                    'po_count': po_count,
                    'pv_last': round(pv_last, 2),
                    'ev_last': round(ev_last, 2),
                    'ac_last': round(ac_last, 2),
                    'cpi': round(float(metrics.get('cpi', 0.0)), 4),
                    'spi': round(float(metrics.get('spi', 0.0)), 4),
                    'eac': round(float(metrics.get('eac', 0.0)), 2),
                    'etc': round(float(metrics.get('etc', 0.0)), 2),
                    'vac': round(float(metrics.get('vac', 0.0)), 2),
                    'pmi_compliant': 1 if pmi_compliant else 0,
                    'missing_data': '; '.join(missing_data_flags)
                })

                months = curve.get('months', [])
                pv_series = curve.get('pv', [])
                ev_series = curve.get('ev', [])
                ac_series = curve.get('ac', [])
                for idx, m in enumerate(months):
                    series_writer.writerow({
                        'project_id': project_id,
                        'month_index': m,
                        'pv': round(float(pv_series[idx]) if idx < len(pv_series) else 0.0, 2),
                        'ev': round(float(ev_series[idx]) if idx < len(ev_series) else 0.0, 2),
                        'ac': round(float(ac_series[idx]) if idx < len(ac_series) else 0.0, 2),
                    })

        self.stdout.write(self.style.SUCCESS(f'CSV generado: {summary_path}'))
        self.stdout.write(self.style.SUCCESS(f'CSV series: {series_path}'))
        self.stdout.write(self.style.WARNING(
            'Fórmulas: EV=BAC*(avance físico), PV según cronograma (lineal acumulado), AC acumulado por OCs; '
            'CPI=EV/AC; SPI=EV/PV; EAC=BAC/CPI; ETC=EAC-AC; VAC=BAC-EAC'
        ))