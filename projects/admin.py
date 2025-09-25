from django.contrib import admin
from .models import (
    Costumer, Supplier, Product,
    Chance, Projects, Respon,
    Presale, Billing, Hoursrecord,
    PODetailProduct
)

# ------------------------------
# COSTUMER
# ------------------------------
@admin.register(Costumer)
class CostumerAdmin(admin.ModelAdmin):
    list_display = ("ruc_costumer", "com_name", "type_costumer", "contac_costumer")
    search_fields = ("ruc_costumer", "com_name")
    list_filter = ("type_costumer",)


# ------------------------------
# SUPPLIER
# ------------------------------
@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("ruc_supplier", "name_supplier")
    search_fields = ("ruc_supplier", "name_supplier")


# ------------------------------
# PRODUCT
# ------------------------------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("code_art", "part_number", "manufac", "ruc_supplier", "cost")
    search_fields = ("part_number", "manufac")
    list_filter = ("manufac",)


# ------------------------------
# CHANCE
# ------------------------------
@admin.register(Chance)
class ChanceAdmin(admin.ModelAdmin):
    list_display = ("cod_projects", "info_costumer", "dres_chance", "cost_aprox_chance", "aprox_uti", "regis_date")
    search_fields = ("cod_projects", "info_costumer__com_name")
    list_filter = ("regis_date",)


# ------------------------------
# PROJECTS
# ------------------------------
@admin.register(Projects)
class ProjectsAdmin(admin.ModelAdmin):
    list_display = ("cod_projects", "respon_projects", "state_projects", "start_date", "estimated_end_date")
    search_fields = ("cod_projects__cod_projects", "respon_projects__name")
    list_filter = ("state_projects",)


# ------------------------------
# RESPONSABLE
# ------------------------------
@admin.register(Respon)
class ResponAdmin(admin.ModelAdmin):
    list_display = ("emplo_cod", "name", "role")
    search_fields = ("name", "role")


# ------------------------------
# PRESALE
# ------------------------------
@admin.register(Presale)
class PresaleAdmin(admin.ModelAdmin):
    list_display = ("job_name", "cost_center", "contract_amount", "total_cost", "created_at")
    search_fields = ("job_name", "cost_center")
    list_filter = ("created_at",)


# ------------------------------
# BILLING
# ------------------------------
@admin.register(Billing)
class BillingAdmin(admin.ModelAdmin):
    list_display = ("projects", "month", "amount", "cost_material", "cost_h", "outsourced", "overhead_costs")
    search_fields = ("projects__cod_projects__dres_chance",)
    list_filter = ("month", "regis_date")


# ------------------------------
# HOURS RECORD
# ------------------------------
@admin.register(Hoursrecord)
class HoursrecordAdmin(admin.ModelAdmin):
    list_display = ("pro", "respon", "date", "hours", "acti")
    search_fields = ("respon", "acti")
    list_filter = ("date",)


# ------------------------------
# PURCHASE ORDER DETAIL
# ------------------------------
@admin.register(PODetailProduct)
class PODetailProductAdmin(admin.ModelAdmin):
    list_display = ("po_number", "product_code", "units", "unit_amount", "subtotal", "tax", "total")
    search_fields = ("po_number__numero_oc", "product_code__part_number")
    list_filter = ("po_number",)
