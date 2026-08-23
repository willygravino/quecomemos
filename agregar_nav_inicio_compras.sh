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
PARTIAL="AdminVideos/templates/AdminVideos/partials/_main_nav.html"
MENU_JS="AdminVideos/static/AdminVideos/js/menu_programado.js"

for f in "$BASE" "$MENU_JS"; do
  if [ ! -f "$f" ]; then
    echo "ERROR: falta $f"
    exit 1
  fi
done

STAMP="$(date +"%Y%m%d_%H%M%S")"
BACKUP_DIR=".backup_nav_principal_${STAMP}"

mkdir -p "$BACKUP_DIR/$(dirname "$BASE")"
mkdir -p "$BACKUP_DIR/$(dirname "$MENU_JS")"
cp "$BASE" "$BACKUP_DIR/$BASE"
cp "$MENU_JS" "$BACKUP_DIR/$MENU_JS"

if [ -f "$PARTIAL" ]; then
  mkdir -p "$BACKUP_DIR/$(dirname "$PARTIAL")"
  cp "$PARTIAL" "$BACKUP_DIR/$PARTIAL"
fi

git diff > "$BACKUP_DIR/pre_patch.diff" || true
git status --short > "$BACKUP_DIR/pre_patch_status.txt" || true

"$PYTHON_BIN" - <<'PY'
from pathlib import Path
import re

base_path = Path("AdminVideos/templates/AdminVideos/base.html")
partial_path = Path("AdminVideos/templates/AdminVideos/partials/_main_nav.html")
menu_js_path = Path("AdminVideos/static/AdminVideos/js/menu_programado.js")

base = base_path.read_text(encoding="utf-8")
menu_js = menu_js_path.read_text(encoding="utf-8")

partial_lines = [
    "{% if user.is_authenticated %}",
    "  {% with current_url=request.resolver_match.url_name %}",
    '    <nav class="px-2 px-md-3 mb-2" aria-label="Navegación principal">',
    '      <div class="nav nav-pills nav-fill gap-1 p-1 bg-body-tertiary border rounded">',
    '        <a href="{% url \'filtro-de-platos\' %}"',
    '           class="nav-link py-2 d-flex align-items-center justify-content-center gap-2 {% if current_url == \'filtro-de-platos\' or current_url == \'index\' %}active{% endif %}"',
    '           {% if current_url == \'filtro-de-platos\' or current_url == \'index\' %}aria-current="page"{% endif %}>',
    '          <i class="fa-solid fa-house" aria-hidden="true"></i>',
    "          <span>Inicio</span>",
    "        </a>",
    "",
    '        <a href="{% url \'menu-elegido\' %}"',
    '           class="nav-link py-2 d-flex align-items-center justify-content-center gap-2 {% if current_url == \'menu-elegido\' %}active{% endif %}"',
    '           {% if current_url == \'menu-elegido\' %}aria-current="page"{% endif %}>',
    '          <i class="fa-solid fa-cart-shopping" aria-hidden="true"></i>',
    "          <span>Lista de compras</span>",
    "        </a>",
    "      </div>",
    "    </nav>",
    "  {% endwith %}",
    "{% endif %}",
]
partial = "\n".join(partial_lines) + "\n"

partial_path.parent.mkdir(parents=True, exist_ok=True)
partial_path.write_text(partial, encoding="utf-8")

include_line = '            {% include "AdminVideos/partials/_main_nav.html" %}'

if include_line not in base:
    anchor = "            <!-- End of Topbar -->"
    if anchor not in base:
        raise RuntimeError("No encuentro el final del topbar en base.html.")
    base = base.replace(anchor, anchor + "\n\n" + include_line, 1)

floating_start = '<div id="botonListaComprasFlotanteWrap">'
if floating_start in base:
    start = base.index(floating_start)
    finish = None
    for marker in ("\n\n\n<script>", "\n\n<script>"):
        pos = base.find(marker, start)
        if pos != -1:
            finish = pos
            break
    if finish is None:
        raise RuntimeError("No pude delimitar el carrito flotante.")
    base = base[:start] + base[finish:]
