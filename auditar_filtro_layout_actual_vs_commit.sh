#!/bin/bash

set -e

echo "=============================================="
echo " AUDITORIA FILTRO: ACTUAL VS COMMIT 8161FAA"
echo "=============================================="

ARCHIVO="AdminVideos/templates/AdminVideos/lista_filtrada.html"
COMMIT="8161faa"
FECHA=$(date +"%Y%m%d_%H%M%S")
REPORTE="auditoria_filtro_layout_${FECHA}.txt"

if [ ! -f "$ARCHIVO" ]; then
  echo "No existe: $ARCHIVO"
  exit 1
fi

if ! git cat-file -e "${COMMIT}:${ARCHIVO}" 2>/dev/null; then
  echo "No se encontró $ARCHIVO en el commit $COMMIT"
  exit 1
fi

{
echo "Fecha:"
date
echo ""

echo "Commit base:"
git show -s --format='%h %s' "$COMMIT"
echo ""

echo "=============================================="
echo "1) DIFF ACTUAL VS 8161FAA"
echo "=============================================="

git diff "$COMMIT" -- "$ARCHIVO"

echo ""

echo "=============================================="
echo "2) ESTRUCTURA ACTUAL DEL CONTROL"
echo "=============================================="

grep -n -A45 -B5 \
-E "filtroPlatosMobileControls|filtro-platos-y-lo-que-tengo|form-filtros-platos|_control_lo_que_tengo_global" \
"$ARCHIVO"

echo ""

echo "=============================================="
echo "3) ESTRUCTURA EN 8161FAA"
echo "=============================================="

git show "${COMMIT}:${ARCHIVO}" | grep -n -A45 -B5 \
-E "filtroPlatosMobileControls|filtro-platos-y-lo-que-tengo|form-filtros-platos|_control_lo_que_tengo_global"

echo ""

echo "=============================================="
echo "4) REGLAS CSS ACTUALES RELACIONADAS"
echo "=============================================="

grep -n -A45 -B10 \
-E "filtroPlatosMobileControls|filtro-platos-mobile-shell|filtro-mobile-keyword-box|filtro-mobile-filter|lo-que-tengo-global" \
"$ARCHIVO"

echo ""

echo "=============================================="
echo "5) BACKUPS RECIENTES"
echo "=============================================="

ls -1t AdminVideos/templates/AdminVideos/lista_filtrada.html.backup_* 2>/dev/null | head -20 || true

echo ""

echo "=============================================="
echo "6) ESTADO GIT"
echo "=============================================="

git status --short

echo ""

echo "=============================================="
echo " FIN DE AUDITORIA"
echo "=============================================="

} > "$REPORTE"

echo ""
echo "Reporte generado:"
echo "$REPORTE"
