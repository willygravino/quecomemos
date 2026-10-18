#!/bin/bash

echo "=============================================="
echo " BUSCAR UBICACION REAL FORM FILTROS PLATOS"
echo "=============================================="

FECHA=$(date +"%Y%m%d_%H%M%S")
REPORTE="ubicacion_form_filtros_real_${FECHA}.txt"

{
echo "Fecha:"
date
echo ""

echo "=============================================="
echo "1) TODAS LAS REFERENCIAS form-filtros-platos"
echo "=============================================="

grep -Rni \
--exclude-dir=.venv \
--exclude-dir=.git \
"form-filtros-platos" \
AdminVideos/

echo ""

echo "=============================================="
echo "2) INCLUDES DE FILTROS"
echo "=============================================="

grep -Rni \
--exclude-dir=.venv \
--exclude-dir=.git \
-E "include.*filtro|filtro.*include|filtros_platos" \
AdminVideos/templates/AdminVideos/

echo ""

echo "=============================================="
echo "FIN"
echo "=============================================="

} > "$REPORTE"

echo ""
echo "Reporte generado:"
echo "$REPORTE"
