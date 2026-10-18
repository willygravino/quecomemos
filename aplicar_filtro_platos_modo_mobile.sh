#!/bin/bash

set -e

echo "=============================================="
echo " UNIFICAR FILTRO PLATOS -> MODO MOBILE"
echo "=============================================="

ARCHIVO="AdminVideos/templates/AdminVideos/lista_filtrada.html"

if [ ! -f "$ARCHIVO" ]; then
  echo "No existe: $ARCHIVO"
  exit 1
fi

BACKUP="${ARCHIVO}.backup_filtro_mobile_$(date +"%Y%m%d_%H%M%S")"

cp "$ARCHIVO" "$BACKUP"

echo "Backup creado:"
echo "$BACKUP"

python3 <<'PY'
from pathlib import Path
import re

path = Path("AdminVideos/templates/AdminVideos/lista_filtrada.html")
text = path.read_text(encoding="utf-8")

# 1) El control superior mobile pasa a ser el control único.
text = text.replace(
    'class="filtro-platos-mobile-shell d-md-none mb-2"',
    'class="filtro-platos-mobile-shell mb-2"',
    1
)

# 2) El bloque inline desktop deja de renderizarse.
# Se elimina solo el contenedor visual exterior y el include desktop,
# manteniendo el formulario porque la lógica JS actual lo utiliza.
patron = re.compile(
    r'<div class="filtro-platos-y-lo-que-tengo d-none d-md-flex align-items-stretch gap-2 mb-2">\s*'
    r'<div id="filtroPlatosInlineHome" class="flex-grow-1 min-w-0">.*?'
    r'\{% include "AdminVideos/partials/_control_lo_que_tengo_global\.html" with modo="desktop" %\}\s*'
    r'</div>',
    re.S
)

match = patron.search(text)

if not match:
    raise SystemExit(
        "No se encontró el bloque desktop esperado. No se realizó ningún cambio."
    )

bloque = match.group(0)

# Conservamos el formulario dentro del modal mediante JS, pero retiramos
# la presentación inline desktop.
text = text.replace(bloque, "", 1)

path.write_text(text, encoding="utf-8")
PY

echo ""
echo "Cambio aplicado."
echo "Verificar:"
echo "python manage.py check"
echo "git diff -- AdminVideos/templates/AdminVideos/lista_filtrada.html"
