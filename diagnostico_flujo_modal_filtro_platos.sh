#!/bin/bash

echo "=============================================="
echo " DIAGNOSTICO FLUJO MODAL FILTRO PLATOS"
echo "=============================================="

FECHA=$(date +"%Y%m%d_%H%M%S")
REPORTE="diagnostico_flujo_modal_filtro_${FECHA}.txt"

ARCHIVO="AdminVideos/templates/AdminVideos/lista_filtrada.html"

if [ ! -f "$ARCHIVO" ]; then
  echo "No existe: $ARCHIVO"
  exit 1
fi

{
echo "Archivo:"
echo "$ARCHIVO"
echo ""
echo "Fecha:"
date
echo ""

echo "=============================================="
echo "1) ESTRUCTURA MODAL"
echo "=============================================="

grep -n -A120 -B40 \
"filtroPlatosModal" \
"$ARCHIVO"

echo ""

echo "=============================================="
echo "2) FORMULARIO Y ANCLAS"
echo "=============================================="

grep -n -A20 -B20 \
-E "form-filtros-platos|filtroPlatosInlineHome|filtroPlatosModalBody" \
"$ARCHIVO"

echo ""

echo "=============================================="
echo "3) FUNCION MOVIMIENTO FORMULARIO"
echo "=============================================="

grep -n -A120 -B20 \
"moverFormSegunPantalla" \
"$ARCHIVO"

echo ""

echo "=============================================="
echo "4) REFERENCIAS JAVASCRIPT FILTRO"
echo "=============================================="

grep -n -A40 -B20 \
-E "media.matches|appendChild|DOMContentLoaded|initFiltroResponsiveMobile" \
"$ARCHIVO"

echo ""

echo "=============================================="
echo " FIN"
echo "=============================================="

} > "$REPORTE"

echo ""
echo "Reporte generado:"
echo "$REPORTE"
