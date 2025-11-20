from decimal import Decimal, InvalidOperation
import re
from datetime import datetime, date, timedelta
import uuid
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget

from .models import (
    Costumer, Supplier, Product, Chance, Projects,
    PurchaseOrder, PODetailProduct, PODetailSupplier, Invoice,
    ProjectActivity, ClientInvoice, ProjectMonthlyBaseline
)


# ========================================
# CLASE BASE - REUTILIZABLE PARA TODOS
# ========================================

class BaseModelResource(resources.ModelResource):
    """
    Clase base abstracta con funcionalidad común para TODOS los modelos.
    
    Características:
    - Eliminación automática de columna 'id'
    - Mapeo flexible de encabezados
    - Limpieza automática de valores N/A
    - Conversión segura de decimales y fechas
    - Debug detallado configurable
    - Validación de foreign keys
    """
    
    # 🔧 Configuración (sobrescribir en subclases)
    HEADER_MAPPINGS = {}
    REQUIRED_FIELDS = []
    DEBUG_ENABLED = False
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._import_stats = {
            'total_rows': 0,
            'processed': 0,
            'errors': 0,
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'error_details': []
        }
    
    # ========================================
    # CICLO DE VIDA DE IMPORTACIÓN
    # ========================================
    
    def before_import(self, dataset, **kwargs):
        """Preparación global antes de importar"""
        if self.DEBUG_ENABLED:
            self._log_import_start(dataset)
        
        self._remove_id_column(dataset)
        
        if self.HEADER_MAPPINGS:
            self._map_headers(dataset)
        
        if self.REQUIRED_FIELDS:
            self._validate_required_fields(dataset)
        
        if self.DEBUG_ENABLED and len(dataset) > 0:
            self._log_first_row_example(dataset)
        
        self._import_stats['total_rows'] = len(dataset)
        
        if self.DEBUG_ENABLED:
            print("="*100 + "\n")
    
    def before_import_row(self, row, row_number=None, **kwargs):
        """Procesamiento por fila"""
        self._import_stats['processed'] += 1
        
        if self.DEBUG_ENABLED:
            print(f"\n{'='*80}")
            print(f"🔄 PROCESANDO FILA {row_number}/{self._import_stats['total_rows']}")
            print(f"{'='*80}")
    
    def after_import_row(self, row, row_result, **kwargs):
        """Registrar estadísticas"""
        if row_result.import_type == 'new':
            self._import_stats['created'] += 1
        elif row_result.import_type == 'update':
            self._import_stats['updated'] += 1
        elif row_result.import_type == 'skip':
            self._import_stats['skipped'] += 1
        
        if hasattr(row_result, 'errors') and row_result.errors:
            self._import_stats['errors'] += 1
    
    def after_import(self, dataset, result, **kwargs):
        """Resumen final"""
        if self.DEBUG_ENABLED:
            self._log_import_summary()

    # ========================================
    # CONTROL DE OMISIÓN DE FILAS
    # ========================================
    def init_instance(self, row=None):
        """Inicializa instancia y propaga bandera de omisión desde la fila."""
        instance = super().init_instance(row=row)
        try:
            if isinstance(row, dict) and row.get('__skip__'):
                setattr(instance, '_skip_import', True)
                setattr(instance, '_skip_reason', row.get('__skip_reason'))
        except Exception:
            pass
        return instance

    def skip_row(self, instance, original, row=None, import_func=None, dry_run=None):
        """Permite omitir filas marcadas para skip; compatible con distintas firmas."""
        try:
            # Preferir marca en la fila
            if isinstance(row, dict) and row.get('__skip__'):
                if self.DEBUG_ENABLED:
                    print(f"   ⏭️  Saltando fila por regla: {row.get('__skip_reason')}")
                return True
        except Exception:
            pass

        # Fallback: bandera en la instancia
        skip_flag = bool(getattr(instance, '_skip_import', False))
        if skip_flag and self.DEBUG_ENABLED:
            reason = getattr(instance, '_skip_reason', None)
            print(f"   ⏭️  Saltando fila por regla: {reason}")
        return skip_flag
    
    # ========================================
    # MÉTODOS PRIVADOS DE UTILIDAD
    # ========================================
    
    def _remove_id_column(self, dataset):
        """Elimina columna 'id' si existe"""
        if 'id' in dataset.headers:
            headers = list(dataset.headers)
            headers.remove('id')
            dataset.headers = headers
            
            for row in dataset.dict:
                if 'id' in row:
                    del row['id']
            
            if self.DEBUG_ENABLED:
                print("   ⚠️  Columna 'id' eliminada automáticamente")
    
    def _map_headers(self, dataset):
        """Mapea nombres de columnas alternativos"""
        if self.DEBUG_ENABLED:
            print("🔄 MAPEANDO ENCABEZADOS:")
        
        new_headers = []
        for header in dataset.headers:
            header_lower = header.lower().strip()
            mapped = False
            
            for model_field, possible_names in self.HEADER_MAPPINGS.items():
                if header_lower in [name.lower() for name in possible_names]:
                    new_headers.append(model_field)
                    if self.DEBUG_ENABLED and header != model_field:
                        print(f"   🔄 '{header}' → '{model_field}'")
                    mapped = True
                    break
            
            if not mapped:
                new_headers.append(header)
        
        dataset.headers = new_headers
    
    def _validate_required_fields(self, dataset):
        """Valida campos requeridos"""
        missing = [field for field in self.REQUIRED_FIELDS if field not in dataset.headers]
        if missing:
            raise ValueError(
                f"❌ Faltan columnas requeridas: {missing}\n"
                f"Columnas disponibles: {list(dataset.headers)}"
            )
    
    def _log_import_start(self, dataset):
        """Log de inicio"""
        print("\n" + "="*100)
        print(f"📊 IMPORTACIÓN: {self.Meta.model.__name__}")
        print("="*100)
        print(f"📋 Columnas detectadas: {list(dataset.headers)}")
        print(f"📈 Total de filas: {len(dataset)}")
    
    def _log_first_row_example(self, dataset):
        """Muestra primera fila"""
        print(f"\n🔍 EJEMPLO - PRIMERA FILA:")
        if len(dataset) == 0:
            print("   (Dataset vacío)")
            return

        first_row = dataset[0]
        # Tablib devuelve tuplas/listas; convertir a dict usando headers si es necesario
        if hasattr(first_row, 'items'):
            row_dict = dict(first_row)
        else:
            headers = list(dataset.headers or [])
            # Emparejar headers con valores; si faltan valores, usar None
            if headers:
                row_dict = {
                    headers[i]: (first_row[i] if i < len(first_row) else None)
                    for i in range(len(headers))
                }
            else:
                # Sin headers: indexar por posición
                row_dict = {str(i): first_row[i] for i in range(len(first_row))}

        for key, value in row_dict.items():
            if isinstance(value, str) and len(value) > 60:
                print(f"   {key}: '{value[:60]}...'")
            else:
                print(f"   {key}: '{value}'")
    
    def _log_import_summary(self):
        """Log de resumen"""
        print("\n" + "="*100)
        print("📊 RESUMEN DE IMPORTACIÓN")
        print("="*100)
        print(f"Total procesadas: {self._import_stats['processed']}")
        print(f"✅ Creadas:       {self._import_stats['created']}")
        print(f"🔄 Actualizadas:  {self._import_stats['updated']}")
        print(f"⏭️  Saltadas:     {self._import_stats['skipped']}")
        print(f"❌ Errores:       {self._import_stats['errors']}")
        print("="*100 + "\n")
    
    # ========================================
    # MÉTODOS PÚBLICOS DE LIMPIEZA - REUTILIZABLES
    # ========================================
    
    @staticmethod
    def clean_string(value, default='', max_length=None, to_upper=False):
        """Limpia y normaliza strings"""
        if value is None:
            return default
        
        s = str(value).strip()
        
        if s.upper() in ('N/A', 'NA', 'NONE', '', '-'):
            return default
        
        if to_upper:
            s = s.upper()
        
        if max_length and len(s) > max_length:
            s = s[:max_length]
        
        return s
    
    @staticmethod
    def clean_decimal(value, default='0.00', decimal_places=2):
        """Convierte valores a Decimal de forma segura"""
        if value is None or str(value).strip() == '':
            return Decimal(default)
        
        s = str(value).strip().replace(',', '').replace(' ', '')
        
        if s.upper() in ('N/A', 'NA', 'NONE', '-'):
            return Decimal(default)
        
        try:
            d = Decimal(s)
            quantizer = Decimal('1').scaleb(-decimal_places)
            return d.quantize(quantizer)
        except (InvalidOperation, ValueError):
            return Decimal(default)
    
    @staticmethod
    def clean_date(value, default=None):
        """Convierte valores a fecha de forma segura"""
        if value is None:
            return default
        
        if isinstance(value, date):
            return value
        if isinstance(value, datetime):
            return value.date()
        
        s = str(value).strip()
        
        if s == '' or s.upper() in ('N/A', 'NA', 'NONE', '-'):
            return default
        
        # Intentar formatos comunes
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d', '%d-%m-%Y', '%m/%d/%Y'):
            try:
                return datetime.strptime(s, fmt).date()
            except ValueError:
                continue
        
        # Intentar serial de Excel
        try:
            if s.replace('.', '').isdigit():
                serial = float(s)
                dt = datetime(1899, 12, 30) + timedelta(days=serial)
                return dt.date()
        except (ValueError, OverflowError):
            pass
        
        return default
    
    @staticmethod
    def clean_integer(value, default=0):
        """Convierte valores a entero de forma segura"""
        if value is None or str(value).strip() == '':
            return default
        
        s = str(value).strip().replace(',', '').replace(' ', '')
        
        if s.upper() in ('N/A', 'NA', 'NONE', '-'):
            return default
        
        try:
            return int(float(s))
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def clean_code(value, remove_leading_zeros=True, auto_generate=False):
        """Limpia códigos (elimina ceros a la izquierda)"""
        if not value or str(value).strip() == '':
            if auto_generate:
                return f"AUTO_{uuid.uuid4().hex[:8].upper()}"
            return None
        
        code = str(value).strip()
        
        if remove_leading_zeros:
            try:
                if code.replace('.', '').replace('-', '').isdigit():
                    code = str(int(float(code)))
            except (ValueError, TypeError):
                pass
        
        return code

    # ================================
    # Resolución robusta de Órdenes de Compra
    # ================================
    def _po_candidates(self, po_raw):
        """Genera posibles variantes de po_number para intentar coincidencias.
        Maneja sufijos decimales ('.0', '.00', etc.), coma decimal, y espacios.
        """
        s = self.clean_string(po_raw)
        if not s:
            return []

        base = self.clean_code(s, remove_leading_zeros=True) or s
        normalized = base.strip()
        # Quitar espacios internos
        normalized = normalized.replace(' ', '')

        candidates = []

        # 1) Original limpio
        candidates.append(normalized)

        # 2) Reemplazar coma por punto
        if ',' in normalized:
            candidates.append(normalized.replace(',', '.'))

        # 3) Extraer parte entera si tiene decimal con solo ceros (.,0+ o ,0+)
        m = re.match(r"^(\d+)[\.,]?0*$", normalized)
        if m:
            integer_part = m.group(1)
            candidates.append(integer_part)
            # sufijos comunes con punto
            for zeros in ('0', '00', '000', '0000'):
                candidates.append(f"{integer_part}.{zeros}")
            # sufijos comunes con coma
            for zeros in ('0', '00', '000', '0000'):
                candidates.append(f"{integer_part},{zeros}")

        # 4) Quitar posibles separadores de miles (comas) completamente
        if ',' in normalized and not re.search(r",\d$", normalized):
            candidates.append(normalized.replace(',', ''))

        # Deduplicar preservando orden
        seen = set()
        unique_candidates = []
        for c in candidates:
            if c and c not in seen:
                unique_candidates.append(c)
                seen.add(c)

        return unique_candidates

    def _digits_only(self, s):
        """Extrae solo dígitos de una cadena. Devuelve '' si no hay dígitos."""
        if s is None:
            return ''
        try:
            import re as _re
            return _re.sub(r"\D", "", str(s))
        except Exception:
            return ''.join(ch for ch in str(s) if ch.isdigit())

    def resolve_purchase_order(self, po_raw, project_code=None):
        """Intenta resolver una PurchaseOrder probando múltiples variantes del número.
        Devuelve el objeto o None si no se encuentra.
        
        Estrategia:
        1) Coincidencia exacta contra candidatos generados (decimales, coma, espacios).
        2) Si falla, fallback por dígitos: buscar por contains del tramo numérico y
           elegir la OC cuyo `po_number` al quitar no-dígitos coincida exactamente
           con el tramo numérico (cubre prefijos/sufijos no estándar y espacios).
        """
        candidates = self._po_candidates(po_raw)
        if not candidates:
            return None

        # 1) Exact match por candidatos
        qs = PurchaseOrder.objects.filter(po_number__in=candidates)
        if project_code:
            qs = qs.filter(project_code__cod_projects=self.clean_string(project_code))
        po = qs.order_by('-issue_date', '-id').first()
        if po:
            return po

        # 2) Fallback: dígitos únicamente (para casos con prefijos/sufijos/espacios)
        #    Ej.: 'OC 10000460', 'N°10000460', '10000460.0000', '10000460,0'
        integer_part = ''
        try:
            import re as _re
            s = self.clean_string(po_raw)
            # Preferir entero si es forma '<digits>[.,]0*'
            m = _re.match(r"^(\d+)[\.,]?0*$", s.replace(' ', ''))
            if m:
                integer_part = m.group(1)
            else:
                integer_part = self._digits_only(s)
        except Exception:
            integer_part = self._digits_only(po_raw)

        if not integer_part:
            return None

        qs2 = PurchaseOrder.objects.all()
        if project_code:
            qs2 = qs2.filter(project_code__cod_projects=self.clean_string(project_code))

        # Buscar por contains para reducir candidatos, luego validar por dígitos exactos
        qs2 = qs2.filter(po_number__icontains=integer_part).order_by('-issue_date', '-id')
        for cand in qs2[:20]:  # limitar inspección
            cand_digits = self._digits_only(cand.po_number)
            if cand_digits == integer_part:
                return cand

        # Si nada coincide en fallback, devolver None
        return None
    
    @staticmethod
    def validate_foreign_key(model_class, field_name, value, allow_null=True):
        """Valida que existe una foreign key"""
        if not value or str(value).strip() == '':
            if allow_null:
                return None
            raise ValueError(f"{model_class.__name__} - {field_name} es requerido pero está vacío")
        
        value_clean = str(value).strip()
        
        if value_clean.upper() in ('N/A', 'NA', 'NONE', ''):
            if allow_null:
                return None
            raise ValueError(f"{model_class.__name__} - {field_name} es requerido pero tiene valor N/A")
        
        try:
            kwargs = {field_name: value_clean}
            obj = model_class.objects.get(**kwargs)
            return value_clean
        except model_class.DoesNotExist:
            if allow_null:
                return None
            raise ValueError(f"{model_class.__name__} con {field_name}='{value_clean}' no existe en la base de datos")
        except model_class.MultipleObjectsReturned:
            raise ValueError(f"Múltiples {model_class.__name__} con {field_name}='{value_clean}'")


