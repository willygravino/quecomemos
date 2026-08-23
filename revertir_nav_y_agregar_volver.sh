#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
cd "$ROOT"

if [ ! -f manage.py ] || [ ! -d .git ]; then
  echo "ERROR: ejecutá este script desde la raíz del repo Django."
  exit 1
fi

if [ -x ".venv/bin/python" ]; then
  PYTHON_BIN=".venv/bin/python"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
else
  echo "ERROR: no encuentro Python."
  exit 1
fi

BASE="AdminVideos/templates/AdminVideos/base.html"
LISTA="AdminVideos/templates/AdminVideos/lista_de_compras.html"
PARTIAL="AdminVideos/templates/AdminVideos/partials/_main_nav.html"
MENU_JS="AdminVideos/static/AdminVideos/js/menu_programado.js"

LATEST_BACKUP="$(ls -dt .backup_nav_principal_* 2>/dev/null | head -1 || true)"

if [ -z "$LATEST_BACKUP" ]; then
  echo "ERROR: no encuentro el backup creado por agregar_nav_inicio_compras.sh."
  echo "No voy a intentar una reversión parcial a ciegas."
  exit 1
fi

for f in "$BASE" "$MENU_JS"; do
  if [ ! -f "$LATEST_BACKUP/$f" ]; then
    echo "ERROR: el backup no contiene $f"
    exit 1
  fi
done

STAMP="$(date +"%Y%m%d_%H%M%S")"
SAFETY_BACKUP=".backup_volver_compras_${STAMP}"
mkdir -p "$SAFETY_BACKUP/$(dirname "$BASE")"
mkdir -p "$SAFETY_BACKUP/$(dirname "$LISTA")"
mkdir -p "$SAFETY_BACKUP/$(dirname "$MENU_JS")"
cp "$BASE" "$SAFETY_BACKUP/$BASE"
cp "$LISTA" "$SAFETY_BACKUP/$LISTA"
cp "$MENU_JS" "$SAFETY_BACKUP/$MENU_JS"
if [ -f "$PARTIAL" ]; then
  mkdir -p "$SAFETY_BACKUP/$(dirname "$PARTIAL")"
  cp "$PARTIAL" "$SAFETY_BACKUP/$PARTIAL"
fi
git diff > "$SAFETY_BACKUP/pre_patch.diff" || true

echo "============================================================"
echo "RESTAURANDO NAVEGACIÓN ANTERIOR"
echo "============================================================"

cp "$LATEST_BACKUP/$BASE" "$BASE"
cp "$LATEST_BACKUP/$MENU_JS" "$MENU_JS"

if [ -f "$LATEST_BACKUP/$PARTIAL" ]; then
  cp "$LATEST_BACKUP/$PARTIAL" "$PARTIAL"
else
  rm -f "$PARTIAL"
fi

echo "OK: barra Inicio / Lista de compras revertida."
echo "OK: carrito flotante anterior restaurado."

echo
echo "============================================================"
echo "AGREGANDO BOTÓN VOLVER"
echo "============================================================"

"$PYTHON_BIN" - <<'PY'
from pathlib import Path

path = Path("AdminVideos/templates/AdminVideos/lista_de_compras.html")
text = path.read_text(encoding="utf-8")

marker = "{% block pestanias-menues-platos %}\n"

if marker not in text:
    raise RuntimeError("No encuentro el inicio del bloque principal de lista_de_compras.html.")

button_id = 'id="btn-volver-lista-compras"'

if button_id not in text:
    button = (
        "\n"
        '  <div class="px-2 pt-1 mb-2">\n'
        '    <a id="btn-volver-lista-compras"\n'
        '       href="{% url \'filtro-de-platos\' %}"\n'
        '       class="btn btn-sm btn-outline-secondary d-inline-flex align-items-center gap-1">\n'
        '      <i class="fa-solid fa-arrow-left" aria-hidden="true"></i>\n'
        '      <span>Volver</span>\n'
        "    </a>\n"
        "  </div>\n"
    )
    text = text.replace(marker, marker + button, 1)

if text.count(button_id) != 1:
    raise RuntimeError("El botón Volver no quedó exactamente una vez.")

if "{% url \'filtro-de-platos\' %}" not in text:
    raise RuntimeError("El botón Volver no apunta a la pantalla principal.")

path.write_text(text, encoding="utf-8")
print("OK: botón Volver agregado sólo a Lista de compras.")
PY

echo
echo "============================================================"
echo "CHECKS"
echo "============================================================"

git diff --check
"$PYTHON_BIN" manage.py check
"$PYTHON_BIN" manage.py makemigrations --check --dry-run

if command -v node >/dev/null 2>&1; then
  node --check "$MENU_JS"
  echo "JavaScript: OK"
else
  echo "Node no instalado; se omite node --check."
fi

echo
echo "Verificando navegación:"

if grep -q 'AdminVideos/partials/_main_nav.html' "$BASE"; then
  echo "ERROR: todavía quedó incluida la barra de navegación nueva."
  exit 1
fi

if ! grep -q 'botonListaComprasFlotanteWrap' "$BASE"; then
  echo "ERROR: no se restauró el carrito flotante."
  exit 1
fi

if ! grep -q 'id="btn-volver-lista-compras"' "$LISTA"; then
  echo "ERROR: falta el botón Volver."
  exit 1
fi

echo "OK: sin barra global nueva."
echo "OK: carrito flotante restaurado."
echo "OK: botón Volver presente en Lista de compras."

echo
echo "============================================================"
echo "CAMBIOS"
echo "============================================================"
git diff --stat
echo
git status --short

echo
echo "============================================================"
echo "LISTO PARA PROBAR"
echo "============================================================"
echo "1. Pantalla principal: debe volver a verse como antes, con carrito flotante."
echo "2. Entrá a Lista de compras."
echo "3. Arriba debe aparecer un botón compacto: ← Volver."
echo "4. Volver debe llevar a menú programado + sugerencias."
echo "5. Revisá especialmente en celular que no robe altura innecesaria."
echo
echo "Todavía NO hace commit."
echo "Backup de seguridad: $SAFETY_BACKUP"
