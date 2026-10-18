#!/bin/bash

echo "=============================================="
echo " EXTRACCIÓN BLOQUE FILTRO PLATOS"
echo "=============================================="

ARCHIVO="AdminVideos/templates/AdminVideos/lista_filtrada.html"

if [ ! -f "$ARCHIVO" ]; then
  echo "No se encontró: $ARCHIVO"
  exit 1
fi

FECHA=$(date +"%Y%m%d_%H%M%S")
REPORTE="bloque_filtro_platos_${FECHA}.txt"

{
echo "Archivo analizado:"
echo "$ARCHIVO"
echo ""
echo "Fecha:"
date
echo ""

echo "=============================================="
echo "LÍNEAS RELEVANTES"
echo "=============================================="

grep -n -A220 -B20 \
-E "filtroPlatosMobileControls|filtroPlatosInlineHome|form-filtros-platos|filtroPlatosModal|lo-que-tengo|Lo que tengo" \
"$ARCHIVO"

echo ""

echo "=============================================="
echo " FIN DEL REPORTE"
echo "=============================================="

} > "$REPORTE"

echo ""
echo "Reporte generado:"
echo "$REPORTE"
