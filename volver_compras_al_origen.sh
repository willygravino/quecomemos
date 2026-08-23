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
VIEWS="AdminVideos/views.py"

for f in "$BASE" "$LISTA" "$VIEWS"; do
  if [ ! -f "$f" ]; then
    echo "ERROR: falta $f"
    exit 1
  fi
done

STAMP="$(date +"%Y%m%d_%H%M%S")"
BACKUP_DIR=".backup_return_to_compras_${STAMP}"
for f in "$BASE" "$LISTA" "$VIEWS"; do
  mkdir -p "$BACKUP_DIR/$(dirname "$f")"
  cp "$f" "$BACKUP_DIR/$f"
done
git diff > "$BACKUP_DIR/pre_patch.diff" || true

"$PYTHON_BIN" - <<'PY'
from pathlib import Path
import re

base_path = Path("AdminVideos/templates/AdminVideos/base.html")
lista_path = Path("AdminVideos/templates/AdminVideos/lista_de_compras.html")
views_path = Path("AdminVideos/views.py")

base = base_path.read_text(encoding="utf-8")
lista = lista_path.read_text(encoding="utf-8")
views = views_path.read_text(encoding="utf-8")

# ------------------------------------------------------------
# 1) El carrito lleva la URL exacta de origen.
# ------------------------------------------------------------
old_cart = 'href="{% url \'menu-elegido\' %}"'
new_cart = (
    'href="{% url \'menu-elegido\' %}?return_to='
    '{{ request.get_full_path|urlencode }}"'
)

if new_cart not in base:
    if old_cart not in base:
        raise RuntimeError("No encuentro el href del carrito flotante.")
    base = base.replace(old_cart, new_cart, 1)

# ------------------------------------------------------------
# 2) Resolver return_to una sola vez y validarlo en la vista.
#    El import de url_has_allowed_host_and_scheme ya existe.
# ------------------------------------------------------------
def_start = re.search(r"(?m)^def lista_de_compras\(request\):\n", views)
if not def_start:
    raise RuntimeError("No encuentro lista_de_compras().")

next_def = re.search(
    r"(?m)^(?:def |class |@[A-Za-z_])",
    views[def_start.end():],
)
def_end = (
    def_start.end() + next_def.start()
    if next_def
    else len(views)
)
block = views[def_start.start():def_end]

return_block = (
    '    return_to = (request.GET.get("return_to") or request.POST.get("return_to") or "").strip()\n'
    '    if not return_to or not url_has_allowed_host_and_scheme(\n'
    '        return_to,\n'
    '        allowed_hosts={request.get_host()},\n'
    '        require_https=request.is_secure(),\n'
    '    ):\n'
    '        return_to = reverse("filtro-de-platos")\n\n'
)

if "allowed_hosts={request.get_host()}" not in block:
    anchor = "def lista_de_compras(request):\n"
    block = block.replace(anchor, anchor + return_block, 1)

# Agregar return_to a todos los contextos explícitos de esta vista.
# Caso temprano: no hay platos elegidos.
early_anchor = '                "share_url": share_url,\n'
early_with_return = early_anchor + '                "return_to": return_to,\n'
if early_with_return not in block:
    if early_anchor not in block:
        raise RuntimeError("No encuentro contexto temprano de lista_de_compras.")
    block = block.replace(early_anchor, early_with_return, 1)

# Contexto final.
final_anchor = '        "share_url": share_url,\n'
final_with_return = final_anchor + '        "return_to": return_to,\n'
if final_with_return not in block:
    # Evitar volver a tocar el contexto temprano (indentación diferente).
    if final_anchor not in block:
        raise RuntimeError("No encuentro contexto final de lista_de_compras.")
    block = block.replace(final_anchor, final_with_return, 1)

views = views[:def_start.start()] + block + views[def_end:]

# ------------------------------------------------------------
# 3) El botón Volver usa el destino validado.
# ------------------------------------------------------------
button_pattern = re.compile(
    r'(id="btn-volver-lista-compras"\s*\n\s*href=")[^"]+(")',
    flags=re.M,
)
lista, count = button_pattern.subn(
    r'\1{{ return_to }}\2',
    lista,
    count=1,
)
if count != 1 and 'id="btn-volver-lista-compras"' in lista:
    # Variante donde id/href pueden estar en la misma línea.
    lista, count = re.subn(
        r'(id="btn-volver-lista-compras"[^>]*?href=")[^"]+(")',
        r'\1{{ return_to }}\2',
        lista,
        count=1,
        flags=re.S,
    )

if count != 1:
    raise RuntimeError("No pude actualizar el href del botón Volver.")

# ------------------------------------------------------------
# 4) Preservarlo también si el form hace POST no-AJAX.
# ------------------------------------------------------------
old_action = '<form id="frm-menu" action="{% url \'menu-elegido\' %}" method="post">'
new_action = (
    '<form id="frm-menu" action="{% url \'menu-elegido\' %}?return_to={{ return_to|urlencode }}" method="post">'
)
if new_action not in lista:
    if old_action not in lista:
        raise RuntimeError("No encuentro el form principal de Lista de compras.")
    lista = lista.replace(old_action, new_action, 1)

# ------------------------------------------------------------
# Validaciones.
# ------------------------------------------------------------
if base.count("request.get_full_path|urlencode") < 2:
    # Ya existía en Agregar; ahora debe existir también en carrito.
    raise RuntimeError("El carrito no está preservando la URL de origen.")

if 'href="{{ return_to }}"' not in lista:
    raise RuntimeError("Volver no usa return_to.")

if "return_to={{ return_to|urlencode }}" not in lista:
    raise RuntimeError("El form no preserva return_to.")

if block.count('"return_to": return_to') < 2:
    raise RuntimeError("No todos los renders de Lista reciben return_to.")

base_path.write_text(base, encoding="utf-8")
lista_path.write_text(lista, encoding="utf-8")
views_path.write_text(views, encoding="utf-8")

print("OK: el carrito conserva la URL exacta de origen.")
print("OK: return_to se valida antes de usarlo.")
print("OK: Volver regresa al contexto anterior.")
print("OK: POSTs de Lista conservan return_to.")
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
from urllib.parse import quote

origen = reverse("filtro-de-platos") + "?tipopag=Guarnicion"
compras = reverse("menu-elegido") + "?return_to=" + quote(origen, safe="")

print("Ejemplo esperado:")
print("  origen :", origen)
print("  compras:", compras)
print("  volver :", origen)
PY

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
echo "1. Entrá a Guarniciones (o cualquier categoría/filtro)."
echo "2. Abrí Lista de compras desde el carrito."
echo "3. Tocá Volver."
echo "4. Debe regresar exactamente a la URL anterior, no sólo a Inicio."
echo "5. Repetí desde otra categoría para confirmar."
echo
echo "Si abrís Lista de compras directamente, Volver cae en la pantalla principal."
echo "No hace commit."
echo "Backup: $BACKUP_DIR"
