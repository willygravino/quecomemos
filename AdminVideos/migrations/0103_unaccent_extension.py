from django.contrib.postgres.operations import UnaccentExtension
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("AdminVideos", "0102_alter_nombre_plato_100"),
    ]

    operations = [
        UnaccentExtension(),
    ]
