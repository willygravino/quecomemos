#!/bin/bash

echo "=============================================="
echo " DIAGNOSTICO FORMULARIO FILTRO MODAL"
echo "=============================================="

FECHA=$(date +"%Y%m%d_%H%M%S")
REPORTE="diagnostico_formulario_modal_${FECHA}.txt"

ARCHIVO="AdminVideos/templates/AdminVideos/lista_filtrada.html"

{
echo "Archivo:"
echo "$ARCHIVO"
echo ""

echo "=============================================="
echo "FORMULARIO"
echo "=============================================="

grep -n -A30 -B20 "form-filtros-platos" "$ARCHIVO"

echo ""

echo "=============================================="
echo "INCLUDES / CONTENEDORES FILTRO"
echo "=============================================="

grep -n -A30 -B20 -E "filtroPlatosModalBody|filtroPlatosInlineHome|include.*filtro|filtros_platos" "$ARCHIVO"

echo ""

echo "=============================================="
echo "FIN"
echo "=============================================="

} > "$REPORTE"

echo ""
echo "Reporte generado:"
echo "$REPORTE"
