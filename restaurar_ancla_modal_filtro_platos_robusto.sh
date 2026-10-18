#!/bin/bash

set -e

echo "=============================================="
echo " RESTAURAR ANCLA FORMULARIO FILTRO (ROBUSTO)"
echo "=============================================="

ARCHIVO="AdminVideos/templates/AdminVideos/lista_filtrada.html"

if [ ! -f "$ARCHIVO" ]; then
  echo "No existe: $ARCHIVO"
  exit 1
fi

STAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP="${ARCHIVO}.backup_ancla_filtro_robusta_$STAMP"

cp "$ARCHIVO" "$BACKUP"

echo "Backup creado:"
echo "$BACKUP"

python3 <<'PY'
from pathlib import Path
import re

path = Path("AdminVideos/templates/AdminVideos/lista_filtrada.html")
text = path.read_text(encoding="utf-8")

if 'id="filtroPlatosInlineHome"' in text:
    print("El ancla ya existe. No se modifica nada.")
    raise SystemExit(0)

patron = r'(<div\s+class="modal-body"\s+id="filtroPlatosModalBody"></div>)'

match = re.search(patron, text)

if not match:
    patron = r'(<div[^>]*id="filtroPlatosModalBody"[^>]*></div>)'
    match = re.search(patron, text)

if not match:
    raise SystemExit(
        "No se encontró filtroPlatosModalBody. Revisar estructura actual del template."
    )

ancla = '<div id="filtroPlatosInlineHome" class="d-none"></div>\n\n'

text = text[:match.start()] + ancla + match.group(1) + text[match.end():]

path.write_text(text, encoding="utf-8")

print("Ancla creada correctamente.")
PY

echo ""
echo "Validar:"
echo "python manage.py check"
echo "git diff -- AdminVideos/templates/AdminVideos/lista_filtrada.html"
