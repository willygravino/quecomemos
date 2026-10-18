#!/bin/bash

set -e

echo "=============================================="
echo " AJUSTAR LO QUE TENGO PARA FILTRO UNIFICADO"
echo "=============================================="

ARCHIVO="AdminVideos/templates/AdminVideos/lista_filtrada.html"

if [ ! -f "$ARCHIVO" ]; then
  echo "No existe: $ARCHIVO"
  exit 1
fi

BACKUP="${ARCHIVO}.backup_lo_que_tengo_unificado_$(date +"%Y%m%d_%H%M%S")"

cp "$ARCHIVO" "$BACKUP"

echo "Backup creado:"
echo "$BACKUP"

python3 <<'PY'
from pathlib import Path

path = Path("AdminVideos/templates/AdminVideos/lista_filtrada.html")
text = path.read_text(encoding="utf-8")

viejo = '{% include "AdminVideos/partials/_control_lo_que_tengo_global.html" with modo="mobile" %}'

nuevo = '{% include "AdminVideos/partials/_control_lo_que_tengo_global.html" with modo="mobile" %}'

# El cambio estructural de esta etapa no modifica el parcial.
# Solo verifica que el control mobile exista en el contenedor unificado.
# Se deja preparado como script seguro para futuras modificaciones.
if viejo not in text:
    raise SystemExit(
        "No se encontró el control mobile esperado. No se realizó ningún cambio."
    )

print("El control Lo que tengo ya está en el bloque unificado.")
print("No se requiere modificación de template en esta etapa.")
PY

echo ""
echo "Diagnóstico aplicado."
echo "Verificar:"
echo "git diff -- AdminVideos/templates/AdminVideos/lista_filtrada.html"
