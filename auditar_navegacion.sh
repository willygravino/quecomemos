#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
cd "$ROOT"

if [ ! -f manage.py ] || [ ! -d .git ]; then
  echo "ERROR: ejecutá este script desde la raíz del repo Django."
  exit 1
fi

STAMP="$(date +"%Y%m%d_%H%M%S")"
OUT="auditoria_navegacion_${STAMP}.txt"

{
  echo "============================================================"
  echo "AUDITORÍA DE NAVEGACIÓN"
  echo "Fecha: $(date)"
  echo "Repo:  $(pwd)"
  echo "============================================================"
  echo

  echo "1) ESTADO GIT"
  echo "------------------------------------------------------------"
  git status --short
  echo

  echo "2) DIFF ACTUAL DE NAVEGACIÓN"
  echo "------------------------------------------------------------"
  git diff -- \
    AdminVideos/templates/AdminVideos/base.html \
    AdminVideos/templates/AdminVideos/lista_de_compras.html \
    AdminVideos/static/AdminVideos/js/menu_programado.js \
    AdminVideos/static/AdminVideos/js/navigation.js \
    AdminVideos/views.py \
    nuestrotubo/urls.py 2>/dev/null || true
  echo

  echo "3) URLS NOMBRADAS"
  echo "------------------------------------------------------------"
  grep -nE "path\(.*name=" nuestrotubo/urls.py || true
  echo

  echo "4) REDIRECT / REVERSE EN VIEWS"
  echo "------------------------------------------------------------"
  grep -nE "redirect\(|reverse\(|reverse_lazy\(" AdminVideos/views.py || true
  echo

  echo "5) TODOS LOS return_to"
  echo "------------------------------------------------------------"
  grep -RIn --exclude-dir=.git --exclude-dir=.venv --exclude-dir=venv \
    --exclude-dir="backup*" --exclude="*.pyc" "return_to" AdminVideos nuestrotubo || true
  echo

  echo "6) VALIDACIÓN DE return_to"
  echo "------------------------------------------------------------"
  grep -RIn --exclude-dir=.git --exclude-dir=.venv --exclude-dir=venv \
    "url_has_allowed_host_and_scheme" AdminVideos || true
  echo

  echo "7) HISTORY / STORAGE / LOCATION"
  echo "------------------------------------------------------------"
  grep -RInE --exclude-dir=.git --exclude-dir=.venv --exclude-dir=venv \
    --exclude-dir="backup*" \
    "history\.(back|go|pushState|replaceState)|window\.location|location\.(href|assign|replace)|sessionStorage|localStorage" \
    AdminVideos/templates AdminVideos/static/AdminVideos/js || true
  echo

  echo "8) HANDLERS INLINE EN TEMPLATES"
  echo "------------------------------------------------------------"
  grep -RInE --exclude-dir=.git --exclude-dir="backup*" \
    "on(click|submit|change|input|keydown|keyup)=" \
    AdminVideos/templates/AdminVideos || true
  echo

  echo "9) resolver_match / url_name"
  echo "------------------------------------------------------------"
  grep -RInE --exclude-dir=.git --exclude-dir="backup*" \
    "resolver_match|url_name" AdminVideos/templates/AdminVideos || true
  echo

  echo "10) BOTONES DE NAVEGACIÓN ACTUALES"
  echo "------------------------------------------------------------"
  grep -RInE --exclude-dir=.git --exclude-dir="backup*" \
    "botonCrearPlatoFlotante|botonListaComprasFlotanteWrap|btn-volver-lista-compras|qc_lista_compras_origen" \
    AdminVideos/templates AdminVideos/static/AdminVideos/js || true
  echo

  echo "11) POSIBLES URLS INTERNAS HARDCODEADAS"
  echo "------------------------------------------------------------"
  grep -RInE --exclude-dir=.git --exclude-dir=.venv --exclude-dir=venv \
    --exclude-dir="backup*" --exclude="*.min.js" --exclude="*.map" \
    "href=\"/|action=\"/|fetch\(\"/|redirect\(\"/" \
    AdminVideos nuestrotubo || true
  echo

  echo "12) CONTEXTO base.html"
  echo "------------------------------------------------------------"
  if grep -nE "botonCrearPlatoFlotante|botonListaComprasFlotanteWrap|qc_lista_compras_origen|resolver_match.url_name" \
      AdminVideos/templates/AdminVideos/base.html > /tmp/qc_nav_base_hits.txt; then
    cat /tmp/qc_nav_base_hits.txt
  else
    echo "Sin coincidencias."
  fi
  echo

  echo "13) CONTEXTO lista_de_compras.html"
  echo "------------------------------------------------------------"
  if grep -nE "btn-volver-lista-compras|volver-lista-compras-origen|qc_lista_compras_origen|return_to" \
      AdminVideos/templates/AdminVideos/lista_de_compras.html > /tmp/qc_nav_lista_hits.txt; then
    cat /tmp/qc_nav_lista_hits.txt
  else
    echo "Sin coincidencias."
  fi
  echo

  echo "14) CHECKS"
  echo "------------------------------------------------------------"
  if [ -x ".venv/bin/python" ]; then
    PY=".venv/bin/python"
  elif command -v python >/dev/null 2>&1; then
    PY="python"
  else
    PY="python3"
  fi
  "$PY" manage.py check
  "$PY" manage.py makemigrations --check --dry-run
  git diff --check
  echo

  echo "============================================================"
  echo "FIN AUDITORÍA"
  echo "============================================================"
} > "$OUT" 2>&1

cat "$OUT"
echo
echo "Reporte guardado en: $OUT"
