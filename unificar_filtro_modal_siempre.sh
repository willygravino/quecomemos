#!/bin/bash

set -e

echo "=============================================="
echo " UNIFICAR MOVIMIENTO FILTRO AL MODAL SIEMPRE"
echo "=============================================="

ARCHIVO="AdminVideos/templates/AdminVideos/lista_filtrada.html"

if [ ! -f "$ARCHIVO" ]; then
  echo "No existe: $ARCHIVO"
  exit 1
fi

STAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP="${ARCHIVO}.backup_filtro_modal_unico_$STAMP"

cp "$ARCHIVO" "$BACKUP"

echo "Backup creado:"
echo "$BACKUP"

python3 <<'PY'
from pathlib import Path
import re

path = Path("AdminVideos/templates/AdminVideos/lista_filtrada.html")
text = path.read_text(encoding="utf-8")

original = text

text = re.sub(
    r'\s*const media = window\.matchMedia\("\(max-width: 767\.98px\)"\);\s*',
    '\n',
    text
)

patron = re.compile(
    r'  function moverFormSegunPantalla\(\) \{.*?\n  \}\n',
    re.S
)

nuevo = """  function moverFormSegunPantalla() {
    const form = getForm();
    const modalBody = getModalBody();

    if (!form || !modalBody) return;

    if (form.parentElement !== modalBody) {
      modalBody.appendChild(form);
    }

    form.classList.remove("mb-3");
    form.classList.add("mb-0");

    actualizarResumenMobile();
  }
"""

if not patron.search(text):
    raise SystemExit("No se encontró moverFormSegunPantalla. No se realizaron cambios.")

text = patron.sub(nuevo, text, count=1)

text = re.sub(
    r'\n\s*if \(media\.addEventListener\).*?\n\s*\}\s*else if \(media\.addListener\).*?\n\s*\}\s*',
    '\n',
    text,
    flags=re.S
)

if text == original:
    raise SystemExit("No hubo cambios.")

path.write_text(text, encoding="utf-8")

print("Cambio aplicado.")
PY

echo ""
echo "Validar:"
echo "python manage.py check"
echo "git diff -- AdminVideos/templates/AdminVideos/lista_filtrada.html"
