#!/bin/bash

echo "=============================================="
echo " DIAGNOSTICO CSS LO QUE TENGO"
echo "=============================================="

FECHA=$(date +"%Y%m%d_%H%M%S")
REPORTE="diagnostico_css_lo_que_tengo_${FECHA}.txt"

{
echo "Fecha:"
date
echo ""

echo "=============================================="
echo "1) BUSQUEDA DE CLASES EN TODO EL PROYECTO"
echo "=============================================="

grep -Rni \
--exclude-dir=.venv \
--exclude-dir=.git \
-E "lo-que-tengo-global-mobile|lo-que-tengo-global-desktop|selector-lo-que-tengo|lo-que-tengo-activo" \
AdminVideos/ 2>/dev/null

echo ""

echo "=============================================="
echo "2) ARCHIVOS CSS RELACIONADOS"
echo "=============================================="

find AdminVideos/static/AdminVideos/css \
-type f \
-name "*.css" \
-print

echo ""

echo "=============================================="
echo " FIN DEL REPORTE"
echo "=============================================="

} > "$REPORTE"

echo ""
echo "Reporte generado:"
echo "$REPORTE"
