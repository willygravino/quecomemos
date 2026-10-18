#!/bin/bash

set -e

echo "=============================================="
echo " CORREGIR LAYOUT MOBILE SIN AFECTAR DESKTOP"
echo "=============================================="

TEMPLATE="AdminVideos/templates/AdminVideos/lista_filtrada.html"

if [ ! -f "$TEMPLATE" ]; then
  echo "No existe: $TEMPLATE"
  exit 1
fi

STAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP="${TEMPLATE}.backup_layout_mobile_sin_desktop_$STAMP"
cp "$TEMPLATE" "$BACKUP"

echo "Backup creado:"
echo "$BACKUP"

python3 <<'PY'
from pathlib import Path
import re

path = Path("AdminVideos/templates/AdminVideos/lista_filtrada.html")
text = path.read_text(encoding="utf-8")

# Normaliza únicamente las estructuras introducidas por el ajuste 95/5 anterior.
text = re.sub(
    r'\n  \.filtro-mobile-main-row \{.*?\n  \.filtro-mobile-lo-que-tengo-row \{.*?\n  \}\n\n',
    '\n',
    text,
    flags=re.S,
)

text = text.replace(
    'class="d-flex align-items-stretch gap-2 filtro-mobile-main-row"',
    'class="d-flex align-items-stretch gap-2"',
)

old_html = """  <div class="d-flex align-items-stretch gap-2">

    <div class="input-group input-group-sm filtro-mobile-keyword-box {% if formulario.palabra_clave.value %}filtro-keyword-activo{% endif %}">
      <span class="input-group-text">
        <i class="fa-solid fa-magnifying-glass"></i>
      </span>

      <input
        type="text"
        class="form-control {% if formulario.palabra_clave.value %}text-danger fw-semibold{% endif %}"
        id="palabraClaveMobile"
        value="{{ formulario.palabra_clave.value|default:'' }}"
        placeholder="Buscar">

      <button
        type="button"
        class="filtro-mobile-keyword-clear {% if not formulario.palabra_clave.value %}d-none{% endif %}"
        id="limpiarPalabraClaveMobile"
        aria-label="Borrar palabra clave">
        <i class="fa-solid fa-xmark"></i>
      </button>
    </div>

    <button
      type="button"
      class="btn btn-primary btn-sm fw-semibold filtro-mobile-filter-button"
      data-bs-toggle="modal"
      data-bs-target="#filtroPlatosModal"
      aria-label="Abrir filtros"
      title="Filtros">
      <i class="fa-solid fa-sliders"></i>
      <span class="filtro-mobile-filter-label">Filtros</span>
    </button>

  </div>

  <div class="filtro-mobile-lo-que-tengo-row">
    {% include "AdminVideos/partials/_control_lo_que_tengo_global.html" with modo="mobile" %}
  </div>"""

new_html = """  <div class="d-flex align-items-stretch gap-2 filtro-mobile-main-row">

    <div class="input-group input-group-sm flex-grow-1 filtro-mobile-keyword-box {% if formulario.palabra_clave.value %}filtro-keyword-activo{% endif %}">
      <span class="input-group-text">
        <i class="fa-solid fa-magnifying-glass"></i>
      </span>

      <input
        type="text"
        class="form-control {% if formulario.palabra_clave.value %}text-danger fw-semibold{% endif %}"
        id="palabraClaveMobile"
        value="{{ formulario.palabra_clave.value|default:'' }}"
        placeholder="Buscar">

      <button
        type="button"
        class="filtro-mobile-keyword-clear {% if not formulario.palabra_clave.value %}d-none{% endif %}"
        id="limpiarPalabraClaveMobile"
        aria-label="Borrar palabra clave">
        <i class="fa-solid fa-xmark"></i>
      </button>
    </div>

    <button
      type="button"
      class="btn btn-primary btn-sm fw-semibold flex-shrink-0 filtro-mobile-filter-button"
      data-bs-toggle="modal"
      data-bs-target="#filtroPlatosModal"
      aria-label="Abrir filtros"
      title="Filtros">
      <i class="fa-solid fa-sliders"></i>
      <span class="filtro-mobile-filter-label">Filtros</span>
    </button>

    {% include "AdminVideos/partials/_control_lo_que_tengo_global.html" with modo="mobile" %}

  </div>"""

if old_html in text:
    text = text.replace(old_html, new_html, 1)
elif 'filtro-mobile-main-row' not in text:
    raise SystemExit("No se encontró la estructura esperada del filtro mobile.")

marker = "  .filtro-platos-mobile-shell {\n"
css = """  @media (max-width: 767.98px) {
    .filtro-mobile-main-row {
      display: grid !important;
      grid-template-columns: minmax(0, 19fr) minmax(0, 1fr);
      gap: .5rem;
      width: 100%;
      align-items: stretch;
    }

    .filtro-mobile-main-row .filtro-mobile-keyword-box {
      min-width: 0;
      width: 100%;
    }

    .filtro-mobile-main-row .filtro-mobile-filter-button {
      width: 100%;
      min-width: 0;
      padding-left: .25rem;
      padding-right: .25rem;
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }

    .filtro-mobile-main-row .filtro-mobile-filter-label {
      display: none;
    }

    .filtro-mobile-main-row > .lo-que-tengo-global {
      grid-column: 1 / -1;
      width: 100%;
    }
  }

"""
if marker not in text:
    raise SystemExit("No se encontró el punto de inserción CSS.")

if '@media (max-width: 767.98px)' not in text:
    text = text.replace(marker, css + marker, 1)

path.write_text(text, encoding="utf-8")
print("Layout corregido: desktop intacto; cambio aplicado solo en mobile.")
PY

echo ""
echo "Validar:"
echo "python manage.py check"
echo "git diff -- AdminVideos/templates/AdminVideos/lista_filtrada.html"
