from django.db import models

class Respon(models.Model):
    emplo_cod = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=50)

    class Meta:
        db_table = "respon"

    def __str__(self):
        return f"{self.name} - {self.role}"
