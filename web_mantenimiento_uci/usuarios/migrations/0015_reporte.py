# Generated by Django 4.2.19 on 2025-03-13 00:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0014_material'),
    ]

    operations = [
        migrations.CreateModel(
            name='Reporte',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(max_length=50)),
                ('fecha', models.DateTimeField()),
                ('descripcion', models.TextField()),
                ('reporte_incidencia', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='usuarios.incidencia')),
                ('reporte_material', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='usuarios.material')),
            ],
        ),
    ]
