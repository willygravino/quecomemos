# Generated by Django 5.0.3 on 2024-08-14 12:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('AdminVideos', '0007_alter_plato_descripcion_plato_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='ingredientes_que_tengo',
            field=models.JSONField(blank=True, default=list),
        ),
    ]