# ========================================
# RESOURCES ESPECÍFICOS - HEREDAN DE BASE
# ========================================

# ------------------------------
# COSTUMER
# ------------------------------
class CostumerResource(BaseModelResource):
    HEADER_MAPPINGS = {
        'ruc_costumer': ['ruc_costumer', 'ruc', 'nro_ruc'],
        'com_name': ['com_name', 'nombre', 'razon_social', 'empresa'],
        'type_costumer': ['type_costumer', 'tipo', 'tipo_cliente'],
        'contac_costumer': ['contac_costumer', 'contacto', 'persona_contacto']
    }
    REQUIRED_FIELDS = ['ruc_costumer', 'com_name']
    DEBUG_ENABLED = False

    def before_import_row(self, row, row_number=None, **kwargs):
        super().before_import_row(row, row_number, **kwargs)
        row['ruc_costumer'] = self.clean_string(row.get('ruc_costumer'))
        row['com_name'] = self.clean_string(row.get('com_name'), max_length=200)
        row['type_costumer'] = self.clean_string(row.get('type_costumer', 'CLIENTE'))
        row['contac_costumer'] = self.clean_string(row.get('contac_costumer'), max_length=100)

    class Meta:
        model = Costumer
        import_id_fields = ['ruc_costumer']
        skip_unchanged = True
        report_skipped = True
        fields = ('ruc_costumer', 'com_name', 'type_costumer', 'contac_costumer')


