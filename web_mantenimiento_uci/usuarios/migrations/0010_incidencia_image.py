# Generated by Django 4.2.19 on 2025-03-04 22:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0009_alter_incidencia_estado_alter_incidencia_prioridad_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='incidencia',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='incidencias/'),
        ),
    ]
