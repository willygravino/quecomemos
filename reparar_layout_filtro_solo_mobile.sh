#!/bin/bash

set -e

echo "=============================================="
echo " REPARAR LAYOUT: SOLO MOBILE"
echo "=============================================="

TEMPLATE="AdminVideos/templates/AdminVideos/lista_filtrada.html"

if [ ! -f "$TEMPLATE" ]; then
  echo "No existe: $TEMPLATE"
  exit 1
fi

# Este script parte del bloque estructural versionado en HEAD.
# No restaura el archivo completo: solo reemplaza el bloque del
# control superior y sus reglas CSS agregadas por el intento anterior.

STAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP="${TEMPLATE}.backup_reparar_layout_mobile_$STAMP"
cp "$TEMPLATE" "$BACKUP"

echo "Backup creado:"
echo "$BACKUP"

python3 <<'PY'
from pathlib import Path
import subprocess
import re

path = Path("AdminVideos/templates/AdminVideos/lista_filtrada.html")
current = path.read_text(encoding="utf-8")

head = subprocess.check_output(
    ["git", "show", "HEAD:AdminVideos/templates/AdminVideos/lista_filtrada.html"],
    text=True
)

# Recuperar SOLO la estructura HTML del control superior tal como quedó
# en el commit estable. No se toca el resto del template.
pat = re.compile(
    r'<div id="filtroPlatosMobileControls" class="filtro-platos-mobile-shell mb-2">.*?'
    r'<div id="filtroPlatosMobileSummary" class="filtro-platos-mobile-summary mt-2 d-none"></div>\s*</div>',
    re.S
)

m_head = pat.search(head)
m_current = pat.search(current)

if not m_head:
    raise SystemExit("No se encontró el bloque estable en HEAD.")

if not m_current:
    raise SystemExit("No se encontró el bloque actual del filtro.")

current = current[:m_current.start()] + m_head.group(0) + current[m_current.end():]

# Quitar exclusivamente el bloque @media agregado por el intento anterior.
current, removed = re.subn(
    r'\n\s*@media \(max-width: 767\.98px\) \{\s*'
    r'\.filtro-mobile-main-row \{.*?'
    r'\n\s*\}\s*\n',
    '\n',
    current,
    count=1,
    flags=re.S,
)

if removed != 1:
    raise SystemExit(
        "No se encontró el bloque @media agregado por el ajuste anterior."
    )

# El bloque anterior pudo haber dejado reglas fuera del media query.
# Se eliminan únicamente las reglas que pertenecen a ese intento.
for selector in [
    "  .filtro-mobile-main-row {\n",
    "  .filtro-mobile-keyword-box {\n",
    "  .filtro-mobile-filter-button {\n",
    "  .filtro-mobile-filter-label {\n",
    "  .filtro-mobile-lo-que-tengo-row {\n",
]:
    pass

# El HTML estable no usa esas clases. Eliminamos sus reglas globales,
# sin tocar .filtro-mobile-keyword-box ya existente si está dentro del
# bloque original del CSS.
current, removed_global = re.subn(
    r'\n\s*\.filtro-mobile-main-row \{.*?\n\s*\}\s*'
    r'\n\s*\.filtro-mobile-keyword-box \{.*?\n\s*\}\s*'
    r'\n\s*\.filtro-mobile-filter-button \{.*?\n\s*\}\s*'
    r'\n\s*\.filtro-mobile-filter-label \{.*?\n\s*\}\s*'
    r'\n\s*\.filtro-mobile-lo-que-tengo-row \{.*?\n\s*\}\s*',
    '\n',
    current,
    count=1,
    flags=re.S,
)

# Agregar una única regla responsive, en un bloque claramente delimitado.
marker = "  .filtro-platos-mobile-shell {\n"
mobile_css = """  /* Layout mobile del filtro: búsqueda 95% + filtros 5%.
     En desktop se conserva íntegramente el layout existente. */
  @media (max-width: 767.98px) {
    #filtroPlatosMobileControls > .d-flex {
      display: grid !important;
      grid-template-columns: minmax(0, 19fr) minmax(0, 1fr);
      gap: .5rem;
      width: 100%;
      align-items: stretch;
    }

    #filtroPlatosMobileControls > .d-flex > .filtro-mobile-keyword-box {
      min-width: 0;
      width: 100%;
      grid-column: 1;
      grid-row: 1;
    }

    #filtroPlatosMobileControls > .d-flex > .filtro-mobile-filter-button {
      grid-column: 2;
      grid-row: 1;
      width: 100%;
      min-width: 0;
      padding-left: .25rem;
      padding-right: .25rem;
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }

    #filtroPlatosMobileControls > .d-flex > .filtro-mobile-filter-button .filtro-mobile-filter-label {
      display: none;
    }

    #filtroPlatosMobileControls > .d-flex > .lo-que-tengo-global {
      grid-column: 1 / -1;
      grid-row: 2;
      width: 100%;
    }
  }

"""
if marker not in current:
    raise SystemExit("No se encontró el punto de inserción CSS.")

current = current.replace(marker, mobile_css + marker, 1)

path.write_text(current, encoding="utf-8")
print("Reparación aplicada: desktop conserva el HTML/layout de HEAD; responsive solo en mobile.")
PY

echo ""
echo "Validar:"
echo "python manage.py check"
echo "git diff --check"
echo "git diff -- AdminVideos/templates/AdminVideos/lista_filtrada.html"