# ------------------------------
# SUPPLIER
# ------------------------------
class SupplierResource(BaseModelResource):
    HEADER_MAPPINGS = {
        'ruc_supplier': ['ruc_supplier', 'ruc', 'nro_ruc'],
        'name_supplier': ['name_supplier', 'nombre', 'razon_social', 'proveedor']
    }
    REQUIRED_FIELDS = ['ruc_supplier', 'name_supplier']
    DEBUG_ENABLED = False

    def before_import_row(self, row, row_number=None, **kwargs):
        super().before_import_row(row, row_number, **kwargs)
        row['ruc_supplier'] = self.clean_string(row.get('ruc_supplier'))
        row['name_supplier'] = self.clean_string(row.get('name_supplier'), max_length=200, to_upper=True)

    class Meta:
        model = Supplier
        import_id_fields = ['ruc_supplier']
        skip_unchanged = True
        report_skipped = True
        fields = ('ruc_supplier', 'name_supplier')


# ------------------------------
# PRODUCT
# ------------------------------
class ProductResource(BaseModelResource):
    ruc_supplier = fields.Field(
        attribute='ruc_supplier',
        widget=ForeignKeyWidget(Supplier, 'ruc_supplier')
    )

    HEADER_MAPPINGS = {
        'code_art': ['code_art', 'codigo', 'código', 'sku', 'articulo'],
        'part_number': ['part_number', 'numero_parte', 'número_parte', 'parte'],
        'descrip': ['descrip', 'descripcion', 'descripción', 'producto'],
        'ruc_supplier': ['ruc_supplier', 'ruc', 'proveedor'],
        'manufac': ['manufac', 'fabricante', 'marca'],
        'model': ['model', 'modelo'],
        'cost': ['cost', 'costo', 'precio']
    }
    REQUIRED_FIELDS = ['code_art', 'descrip']
    DEBUG_ENABLED = True

    def before_import_row(self, row, row_number=None, **kwargs):
        super().before_import_row(row, row_number, **kwargs)
        
        row['code_art'] = self.clean_code(row.get('code_art'), remove_leading_zeros=True, auto_generate=True)
        row['part_number'] = self.clean_string(row.get('part_number'), default='SIN_NUMERO', to_upper=True)
        row['descrip'] = self.clean_string(row.get('descrip'), default=f"Producto {row['code_art']}", max_length=500)
        row['manufac'] = self.clean_string(row.get('manufac'), default='NO_ESPECIFICADO', to_upper=True)
        row['model'] = self.clean_string(row.get('model'), default='NO_ESPECIFICADO', to_upper=True)
        row['ruc_supplier'] = self.validate_foreign_key(Supplier, 'ruc_supplier', row.get('ruc_supplier'), allow_null=True)
        row['cost'] = self.clean_decimal(row.get('cost'), default='0.00', decimal_places=2)
        
        if self.DEBUG_ENABLED:
            print(f"   ✅ code_art: '{row['code_art']}' | cost: S/ {row['cost']}")

    class Meta:
        model = Product
        import_id_fields = ['code_art']
        skip_unchanged = True
        report_skipped = True
        exclude = ('id',)
        fields = ('code_art', 'part_number', 'descrip', 'ruc_supplier', 'manufac', 'model', 'cost')


# ------------------------------
# CHANCE
# ------------------------------
class ChanceResource(BaseModelResource):
    info_costumer = fields.Field(
        attribute='info_costumer',
        widget=ForeignKeyWidget(Costumer, 'ruc_costumer')
    )

    HEADER_MAPPINGS = {
        'cod_projects': ['cod_projects', 'codigo_proyecto', 'proyecto', 'codigo'],
        'info_costumer': ['info_costumer', 'cliente', 'ruc_cliente', 'costumer'],
        'dres_chance': ['dres_chance', 'descripcion', 'oportunidad', 'descripción'],
        'cost_aprox_chance': ['cost_aprox_chance', 'costo_aproximado', 'monto', 'costo'],
        'date_aprox_close': ['date_aprox_close', 'fecha_cierre', 'cierre']
    }
    REQUIRED_FIELDS = ['cod_projects', 'info_costumer']
    DEBUG_ENABLED = False

    def before_import_row(self, row, row_number=None, **kwargs):
        super().before_import_row(row, row_number, **kwargs)
        
        row['cod_projects'] = self.clean_string(row.get('cod_projects'))
        row['info_costumer'] = self.validate_foreign_key(Costumer, 'ruc_costumer', row.get('info_costumer'), allow_null=False)
        row['dres_chance'] = self.clean_string(row.get('dres_chance'), max_length=1000)
        row['cost_aprox_chance'] = self.clean_decimal(row.get('cost_aprox_chance'), decimal_places=2)
        row['material_cost'] = self.clean_decimal(row.get('material_cost', 0), decimal_places=2)
        row['labor_cost'] = self.clean_decimal(row.get('labor_cost', 0), decimal_places=2)
        row['subcontracted_cost'] = self.clean_decimal(row.get('subcontracted_cost', 0), decimal_places=2)
        row['overhead_cost'] = self.clean_decimal(row.get('overhead_cost', 0), decimal_places=2)
        row['date_aprox_close'] = self.clean_date(row.get('date_aprox_close'))
        row['exchange_rate'] = self.clean_decimal(row.get('exchange_rate', '1.0000'), decimal_places=4)

    class Meta:
        model = Chance
        import_id_fields = ['cod_projects']
        skip_unchanged = True
        report_skipped = True
        fields = (
            'cod_projects', 'info_costumer', 'staff_presale', 'cost_center', 'com_exe',
            'dres_chance', 'date_aprox_close', 'currency', 'exchange_rate',
            'cost_aprox_chance', 'material_cost', 'labor_cost', 'subcontracted_cost', 
            'overhead_cost', 'estimated_duration'
        )


