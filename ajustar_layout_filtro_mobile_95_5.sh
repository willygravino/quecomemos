#!/bin/bash

set -e

echo "=============================================="
echo " AJUSTAR LAYOUT FILTRO MOBILE 95/5"
echo "=============================================="

TEMPLATE="AdminVideos/templates/AdminVideos/lista_filtrada.html"

if [ ! -f "$TEMPLATE" ]; then
  echo "No existe: $TEMPLATE"
  exit 1
fi

STAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP="${TEMPLATE}.backup_layout_95_5_$STAMP"
cp "$TEMPLATE" "$BACKUP"

echo "Backup creado:"
echo "$BACKUP"

python3 <<'PY'
from pathlib import Path

path = Path("AdminVideos/templates/AdminVideos/lista_filtrada.html")
text = path.read_text(encoding="utf-8")
original = text

old = """  <div class="d-flex align-items-stretch gap-2">

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
      class="btn btn-primary btn-sm fw-semibold flex-shrink-0"
      data-bs-toggle="modal"
      data-bs-target="#filtroPlatosModal">
      <i class="fa-solid fa-sliders me-1"></i>
      Filtros
    </button>

    {% include "AdminVideos/partials/_control_lo_que_tengo_global.html" with modo="mobile" %}

  </div>"""

new = """  <div class="filtro-mobile-main-row">

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

if old not in text:
    raise SystemExit("No se encontró el bloque HTML esperado. No se realizó ningún cambio.")

text = text.replace(old, new, 1)

marker = "  .filtro-platos-mobile-shell {\n"
css = """  .filtro-mobile-main-row {
    display: grid;
    grid-template-columns: minmax(0, 19fr) minmax(0, 1fr);
    gap: .5rem;
    width: 100%;
    align-items: stretch;
  }

  .filtro-mobile-keyword-box {
    min-width: 0;
    width: 100%;
  }

  .filtro-mobile-filter-button {
    width: 100%;
    min-width: 0;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding-left: .25rem;
    padding-right: .25rem;
  }

  .filtro-mobile-filter-label {
    display: none;
  }

  .filtro-mobile-lo-que-tengo-row {
    width: 100%;
    margin-top: .5rem;
  }

"""
if marker not in text:
    raise SystemExit("No se encontró el bloque CSS esperado. No se realizó ningún cambio.")

text = text.replace(marker, css + marker, 1)

path.write_text(text, encoding="utf-8")
print("Layout 95/5 aplicado.")
PY

echo ""
echo "Validar:"
echo "python manage.py check"
echo "git diff -- AdminVideos/templates/AdminVideos/lista_filtrada.html"
