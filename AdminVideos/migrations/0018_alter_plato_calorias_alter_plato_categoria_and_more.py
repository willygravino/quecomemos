# Generated by Django 4.1.7 on 2024-03-14 14:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('AdminVideos', '0017_alter_elegidos_nombre_plato_elegido_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='plato',
            name='calorias',
            field=models.CharField(blank=True, choices=[('-', '-'), ('Calórico', 'Calórico'), ('Liviano', 'Liviano'), ('Normal', 'Normal'), ('Plato de invierno', 'Plato de invierno')], default='-', max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='plato',
            name='categoria',
            field=models.CharField(blank=True, choices=[('-', '-'), ('Común', 'Común'), ('Especial', 'Especial')], default='-', max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='plato',
            name='medios',
            field=models.CharField(blank=True, choices=[('-', '-'), ('horno', 'horno'), ('cocina', 'cocina'), ('parrilla', 'parrilla'), ('wok', 'wok'), ('sin coccion', 'sin cocción')], default='-', max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='plato',
            name='preparacion',
            field=models.CharField(blank=True, choices=[('-', '-'), ('Mucho', 'Mucho'), ('Poco', 'Poco'), ('Nada', 'Nada')], default='-', max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='plato',
            name='tipo',
            field=models.CharField(blank=True, choices=[('-', '-'), ('entrada', 'Entrada'), ('salsa', 'Salsa'), ('picada', 'Picada'), ('Plato principal', 'Plato principal'), ('postre', 'postre'), ('torta', 'torta'), ('untable', 'untable'), ('trago', 'trago'), ('guarnicion', 'guarnicion')], default='-', max_length=20, null=True),
        ),
    ]