# ------------------------------
# PURCHASE ORDER
# ------------------------------
class PurchaseOrderResource(BaseModelResource):
    project_code = fields.Field(
        attribute='project_code',
        widget=ForeignKeyWidget(Projects, 'cod_projects')
    )

    HEADER_MAPPINGS = {
        'po_number': ['po_number', 'po', 'oc', 'orden_compra', 'orden'],
        'project_code': ['project_code', 'project', 'cod_projects', 'proyecto'],
        'issue_date': ['issue_date', 'fecha_emision', 'fecha', 'emision'],
        'currency': ['currency', 'moneda'],
        'po_status': ['po_status', 'status', 'estado']
    }
    REQUIRED_FIELDS = ['po_number', 'project_code']
    DEBUG_ENABLED = True

    def before_import_row(self, row, row_number=None, **kwargs):
        super().before_import_row(row, row_number, **kwargs)
        
        # Normalizar po_number para evitar valores como 10000465.0 (Excel)
        row['po_number'] = self.clean_code(row.get('po_number'), remove_leading_zeros=True)
        
        project_code = self.clean_string(row.get('project_code'))
        row['project_code'] = self.validate_foreign_key(Projects, 'cod_projects', project_code, allow_null=False)
        
        row['issue_date'] = self.clean_date(row.get('issue_date'))
        row['initial_delivery_date'] = self.clean_date(row.get('initial_delivery_date'))
        row['final_delivery_date'] = self.clean_date(row.get('final_delivery_date'))
        row['guide_date'] = self.clean_date(row.get('guide_date'))
        
        row['exchange_rate'] = self.clean_decimal(row.get('exchange_rate', '1.0000'), decimal_places=4)
        row['total_amount'] = self.clean_decimal(row.get('total_amount', '0.00'), decimal_places=2)
        row['te'] = self.clean_integer(row.get('te', 0))
        
        # ✅ CORRECCIÓN 1: Primero normalizar currency
        cur = self.clean_string(row.get('currency', 'PEN'), to_upper=True)
        if cur in ('SOLES', 'SOL', 'S/', 'PEN', 'S/.'):
            cur = 'PEN'
        elif cur in ('DOLAR', 'DOLARES', '$', 'USD'):
            cur = 'USD'
        row['currency'] = cur

        # ✅ CORRECCIÓN 2: LÓGICA INTELIGENTE LOCAL/IMPORT
        li_specified = self.clean_string(row.get('local_import'), to_upper=True)
        if li_specified:
            if li_specified in ('LOCAL', 'LOC', 'L', 'NACIONAL'):
                li = 'LOCAL'
            elif li_specified in ('IMPORT', 'IMP', 'I', 'IMPORTADO', 'IMPORTACION'):
                li = 'IMPORT'
            else:
                li = 'LOCAL'
        else:
            if cur == 'PEN':
                li = 'LOCAL'
            elif cur == 'USD':
                li = 'IMPORT'
            else:
                li = 'LOCAL'
        row['local_import'] = li

        # ✅ CORRECCIÓN 3: TIPO DE CAMBIO INTELIGENTE
        if cur == 'PEN':
            row['exchange_rate'] = Decimal('1.0000')
        elif cur == 'USD' and row['exchange_rate'] == Decimal('1.0000'):
            row['exchange_rate'] = Decimal('3.8000')

        row['po_status'] = self.clean_string(row.get('po_status', 'ENTREGADO'), to_upper=True)

        if self.DEBUG_ENABLED:
            print(
                f"   ✅ PO: {row['po_number']} | Proyecto: {project_code} | "
                f"Moneda: {cur} | Tipo: {li} | TC: {row['exchange_rate']}"
            )

    class Meta:
        model = PurchaseOrder
        import_id_fields = ['po_number', 'project_code']
        skip_unchanged = True
        report_skipped = True
        fields = (
            'po_number', 'project_code', 'issue_date', 'initial_delivery_date', 'final_delivery_date',
            'currency', 'exchange_rate', 'local_import', 'te', 'forma_pago', 'pagar_a',
            'guide_number', 'guide_date', 'observations', 'po_status', 'total_amount'
        )


