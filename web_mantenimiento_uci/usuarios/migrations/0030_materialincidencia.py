# Generated by Django 4.2.19 on 2025-06-09 03:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0029_respuestasoporte'),
    ]

    operations = [
        migrations.CreateModel(
            name='MaterialIncidencia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad_usada', models.PositiveIntegerField(default=1)),
                ('fecha_asignacion', models.DateTimeField(auto_now_add=True)),
                ('incidencia', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='usuarios.incidencia')),
                ('material', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='usuarios.material')),
            ],
        ),
    ]
