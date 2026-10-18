#!/bin/bash

set -e

echo "=============================================="
echo " RESTAURAR FORMULARIO FILTRO - VERSION ROBUSTA"
echo "=============================================="

ACTUAL="AdminVideos/templates/AdminVideos/lista_filtrada.html"
BACKUP="AdminVideos/templates/AdminVideos/lista_filtrada.html.backup_filtro_mobile_20260906_113420"

if [ ! -f "$ACTUAL" ] || [ ! -f "$BACKUP" ]; then
  echo "Falta archivo actual o backup."
  exit 1
fi

STAMP=$(date +"%Y%m%d_%H%M%S")
cp "$ACTUAL" "${ACTUAL}.backup_antes_restaurar_form_robusto_$STAMP"

python3 <<'PY'
from pathlib import Path
import re

actual = Path("AdminVideos/templates/AdminVideos/lista_filtrada.html")
backup = Path("AdminVideos/templates/AdminVideos/lista_filtrada.html.backup_filtro_mobile_20260906_113420")

a = actual.read_text(encoding="utf-8")
b = backup.read_text(encoding="utf-8")

form = re.search(
    r'<form[^>]*id=["\']form-filtros-platos["\'][^>]*>.*?</form>',
    b,
    re.S
)

if not form:
    raise SystemExit("No se encontró form-filtros-platos en backup.")

if 'id="form-filtros-platos"' in a:
    raise SystemExit("El formulario ya existe en el archivo actual.")

# Busca cualquier modal body del filtro, aunque tenga espacios/clases distintas.
marker = re.search(
    r'(<div[^>]*id=["\']filtroPlatosModalBody["\'][^>]*>\s*</div>)',
    a
)

if not marker:
    raise SystemExit("No se encontró filtroPlatosModalBody.")

a = a[:marker.start()] + form.group(0) + "\n\n" + marker.group(1) + a[marker.end():]

actual.write_text(a, encoding="utf-8")

print("Formulario restaurado.")
PY

echo ""
echo "Validar:"
echo "python manage.py check"
echo "grep -n 'form-filtros-platos' AdminVideos/templates/AdminVideos/lista_filtrada.html"