# ------------------------------
# PO DETAIL PRODUCT
# ------------------------------
class PODetailProductResource(BaseModelResource):
    purchase_order = fields.Field(
        attribute='purchase_order',
        widget=ForeignKeyWidget(PurchaseOrder, 'id')
    )
    product = fields.Field(
        attribute='product',
        widget=ForeignKeyWidget(Product, 'code_art')
    )

    HEADER_MAPPINGS = {
        'purchase_order': ['purchase_order', 'po_number', 'po', 'oc', 'orden_compra'],
        'product': ['product', 'code_art', 'codigo', 'sku'],
        'quantity': ['quantity', 'cantidad', 'qty'],
        'unit_price': ['unit_price', 'precio_unitario', 'precio', 'price'],
        # Soporte para desambiguar OC por proyecto
        'project': ['project', 'cod_projects', 'proyecto'],
        # Opcionales para autocompletar/crear catálogo de producto
        'product_name': ['product_name', 'descripcion', 'descripción', 'producto'],
        'part_number': ['part_number', 'numero_parte', 'número_parte', 'parte'],
        'manufac': ['manufac', 'fabricante', 'marca'],
        'model': ['model', 'modelo'],
        'supplier_ruc': ['supplier_ruc', 'ruc_supplier', 'ruc', 'proveedor']
    }
    REQUIRED_FIELDS = ['purchase_order', 'product', 'quantity']
    DEBUG_ENABLED = True

    def before_import(self, dataset, **kwargs):
        # Pre-filtrar filas con OC vacía o inexistente ANTES de resolver FKs
        super().before_import(dataset, **kwargs)

        headers = list(dataset.headers)
        po_idx = headers.index('purchase_order') if 'purchase_order' in headers else None
        project_idx = headers.index('project') if 'project' in headers else None

        to_delete = []
        skipped = 0
        for i, row in enumerate(list(dataset.dict), start=1):
            po_raw = (
                row.get('purchase_order')
                or row.get('po_number')
                or row.get('po')
                or row.get('oc')
                or row.get('orden_compra')
            )
            po_number = self.clean_code(po_raw, remove_leading_zeros=True) or self.clean_string(po_raw)
            project_code = self.clean_string(row.get('project', ''))

            if not po_number:
                # No eliminar: permitir factura sin OC
                if po_idx is not None:
                    row_values = list(dataset[i - 1])
                    row_values[po_idx] = ''
                    dataset[i - 1] = tuple(row_values)
                if self.DEBUG_ENABLED:
                    print(f"   ⚠️  Pre-filtro: fila {i} sin OC; purchase_order=NULL")
                # Continuar a validar factura/fecha

            try:
                if project_code:
                    po = PurchaseOrder.objects.get(po_number=po_number, project_code__cod_projects=project_code)
                else:
                    po = PurchaseOrder.objects.get(po_number=po_number)
            except PurchaseOrder.MultipleObjectsReturned:
                po = PurchaseOrder.objects.filter(po_number=po_number).order_by('-issue_date', '-id').first()
                if not po:
                    to_delete.append(i - 1)
                    skipped += 1
                    if self.DEBUG_ENABLED:
                        print(f"   ⏭️  Pre-filtro: fila {i} eliminada (OC '{po_number}' múltiple y no resolvible)")
                    continue
            except PurchaseOrder.DoesNotExist:
                # Fallback: sufijos decimales almacenados en BD (ej. 10000460.0)
                alt_numbers = [f"{po_number}.0", f"{po_number}.00"]
                qs = PurchaseOrder.objects.filter(po_number__in=alt_numbers)
                if project_code:
                    qs = qs.filter(project_code__cod_projects=project_code)
                po = qs.order_by('-issue_date', '-id').first()
                if not po:
                    to_delete.append(i - 1)
                    skipped += 1
                    if self.DEBUG_ENABLED:
                        print(f"   ⏭️  Pre-filtro: fila {i} eliminada (OC '{po_number}' no existe)")
                    continue

            # Si existe, escribir el id directo en el dataset para el FK widget
            if po_idx is not None:
                row_values = list(dataset[i - 1])
                row_values[po_idx] = str(po.id)
                dataset[i - 1] = tuple(row_values)

        # Eliminar filas desde el final para mantener índices
        for idx in reversed(to_delete):
            del dataset[idx]
        self._import_stats['skipped'] += skipped
        if self.DEBUG_ENABLED and skipped:
            print(f"   ⏭️  Pre-filtro: {skipped} filas eliminadas por OC inválida")

    def before_import_row(self, row, row_number=None, **kwargs):
        super().before_import_row(row, row_number, **kwargs)
        
        # Resolver purchase_order por po_number
        # Tomar de cualquiera de los encabezados posibles y normalizar
        po_raw = (
            row.get('purchase_order')
            or row.get('po_number')
            or row.get('po')
            or row.get('oc')
            or row.get('orden_compra')
        )
        # Normalizar para evitar valores como 10000465.0 (Excel)
        po_number = self.clean_code(po_raw, remove_leading_zeros=True) or self.clean_string(po_raw)
        project_code = self.clean_string(row.get('project', ''))
        if not po_number:
            # Omitir filas sin OC
            row['__skip__'] = True
            row['__skip_reason'] = "Fila omitida: OC vacía"
            # Neutralizar campo para evitar resolución del ForeignKeyWidget
            row['purchase_order'] = ''
            if self.DEBUG_ENABLED:
                print(f"   ⏭️  Omitida fila {row_number}: OC vacía")
            return
        
        try:
            if project_code:
                po = PurchaseOrder.objects.get(po_number=po_number, project_code__cod_projects=project_code)
            else:
                po = PurchaseOrder.objects.get(po_number=po_number)
            # Pasar ID porque el po_number no es único entre proyectos
            row['purchase_order'] = str(po.id)
        except PurchaseOrder.DoesNotExist:
            # Fallback: sufijos decimales en BD
            alt_numbers = [f"{po_number}.0", f"{po_number}.00"]
            qs = PurchaseOrder.objects.filter(po_number__in=alt_numbers)
            if project_code:
                qs = qs.filter(project_code__cod_projects=project_code)
            po = qs.order_by('-issue_date', '-id').first()
            if not po:
                # Omitir si no existe la OC
                row['__skip__'] = True
                row['__skip_reason'] = f"Fila omitida: OC '{po_number}' no existe"
                # Neutralizar campo para evitar resolución del ForeignKeyWidget
                row['purchase_order'] = ''
                if self.DEBUG_ENABLED:
                    print(f"   ⏭️  Omitida fila {row_number}: OC '{po_number}' no existe")
                return
            else:
                row['purchase_order'] = str(po.id)
        except PurchaseOrder.MultipleObjectsReturned:
            # Sin columna 'project': elegir una OC de forma determinista (la más reciente)
            po = PurchaseOrder.objects.filter(po_number=po_number).order_by('-issue_date', '-id').first()
            if not po:
                raise ValueError(f"OC '{po_number}' existe en múltiples proyectos, y no se pudo seleccionar.")
            row['purchase_order'] = str(po.id)
        
        # Validar/crear producto del catálogo si falta
        product_code = self.clean_string(row.get('product'))
        if not product_code:
            # Omitir si no hay código de producto
            row['__skip__'] = True
            row['__skip_reason'] = "Fila omitida: product vacío"
            # Neutralizar campo para evitar resolución del ForeignKeyWidget
            row['product'] = ''
            if self.DEBUG_ENABLED:
                print(f"   ⏭️  Omitida fila {row_number}: product vacío")
            return
        try:
            # Validación estándar
            row['product'] = self.validate_foreign_key(Product, 'code_art', product_code, allow_null=False)
        except ValueError as e:
            # Intento de creación con campos opcionales si están presentes
            supplier_ruc = self.clean_string(row.get('supplier_ruc'))
            part_number = self.clean_string(row.get('part_number'), default=product_code or 'SIN_NUMERO', to_upper=True)
            manufac = self.clean_string(row.get('manufac'), default='NO_ESPECIFICADO', to_upper=True)
            model = self.clean_string(row.get('model'), default='')
            descrip = self.clean_string(row.get('product_name'), default='')

            if product_code and part_number and manufac:
                try:
                    # Si no se proporciona supplier_ruc, usar un proveedor por defecto
                    if supplier_ruc:
                        supplier = Supplier.objects.get(ruc_supplier=supplier_ruc)
                    else:
                        supplier, _ = Supplier.objects.get_or_create(
                            ruc_supplier='DUMMY',
                            defaults={'name_supplier': 'SIN_PROVEEDOR'}
                        )
                except Supplier.DoesNotExist:
                    # Omitir si no se puede crear producto por proveedor inexistente
                    row['__skip__'] = True
                    row['__skip_reason'] = (
                        f"Fila omitida: Producto '{product_code}' no existe y proveedor '{supplier_ruc}' no está registrado"
                    )
                    # Neutralizar campo para evitar resolución del ForeignKeyWidget
                    row['product'] = ''
                    if self.DEBUG_ENABLED:
                        print(f"   ⏭️  Omitida fila {row_number}: proveedor '{supplier_ruc}' no existe")
                    return
                # Crear producto mínimo con defaults razonables
                Product.objects.create(
                    code_art=product_code,
                    part_number=part_number,
                    descrip=descrip or f"Producto {product_code}",
                    ruc_supplier=supplier,
                    manufac=manufac,
                    model=model,
                    cost=self.clean_decimal(row.get('unit_price'), default='0.00', decimal_places=2)
                )
                row['product'] = product_code
            else:
                # Omitir si no hay suficientes datos para crear producto
                row['__skip__'] = True
                row['__skip_reason'] = (
                    f"Fila omitida: Producto '{product_code}' no existe y faltan datos mínimos (part_number/manufac)"
                )
                # Neutralizar campo para evitar resolución del ForeignKeyWidget
                row['product'] = ''
                if self.DEBUG_ENABLED:
                    print(f"   ⏭️  Omitida fila {row_number}: producto '{product_code}' sin datos mínimos")
                return
        
        row['product_name'] = self.clean_string(row.get('product_name'), max_length=200)
        row['quantity'] = self.clean_decimal(row.get('quantity'), decimal_places=2)
        row['unit_price'] = self.clean_decimal(row.get('unit_price'), decimal_places=2)
        # Normalizar unidad de medida a las opciones del modelo
        mu_raw = self.clean_string(row.get('measurement_unit', 'unidades'), to_upper=True)
        mu_map = {
            'UNIDADES': 'unidades', 'UND': 'unidades', 'UNIDAD': 'unidades', 'U': 'unidades',
            'M2': 'm²', 'M²': 'm²', 'M': 'm', 'METROS': 'm',
            'KG': 'kg', 'KGS': 'kg', 'KILOS': 'kg', 'KILOGRAMOS': 'kg',
            'LT': 'lt', 'LITROS': 'lt',
            'GL': 'gl', 'GALONES': 'gl',
            'CAJA': 'caja', 'CAJAS': 'caja',
            'JUEGO': 'juego', 'JUEGOS': 'juego'
        }
        row['measurement_unit'] = mu_map.get(mu_raw, 'unidades')
        row['comment'] = self.clean_string(row.get('comment'), max_length=500)
        
        if self.DEBUG_ENABLED:
            print(f"   ✅ OC: {po_number} | Producto: {row['product']} | Qty: {row['quantity']}")

    def get_instance(self, instance_loader, row):
        """Actualizar si ya existe detalle por (purchase_order, product)"""
        po_id = row.get('purchase_order')
        prod_code = self.clean_string(row.get('product'))
        try:
            if po_id and prod_code:
                return PODetailProduct.objects.get(
                    purchase_order_id=int(po_id),
                    product__code_art=prod_code
                )
        except (PODetailProduct.DoesNotExist, ValueError, TypeError):
            return None

    class Meta:
        model = PODetailProduct
        import_id_fields = ['purchase_order', 'product']
        skip_unchanged = True
        report_skipped = True
        fields = ('purchase_order', 'product', 'product_name', 'quantity', 'measurement_unit', 'unit_price', 'comment')


