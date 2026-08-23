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

if [ ! -f "$BASE" ]; then
  echo "ERROR: falta $BASE"
  exit 1
fi

STAMP="$(date +"%Y%m%d_%H%M%S")"
BACKUP_DIR=".backup_ocultar_flotantes_${STAMP}"
mkdir -p "$BACKUP_DIR/$(dirname "$BASE")"
cp "$BASE" "$BACKUP_DIR/$BASE"
git diff > "$BACKUP_DIR/pre_patch.diff" || true

"$PYTHON_BIN" - <<'PY'
from pathlib import Path

path = Path("AdminVideos/templates/AdminVideos/base.html")
text = path.read_text(encoding="utf-8")

create_marker = "{# Botón flotante: crear plato rápido según la sección actual #}"
cart_marker = "{# Botón flotante: acceso rápido a la lista de compras #}"

if create_marker not in text:
    raise RuntimeError("No encuentro el bloque del botón flotante Agregar.")
if cart_marker not in text:
    raise RuntimeError("No encuentro el bloque del carrito flotante.")

# Si ya fue aplicado, no duplicar.
guard_start = "{% with current_url=request.resolver_match.url_name %}\n{% if current_url != 'menu-elegido' and current_url != 'videos-create' and current_url != 'videos-update' %}"
guard_end = "{% endif %}\n{% endwith %}"

if guard_start not in text:
    start = text.index(create_marker)

    # Incluir también cualquier comentario/espacio inmediatamente anterior
    # sólo si pertenece al bloque. Dejamos el marker dentro del guard.
    script_pos = text.find("\n<script>", text.index(cart_marker))
    if script_pos == -1:
        script_pos = text.find("\n\n<script>", text.index(cart_marker))
    if script_pos == -1:
        raise RuntimeError("No pude delimitar el final de los botones flotantes.")

    block = text[start:script_pos]
    wrapped = guard_start + "\n" + block.rstrip() + "\n" + guard_end + "\n"
    text = text[:start] + wrapped + text[script_pos:]
else:
    print("AVISO: la condición ya estaba presente; no se duplica.")

# Validaciones estructurales.
if text.count(guard_start) != 1:
    raise RuntimeError("La condición de visibilidad no quedó exactamente una vez.")

for url_name in ("menu-elegido", "videos-create", "videos-update"):
    if url_name not in guard_start:
        raise RuntimeError(f"Falta excluir {url_name}.")

# Los dos botones deben quedar dentro del mismo guard.
gstart = text.index(guard_start)
gend = text.index(guard_end, gstart)
section = text[gstart:gend]

if create_marker not in section:
    raise RuntimeError("Agregar quedó fuera del guard común.")
if cart_marker not in section:
    raise RuntimeError("Carrito quedó fuera del guard común.")

path.write_text(text, encoding="utf-8")

print("OK: Agregar y Lista de compras comparten una única regla de visibilidad.")
print("OK: ocultos en compras, crear plato y editar plato.")
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

checks = {
    "compras": reverse("menu-elegido"),
    "crear": reverse("videos-create"),
    "editar": reverse("videos-update", kwargs={"pk": 1}),
}

for nombre, url in checks.items():
    assert url
    print(f"{nombre}: {url}")
PY

echo
echo "============================================================"
echo "LISTO PARA PROBAR"
echo "============================================================"
echo "1. Pantalla principal: deben verse Agregar y carrito (si corresponde)."
echo "2. Lista de compras: no debe verse ninguno de los dos."
echo "3. Crear plato: no debe verse ninguno de los dos."
echo "4. Editar plato: no debe verse ninguno de los dos."
echo "5. Volver desde compras debe seguir regresando al contexto anterior."
echo
echo "No hace commit."
echo "Backup: $BACKUP_DIR"
