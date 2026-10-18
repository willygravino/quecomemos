#!/bin/bash

set -e

echo "=============================================="
echo " NORMALIZAR LO QUE TENGO COMO COMPONENTE UNICO"
echo "=============================================="

PARCIAL="AdminVideos/templates/AdminVideos/partials/_control_lo_que_tengo_global.html"
CSS="AdminVideos/static/AdminVideos/css/mi-css.css"

if [ ! -f "$PARCIAL" ] || [ ! -f "$CSS" ]; then
  echo "No se encontraron archivos necesarios."
  exit 1
fi

STAMP=$(date +"%Y%m%d_%H%M%S")

BACKUP_PAR="$PARCIAL.backup_lo_que_tengo_unico_$STAMP"
BACKUP_CSS="$CSS.backup_lo_que_tengo_unico_$STAMP"

cp "$PARCIAL" "$BACKUP_PAR"
cp "$CSS" "$BACKUP_CSS"

echo "Backups:"
echo "$BACKUP_PAR"
echo "$BACKUP_CSS"

python3 <<'PY'
from pathlib import Path

parcial = Path("AdminVideos/templates/AdminVideos/partials/_control_lo_que_tengo_global.html")
css = Path("AdminVideos/static/AdminVideos/css/mi-css.css")

text = parcial.read_text(encoding="utf-8")

old = "{% if modo == 'mobile' %}lo-que-tengo-global-mobile{% else %}lo-que-tengo-global-desktop{% endif %}"

if old in text:
    text = text.replace(old, "lo-que-tengo-global")
else:
    raise SystemExit("No se encontró la lógica modo mobile/desktop esperada en el parcial.")

parcial.write_text(text, encoding="utf-8")

css_text = css.read_text(encoding="utf-8")

# Reemplazo selectivo: las reglas comunes ya existen.
# Solo elimina dependencias del nombre mobile cuando no aportan comportamiento.
css_text = css_text.replace(".lo-que-tengo-global-mobile", ".lo-que-tengo-global")

css.write_text(css_text, encoding="utf-8")

print("Normalización aplicada.")
PY

echo ""
echo "Verificar:"
echo "git diff -- AdminVideos/templates/AdminVideos/partials/_control_lo_que_tengo_global.html"
echo "git diff -- AdminVideos/static/AdminVideos/css/mi-css.css"
echo "python manage.py check"
