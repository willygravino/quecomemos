#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

python - <<'PY'
from datetime import datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

raiz = Path.cwd()
marca = datetime.now().strftime("%Y%m%d_%H%M%S")
salida = raiz / f"diagnostico_selector_horizontal_{marca}.zip"

rutas = [
    "AdminVideos/templates/AdminVideos/base.html",
    "AdminVideos/templates/AdminVideos/pre-base.html",
    "AdminVideos/templates/AdminVideos/lista_filtrada.html",
    "AdminVideos/templates/AdminVideos/partials/_menu_programado_dias.html",
    "AdminVideos/static/AdminVideos/css/mi-css.css",
    "AdminVideos/static/AdminVideos/js/filtros_platos.js",
    "AdminVideos/static/AdminVideos/js/lo_que_tengo.js",
    "AdminVideos/views.py",
    "AdminVideos/context_processors.py",
    "nuestrotubo/urls.py",
]

faltantes = [ruta for ruta in rutas if not (raiz / ruta).is_file()]
if faltantes:
    listado = "\n- ".join(faltantes)
    raise SystemExit(f"DETENIDO: faltan archivos necesarios:\n- {listado}")

terminos = (
    "accordionSidebar", "sidebar", "js-filtro-tipopag",
    "js-filtro-lo-que-tengo", "LoQueTengo", "lo_que_tengo",
    "tipopag", "Todos", "contenedor-menu-programado-dias",
    "actualizarMenuLateralActivo", "actualizarEstadoLoQueTengo",
)

referencias = []
for ruta in rutas:
    archivo = raiz / ruta
    texto = archivo.read_text(encoding="utf-8", errors="replace")
    for numero, linea in enumerate(texto.splitlines(), 1):
        if any(termino in linea for termino in terminos):
            referencias.append(f"{ruta}:{numero}: {linea}")

contenido_referencias = (
    "REFERENCIAS PARA EL SELECTOR HORIZONTAL\n"
    + "=" * 72
    + "\n\n"
    + "\n".join(referencias)
    + "\n"
)

with ZipFile(salida, "w", compression=ZIP_DEFLATED) as zipf:
    for ruta in rutas:
        zipf.write(raiz / ruta, arcname=ruta)
    zipf.writestr("referencias_selector_horizontal.txt", contenido_referencias)

print("OK: diagnóstico preparado.")
print(f"Archivo generado: {salida.name}")
print("No se modificó ningún archivo de la aplicación.")
print("Subí el ZIP al chat para preparar la primera etapa.")
PY
