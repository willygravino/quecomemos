# Generated by Django 4.1.7 on 2024-03-10 12:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('AdminVideos', '0005_rename_elegidospordia_elegidosxsemana_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='elegidos',
            name='nombre_plato',
            field=models.CharField(max_length=30, unique=True),
        ),
    ]