from django.db import models
from django.core.validators import MinValueValidator 
from django.apps import apps
from decimal import Decimal
from projects.models.costumer import Costumer
from projects.models.choices import currency as CURRENCY_CHOICES

class Chance(models.Model):
    # ========== IDENTIFICACIÓN ==========
    cod_projects = models.CharField(max_length=20, primary_key=True)
    info_costumer = models.ForeignKey(Costumer, on_delete=models.CASCADE)
    staff_presale = models.CharField(max_length=100)
    cost_center = models.CharField(max_length=20)
    # Lista opcional de centros de costo adicionales (solo códigos)
    extra_cost_centers = models.JSONField(
        default=list,
        blank=True,
        null=True,
        help_text="Centros de costo adicionales (solo códigos)"
    )
    com_exe = models.CharField(max_length=100)
    regis_date = models.DateField(auto_now_add=True)
    dres_chance = models.CharField(max_length=255)
    date_aprox_close = models.DateField(null=True, blank=True)
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='PEN',
        verbose_name="Moneda"
    )
    exchange_rate = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=Decimal('1.0000'),
        verbose_name="Tipo de Cambio a S/"
    )
    cost_aprox_chance = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0.00)]
    )
    
    # ========== COSTOS DESGLOSADOS ==========
    material_cost = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0.00)]
    )
    labor_cost = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0.00)]
    )
    subcontracted_cost = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0.00)]
    )
    overhead_cost = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0.00)]
    )
    estimated_duration = models.IntegerField(
        default=8, 
        validators=[MinValueValidator(1)]
    )
    
    # ========== CAMPOS CALCULADOS (se guardan en BD) ==========
    total_costs = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00,
        editable=False
    )
    aprox_uti = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00,
        editable=False
    )
    # Totales convertidos a PEN
    cost_aprox_chance_pen = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        editable=False
    )
    total_costs_pen = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        editable=False
    )
    aprox_uti_pen = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        editable=False
    )
    
    # ⬇️ NUEVOS CAMPOS: PORCENTAJES (se guardan en BD)
    profit_margin_pct = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        editable=False,
        verbose_name="Margen de Utilidad (%)"
    )
    material_cost_pct = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        editable=False,
        verbose_name="Costo Material (%)"
    )
    labor_cost_pct = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        editable=False,
        verbose_name="Costo Mano de Obra (%)"
    )
    subcontracted_cost_pct = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        editable=False,
        verbose_name="Costo Subcontratado (%)"
    )
    overhead_cost_pct = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        editable=False,
        verbose_name="Costo Gastos Generales (%)"
    )
    
    class Meta:
        db_table = "chance"
    def __str__(self):
        symbol_map = {
            'PEN': 'S/',
            'USD': '$',
            'EUR': '€',
        }
        symbol = symbol_map.get(self.currency, '')
        return f"{self.dres_chance} - {self.info_costumer.com_name} ({symbol}{self.cost_aprox_chance:,.2f})"
    
    def save(self, *args, **kwargs):
        """Calcula todos los campos antes de guardar"""
        # Normalizar tipo de cambio cuando sea moneda local
        if self.currency == 'PEN' or not self.exchange_rate:
            self.exchange_rate = Decimal('1.0000')
        else:
            # Asegurar que no sea negativo o cero
            if self.exchange_rate <= 0:
                self.exchange_rate = Decimal('1.0000')

        # Calcular total de costos
        self.total_costs = (
            self.material_cost +
            self.labor_cost +
            self.subcontracted_cost +
            self.overhead_cost
        )

        # Calcular utilidad
        self.aprox_uti = self.cost_aprox_chance - self.total_costs

        # Calcular conversiones a PEN
        rate = self.exchange_rate if self.exchange_rate else Decimal('1.0000')
        self.cost_aprox_chance_pen = (self.cost_aprox_chance or Decimal('0')) * rate
        self.total_costs_pen = (self.total_costs or Decimal('0')) * rate
        self.aprox_uti_pen = self.cost_aprox_chance_pen - self.total_costs_pen

        # ⬇️ CALCULAR PORCENTAJES (se guardan en BD)
        if self.cost_aprox_chance and self.cost_aprox_chance > 0:
            self.profit_margin_pct = round((self.aprox_uti / self.cost_aprox_chance) * 100, 2)
            self.material_cost_pct = round((self.material_cost / self.cost_aprox_chance) * 100, 2)
            self.labor_cost_pct = round((self.labor_cost / self.cost_aprox_chance) * 100, 2)
            self.subcontracted_cost_pct = round((self.subcontracted_cost / self.cost_aprox_chance) * 100, 2)
            self.overhead_cost_pct = round((self.overhead_cost / self.cost_aprox_chance) * 100, 2)
        else:
            self.profit_margin_pct = 0.0
            self.material_cost_pct = 0.0
            self.labor_cost_pct = 0.0
            self.subcontracted_cost_pct = 0.0
            self.overhead_cost_pct = 0.0

        # ⬇️ GUARDAR EL CHANCE
        super().save(*args, **kwargs)

        # ⬇️ CREAR PROJECTS SI NO EXISTE (evitar import circular usando apps.get_model)
        Projects = apps.get_model('projects', 'Projects')
        try:
            Projects.objects.get(cod_projects=self)
        except Projects.DoesNotExist:
            Projects.objects.create(
                cod_projects=self,
                state_projects="Planeado",
                cost_center=self.cost_center,  # ✅ Guardar el centro de costo real
                estimated_duration=self.estimated_duration,
            )

    def set_extra_cost_centers(self, centers, replace=False):
        normalized = []
        if centers is None:
            if replace:
                self.extra_cost_centers = []
            return
        if isinstance(centers, str):
            s = centers.strip()
            if s:
                import json as _json
                try:
                    data = _json.loads(s)
                    if isinstance(data, list):
                        normalized = [str(x).strip() for x in data if str(x).strip()]
                    else:
                        normalized = [t.strip() for t in s.split(',') if t.strip()]
                except Exception:
                    normalized = [t.strip() for t in s.split(',') if t.strip()]
        elif isinstance(centers, (list, tuple)):
            normalized = [str(x).strip() for x in centers if str(x).strip()]
        else:
            normalized = []
        seen = set()
        unique = []
        for c in normalized:
            if c not in seen:
                seen.add(c)
                unique.append(c)
        if unique or replace:
            self.extra_cost_centers = unique