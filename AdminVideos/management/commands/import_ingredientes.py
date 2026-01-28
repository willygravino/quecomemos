import csv
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from AdminVideos.models import Ingrediente


class Command(BaseCommand):
    help = "Importa ingredientes desde un CSV (nombre,tipo,detalle)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            type=str,
            required=True,
            help="Ruta al archivo CSV dentro del proyecto",
        )

    def handle(self, *args, **options):
        csv_path = Path(options["path"])

        if not csv_path.exists():
            self.stderr.write(self.style.ERROR(f"No existe el archivo: {csv_path}"))
            return

        creados = 0
        existentes = 0
        skipped = 0

        def norm(s: str) -> str:
            return (s or "").strip()

        with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)

            # Validación de columnas
            expected = {"nombre", "tipo", "detalle"}
            if set(reader.fieldnames or []) != expected:
                self.stderr.write(self.style.ERROR(
                    f"Columnas inválidas. Deben ser exactamente: {expected}. "
                    f"Encontradas: {reader.fieldnames}"
                ))
                return

            with transaction.atomic():
                for i, row in enumerate(reader, start=2):
                    nombre = norm(row.get("nombre"))
                    tipo = norm(row.get("tipo"))
                    detalle = norm(row.get("detalle"))

                    if not nombre:
                        skipped += 1
                        continue

                    obj, created = Ingrediente.objects.get_or_create(
                        nombre=nombre,
                        defaults={
                            "tipo": tipo or Ingrediente.OTRO,
                            "detalle": detalle,
                        },
                    )

                    if created:
                        creados += 1
                    else:
                        existentes += 1

        self.stdout.write(self.style.SUCCESS(
            f"Importación finalizada. Creados: {creados}, Existentes: {existentes}, Omitidos: {skipped}"
        ))
