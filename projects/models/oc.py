from django.db import models
from projects.models.projects import Projects  # Projects model (where PO belongs)
from projects.models.projects import Projects  # Projects model (where PO belongs)
from .choices import oc_state

class PurchaseOrder(models.Model):
    po_number = models.CharField(max_length=30, primary_key=True)
    project_code = models.ForeignKey(Projects, on_delete=models.CASCADE)
    project_code = models.ForeignKey(Projects, on_delete=models.CASCADE)
    initial_delivery_date = models.DateField()
    final_delivery_date = models.DateField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10)
    po_status = models.CharField(max_length=30, choices=oc_state)
    observations = models.TextField(blank=True)

    class Meta:
         db_table = "purchase_order"
    
    def __str__(self):
          return f"PO {self.po_number} - Project {self.project_code}"
    
    def update_totals(self):
        details = self.podetailproduct_set.all()
        self.total_amount = sum([d.total for d in details])
        self.save()
         



    
    


    


