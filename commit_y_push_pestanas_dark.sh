#!/usr/bin/env bash
set -euo pipefail

LOG="commit_y_push_pestanas_dark_$(date +%Y%m%d_%H%M%S).txt"

{
  echo "=================================================="
  echo "Commit + push pestañas dark"
  echo "Fecha: $(date)"
  echo "Directorio: $(pwd)"
  echo "=================================================="

  echo ""
  echo "---- estado inicial ----"
  git --no-pager status --short || true

  echo ""
  echo "---- verificar fix de pestañas ----"
  python - <<'PY'
from pathlib import Path
import re

base_path = Path("AdminVideos/templates/AdminVideos/base.html")
css_path = Path("AdminVideos/static/AdminVideos/css/mi-css.css")

for path in (base_path, css_path):
    if not path.exists():
        raise SystemExit(f"ERROR: no existe {path}")

base = base_path.read_text()
css = css_path.read_text()

checks = [
    ("bloque pestañas presente", "QC dark exacto: pestañas Bootstrap activas" in css),
    ("nav-tabs activo oscuro", ".nav-tabs .nav-link.active" in css and "background-color: #212529" in css),
    ("nav-pills activo oscuro", ".nav-pills .nav-link.active" in css and "background-color: #343a40" in css),
    ("no toca btn-check", "QC dark exacto: pestañas Bootstrap activas" in css and ".btn-check" not in css.split("QC dark exacto: pestañas Bootstrap activas", 1)[1]),
    ("base carga mi-css con cache bust", "mi-css.css' %}?v=" in base),
]

ok = True
for name, result in checks:
    print(("OK: " if result else "ERROR: ") + name)
    ok = ok and result

if not ok:
    raise SystemExit("Falló la verificación de pestañas dark. No comiteo.")
PY

  echo ""
  echo "---- limpiar temporales generados por parches/rollback ----"
  python - <<'PY'
from pathlib import Path
import shutil
import subprocess

result = subprocess.run(
    ["git", "ls-files", "--others", "--exclude-standard"],
    check=True,
    text=True,
    capture_output=True,
)

prefixes_files = (
    "fix_solo_pestanas_activas_dark",
    "rollback_visual_a_ultimo_commit_limpio",
    "rollback_a_pestana_bien_sin_filtros_experimentos",
    "fix_quirurgico_filtros_pestana_menu_v2",
    "fix_filtros_integrados_uniformes_v3",
    "parche_quirurgico_filtros_menu_programado_v1",
    "parche_bootstrap_filtros_programado_minimo_v1",
    "diagnostico_y_parche_filtros_programado_v3",
    "parche_superficies_filtros_menu_oscuro_v1",
    "parche_superficies_blancas_modo_oscuro_v2",
    "rollback_filtros_programado_a_v2",
)

prefixes_dirs = (
    "backup_visual_antes_rollback_",
)

deleted = []
for raw in result.stdout.splitlines():
    p = Path(raw)

    # No tocar media ni otros archivos del usuario.
    if str(p).startswith("media/"):
        continue

    if p.is_dir() and p.name.startswith(prefixes_dirs):
        shutil.rmtree(p)
        deleted.append(str(p) + "/")
        continue

    if p.suffix.lower() in {".sh", ".txt"} and p.name.startswith(prefixes_files):
        try:
            p.unlink()
            deleted.append(str(p))
        except FileNotFoundError:
            pass

if deleted:
    for item in deleted:
        print(f"BORRADO: {item}")
else:
    print("OK: no había temporales para borrar")
PY

  echo ""
  echo "---- checks ----"
  python -m py_compile AdminVideos/views.py AdminVideos/forms.py AdminVideos/models.py
  python manage.py check
  git --no-pager diff --check

  echo ""
  echo "---- add sólo pestañas ----"
  git add \
    AdminVideos/static/AdminVideos/css/mi-css.css \
    AdminVideos/templates/AdminVideos/base.html

  echo ""
  echo "---- staged diff resumido ----"
  git --no-pager diff --cached --stat

  echo ""
  echo "---- confirmar que media NO está staged ----"
  if git --no-pager diff --cached --name-only | grep -q '^media/'; then
    echo "ERROR: hay archivos media staged. Cancelo."
    exit 1
  fi
  echo "OK: no hay media staged"

  echo ""
  echo "---- commit ----"
  if git diff --cached --quiet; then
    echo "AVISO: no hay cambios staged para comitear."
  else
    git commit -m "Ajusta pestañas activas en modo oscuro"
  fi

  echo ""
  echo "---- estado antes de push ----"
  git --no-pager status --short
  git --no-pager log --oneline --decorate -6

  echo ""
  echo "---- push ----"
  if git push; then
    echo "OK: push completado"
  else
    echo "ERROR: git push falló."
    echo "Si aparece 'Could not resolve host: github.com', es conexión/DNS. El commit local quedó hecho; reintentá luego con: git push"
    exit 2
  fi

  echo ""
  echo "---- estado final ----"
  git --no-pager status --short
  git --no-pager log --oneline --decorate -6

  echo ""
  echo "=================================================="
  echo "Archivo generado: $LOG"
  echo "=================================================="

} > "$LOG" 2>&1

cat "$LOG"

echo ""
echo "---- archivo generado ----"
ls -lh "$LOG"
