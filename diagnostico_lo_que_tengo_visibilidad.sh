#!/bin/bash

echo "=============================================="
echo " DIAGNOSTICO VISIBILIDAD LO QUE TENGO"
echo "=============================================="

FECHA=$(date +"%Y%m%d_%H%M%S")
REPORTE="diagnostico_lo_que_tengo_visibilidad_${FECHA}.txt"

{
echo "Fecha:"
date
echo ""

echo "=============================================="
echo "1) CONTROL LO QUE TENGO EN TEMPLATES"
echo "=============================================="

grep -Rni \
--exclude-dir=.venv \
--exclude-dir=.git \
"control_lo_que_tengo" \
AdminVideos/templates/AdminVideos/

echo ""

echo "=============================================="
echo "2) CLASES RESPONSIVE RELACIONADAS"
echo "=============================================="

grep -Rni \
--exclude-dir=.venv \
--exclude-dir=.git \
-E "d-none|d-md|d-lg|d-xl|display|mobile|desktop|responsive" \
AdminVideos/templates/AdminVideos/partials/_control_lo_que_tengo_global.html \
AdminVideos/templates/AdminVideos/lista_filtrada.html 2>/dev/null

echo ""

echo "=============================================="
echo "3) CONTENIDO PARCIAL"
echo "=============================================="

sed -n '1,220p' \
AdminVideos/templates/AdminVideos/partials/_control_lo_que_tengo_global.html 2>/dev/null

echo ""

echo "=============================================="
echo " FIN"
echo "=============================================="

} > "$REPORTE"

echo ""
echo "Reporte generado:"
echo "$REPORTE"
