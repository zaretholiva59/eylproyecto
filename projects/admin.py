from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import (
    Costumer, Supplier, Product,
    Chance, Projects, Respon,
    Billing, Hoursrecord,
    PurchaseOrder, PODetailProduct, PODetailSupplier, Invoice,
    BudgetChange,
    ProjectBaseline, ProjectMonthlyBaseline, ProjectActivity, ClientInvoice
)

# ✅ IMPORTAR RESOURCES DESDE resources.py
from .resources import (
    CostumerResource,
    SupplierResource,
    ProductResource,
    ChanceResource,
    PurchaseOrderResource,
    PODetailProductResource,
    InvoiceResource,
    PODetailSupplierResource,
    ProjectActivityResource,
    ClientInvoiceResource,
    ProjectMonthlyBaselineResource
)


# ========================================
# MODELOS CON IMPORT/EXPORT
# ========================================

# ------------------------------
# COSTUMER
# ------------------------------
@admin.register(Costumer)
class CostumerAdmin(ImportExportModelAdmin):
    resource_class = CostumerResource
    
    list_display = ("ruc_costumer", "com_name", "type_costumer", "contac_costumer")
    search_fields = ("ruc_costumer", "com_name")
    list_filter = ("type_costumer",)

    def get_import_formats(self):
        from import_export.formats import base_formats
        return [base_formats.XLSX, base_formats.CSV]

    def get_export_formats(self):
        from import_export.formats import base_formats
        return [base_formats.XLSX, base_formats.CSV]


# ------------------------------
# SUPPLIER
# ------------------------------
@admin.register(Supplier)
class SupplierAdmin(ImportExportModelAdmin):
    resource_class = SupplierResource
    
    list_display = ("ruc_supplier", "name_supplier")
    search_fields = ("ruc_supplier", "name_supplier")

    def get_import_formats(self):
        from import_export.formats import base_formats
        return [base_formats.XLSX, base_formats.CSV]

    def get_export_formats(self):
        from import_export.formats import base_formats
        return [base_formats.XLSX, base_formats.CSV]


# ------------------------------
# PRODUCT
# ------------------------------
@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    resource_class = ProductResource
    
    list_display = ("code_art", "part_number", "descrip", "ruc_supplier", "cost")
    search_fields = ("part_number", "manufac")
    list_filter = ("manufac",)

    def get_import_formats(self):
        from import_export.formats import base_formats
        return [base_formats.XLSX, base_formats.CSV]

    def get_export_formats(self):
        from import_export.formats import base_formats
        return [base_formats.XLSX, base_formats.CSV]


# ------------------------------
# CHANCE
# ------------------------------
@admin.register(Chance)
class ChanceAdmin(ImportExportModelAdmin):
    resource_class = ChanceResource
    
    list_display = ("cod_projects", "info_costumer", "dres_chance", "cost_aprox_chance", "aprox_uti", "regis_date")
    search_fields = ("cod_projects", "info_costumer__com_name")
    list_filter = ("regis_date",)

    def get_import_formats(self):
        from import_export.formats import base_formats
        return [base_formats.XLSX, base_formats.CSV]

    def get_export_formats(self):
        from import_export.formats import base_formats
        return [base_formats.XLSX, base_formats.CSV]


# ------------------------------
# PROJECTS (Sin Import/Export)
# ------------------------------
@admin.register(Projects)
class ProjectsAdmin(admin.ModelAdmin):
    list_display = ("cod_projects", "respon_projects", "state_projects", "start_date", "estimated_end_date")
    search_fields = ("cod_projects__cod_projects", "respon_projects__name")
    list_filter = ("state_projects",)


# ------------------------------
# RESPONSIBLE (Sin Import/Export)
# ------------------------------
@admin.register(Respon)
class ResponAdmin(admin.ModelAdmin):
    list_display = ("emplo_cod", "name", "role")
    search_fields = ("name", "role")


# ------------------------------
# BILLING (Sin Import/Export)
# ------------------------------
@admin.register(Billing)
class BillingAdmin(admin.ModelAdmin):
    list_display = ("projects", "month", "amount", "cost_material", "cost_h", "outsourced", "overhead_costs")
    search_fields = ("projects__cod_projects__dres_chance",)
    list_filter = ("month", "regis_date")


# ------------------------------
# HOURS RECORD (Sin Import/Export)
# ------------------------------
@admin.register(Hoursrecord)
class HoursrecordAdmin(admin.ModelAdmin):
    list_display = ("pro", "respon", "date", "hours", "acti")
    search_fields = ("respon", "acti")
    list_filter = ("date",)


# ------------------------------
# PURCHASE ORDER
# ------------------------------
class PODetailSupplierInline(admin.TabularInline):
    model = PODetailSupplier
    extra = 0
    fields = ('supplier', 'supplier_amount', 'delivery_date', 'supplier_status', 'status_factura_contabilidad')
    readonly_fields = ('supplier_amount',)
    can_delete = True

class InvoiceInline(admin.TabularInline):
    model = Invoice
    fk_name = 'purchase_order'
    extra = 0
    max_num = 1
    fields = ('invoice_number', 'issue_date')
    can_delete = True

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(ImportExportModelAdmin):
    resource_class = PurchaseOrderResource
    
    list_display = ("po_number", "project_code", "issue_date", "initial_delivery_date", "final_delivery_date", "currency", "po_status", "total_amount")
    search_fields = ("po_number", "project_code__cod_projects")
    list_filter = ("currency", "po_status", "issue_date")
    inlines = [PODetailSupplierInline, InvoiceInline]

    def get_import_formats(self):
        from import_export.formats import base_formats
        return [base_formats.XLSX, base_formats.CSV]

    def get_export_formats(self):
        from import_export.formats import base_formats
        return [base_formats.XLSX, base_formats.CSV]


