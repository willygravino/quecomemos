# Generated by Django 4.1.7 on 2024-03-07 12:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('AdminVideos', '0002_elegidos_alter_plato_image'),
    ]

    operations = [
        migrations.CreateModel(
            name='ElegidosPorDia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre_plato', models.CharField(max_length=30)),
                ('fecha', models.DateTimeField(verbose_name='Fecha de captura del video:')),
            ],
        ),
    ]