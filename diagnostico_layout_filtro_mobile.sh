#!/bin/bash

echo "=============================================="
echo " DIAGNOSTICO LAYOUT FILTRO MOBILE"
echo "=============================================="

FECHA=$(date +"%Y%m%d_%H%M%S")
REPORTE="diagnostico_layout_filtro_mobile_${FECHA}.txt"

TEMPLATE="AdminVideos/templates/AdminVideos/lista_filtrada.html"
CSS="AdminVideos/static/AdminVideos/css/mi-css.css"

{
echo "Fecha:"
date
echo ""

echo "=============================================="
echo "1) BLOQUE HTML DEL FILTRO MOBILE"
echo "=============================================="

grep -n -A80 -B20 \
-E "filtroPlatosMobileControls|filtro-platos-mobile-shell|filtro-mobile-keyword-box|form-filtros-platos" \
"$TEMPLATE"

echo ""

echo "=============================================="
echo "2) CSS DEL LAYOUT MOBILE EN TEMPLATE"
echo "=============================================="

grep -n -A80 -B20 \
-E "filtro-platos-mobile-shell|filtro-platos-mobile-summary|filtro-mobile-keyword-box|filtro-mobile-keyword-clear" \
"$TEMPLATE"

echo ""

echo "=============================================="
echo "3) CSS EN MI-CSS"
echo "=============================================="

grep -n -A80 -B20 \
-E "filtro-platos-mobile-shell|filtro-platos-mobile-summary|filtro-mobile-keyword-box|filtro-mobile-keyword-clear" \
"$CSS"

echo ""

echo "=============================================="
echo " FIN"
echo "=============================================="

} > "$REPORTE"

echo ""
echo "Reporte generado:"
echo "$REPORTE"
