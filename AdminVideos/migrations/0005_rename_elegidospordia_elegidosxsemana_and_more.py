# Generated by Django 4.1.7 on 2024-03-08 20:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('AdminVideos', '0004_remove_elegidospordia_fecha_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ElegidosPorDia',
            new_name='ElegidosXSemana',
        ),
        migrations.RenameField(
            model_name='elegidosxsemana',
            old_name='elegidos_por_dia',
            new_name='elegidos_por_semana',
        ),
    ]