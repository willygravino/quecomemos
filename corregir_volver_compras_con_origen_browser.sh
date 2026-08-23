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
  [ -f "$f" ] || { echo "ERROR: falta $f"; exit 1; }
done

STAMP="$(date +"%Y%m%d_%H%M%S")"
BACKUP_DIR=".backup_volver_browser_${STAMP}"
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

KEY = "qc_lista_compras_origen"

# ------------------------------------------------------------
# A) Limpiar el intento anterior de return_to en lista_de_compras.
# ------------------------------------------------------------
base = base.replace(
    'href="{% url \'menu-elegido\' %}?return_to={{ request.get_full_path|urlencode }}"',
    'href="{% url \'menu-elegido\' %}"',
)

lista = lista.replace(
    '<form id="frm-menu" action="{% url \'menu-elegido\' %}?return_to={{ return_to|urlencode }}" method="post">',
    '<form id="frm-menu" action="{% url \'menu-elegido\' %}" method="post">',
)

# Volver vuelve a tener un href seguro de fallback.
lista = re.sub(
    r'(id="btn-volver-lista-compras"\s*\n\s*href=")[^"]+(")',
    r'\1{% url \'filtro-de-platos\' %}\2',
    lista,
    count=1,
)

# Quitar sólo el bloque que agregó el script anterior dentro de lista_de_compras.
m = re.search(r"(?m)^def lista_de_compras\(request\):\n", views)
if not m:
    raise RuntimeError("No encuentro lista_de_compras().")

next_def = re.search(r"(?m)^def ", views[m.end():])
end = m.end() + next_def.start() if next_def else len(views)
block = views[m.start():end]

block = re.sub(
    r'    return_to = \(request\.GET\.get\("return_to"\) or request\.POST\.get\("return_to"\) or ""\)\.strip\(\)\n'
    r'    if not return_to or not url_has_allowed_host_and_scheme\(\n'
    r'        return_to,\n'
    r'        allowed_hosts=\{request\.get_host\(\)\},\n'
    r'        require_https=request\.is_secure\(\),\n'
    r'    \):\n'
    r'        return_to = reverse\("filtro-de-platos"\)\n\n',
    "",
    block,
    count=1,
)
block = re.sub(r'^\s*"return_to": return_to,\n', "", block, flags=re.M)
views = views[:m.start()] + block + views[end:]

# ------------------------------------------------------------
# B) Al tocar carrito, guardar la URL REAL del navegador.
#    Esto sobrevive a querystrings y no depende del backend.
# ------------------------------------------------------------
cart_anchor = re.search(
    r'<a\s+href="\{% url \'menu-elegido\' %\}"(?P<attrs>[^>]*)>',
    base,
    flags=re.S,
)
if not cart_anchor:
    raise RuntimeError("No encuentro el enlace flotante a Lista de compras.")

anchor_text = cart_anchor.group(0)
if "qc_lista_compras_origen" not in anchor_text:
    replacement = anchor_text[:-1] + (
        ' onclick="try{sessionStorage.setItem(\'qc_lista_compras_origen\', window.location.href);}catch(e){}">'
    )
    base = base[:cart_anchor.start()] + replacement + base[cart_anchor.end():]

# ------------------------------------------------------------
# C) Volver lee ese origen y navega allí.
#    Si no existe, el href normal funciona como fallback.
# ------------------------------------------------------------
script_id = 'id="volver-lista-compras-origen"'
if script_id not in lista:
    button = re.search(
        r'<a\s+id="btn-volver-lista-compras"[\s\S]*?</a>',
        lista,
    )
    if not button:
        raise RuntimeError("No encuentro el botón Volver.")

    js = r'''
<script id="volver-lista-compras-origen">
(function () {
  const KEY = "qc_lista_compras_origen";
  const btn = document.getElementById("btn-volver-lista-compras");
  if (!btn) return;

  btn.addEventListener("click", function (event) {
    let origen = "";
    try {
      origen = sessionStorage.getItem(KEY) || "";
    } catch (error) {
      return;
    }

    if (!origen) return;

    try {
      const destino = new URL(origen, window.location.origin);
      if (destino.origin !== window.location.origin) return;

      event.preventDefault();
      sessionStorage.removeItem(KEY);
      window.location.assign(destino.href);
    } catch (error) {
      // El href del botón queda como fallback seguro.
    }
  });
})();
</script>
'''
    lista = lista[:button.end()] + "\n" + js.strip() + lista[button.end():]

# ------------------------------------------------------------
# D) Validaciones.
# ------------------------------------------------------------
if base.count("qc_lista_compras_origen") != 1:
    raise RuntimeError("El guardado de origen no quedó exactamente una vez.")

if lista.count('id="volver-lista-compras-origen"') != 1:
    raise RuntimeError("El JS de Volver no quedó exactamente una vez.")

if lista.count('id="btn-volver-lista-compras"') != 1:
    raise RuntimeError("El botón Volver no quedó exactamente una vez.")

if "?return_to=" in re.search(
    r'<a\s+href="\{% url \'menu-elegido\' %\}"[^>]*>', base, re.S
).group(0):
    raise RuntimeError("El carrito todavía conserva return_to.")

if 'href="{{ return_to }}"' in lista:
    raise RuntimeError("Volver todavía depende de return_to.")

if '"return_to": return_to' in block:
    raise RuntimeError("Quedó return_to agregado en la vista.")

base_path.write_text(base, encoding="utf-8")
lista_path.write_text(lista, encoding="utf-8")
views_path.write_text(views, encoding="utf-8")

print("OK: eliminado el intento anterior con return_to.")
print("OK: el carrito guarda window.location.href en sessionStorage.")
print("OK: Volver usa ese origen exacto y tiene fallback seguro.")
PY

echo
echo "============================================================"
echo "CHECKS"
echo "============================================================"
git diff --check
"$PYTHON_BIN" manage.py check
"$PYTHON_BIN" manage.py makemigrations --check --dry-run

echo
echo "============================================================"
echo "AUDITORÍA"
echo "============================================================"

COUNT_KEY="$(grep -Roh "qc_lista_compras_origen" "$BASE" "$LISTA" | wc -l | tr -d " ")"
if [ "$COUNT_KEY" -lt "2" ]; then
  echo "ERROR: falta una de las dos puntas del mecanismo de Volver."
  exit 1
fi

if grep -q 'href="{{ return_to }}"' "$LISTA"; then
  echo "ERROR: el botón Volver todavía depende de return_to."
  exit 1
fi

echo "OK: mecanismo local y acotado a carrito + Volver."

echo
echo "============================================================"
echo "LISTO PARA PROBAR"
echo "============================================================"
echo "IMPORTANTE: probá entrando a Compras NUEVAMENTE desde el carrito."
echo "La pestaña que ya estaba abierta antes del cambio no tiene origen guardado."
echo
echo "1. Volvé manualmente a Guarniciones."
echo "2. Tocá el carrito."
echo "3. En Lista de compras, tocá Volver."
echo "4. Debe volver exactamente a Guarniciones (misma URL/filtros)."
echo "5. Repetí desde otra categoría."
echo
echo "No hace commit."
echo "Backup: $BACKUP_DIR"