# ------------------------------
# INVOICE
# ------------------------------
class InvoiceResource(BaseModelResource):
    purchase_order = fields.Field(
        attribute='purchase_order',
        widget=ForeignKeyWidget(PurchaseOrder, 'id')
    )

    HEADER_MAPPINGS = {
        'purchase_order': ['purchase_order', 'po_number', 'po', 'oc', 'orden_compra'],
        # Soporte para desambiguar OC por proyecto
        'project': ['project', 'cod_projects', 'proyecto'],
        'invoice_number': ['invoice_number', 'factura', 'nro_factura', 'numero'],
        'issue_date': ['issue_date', 'fecha', 'fecha_emision']
    }
    REQUIRED_FIELDS = ['invoice_number', 'issue_date']
    DEBUG_ENABLED = True

    def before_import(self, dataset, **kwargs):
        # Pre-filtrar filas con OC vacía/inexistente y facturas anuladas antes de resolver FKs
        super().before_import(dataset, **kwargs)
        # Inicializar conjunto para deduplicar números de factura dentro del archivo
        self._seen_invoice_numbers = set()

        headers = list(dataset.headers)
        po_idx = headers.index('purchase_order') if 'purchase_order' in headers else None
        inv_idx = headers.index('invoice_number') if 'invoice_number' in headers else None
        date_idx = headers.index('issue_date') if 'issue_date' in headers else None
        project_idx = headers.index('project') if 'project' in headers else None

        # Acumular filas adicionales cuando un registro trae varias facturas en una celda
        rows_to_append = []

        to_delete = []
        skipped = 0
        for i, row in enumerate(list(dataset.dict), start=1):
            po_raw = (
                row.get('purchase_order')
                or row.get('po_number')
                or row.get('po')
                or row.get('oc')
                or row.get('orden_compra')
            )
            project_code = self.clean_string(row.get('project', ''))

            if not self.clean_string(po_raw):
                to_delete.append(i - 1)
                skipped += 1
                if self.DEBUG_ENABLED:
                    print(f"   ⏭️  Pre-filtro: fila {i} eliminada por OC vacía")
                continue

            # Resolver con helper robusto
            po = self.resolve_purchase_order(po_raw, project_code)
            if not po:
                # No eliminar: importar sin OC
                if po_idx is not None:
                    row_values = list(dataset[i - 1])
                    row_values[po_idx] = ''
                    dataset[i - 1] = tuple(row_values)
                if self.DEBUG_ENABLED:
                    print(f"   ⚠️  Pre-filtro: fila {i} OC '{self.clean_string(po_raw)}' no existe; purchase_order=NULL")
            else:
                # Escribir id de OC para el FK widget
                if po_idx is not None:
                    row_values = list(dataset[i - 1])
                    row_values[po_idx] = str(po.id)
                    dataset[i - 1] = tuple(row_values)

            # Marcar y eliminar facturas 'ANULADA'
            invoice_number = (self.clean_string(row.get('invoice_number')) or '').strip().upper()
            issue_token = (self.clean_string(row.get('issue_date')) or '').strip().upper()
            if invoice_number == 'ANULADA' or issue_token == 'ANULADA':
                # Actualizar estado de la OC
                if po:
                    po.po_status = 'ANULADA'
                    po.save()
                to_delete.append(i - 1)
                skipped += 1
                if self.DEBUG_ENABLED:
                    print(f"   🚫  Pre-filtro: fila {i} eliminada (OC {po.po_number if po else 'N/A'} ANULADA)")
                continue

            # Validaciones mínimas
            if not self.clean_string(row.get('invoice_number')) or not self.clean_date(row.get('issue_date')):
                to_delete.append(i - 1)
                skipped += 1
                if self.DEBUG_ENABLED:
                    print(f"   ⏭️  Pre-filtro: fila {i} eliminada (factura/fecha inválida)")
                continue

            # Si se resolvió OC arriba, ya se escribió; si no, queda NULL

            # Dividir celdas con múltiples números de factura (separados por '/')
            if inv_idx is not None:
                inv_raw = row.get('invoice_number') or ''
                parts = [p for p in str(inv_raw).split('/') if str(p).strip()]
                if len(parts) > 1:
                    # Normalizar quitando espacios internos
                    norm_parts = [p.replace(' ', '') for p in parts]
                    # Actualizar la fila actual con el primer número
                    base_values = list(dataset[i - 1])
                    base_values[inv_idx] = norm_parts[0]
                    dataset[i - 1] = tuple(base_values)
                    # Crear filas adicionales por cada número restante
                    for extra in norm_parts[1:]:
                        new_values = list(base_values)
                        new_values[inv_idx] = extra
                        rows_to_append.append(tuple(new_values))

        for idx in reversed(to_delete):
            del dataset[idx]
        # Agregar filas generadas por división de celdas de factura
        for values in rows_to_append:
            dataset.append(values)
        self._import_stats['skipped'] += skipped
        if self.DEBUG_ENABLED and skipped:
            print(f"   ⏭️  Pre-filtro: {skipped} filas eliminadas (ANULADA/factura o fecha inválida)")

    def before_import_row(self, row, row_number=None, **kwargs):
        super().before_import_row(row, row_number, **kwargs)
        
        # Resolver purchase_order por po_number (+ proyecto si viene)
        po_raw = (
            row.get('purchase_order')
            or row.get('po_number')
            or row.get('po')
            or row.get('oc')
            or row.get('orden_compra')
        )
        project_code = self.clean_string(row.get('project', ''))

        # Si ya viene el ID (del pre-filtro), no intentar resolver por número
        po_raw_str = self.clean_string(po_raw)
        if po_raw_str and po_raw_str.isdigit():
            try:
                po_id = int(po_raw_str)
                PurchaseOrder.objects.get(id=po_id)
                row['purchase_order'] = str(po_id)
                if self.DEBUG_ENABLED:
                    print(f"   ✅ Fila {row_number}: OC por id {po_id} confirmada")
            except PurchaseOrder.DoesNotExist:
                # Si el id no existe, intentar resolver por número usando el texto original
                po = self.resolve_purchase_order(po_raw_str, project_code)
                if not po:
                    row['purchase_order'] = ''
                    if self.DEBUG_ENABLED:
                        print(f"   ⚠️  Fila {row_number}: OC id '{po_raw_str}'/num no existe; purchase_order=NULL")
                else:
                    row['purchase_order'] = str(po.id)
        else:
            if not self.clean_string(po_raw):
                # Permitir factura sin OC (campo nullable en modelo)
                row['purchase_order'] = ''
                if self.DEBUG_ENABLED:
                    print(f"   ⚠️  Fila {row_number}: sin OC; se importará con purchase_order=NULL")
            else:
                po = self.resolve_purchase_order(po_raw, project_code)
                if not po:
                    row['purchase_order'] = ''
                    if self.DEBUG_ENABLED:
                        print(f"   ⚠️  Fila {row_number}: OC '{self.clean_string(po_raw)}' no existe; purchase_order=NULL")
                else:
                    row['purchase_order'] = str(po.id)

        # Tratar 'ANULADA' como estado de la OC: no crear factura
        invoice_number = self.clean_string(row.get('invoice_number'))
        # Normalizar formato del número de factura para evitar duplicados por espacios/variaciones
        if invoice_number:
            invoice_number = invoice_number.replace(' ', '')
        invoice_token = (invoice_number or '').strip().upper()
        issue_date_val = self.clean_string(row.get('issue_date'))
        if invoice_token == 'ANULADA' or (issue_date_val and issue_date_val.strip().upper() == 'ANULADA'):
            # Si hay OC resuelta, actualizar estado; si no, solo omitir
            po_id_val = row.get('purchase_order')
            if po_id_val:
                try:
                    po_obj = PurchaseOrder.objects.get(id=int(po_id_val))
                    po_obj.po_status = 'ANULADA'
                    po_obj.save()
                except (PurchaseOrder.DoesNotExist, ValueError, TypeError):
                    pass
            row['__skip__'] = True
            row['__skip_reason'] = "Fila omitida: ANULADA"
            if self.DEBUG_ENABLED:
                print(f"   🚫  Fila {row_number}: ANULADA (saltada)")
            return

        # Deduplicación dentro del archivo (si el mismo número aparece múltiples veces)
        if invoice_number:
            if invoice_number in getattr(self, '_seen_invoice_numbers', set()):
                row['__skip__'] = True
                row['__skip_reason'] = f"Fila omitida: factura duplicada en el archivo ({invoice_number})"
                if self.DEBUG_ENABLED:
                    print(f"   ⏭️  Omitida fila {row_number}: factura duplicada en archivo ({invoice_number})")
                return
            else:
                self._seen_invoice_numbers.add(invoice_number)

        # Validaciones mínimas: número de factura y fecha
        if not invoice_number:
            row['__skip__'] = True
            row['__skip_reason'] = "Fila omitida: factura vacía"
            if self.DEBUG_ENABLED:
                print(f"   ⏭️  Omitida fila {row_number}: factura vacía")
            return

        issue_date_clean = self.clean_date(row.get('issue_date'))
        if not issue_date_clean:
            row['__skip__'] = True
            row['__skip_reason'] = "Fila omitida: fecha de emisión inválida"
            if self.DEBUG_ENABLED:
                print(f"   ⏭️  Omitida fila {row_number}: fecha emisión inválida")
            return

        # Si existe ya la factura en BD, validar conflictos de enlace OneToOne con OC
        try:
            existing_invoice = Invoice.objects.get(invoice_number=invoice_number)
        except Invoice.DoesNotExist:
            existing_invoice = None

        po_id_val = row.get('purchase_order')
        if existing_invoice and po_id_val:
            try:
                po_id_int = int(po_id_val)
                # Si la factura ya está enlazada a otra OC distinta, omitir para evitar conflicto OneToOne
                if existing_invoice.purchase_order_id and existing_invoice.purchase_order_id != po_id_int:
                    row['__skip__'] = True
                    row['__skip_reason'] = (
                        f"Fila omitida: factura {invoice_number} ya vinculada a otra OC (id {existing_invoice.purchase_order_id})"
                    )
                    if self.DEBUG_ENABLED:
                        print(f"   ⏭️  Omitida fila {row_number}: {row['__skip_reason']}")
                    return
            except (ValueError, TypeError):
                pass

        # Caso normal: si resolvimos OC, ya se asignó arriba
        row['invoice_number'] = invoice_number
        row['issue_date'] = issue_date_clean

    def get_instance(self, instance_loader, row):
        """Lookup principal por 'invoice_number' para realizar upsert correcto.
        Fallback: si no hay número de factura, intentar por 'purchase_order_id'.
        Si la fila fue marcada como OMITIR, devolvemos None.
        """
        # Si la fila se marcó para omitir, no devolver instancia
        if isinstance(row, dict) and row.get('__skip__'):
            return None

        invoice_number = row.get('invoice_number')
        if invoice_number:
            try:
                return Invoice.objects.get(invoice_number=str(invoice_number))
            except Invoice.DoesNotExist:
                pass
            except (ValueError, TypeError):
                pass

        # Fallback por OC si no hubo número
        po_id = row.get('purchase_order')
        try:
            if po_id:
                return Invoice.objects.get(purchase_order_id=int(po_id))
        except (Invoice.DoesNotExist, ValueError, TypeError):
            return None
        return None

    class Meta:
        model = Invoice
        import_id_fields = ['invoice_number']
        skip_unchanged = False
        report_skipped = True
        fields = ('purchase_order', 'invoice_number', 'issue_date')


