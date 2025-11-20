from django.core.management.base import BaseCommand, CommandError
from decimal import Decimal
from projects.models import Projects, ProjectMonthlyBaseline
from projects.services.baseline_service import BaselineService

class Command(BaseCommand):
    help = "Importa % planificado mensual acumulado (0..100) y recalcula PV baseline"

    def add_arguments(self, parser):
        parser.add_argument('--project_id', required=True, help='ID del proyecto (cod_projects_id)')
        parser.add_argument('--percentages', help='Lista separada por comas, p.ej. 5,10,17,...')
        parser.add_argument('--csv', help='Ruta CSV con columnas month_index,percentage')
        parser.add_argument('--mode', choices=['cumulative','incremental'], default='cumulative', help='Interpretación de los datos')

    def handle(self, *args, **options):
        project_id = options['project_id']
        percentages_arg = options.get('percentages')
        csv_path = options.get('csv')
        mode = options.get('mode', 'cumulative')

        if not percentages_arg and not csv_path:
            raise CommandError('Debe proporcionar --percentages o --csv')

        project = Projects.objects.get(cod_projects_id=project_id)
        # Asegurar baseline inicial
        BaselineService.ensure_baseline(project_id)

        # Filas existentes
        rows = list(ProjectMonthlyBaseline.objects.filter(project=project).order_by('month_index'))
        if not rows:
            raise CommandError('No hay filas de baseline mensual')

        values = []
        if percentages_arg:
            try:
                values = [Decimal(str(x.strip())) for x in percentages_arg.split(',') if x.strip()!='']
            except Exception as e:
                raise CommandError(f'Error parseando --percentages: {e}')
        else:
            import csv as csvmod
            try:
                with open(csv_path, newline='', encoding='utf-8') as f:
                    reader = csvmod.DictReader(f)
                    data_by_idx = {}
                    for row in reader:
                        idx = int(row.get('month_index') or 0)
                        pct = Decimal(str(row.get('percentage') or '0'))
                        data_by_idx[idx] = pct
                    # Ordenar según baseline
                    for r in rows:
                        values.append(data_by_idx.get(r.month_index, Decimal('0')))
            except Exception as e:
                raise CommandError(f'Error leyendo CSV: {e}')

        # Ajustar longitud: rellenar o recortar
        if len(values) < len(rows):
            values += [values[-1] if values else Decimal('0')] * (len(rows) - len(values))
        if len(values) > len(rows):
            values = values[:len(rows)]

        # Convertir incremental a acumulado si corresponde
        if mode == 'incremental':
            cum = Decimal('0')
            out = []
            for v in values:
                if v < 0:
                    v = Decimal('0')
                cum += v
                out.append(cum)
            values = out

        # Guardas y aplicar 0..100 no decreciente
        last = Decimal('0')
        for i, v in enumerate(values):
            if v < last:
                v = last
            if v > Decimal('100'):
                v = Decimal('100')
            rows[i].progress_planned = v
            last = v

        for r in rows:
            r.save()

        # Recalcular PV desde progreso
        count = BaselineService.recalculate_pv_from_progress(project_id)

        self.stdout.write(self.style.SUCCESS(f'Plan importado para {project_id}. Filas: {len(rows)}. PV recalculado: {count}.'))