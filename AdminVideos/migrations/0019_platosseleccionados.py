# Generated by Django 4.1.7 on 2024-03-19 19:03

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('AdminVideos', '0018_alter_plato_calorias_alter_plato_categoria_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlatosSeleccionados',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre_plato_seleccionado', models.CharField(max_length=30)),
                ('fecha_seleccion_del_plato', models.DateTimeField()),
                ('usuario_seleccionados', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='platos_seleccionados', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]