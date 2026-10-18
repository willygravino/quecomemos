#!/usr/bin/env bash
set -euo pipefail

# Parche dirigido para Que Comemos, basado en el reporte del 18/10/2026.
# De forma predeterminada SOLO MUESTRA EL DIFF.
# Ejecutar con --aplicar para modificar archivos, respaldar y validar.

MODO="${1:---revisar}"
if [[ "$MODO" != "--revisar" && "$MODO" != "--aplicar" ]]; then
  echo "Uso: bash $0 [--revisar|--aplicar]" >&2
  exit 2
fi

cd "$(dirname "$0")"
if [[ ! -f manage.py ]]; then
  echo "ERROR: Ubicá este script en la carpeta del proyecto que contiene manage.py." >&2
  exit 2
fi

python3 - "$MODO" <<'PY'
from pathlib import Path
from datetime import datetime
import difflib
import shutil
import subprocess
import sys

modo = sys.argv[1]
archivos = {
    "AdminVideos/static/AdminVideos/js/filtros_platos.js": [
        (
            'nuevaUrl.searchParams.delete("lo_que_tengo");',
            'nuevaUrl.searchParams.set("lo_que_tengo", "0");',
            3,
        ),
    ],
    "AdminVideos/views.py": [
        (
            '        valor_lo_que_tengo = request.session.get("lo_que_tengo_activo", False)',
            '        valor_lo_que_tengo = False  # Sin parametro GET, no reactivar desde sesion.',
            1,
        ),
    ],
    "AdminVideos/templates/AdminVideos/lista_filtrada.html": [
        (
            'AdminVideos/js/filtros_platos.js\' %}?v=20260831_102713',
            'AdminVideos/js/filtros_platos.js\' %}?v=20261018_1',
            1,
        ),
    ],
}

antes = {}
despues = {}
for nombre, operaciones in archivos.items():
    ruta = Path(nombre)
    if not ruta.is_file():
        sys.exit(f"ERROR: No existe {nombre}. No se realizaron cambios.")
    fuente = ruta.read_text(encoding="utf-8")
    editado = fuente
    for antiguo, nuevo, cantidad_esperada in operaciones:
        cantidad = editado.count(antiguo)
        if cantidad != cantidad_esperada:
            sys.exit(
                f"ERROR en {nombre}: se esperaban {cantidad_esperada} coincidencias "
                f"para {antiguo!r}, pero hay {cantidad}. No se realizaron cambios. "
                "Es posible que el proyecto haya cambiado después del reporte."
            )
        editado = editado.replace(antiguo, nuevo)
    antes[nombre] = fuente
    despues[nombre] = editado

print("\nCORRECCION PROPUESTA (solo 3 archivos):\n")
for nombre in archivos:
    print("".join(difflib.unified_diff(
        antes[nombre].splitlines(keepends=True),
        despues[nombre].splitlines(keepends=True),
        fromfile=f"a/{nombre}",
        tofile=f"b/{nombre}",
        n=2,
    )))

if modo == "--revisar":
    print("SOLO VISTA PREVIA: no se modifico ningun archivo.")
    print("Para aplicar: bash corregir_reactivacion_con_lo_que_tengo.sh --aplicar")
    sys.exit(0)

respaldo = Path("backups_fix_lo_que_tengo") / datetime.now().strftime("%Y%m%d_%H%M%S_%f")
respaldo.mkdir(parents=True, exist_ok=False)
for nombre in archivos:
    destino = respaldo / nombre
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(nombre, destino)

try:
    for nombre, editado in despues.items():
        Path(nombre).write_text(editado, encoding="utf-8")

    print("\nVALIDACIONES:")
    if shutil.which("node"):
        print("$ node --check AdminVideos/static/AdminVideos/js/filtros_platos.js", flush=True)
        subprocess.run(["node", "--check", "AdminVideos/static/AdminVideos/js/filtros_platos.js"], check=True)
    else:
        print("Node.js no instalado: se omite control sintactico de JavaScript.")

    python_venv = Path(".venv/bin/python")
    python_exec = str(python_venv) if python_venv.is_file() else sys.executable
    print(f"$ {python_exec} manage.py check", flush=True)
    subprocess.run([python_exec, "manage.py", "check"], check=True)
except Exception as exc:
    for nombre in archivos:
        shutil.copy2(respaldo / nombre, nombre)
    sys.exit(f"\nVALIDACION FALLIDA: {exc}\nSe restauraron los 3 archivos desde {respaldo}.")

reporte = Path("reporte_fix_lo_que_tengo.txt")
reporte.write_text(
    "CORRECCION APLICADA - CON LO QUE TENGO\n"
    f"Fecha: {datetime.now().isoformat(timespec='seconds')}\n"
    f"Backup: {respaldo}\n"
    "Archivos: filtros_platos.js, views.py, lista_filtrada.html (version del JS)\n"
    "Verificaciones: node --check (si disponible); python manage.py check\n"
    "Cambio de comportamiento: en GET sin lo_que_tengo, el filtro inicia APAGADO.\n"
    "GET con lo_que_tengo=1 sigue activo. LoQueTengo legado se conserva.\n",
    encoding="utf-8",
)
print(f"\nCORRECCION APLICADA. Backup: {respaldo}")
print(f"Reporte: {reporte}")
print("Probar encender/apagar, recargar, navegar, volver, y ambas vistas mobile/desktop.")
PY
