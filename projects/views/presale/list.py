from django.shortcuts import redirect, render
from django.core.cache import cache
from django.db.models import Prefetch
from decimal import Decimal
from projects.models.chance import Chance
from projects.models import ProjectProgress


def pre_sale(request):
    # ✅ OPTIMIZACIÓN: Usar Chance en lugar de Presale
    cache_key = 'chance_list_optimized'
    chances = cache.get(cache_key)
    
    if not chances:
        chances = Chance.objects.select_related(
            'info_costumer'
        ).prefetch_related(
            Prefetch(
                'projects__progress_records',
                queryset=ProjectProgress.objects.order_by('month_number')
            )
        ).all()
        
        # Procesar datos una sola vez
        for chance in chances:
            project = getattr(chance, 'projects', None)
            # Normalizar centros de costo adicionales para asegurar renderizado
            try:
                extra = getattr(chance, 'extra_cost_centers', None)
                if extra is None:
                    normalized = []
                elif isinstance(extra, str):
                    # Intentar decodificar JSON; si falla, dividir por comas
                    import json
                    try:
                        decoded = json.loads(extra)
                        if isinstance(decoded, list):
                            normalized = [str(x).strip() for x in decoded if str(x).strip()]
                        else:
                            normalized = []
                    except Exception:
                        normalized = [s.strip() for s in extra.split(',') if s.strip()]
                elif isinstance(extra, (list, tuple)):
                    normalized = [str(x).strip() for x in extra if str(x).strip()]
                else:
                    normalized = []
                chance.extra_cost_centers = normalized
            except Exception:
                chance.extra_cost_centers = []
            
            # Duración estimada en días (preferir cálculo por fechas de Project)
            resolved_days = 0
            if project and getattr(project, 'start_date', None) and getattr(project, 'estimated_end_date', None):
                try:
                    resolved_days = max((project.estimated_end_date - project.start_date).days, 1)
                except Exception:
                    resolved_days = 0
            else:
                # Fallback al campo estimado (ya calculado y sincronizado)
                resolved_days = (chance.estimated_duration or 0)
            chance.estimated_duration_resolved_days = resolved_days

            # Usar datos ya cargados en lugar de nueva consulta
            records = []
            if project and hasattr(project, 'progress_records'):
                records = [
                    {
                        'month_number': r.month_number,
                        'planned_percentage': float(r.planned_percentage or 0),
                        'actual_percentage': float(r.actual_percentage or 0),
                    }
                    for r in project.progress_records.all()
                ]

            # Atributos dinámicos accesibles desde la plantilla
            chance.monthly_records = records
            chance.has_project = bool(project)

            # ===== Recalcular métricas financieras si están ausentes o en cero =====
            try:
                mat = Decimal(str(getattr(chance, 'material_cost', 0) or 0))
                lab = Decimal(str(getattr(chance, 'labor_cost', 0) or 0))
                sub = Decimal(str(getattr(chance, 'subcontracted_cost', 0) or 0))
                ovh = Decimal(str(getattr(chance, 'overhead_cost', 0) or 0))
                contract = Decimal(str(getattr(chance, 'cost_aprox_chance', 0) or 0))
                total = mat + lab + sub + ovh
                util = contract - total

                # Solo sobrescribir si están ausentes o en cero
                if not getattr(chance, 'total_costs', None) or Decimal(str(chance.total_costs)) == Decimal('0'):
                    chance.total_costs = total
                if not getattr(chance, 'aprox_uti', None) or Decimal(str(chance.aprox_uti)) == Decimal('0'):
                    chance.aprox_uti = util

                if contract > 0:
                    chance.profit_margin_pct = round((util / contract) * 100, 2)
                else:
                    chance.profit_margin_pct = Decimal('0.00')
            except Exception:
                # Si algo falla, no bloquear la carga del listado
                pass
        
        # Cache por 5 minutos
        cache.set(cache_key, list(chances), 300)

    context = {
        'objects': chances
    }
    return render(request, "presale/index.html", context)

