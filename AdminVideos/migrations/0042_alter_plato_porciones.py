# Generated by Django 5.0.3 on 2025-05-24 01:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('AdminVideos', '0041_remove_plato_tipo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='plato',
            name='porciones',
            field=models.PositiveIntegerField(blank=True, help_text='Cantidad de porciones que rinde este plato', null=True),
        ),
    ]
