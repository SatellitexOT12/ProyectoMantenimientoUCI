# Generated by Django 4.2.19 on 2025-06-10 21:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0030_materialincidencia'),
    ]

    operations = [
        migrations.AddField(
            model_name='respuestasoporte',
            name='leido',
            field=models.BooleanField(default=False),
        ),
    ]
