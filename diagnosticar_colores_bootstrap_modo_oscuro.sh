#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

python - <<'PY'
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
import re

raiz = Path.cwd()
salida = raiz / f"diagnostico_colores_bootstrap_modo_oscuro_{datetime.now():%Y%m%d_%H%M%S}.txt"

directorios = [
    raiz / "AdminVideos" / "templates",
    raiz / "AdminVideos" / "static" / "AdminVideos" / "css",
    raiz / "AdminVideos" / "static" / "AdminVideos" / "js",
    raiz / "nuestrotubo",
]

extensiones = {".html", ".css", ".js", ".py"}
omitidos = {"staticfiles", "node_modules", "__pycache__", ".git"}

archivos = []
for directorio in directorios:
    if not directorio.exists():
        continue
    for archivo in directorio.rglob("*"):
        if not archivo.is_file() or archivo.suffix.lower() not in extensiones:
            continue
        if any(parte in omitidos for parte in archivo.parts):
            continue
        if ".bak" in archivo.name:
            continue
        archivos.append(archivo)

clase_re = re.compile(
    r"(?<![\w-])(?:btn|bg|text|border|link|alert|badge|list-group-item|table)-"
    r"(?:primary|secondary|success|danger|warning|info|light|dark)(?![\w-])"
)

tema_re = re.compile(
    r"data-bs-theme|bs-theme|prefers-color-scheme|modo.?oscuro|dark.?mode|"
    r"setAttribute\s*\([^\n]*data-bs-theme|localStorage[^\n]*(?:theme|tema)",
    re.IGNORECASE,
)

variable_re = re.compile(
    r"--bs-(?:primary|secondary|success|danger|warning|info|light|dark)"
    r"(?:-rgb|-text-emphasis|-bg-subtle|-border-subtle)?\s*:|"
    r"--bs-(?:body-bg|body-color|border-color)\s*:",
    re.IGNORECASE,
)

selector_oscuro_re = re.compile(
    r"\[data-bs-theme\s*=\s*['\"]?dark['\"]?\]|"
    r"html\[[^\]]*(?:dark|oscuro)[^\]]*\]|"
    r"body\.[\w-]*(?:dark|oscuro)",
    re.IGNORECASE,
)

conteo_clases = Counter()
por_archivo = defaultdict(Counter)
hallazgos_clases = []
hallazgos_tema = []
hallazgos_variables = []
hallazgos_selectores = []

for archivo in sorted(archivos):
    relativo = archivo.relative_to(raiz).as_posix()
    try:
        lineas = archivo.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        continue

    for numero, linea in enumerate(lineas, 1):
        clases = clase_re.findall(linea)
        if clases:
            conteo_clases.update(clases)
            por_archivo[relativo].update(clases)
            hallazgos_clases.append((relativo, numero, linea.strip()))
        if tema_re.search(linea):
            hallazgos_tema.append((relativo, numero, linea.strip()))
        if variable_re.search(linea):
            hallazgos_variables.append((relativo, numero, linea.strip()))
        if selector_oscuro_re.search(linea):
            inicio = max(0, numero - 2)
            fin = min(len(lineas), numero + 6)
            contexto = "\n".join(
                f"    {i + 1}: {lineas[i]}" for i in range(inicio, fin)
            )
            hallazgos_selectores.append((relativo, numero, contexto))

with salida.open("w", encoding="utf-8") as informe:
    informe.write("DIAGNÓSTICO: COLORES BOOTSTRAP Y MODO OSCURO\n")
    informe.write("=" * 70 + "\n\n")
    informe.write(f"Archivos revisados: {len(archivos)}\n\n")

    informe.write("1. RESUMEN DE CLASES DE COLOR BOOTSTRAP\n")
    informe.write("-" * 70 + "\n")
    if conteo_clases:
        for clase, cantidad in conteo_clases.most_common():
            informe.write(f"{cantidad:5}  {clase}\n")
    else:
        informe.write("No se encontraron clases contextuales.\n")

    informe.write("\n2. ARCHIVOS CON MAYOR CANTIDAD DE COLORES BOOTSTRAP\n")
    informe.write("-" * 70 + "\n")
    resumen_archivos = sorted(
        ((sum(c.values()), nombre, c) for nombre, c in por_archivo.items()),
        reverse=True,
    )
    for total, nombre, clases in resumen_archivos:
        detalle = ", ".join(f"{k}={v}" for k, v in clases.most_common())
        informe.write(f"{total:5}  {nombre}\n       {detalle}\n")

    informe.write("\n3. ACTIVACIÓN Y PERSISTENCIA DEL TEMA\n")
    informe.write("-" * 70 + "\n")
    for nombre, numero, linea in hallazgos_tema:
        informe.write(f"{nombre}:{numero}: {linea}\n")
    if not hallazgos_tema:
        informe.write("No se encontraron referencias.\n")

    informe.write("\n4. SELECTORES ESPECÍFICOS DEL MODO OSCURO, CON CONTEXTO\n")
    informe.write("-" * 70 + "\n")
    for nombre, numero, contexto in hallazgos_selectores:
        informe.write(f"\n### {nombre}:{numero}\n{contexto}\n")
    if not hallazgos_selectores:
        informe.write("No se encontraron selectores específicos.\n")

    informe.write("\n5. VARIABLES DE COLOR BOOTSTRAP REDEFINIDAS\n")
    informe.write("-" * 70 + "\n")
    for nombre, numero, linea in hallazgos_variables:
        informe.write(f"{nombre}:{numero}: {linea}\n")
    if not hallazgos_variables:
        informe.write("No se encontraron variables redefinidas.\n")

    informe.write("\n6. TODAS LAS APARICIONES DE CLASES CONTEXTUALES\n")
    informe.write("-" * 70 + "\n")
    for nombre, numero, linea in hallazgos_clases:
        informe.write(f"{nombre}:{numero}: {linea}\n")

print("OK: diagnóstico terminado.")
print(f"Archivo generado: {salida.name}")
print("Subí ese archivo al chat para que pueda analizarlo.")
PY