# ------------------------------
# PO DETAIL SUPPLIER
# ------------------------------
class PODetailSupplierResource(BaseModelResource):
    purchase_order = fields.Field(
        attribute='purchase_order',
        widget=ForeignKeyWidget(PurchaseOrder, 'id')  # ✅ CORRECTO: usar 'id'
    )
    supplier = fields.Field(
        attribute='supplier',
        widget=ForeignKeyWidget(Supplier, 'ruc_supplier')
    )

    HEADER_MAPPINGS = {
        'purchase_order': ['purchase_order', 'po_number', 'po', 'oc'],
        'supplier': ['supplier', 'ruc_supplier', 'supplier_ruc', 'ruc', 'proveedor'],  # ✅ AGREGADO: 'supplier_ruc'
        'project': ['project', 'cod_projects', 'proyecto'],  # ✅ AGREGADO
        'delivery_date': ['delivery_date', 'fecha_entrega', 'entrega']
    }
    REQUIRED_FIELDS = ['purchase_order', 'supplier']
    DEBUG_ENABLED = True  # ✅ CAMBIO: activar debug

    def before_import(self, dataset, **kwargs):
        super().before_import(dataset, **kwargs)

        headers = list(dataset.headers)
        po_idx = headers.index('purchase_order') if 'purchase_order' in headers else None

        to_delete = []
        skipped = 0
        for i, row in enumerate(list(dataset.dict), start=1):
            po_raw = (
                row.get('purchase_order')
                or row.get('po_number')
                or row.get('po')
                or row.get('oc')
            )
            project_code = self.clean_string(row.get('project', ''))

            if not self.clean_string(po_raw):
                to_delete.append(i - 1)
                skipped += 1
                if self.DEBUG_ENABLED:
                    print(f"   ⏭️  Pre-filtro: fila {i} eliminada por OC vacía")
                continue

            # ✅ Usar resolve_purchase_order
            po = self.resolve_purchase_order(po_raw, project_code)
            if not po:
                to_delete.append(i - 1)
                skipped += 1
                if self.DEBUG_ENABLED:
                    print(f"   ⏭️  Pre-filtro: fila {i} eliminada (OC no existe)")
                continue

            # ✅ Validar proveedor desde múltiples columnas
            supplier_raw = (
                row.get('supplier')
                or row.get('ruc_supplier')
                or row.get('supplier_ruc')
                or row.get('ruc')
                or row.get('proveedor')
            )
            try:
                Supplier.objects.get(ruc_supplier=self.clean_string(supplier_raw))
            except Supplier.DoesNotExist:
                to_delete.append(i - 1)
                skipped += 1
                if self.DEBUG_ENABLED:
                    print(f"   ⏭️  Pre-filtro: fila {i} eliminada (Proveedor no existe)")
                continue

            # ✅ Escribir ID de OC
            if po_idx is not None:
                row_values = list(dataset[i - 1])
                row_values[po_idx] = str(po.id)
                dataset[i - 1] = tuple(row_values)

        for idx in reversed(to_delete):
            del dataset[idx]
        self._import_stats['skipped'] += skipped
        if self.DEBUG_ENABLED and skipped:
            print(f"   ⏭️  Pre-filtro: {skipped} filas eliminadas")

    def before_import_row(self, row, row_number=None, **kwargs):
        super().before_import_row(row, row_number, **kwargs)
        
        po_raw = (
            row.get('purchase_order')
            or row.get('po_number')
            or row.get('po')
            or row.get('oc')
        )
        project_code = self.clean_string(row.get('project', ''))

        po_raw_str = self.clean_string(po_raw)
        if po_raw_str and po_raw_str.isdigit():
            try:
                po_id = int(po_raw_str)
                PurchaseOrder.objects.get(id=po_id)
                row['purchase_order'] = str(po_id)
            except PurchaseOrder.DoesNotExist:
                po = self.resolve_purchase_order(po_raw_str, project_code)
                if not po:
                    row['__skip__'] = True
                    row['__skip_reason'] = f"OC no existe"
                    row['purchase_order'] = ''
                    return
                row['purchase_order'] = str(po.id)
        else:
            if not self.clean_string(po_raw):
                row['__skip__'] = True
                row['__skip_reason'] = "OC vacía"
                row['purchase_order'] = ''
                return
            
            po = self.resolve_purchase_order(po_raw, project_code)
            if not po:
                row['__skip__'] = True
                row['__skip_reason'] = f"OC no existe"
                row['purchase_order'] = ''
                return
            row['purchase_order'] = str(po.id)

        # ✅ Validar proveedor desde múltiples columnas
        supplier_raw = (
            row.get('supplier')
            or row.get('ruc_supplier')
            or row.get('supplier_ruc')
            or row.get('ruc')
            or row.get('proveedor')
        )
        try:
            row['supplier'] = self.validate_foreign_key(Supplier, 'ruc_supplier', supplier_raw, allow_null=False)
        except ValueError as e:
            row['__skip__'] = True
            row['__skip_reason'] = f"Proveedor inválido"
            row['supplier'] = ''
            return

        row['delivery_date'] = self.clean_date(row.get('delivery_date'))

    class Meta:
        model = PODetailSupplier
        import_id_fields = ['purchase_order', 'supplier']
        skip_unchanged = True
        report_skipped = True
        fields = ('purchase_order', 'supplier', 'delivery_date')
