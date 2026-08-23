#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

python - <<'PY'
from datetime import datetime
from pathlib import Path
import re

raiz = Path.cwd()
salida = raiz / f"diagnostico_busqueda_responsive_{datetime.now():%Y%m%d_%H%M%S}.txt"

directorios = [
    raiz / "AdminVideos" / "templates",
    raiz / "AdminVideos" / "static" / "AdminVideos" / "css",
    raiz / "AdminVideos" / "static" / "AdminVideos" / "js",
    raiz / "nuestrotubo",
]

extensiones = {".html", ".css", ".js", ".py"}
omitidos = {
    "bootstrap.min.css", "bootstrap.bundle.min.js", "bootstrap.min.js",
    "sb-admin-2.css", "sb-admin-2.min.css", "sb-admin-2.js",
    "sb-admin-2.min.js", "jquery.min.js", "select2.min.js",
}

patron_busqueda = re.compile(
    r"fa-(?:search|magnifying-glass)|bi-search|glyphicon-search|"
    r"type\s*=\s*['\"]search['\"]|type\s*=\s*['\"]text['\"][^>]*(?:buscar|search)|"
    r"(?:buscar|búsqueda|busqueda|search|lupa)|"
    r"navbar-search|topbar-search|form-inline",
    re.IGNORECASE,
)

patron_responsive = re.compile(
    r"@media|d-(?:none|sm-none|md-none|lg-none|xl-none)|"
    r"d-(?:sm|md|lg|xl)-(?:block|flex|inline|inline-block)|"
    r"navbar-(?:toggler|collapse)|collapse|dropdown|"
    r"matchMedia|innerWidth|clientWidth|resize|"
    r"data-bs-(?:toggle|target)|data-toggle|data-target",
    re.IGNORECASE,
)

archivos = []
for directorio in directorios:
    if not directorio.exists():
        continue
    for archivo in directorio.rglob("*"):
        if not archivo.is_file() or archivo.suffix.lower() not in extensiones:
            continue
        if archivo.name in omitidos or ".bak" in archivo.name:
            continue
        if "__pycache__" in archivo.parts or "staticfiles" in archivo.parts:
            continue
        archivos.append(archivo)


def unir_intervalos(intervalos, total):
    normalizados = []
    for inicio, fin in sorted(intervalos):
        inicio = max(0, inicio)
        fin = min(total, fin)
        if not normalizados or inicio > normalizados[-1][1] + 2:
            normalizados.append([inicio, fin])
        else:
            normalizados[-1][1] = max(normalizados[-1][1], fin)
    return normalizados


hallazgos = []
for archivo in sorted(archivos):
    lineas = archivo.read_text(encoding="utf-8", errors="replace").splitlines()
    coincidencias_busqueda = [
        indice for indice, linea in enumerate(lineas) if patron_busqueda.search(linea)
    ]
    if not coincidencias_busqueda:
        continue

    intervalos = []
    for indice in coincidencias_busqueda:
        # Contexto amplio para ver el formulario, su contenedor y sus clases responsive.
        intervalos.append((indice - 14, indice + 16))

        # Si hay un @media cercano antes, inclúyelo desde su comienzo.
        for anterior in range(indice, max(-1, indice - 55), -1):
            if "@media" in lineas[anterior]:
                intervalos.append((anterior, indice + 22))
                break

    bloques = []
    for inicio, fin in unir_intervalos(intervalos, len(lineas)):
        contenido = "\n".join(
            f"{numero + 1:5}: {lineas[numero]}" for numero in range(inicio, fin)
        )
        tiene_responsive = any(
            patron_responsive.search(lineas[numero]) for numero in range(inicio, fin)
        )
        bloques.append((inicio + 1, fin, tiene_responsive, contenido))

    hallazgos.append((archivo.relative_to(raiz).as_posix(), bloques))

with salida.open("w", encoding="utf-8") as informe:
    informe.write("DIAGNÓSTICO: LUPA Y FORMULARIO DE BÚSQUEDA EN MODO RESPONSIVE\n")
    informe.write("=" * 78 + "\n\n")
    informe.write(f"Archivos propios revisados: {len(archivos)}\n")
    informe.write(f"Archivos con coincidencias: {len(hallazgos)}\n\n")
    informe.write(
        "El informe excluye Bootstrap, SB Admin, jQuery y Select2 para evitar ruido.\n"
        "Los bloques marcados RESPONSIVE contienen clases o reglas que pueden cambiar\n"
        "la visibilidad del buscador según el ancho de pantalla.\n\n"
    )

    if not hallazgos:
        informe.write("No se encontraron referencias al buscador o a la lupa.\n")

    for nombre, bloques in hallazgos:
        informe.write("\n" + "#" * 78 + "\n")
        informe.write(f"ARCHIVO: {nombre}\n")
        informe.write("#" * 78 + "\n")
        for inicio, fin, responsive, contenido in bloques:
            marca = "RESPONSIVE" if responsive else "CONTEXTO"
            informe.write(f"\n[{marca}] líneas {inicio}-{fin}\n")
            informe.write("-" * 78 + "\n")
            informe.write(contenido + "\n")

print("OK: diagnóstico terminado.")
print(f"Archivo generado: {salida.name}")
print("Subí ese archivo al chat para analizar la causa exacta.")
PY
