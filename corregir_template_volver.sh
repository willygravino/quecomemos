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
else
  PYTHON_BIN="python3"
fi

LISTA="AdminVideos/templates/AdminVideos/lista_de_compras.html"
BASE="AdminVideos/templates/AdminVideos/base.html"

[ -f "$LISTA" ] || { echo "ERROR: falta $LISTA"; exit 1; }
[ -f "$BASE" ] || { echo "ERROR: falta $BASE"; exit 1; }

STAMP="$(date +"%Y%m%d_%H%M%S")"
BACKUP_DIR=".backup_fix_template_volver_${STAMP}"
mkdir -p "$BACKUP_DIR/$(dirname "$LISTA")"
cp "$LISTA" "$BACKUP_DIR/$LISTA"
git diff > "$BACKUP_DIR/pre_patch.diff" || true

"$PYTHON_BIN" - <<'PY'
from pathlib import Path

path = Path("AdminVideos/templates/AdminVideos/lista_de_compras.html")
text = path.read_text(encoding="utf-8")

bad = 'href="{% url \\\'filtro-de-platos\\\' %}"'
good = 'href="{% url \'filtro-de-platos\' %}"'

if bad in text:
    text = text.replace(bad, good, 1)
elif good in text:
    print("AVISO: el href ya estaba corregido.")
else:
    raise RuntimeError("No encuentro ni la versión rota ni la correcta del href de Volver.")

if "\\\'filtro-de-platos\\\'" in text:
    raise RuntimeError("Todavía quedó un escape inválido en lista_de_compras.html.")

path.write_text(text, encoding="utf-8")
print("OK: sintaxis Django del botón Volver corregida.")
PY

echo
echo "============================================================"
echo "CHECKS"
echo "============================================================"

git diff --check
"$PYTHON_BIN" manage.py check
"$PYTHON_BIN" manage.py makemigrations --check --dry-run

echo
echo "Buscando escapes accidentales en templates tocados..."
if grep -nF "\\'" "$LISTA" "$BASE"; then
  echo "ERROR: encontré barras invertidas antes de comillas simples en templates."
  exit 1
else
  echo "OK: no quedan escapes accidentales en esos templates."
fi

echo
echo "============================================================"
echo "LISTO"
echo "============================================================"
echo "Recargá /menu/elegido/."
echo "Después probá nuevamente: Guarniciones -> carrito -> Volver."
echo
echo "No hace commit."
echo "Backup: $BACKUP_DIR"