# ------------------------------
# PROJECT ACTIVITY
# ------------------------------
class ProjectActivityResource(BaseModelResource):
    HEADER_MAPPINGS = {
        'project': ['project', 'cod_projects', 'proyecto'],
        'name': ['name', 'nombre', 'actividad'],
        'percentage_completed': ['percentage_completed', 'porcentaje', 'avance'],
        'total_units': ['total_units', 'unidades_totales', 'total'],
        'completed_units': ['completed_units', 'unidades_completadas', 'completadas']
    }
    REQUIRED_FIELDS = ['project', 'name']
    DEBUG_ENABLED = False

    def before_import_row(self, row, row_number=None, **kwargs):
        super().before_import_row(row, row_number, **kwargs)
        
        row['project'] = self.validate_foreign_key(Projects, 'cod_projects', row.get('project'), allow_null=False)
        row['name'] = self.clean_string(row.get('name'), max_length=200)
        row['description'] = self.clean_string(row.get('description'), max_length=1000)
        row['percentage_completed'] = self.clean_decimal(row.get('percentage_completed', 0), decimal_places=2)
        row['total_units'] = self.clean_decimal(row.get('total_units', 0), decimal_places=2)
        row['completed_units'] = self.clean_decimal(row.get('completed_units', 0), decimal_places=2)

    class Meta:
        model = ProjectActivity
        import_id_fields = ['project', 'name']
        skip_unchanged = True
        report_skipped = True
        fields = (
            'project', 'name', 'description',
            'complexity', 'effort', 'impact',
            'unit_of_measure', 'total_units', 'completed_units',
            'percentage_completed', 'calculated_weight', 'is_active'
        )


# ------------------------------
# CLIENT INVOICE
# ------------------------------
class ClientInvoiceResource(BaseModelResource):
    HEADER_MAPPINGS = {
        'project': ['project', 'cod_projects', 'proyecto'],
        'invoice_number': ['invoice_number', 'factura', 'nro_factura', 'numero'],
        'invoice_date': ['invoice_date', 'fecha', 'fecha_emision'],
        'amount': ['amount', 'monto', 'importe'],
        'status': ['status', 'estado'],
        'paid_amount': ['paid_amount', 'monto_pagado', 'pagado']
    }
    REQUIRED_FIELDS = ['project', 'invoice_number', 'invoice_date', 'amount']
    DEBUG_ENABLED = False

    def before_import_row(self, row, row_number=None, **kwargs):
        super().before_import_row(row, row_number, **kwargs)
        
        row['project'] = self.validate_foreign_key(Projects, 'cod_projects', row.get('project'), allow_null=False)
        row['invoice_number'] = self.clean_string(row.get('invoice_number'))
        row['invoice_date'] = self.clean_date(row.get('invoice_date'))
        row['amount'] = self.clean_decimal(row.get('amount'), decimal_places=2)
        row['paid_amount'] = self.clean_decimal(row.get('paid_amount', 0), decimal_places=2)
        row['status'] = self.clean_string(row.get('status', 'PENDING'), to_upper=True)
        
        # Fechas opcionales
        row['due_date'] = self.clean_date(row.get('due_date'))
        row['payment_reported_date'] = self.clean_date(row.get('payment_reported_date'))
        row['bank_verified_date'] = self.clean_date(row.get('bank_verified_date'))
        row['fully_paid_date'] = self.clean_date(row.get('fully_paid_date'))
        
        # Notas y referencias
        row['client_notes'] = self.clean_string(row.get('client_notes'), max_length=500)
        row['bank_reference'] = self.clean_string(row.get('bank_reference'), max_length=100)
        row['bank_confirmation_code'] = self.clean_string(row.get('bank_confirmation_code'), max_length=100)

    class Meta:
        model = ClientInvoice
        import_id_fields = ['invoice_number']
        skip_unchanged = True
        report_skipped = True
        fields = (
            'project', 'invoice_number', 'invoice_date', 'amount', 'status',
            'due_date', 'payment_reported_date', 'bank_verified_date', 'fully_paid_date',
            'paid_amount', 'client_notes', 'bank_reference', 'bank_confirmation_code'
        )


# ------------------------------
# PROJECT MONTHLY BASELINE
# ------------------------------
class ProjectMonthlyBaselineResource(BaseModelResource):
    HEADER_MAPPINGS = {
        'project': ['project', 'cod_projects', 'proyecto'],
        'month_index': ['month_index', 'mes', 'indice_mes'],
        'pv_planned': ['pv_planned', 'pv', 'valor_planificado'],
        'ev_planned': ['ev_planned', 'ev', 'valor_ganado'],
        'ac_planned': ['ac_planned', 'ac', 'costo_real'],
        'client_billing_planned': ['client_billing_planned', 'facturacion', 'billing'],
        'progress_planned': ['progress_planned', 'avance', 'progreso'],
        'label': ['label', 'etiqueta', 'nombre']
    }
    REQUIRED_FIELDS = ['project', 'month_index']
    DEBUG_ENABLED = False

    def before_import_row(self, row, row_number=None, **kwargs):
        super().before_import_row(row, row_number, **kwargs)
        
        row['project'] = self.validate_foreign_key(Projects, 'cod_projects', row.get('project'), allow_null=False)
        row['month_index'] = self.clean_integer(row.get('month_index'))
        row['pv_planned'] = self.clean_decimal(row.get('pv_planned', 0), decimal_places=2)
        row['ev_planned'] = self.clean_decimal(row.get('ev_planned', 0), decimal_places=2)
        row['ac_planned'] = self.clean_decimal(row.get('ac_planned', 0), decimal_places=2)
        row['client_billing_planned'] = self.clean_decimal(row.get('client_billing_planned', 0), decimal_places=2)
        row['progress_planned'] = self.clean_decimal(row.get('progress_planned', 0), decimal_places=2)
        row['label'] = self.clean_string(row.get('label'), max_length=50)

    class Meta:
        model = ProjectMonthlyBaseline
        import_id_fields = ['project', 'month_index']
        skip_unchanged = True
        report_skipped = True
        fields = (
            'project', 'month_index', 'pv_planned', 'ev_planned', 'ac_planned',
            'client_billing_planned', 'progress_planned', 'label'
        )