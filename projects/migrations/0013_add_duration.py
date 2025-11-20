from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0012_earnedvalue_projectprogress'),
    ]

    operations = [
        migrations.AddField(
            model_name='presale',
            name='estimated_duration',
            field=models.IntegerField(
                default=6,
                verbose_name='Duración estimada (meses)'
            ),
        ),
    ]