else:
    print("AVISO: el carrito flotante ya no estaba presente.")

old_consts = (
    '      const carritoListaCompras = document.getElementById("botonListaComprasFlotanteWrap");\n'
    '      const nuevoCarritoListaCompras = doc.getElementById("botonListaComprasFlotanteWrap");\n'
)
menu_js = menu_js.replace(old_consts, "")

menu_js = re.sub(
    r'\n      if \(carritoListaCompras && nuevoCarritoListaCompras\) \{\n'
    r'        carritoListaCompras\.innerHTML = nuevoCarritoListaCompras\.innerHTML;\n'
    r'      \}\n',
    "\n",
    menu_js,
    count=1,
)

if base.count(include_line) != 1:
    raise RuntimeError("La navegación no quedó incluida exactamente una vez.")

if "botonListaComprasFlotanteWrap" in base:
    raise RuntimeError("Quedó el carrito flotante viejo en base.html.")

if "carritoListaCompras" in menu_js:
    raise RuntimeError("Quedó JS dedicado al carrito flotante.")

if partial.count("{% url \'filtro-de-platos\' %}") != 1:
    raise RuntimeError("Falta la URL de Inicio.")

if partial.count("{% url \'menu-elegido\' %}") != 1:
    raise RuntimeError("Falta la URL de Lista de compras.")

base_path.write_text(base, encoding="utf-8")
menu_js_path.write_text(menu_js, encoding="utf-8")

print("OK: navegación Inicio / Lista de compras agregada.")
print("OK: carrito flotante redundante eliminado.")
print("OK: JS exclusivo del carrito eliminado.")
PY

echo
echo "============================================================"
echo "CHECKS"
echo "============================================================"

git diff --check
"$PYTHON_BIN" manage.py check
"$PYTHON_BIN" manage.py makemigrations --check --dry-run

"$PYTHON_BIN" manage.py shell <<'PY'
from django.urls import reverse

inicio = reverse("filtro-de-platos")
compras = reverse("menu-elegido")
assert inicio
assert compras
assert inicio != compras
print("URLs OK:")
print("  Inicio:", inicio)
print("  Lista de compras:", compras)
PY

if command -v node >/dev/null 2>&1; then
  node --check AdminVideos/static/AdminVideos/js/menu_programado.js
  echo "JavaScript: OK"
else
  echo "Node no instalado; se omite node --check."
fi

echo
echo "============================================================"
echo "AUDITORÍA DE DUPLICACIÓN"
echo "============================================================"

if grep -RIn \
  --exclude-dir=.git \
  --exclude-dir=.venv \
  --exclude-dir=venv \
  "botonListaComprasFlotanteWrap" \
  AdminVideos
then
  echo "ERROR: todavía hay referencias al carrito flotante."
  exit 1
else
  echo "OK: no quedan referencias al carrito flotante."
fi

COUNT_MAIN_NAV="$(
  grep -RIl \
    --exclude-dir=.git \
    --exclude-dir=.venv \
    --exclude-dir=venv \
    'aria-label="Navegación principal"' \
    AdminVideos/templates \
  | wc -l \
  | tr -d " "
)"

if [ "$COUNT_MAIN_NAV" != "1" ]; then
  echo "ERROR: esperaba una única definición de navegación principal; encontré $COUNT_MAIN_NAV."
  exit 1
fi

echo "OK: navegación definida una sola vez en un partial."

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
echo "1. Abrí la pantalla principal: Inicio debe estar activo."
echo "2. Entrá a Lista de compras: esa pestaña debe quedar activa."
echo "3. Tocá Inicio: vuelve a menú programado + sugerencias."
echo "4. Revisá desktop y celular."
echo
echo "No cambia vistas, URLs, modelos ni migraciones."
echo "Todavía NO hace commit."
echo "Backup: $BACKUP_DIR"
