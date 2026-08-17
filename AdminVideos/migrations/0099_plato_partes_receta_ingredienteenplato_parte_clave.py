from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("AdminVideos", "0098_alter_plato_receta"),
    ]

    operations = [
        migrations.AddField(
            model_name="plato",
            name="partes_receta",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="Partes ordenadas de la receta: nombre, instrucciones y clave estable.",
            ),
        ),
        migrations.AddField(
            model_name="ingredienteenplato",
            name="parte_clave",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Clave de la parte de receta a la que pertenece este ingrediente.",
                max_length=64,
            ),
        ),
    ]
