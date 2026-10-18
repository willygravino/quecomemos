#!/bin/bash

set -e

echo "=============================================="
echo " RESTAURAR FLUJO MODAL FILTRO UNIFICADO"
echo "=============================================="

ARCHIVO="AdminVideos/templates/AdminVideos/lista_filtrada.html"

if [ ! -f "$ARCHIVO" ]; then
  echo "No existe: $ARCHIVO"
  exit 1
fi

STAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP="${ARCHIVO}.backup_modal_filtro_$STAMP"

cp "$ARCHIVO" "$BACKUP"

echo "Backup creado:"
echo "$BACKUP"

python3 <<'PY'
from pathlib import Path
import re

path = Path("AdminVideos/templates/AdminVideos/lista_filtrada.html")
text = path.read_text(encoding="utf-8")

# Recuperar un punto estable para que el JS pueda mover el formulario.
# No restaura el bloque desktop: solo crea el ancla lógica necesaria.

if 'id="filtroPlatosInlineHome"' not in text:
    marker = '<div id="filtroPlatosModalBody"></div>'

    if marker not in text:
        raise SystemExit(
            "No se encontró el modal body esperado. No se realizó ningún cambio."
        )

    # Insertamos un contenedor oculto de alojamiento fuera de la presentación.
    # El formulario seguirá siendo único.
    replacement = (
        '<div id="filtroPlatosInlineHome" class="d-none"></div>\n\n'
        + marker
    )

    text = text.replace(marker, replacement, 1)

path.write_text(text, encoding="utf-8")
PY

echo ""
echo "Ancla del formulario restaurada."
echo "Ahora validar:"
echo "python manage.py check"
echo "git diff -- AdminVideos/templates/AdminVideos/lista_filtrada.html"
