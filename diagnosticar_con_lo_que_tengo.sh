#!/usr/bin/env bash
# Diagnostico de solo lectura del modo "Con lo que tengo".
# Ejecutar desde la carpeta del proyecto Django (donde esta manage.py).
set -euo pipefail

if [ ! -f manage.py ]; then
  printf '%s\n' 'ERROR: ejecuta este script desde la carpeta que contiene manage.py.' >&2
  exit 1
fi

if [ -x .venv/bin/python ]; then
  PYTHON_BIN=.venv/bin/python
else
  PYTHON_BIN=python3
fi
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1 && [ ! -x "$PYTHON_BIN" ]; then
  printf '%s\n' 'ERROR: no encontre Python 3. Activa .venv o instala Python 3.' >&2
  exit 1
fi

REPORT="reporte_diagnostico_con_lo_que_tengo.txt"
"$PYTHON_BIN" - "$REPORT" <<'PY'
import datetime
import os
import pathlib
import re
import sys

root = pathlib.Path.cwd()
report = root / sys.argv[1]
ignore_dirs = {'.git', '.venv', 'venv', 'env', 'node_modules', '__pycache__', 'staticfiles', 'site-packages', '.idea', '.vscode', 'migrations', 'media'}
extensions = {'.js', '.html', '.py', '.css'}

strong_pattern = re.compile(r'lo[_\s-]*que[_\s-]*tengo|con\s+lo\s+que\s+tengo|con_lo_que_tengo|conLoQueTengo|loQueTengo', re.I)
related_pattern = re.compile(r'(?:disponib|ingrediente|insumo|stock).{0,55}(?:filt|tengo|activ|modo)|(?:filt|tengo|activ|modo).{0,55}(?:disponib|ingrediente|insumo|stock)', re.I)
state_pattern = re.compile(r'localStorage|sessionStorage|\.checked\b|setAttribute\s*\(\s*[\'\"]checked|removeAttribute\s*\(\s*[\'\"]checked|DOMContentLoaded|pageshow|window\.onload|addEventListener\s*\(\s*[\'\"](?:change|click|load|popstate)|URLSearchParams|location\.(?:reload|search)|history\.(?:pushState|replaceState)|fetch\s*\(|htmx:|Alpine|data-.*(?:filt|tengo)|\.classList\.(?:add|toggle|remove)', re.I)
include_pattern = re.compile(r'<script\b|\{%\s*(?:include|extends|block)\b|filtros_platos|lo_que_tengo', re.I)

files = []
for directory, dirs, filenames in os.walk(root):
    dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith('.')]
    for filename in filenames:
        path = pathlib.Path(directory) / filename
        if path.suffix.lower() not in extensions:
            continue
        try:
            if path.stat().st_size > 1_000_000:
                continue
            content = path.read_text(encoding='utf-8', errors='replace')
        except (OSError, PermissionError):
            continue
        files.append((path.relative_to(root), content.splitlines()))

exact = []
related = []
state = []
includes = []
file_relevant = set()

for path, lines in files:
    path_str = str(path)
    is_focus = any(x in path_str.lower() for x in ('lo_que_tengo', 'filtros_platos', 'lista_filtrada', 'base.html', 'menu_programado', '_control_lo_que_tengo'))
    is_focus = is_focus or any(strong_pattern.search(line) for line in lines)
    if is_focus:
        file_relevant.add(path_str)
    for number, line in enumerate(lines, 1):
        row = (path_str, number, line, lines)
        if strong_pattern.search(line):
            exact.append(row)
        elif related_pattern.search(line):
            related.append(row)
        if is_focus and state_pattern.search(line):
            state.append(row)
        if path.suffix.lower() == '.html' and include_pattern.search(line) and (is_focus or 'lo_que_tengo' in line.lower() or 'filtros_platos' in line.lower()):
            includes.append(row)

out = []
def p(s=''):
    out.append(s)
def heading(s):
    p('\n' + '=' * 76)
    p(s)
    p('=' * 76)
def render_rows(rows, max_rows=110, radius=2):
    if not rows:
        p('(Sin coincidencias)')
        return
    for path, num, line, lines in rows[:max_rows]:
        p(f'\n--- {path}:{num} ---')
        for idx in range(max(1, num-radius), min(len(lines), num+radius)+1):
            prefix = '>>' if idx == num else '  '
            value = lines[idx-1].expandtabs(4)
            p(f'{prefix} {idx:>5}: {value[:240]}')
    if len(rows) > max_rows:
        p(f'\n[Omitidas {len(rows)-max_rows} coincidencias adicionales; pedir archivos relevantes si hace falta.]')

p('DIAGNOSTICO ESTATICO - MODO "CON LO QUE TENGO"')
p('Fecha: ' + datetime.datetime.now().astimezone().isoformat(timespec='seconds'))
p('Ruta del proyecto: ' + str(root))
p('Archivos inspeccionados (.py, .js, .html, .css): ' + str(len(files)))
p('IMPORTANTE: es un analisis estatico, no prueba que una linea se ejecute. No se modifico codigo.')

heading('1. ARCHIVOS IMPORTANTES DETECTADOS')
for target in ('lo_que_tengo.js', 'filtros_platos.js', '_control_lo_que_tengo_global.html', 'lista_filtrada.html', 'base.html', 'pre-base.html', 'menu_programado.js'):
    found = sorted(str(path) for path, _ in files if path.name == target)
    p(f'{target}: ' + ('; '.join(found) if found else 'NO ENCONTRADO'))

heading('2. REFERENCIAS DIRECTAS AL MODO - con contexto')
p(f'{len(exact)} referencias directas')
render_rows(exact, max_rows=130, radius=3)

heading('3. REFERENCIAS A DISPONIBILIDAD Y FILTROS')
p(f'{len(related)} referencias potencialmente relacionadas')
render_rows(related, max_rows=70, radius=1)

heading('4. INICIALIZACION, EVENTOS, STORAGE Y CAMBIOS DE ESTADO EN ARCHIVOS RELEVANTES')
p('Buscar particularmente inicializaciones en DOMContentLoaded/pageshow, .checked = true, localStorage/sessionStorage, y funciones que vuelven a mostrar el filtro.')
p(f'{len(state)} coincidencias')
render_rows(state, max_rows=140, radius=2)

heading('5. INCLUSIONES DE TEMPLATES Y CARGA DE JAVASCRIPT')
p(f'{len(includes)} coincidencias')
render_rows(includes, max_rows=75, radius=1)

heading('6. ARCHIVOS RELEVANTES PARA ADJUNTAR SI PERSISTE LA DUDA')
for path in sorted(file_relevant):
    p(path)
p('\nNo se cambio ningun archivo de la aplicacion. Este reporte es el unico archivo escrito.')
report.write_text('\n'.join(out) + '\n', encoding='utf-8')
print(f'Reporte generado: {report.name}')
print(f'Coincidencias directas: {len(exact)}; archivos inspeccionados: {len(files)}')
PY
