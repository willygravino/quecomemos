# Generated by Django 5.0.3 on 2024-11-18 18:06

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('AdminVideos', '0014_alter_preseleccionados_usuario'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameField(
            model_name='preseleccionados',
            old_name='nombre_plato_preseleccionado',
            new_name='nombre_plato_elegido',
        ),
        migrations.AlterField(
            model_name='plato',
            name='tipo',
            field=models.CharField(choices=[('-', '-'), ('Entrada', 'Entrada'), ('Salsa', 'Salsa'), ('Picada', 'Picada'), ('Principal', 'Plato Principal'), ('Postre', 'Postre'), ('Torta', 'Torta'), ('Dip', 'Dip'), ('Trago', 'Trago'), ('Guarnicion', 'Guarnicion')], default='-', max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='preseleccionados',
            name='usuario',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='platos_elegidos', to=settings.AUTH_USER_MODEL),
        ),
    ]