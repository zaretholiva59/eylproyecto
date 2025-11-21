# Generated manually to fix to_field from 'id' to 'po_number'

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0037_alter_clientinvoice_bank_reference'),
    ]

    operations = [
        migrations.AlterField(
            model_name='podetailproduct',
            name='purchase_order',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='projects.purchaseorder',
                to_field='po_number'
            ),
        ),
        migrations.AlterField(
            model_name='podetailsupplier',
            name='purchase_order',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='projects.purchaseorder',
                to_field='po_number'
            ),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='purchase_order',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='invoice',
                to='projects.purchaseorder',
                to_field='po_number',
                verbose_name='Orden de Compra relacionada'
            ),
        ),
    ]

