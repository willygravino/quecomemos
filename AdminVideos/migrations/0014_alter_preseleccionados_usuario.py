# Generated by Django 5.0.3 on 2024-11-18 17:55

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('AdminVideos', '0013_rename_nombre_plato_elegido_preseleccionados_nombre_plato_preseleccionado_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='preseleccionados',
            name='usuario',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='platos_preseleccionados', to=settings.AUTH_USER_MODEL),
        ),
    ]