# ------------------------------
# PURCHASE ORDER DETAIL - PRODUCT
# ------------------------------
@admin.register(PODetailProduct)
class PODetailProductAdmin(ImportExportModelAdmin):
    resource_class = PODetailProductResource
    
    list_display = ("purchase_order", "product", "quantity", "unit_price", "total")
    search_fields = ("purchase_order__po_number", "product__part_number")
    list_filter = ("purchase_order",)

    def get_import_formats(self):
        from import_export.formats import base_formats
        return [base_formats.XLSX, base_formats.CSV]

    def get_export_formats(self):
        from import_export.formats import base_formats
        return [base_formats.XLSX, base_formats.CSV]


# ------------------------------
# INVOICE (Factura Proveedor)
# ------------------------------
@admin.register(Invoice)
class InvoiceAdmin(ImportExportModelAdmin):
    resource_class = InvoiceResource
    
    list_display = ("invoice_number", "issue_date", "purchase_order", "supplier_name", "total_amount", "currency")
    search_fields = ("invoice_number", "supplier_name", "supplier_ruc", "purchase_order__po_number")
    list_filter = ("issue_date", "invoice_type", "currency")

    def get_import_formats(self):
        from import_export.formats import base_formats
        return [base_formats.XLSX, base_formats.CSV]

    def get_export_formats(self):
        from import_export.formats import base_formats
        return [base_formats.XLSX, base_formats.CSV]


# ------------------------------
# PURCHASE ORDER DETAIL - SUPPLIER
# ------------------------------
@admin.register(PODetailSupplier)
class PODetailSupplierAdmin(ImportExportModelAdmin):
    resource_class = PODetailSupplierResource
    
    list_display = ("purchase_order", "supplier", "supplier_amount", "delivery_date", "supplier_status", "status_factura_contabilidad")
    search_fields = ("purchase_order__po_number", "supplier__name_supplier")
    list_filter = ("supplier_status", "delivery_date")
    readonly_fields = ('supplier_amount', 'supplier_status', 'status_factura_contabilidad')

    def get_import_formats(self):
        from import_export.formats import base_formats
        return [base_formats.XLSX, base_formats.CSV]

    def get_export_formats(self):
        from import_export.formats import base_formats
        return [base_formats.XLSX, base_formats.CSV]


# ------------------------------
# BUDGET CHANGES (Sin Import/Export)
# ------------------------------
@admin.register(BudgetChange)
class BudgetChangeAdmin(admin.ModelAdmin):
    list_display = ("project", "amount", "status", "change_date", "reference", "created_at")
    search_fields = ("project__cod_projects__cod_projects", "reference", "reason")
    list_filter = ("status", "change_date", "created_at")


# ------------------------------
# PROJECT BASELINE (Sin Import/Export)
# ------------------------------
@admin.register(ProjectBaseline)
class ProjectBaselineAdmin(admin.ModelAdmin):
    list_display = ("project", "version_name", "start_date", "duration_months", "bac_planned", "contract_planned")
    search_fields = ("project__cod_projects__cod_projects", "version_name")
    list_filter = ("version_name",)


# ------------------------------
# PROJECT MONTHLY BASELINE
# ------------------------------
@admin.register(ProjectMonthlyBaseline)
class ProjectMonthlyBaselineAdmin(ImportExportModelAdmin):
    resource_class = ProjectMonthlyBaselineResource
    
    list_display = ("project", "month_index", "pv_planned", "ev_planned", "ac_planned", "client_billing_planned", "progress_planned", "label")
    search_fields = ("project__cod_projects__cod_projects", "label")
    list_filter = ("month_index", "project")
    ordering = ("project", "month_index")
    
    def get_import_formats(self):
        from import_export.formats import base_formats
        return [base_formats.XLSX, base_formats.CSV]
    
    def get_export_formats(self):
        from import_export.formats import base_formats
        return [base_formats.XLSX, base_formats.CSV]


# ------------------------------
# PROJECT ACTIVITY (PMI)
# ------------------------------
@admin.register(ProjectActivity)
class ProjectActivityAdmin(ImportExportModelAdmin):
    resource_class = ProjectActivityResource
    
    list_display = ("project", "name", "percentage_completed", "calculated_weight", "unit_of_measure", "total_units", "completed_units", "is_active", "updated_at")
    search_fields = ("project__cod_projects__cod_projects", "name", "description")
    list_filter = ("is_active", "complexity", "effort", "impact", "project")
    ordering = ("project", "-calculated_weight", "name")
    
    def get_import_formats(self):
        from import_export.formats import base_formats
        return [base_formats.XLSX, base_formats.CSV]
    
    def get_export_formats(self):
        from import_export.formats import base_formats
        return [base_formats.XLSX, base_formats.CSV]


# ------------------------------
# CLIENT INVOICE (FACTURACIÓN)
# ------------------------------
@admin.register(ClientInvoice)
class ClientInvoiceAdmin(ImportExportModelAdmin):
    resource_class = ClientInvoiceResource
    
    list_display = ("project", "invoice_number", "invoice_date", "amount", "status", "bank_verified_date", "fully_paid_date", "paid_amount")
    search_fields = ("project__cod_projects__cod_projects", "invoice_number")
    list_filter = ("status", "invoice_date", "bank_verified_date", "fully_paid_date", "project")
    ordering = ("-invoice_date", "project")
    
    def get_import_formats(self):
        from import_export.formats import base_formats
        return [base_formats.XLSX, base_formats.CSV]
    
    def get_export_formats(self):
        from import_export.formats import base_formats
        return [base_formats.XLSX, base_formats.CSV]