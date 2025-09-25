from django.db import models

class Presale(models.Model):
        cost_center = models.CharField(max_length=100)
        job_name = models.CharField(max_length=200)
        contract_amount = models.DecimalField(max_digits=12, decimal_places=2)
        material_cost = models.DecimalField(max_digits=12, decimal_places=2)
        labor_cost = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Labor cost (h-h)")
        subcontracted_cost = models.DecimalField(max_digits=12, decimal_places=2)
        overhead_cost = models.DecimalField(max_digits=12, decimal_places=2)
        total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)

        def save(self, *args, **kwargs):
                self.total_cost = (
            self.material_cost +
            self.labor_cost +
            self.subcontracted_cost +
            self.overhead_cost
        )
                super().save(*args, **kwargs)

        def __str__(self):
                return f"{self.job_name} ({self.cost_center})"





