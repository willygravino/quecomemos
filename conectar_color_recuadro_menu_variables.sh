#!/usr/bin/env bash
set -Eeuo pipefail

.venv/bin/python - <<'PY'
from pathlib import Path
import datetime
import shutil
import subprocess

ROOT = Path.cwd()
CSS = ROOT / "AdminVideos/static/AdminVideos/css/mi-css.css"

if not CSS.exists():
    raise SystemExit("ERROR: no existe mi-css.css")

stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
backup = ROOT / f".backup_conectar_color_recuadro_menu_{stamp}"
backup.mkdir()

shutil.copy2(CSS, backup / "mi-css.css")

try:
    css = CSS.read_text(encoding="utf-8")

    old = """#diasTabContent .menu-programado-contenido-solido {
  border-width: 2px !important;
  border-style: solid !important;
  border-color: var(--qc-menu-vacio-activo) !important;
  background-color: var(--bs-tertiary-bg) !important;
  transition: border-color .15s ease, box-shadow .15s ease;
}"""

    new = """#diasTabContent .menu-programado-contenido-solido {
  border-width: 2px !important;
  border-style: solid !important;
  border-color: var(--qc-menu-vacio-activo) !important;
  background-color: color-mix(
    in srgb,
    var(--qc-menu-vacio-activo) 8%,
    var(--bs-tertiary-bg)
  ) !important;
  transition: border-color .15s ease, box-shadow .15s ease;
}"""

    if old not in css:
        raise RuntimeError("No encontré el bloque base del recuadro.")

    css = css.replace(old, new, 1)

    old_programado = """#diasTabContent
.menu-programado-contenido-solido.menu-programado-contenido-programado {
  border-color: var(--qc-menu-programado-activo) !important;
}"""

    new_programado = """#diasTabContent
.menu-programado-contenido-solido.menu-programado-contenido-programado {
  border-color: var(--qc-menu-programado-activo) !important;
  background-color: color-mix(
    in srgb,
    var(--qc-menu-programado-activo) 8%,
    var(--bs-tertiary-bg)
  ) !important;
}"""

    if old_programado not in css:
        raise RuntimeError("No encontré el bloque programado del recuadro.")

    css = css.replace(old_programado, new_programado, 1)

    CSS.write_text(css, encoding="utf-8", newline="\n")

    subprocess.run([".venv/bin/python", "manage.py", "check"], check=True)
    subprocess.run(["git", "diff", "--check"], check=True)

    print("=" * 70)
    print("LISTO - COLOR DE RECUADRO CONECTADO A VARIABLES")
    print("=" * 70)
    print("✓ el borde sigue las variables QC")
    print("✓ el fondo tenue sigue las variables QC")
    print("✓ cambiar --qc-menu-vacio-activo cambia pestaña + recuadro")
    print("✓ cambiar --qc-menu-programado-activo cambia pestaña + recuadro")
    print("✓ backup:", backup)

except Exception:
    shutil.copy2(backup / "mi-css.css", CSS)
    raise
PY
