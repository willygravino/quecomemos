#!/bin/bash

set -e

echo "=============================================="
echo " RESTAURAR FORMULARIO FILTRO DESDE BACKUP"
echo "=============================================="

ACTUAL="AdminVideos/templates/AdminVideos/lista_filtrada.html"
BACKUP="AdminVideos/templates/AdminVideos/lista_filtrada.html.backup_filtro_mobile_20260906_113420"

if [ ! -f "$ACTUAL" ]; then
  echo "No existe actual: $ACTUAL"
  exit 1
fi

if [ ! -f "$BACKUP" ]; then
  echo "No existe backup: $BACKUP"
  exit 1
fi

STAMP=$(date +"%Y%m%d_%H%M%S")
cp "$ACTUAL" "${ACTUAL}.backup_antes_restaurar_form_$STAMP"

echo "Backup actual creado."

python3 <<'PY'
from pathlib import Path
import re

actual = Path("AdminVideos/templates/AdminVideos/lista_filtrada.html")
backup = Path("AdminVideos/templates/AdminVideos/lista_filtrada.html.backup_filtro_mobile_20260906_113420")

a = actual.read_text(encoding="utf-8")
b = backup.read_text(encoding="utf-8")

patron = re.compile(
    r'<form[^>]*id="form-filtros-platos"[^>]*>.*?</form>',
    re.S
)

form = patron.search(b)

if not form:
    raise SystemExit("No se encontró el formulario en el backup.")

if 'id="form-filtros-platos"' in a:
    raise SystemExit("El formulario ya existe en el actual.")

marker = '<div id="filtroPlatosModalBody"></div>'

if marker not in a:
    raise SystemExit("No se encontró el destino del modal.")

a = a.replace(marker, form.group(0) + "\n\n" + marker, 1)

actual.write_text(a, encoding="utf-8")

print("Formulario restaurado dentro del flujo modal.")
PY

echo ""
echo "Validar:"
echo "python manage.py check"
echo "git diff -- AdminVideos/templates/AdminVideos/lista_filtrada.html"
