from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('equipo', '0005_equipo_tipo_combustible'),
    ]

    operations = [
        # Nuevos campos
        migrations.AddField(
            model_name='equipo',
            name='numero_economico',
            field=models.CharField(
                default='00',
                max_length=10,
                unique=True,
                verbose_name='No. Económico',
                help_text='Número de unidad en la flota (ej. 01, 02...)',
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='equipo',
            name='niv',
            field=models.CharField(
                blank=True,
                default='',
                max_length=50,
                verbose_name='NIV / VIN',
                help_text='Número de Identificación Vehicular',
            ),
        ),
        migrations.AddField(
            model_name='equipo',
            name='rendimiento',
            field=models.DecimalField(
                blank=True,
                null=True,
                max_digits=5,
                decimal_places=2,
                verbose_name='Rendimiento (km/L)',
            ),
        ),
        migrations.AddField(
            model_name='equipo',
            name='asignacion',
            field=models.CharField(
                blank=True,
                default='',
                max_length=100,
                verbose_name='Asignación',
                help_text='Operador o área a quien está asignada la unidad',
            ),
        ),

        # Correcciones a campos existentes
        migrations.AlterField(
            model_name='equipo',
            name='placa',
            field=models.CharField(
                blank=True,
                default='',
                max_length=50,
                verbose_name='Placa',
            ),
        ),
        migrations.AlterField(
            model_name='equipo',
            name='marca',
            field=models.CharField(
                blank=True,
                default='',
                max_length=100,
                verbose_name='Marca',
            ),
        ),
        migrations.AlterField(
            model_name='equipo',
            name='modelo',
            field=models.CharField(
                max_length=100,
                verbose_name='Modelo',
            ),
        ),
        migrations.AlterField(
            model_name='equipo',
            name='year',
            field=models.IntegerField(
                blank=True,
                null=True,
                verbose_name='Año',
            ),
        ),
        migrations.AlterField(
            model_name='equipo',
            name='capacidad_tanque',
            field=models.IntegerField(
                blank=True,
                null=True,
                verbose_name='Capacidad del tanque (L)',
            ),
        ),
        migrations.AlterModelOptions(
            name='equipo',
            options={
                'ordering': ['numero_economico'],
                'verbose_name': 'Equipo',
                'verbose_name_plural': 'Equipos',
            },
        ),
    ]
