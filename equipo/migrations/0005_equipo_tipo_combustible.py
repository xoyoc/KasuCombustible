from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('equipo', '0004_equipo_activo_equipo_kilometraje_actual'),
    ]

    operations = [
        migrations.AddField(
            model_name='equipo',
            name='tipo_combustible',
            field=models.CharField(
                choices=[('diesel', 'Diesel'), ('gasolina', 'Gasolina')],
                default='diesel',
                max_length=10,
                verbose_name='Tipo de combustible',
            ),
        ),
    ]
