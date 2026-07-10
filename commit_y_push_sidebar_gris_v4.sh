#!/usr/bin/env bash
set -euo pipefail

LOG="commit_y_push_sidebar_gris_v4_$(date +%Y%m%d_%H%M%S).txt"

{
  echo "=================================================="
  echo "Commit + push sidebar gris v4"
  echo "Fecha: $(date)"
  echo "Directorio: $(pwd)"
  echo "=================================================="

  echo ""
  echo "---- estado inicial ----"
  git --no-pager status --short || true

  echo ""
  echo "---- verificar que la v4 está aplicada ----"
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
    ("Bootstrap 5.3.3 sigue cargado", "bootstrap@5.3.3" in base),
    ("data-bs-theme sigue en html", "data-bs-theme" in re.search(r"<html\b[^>]*>", base).group(0)),
    ("toggle topbar sigue", "qcBootstrapThemeToggle" in base),
    ("sidebar gris v4 presente", "QC Bootstrap-first: sidebar gris modo oscuro v4" in css),
    ("sidebar v2/v3 ausentes", "QC Bootstrap-first: sidebar gris modo oscuro v2" not in css and "QC Bootstrap-first: sidebar gris modo oscuro v3" not in css),
    ("no seleccionados apagados", "rgba(255, 255, 255, .38)" in css),
    ("activo texto claro", "rgba(255, 255, 255, .98)" in css),
    ("activo azul", "rgba(var(--bs-info-rgb), .34)" in css and "rgba(var(--bs-info-rgb), .92)" in css),
    ("sin franja activa de fila", ".menu-item.is-active {\n  background-color: transparent" in css),
]

ok = True
for name, result in checks:
    print(("OK: " if result else "ERROR: ") + name)
    ok = ok and result

if not ok:
    raise SystemExit("Falló la verificación de sidebar v4. No comiteo.")
PY

  echo ""
  echo "---- limpiar temporales de parches/logs sidebar no versionados ----"
  python - <<'PY'
from pathlib import Path
import subprocess

result = subprocess.run(
    ["git", "ls-files", "--others", "--exclude-standard"],
    check=True,
    text=True,
    capture_output=True,
)

deleted = []
for raw in result.stdout.splitlines():
    p = Path(raw)
    if p.suffix.lower() not in {".sh", ".txt"}:
        continue
    if p.name.startswith("parche_sidebar_gris_modo_oscuro_v"):
        try:
            p.unlink()
            deleted.append(str(p))
        except FileNotFoundError:
            pass

if deleted:
    for item in deleted:
        print(f"BORRADO: {item}")
else:
    print("OK: no había temporales sidebar para borrar")
PY

  echo ""
  echo "---- checks ----"
  python -m py_compile AdminVideos/views.py AdminVideos/forms.py AdminVideos/models.py
  python manage.py check
  git --no-pager diff --check

  echo ""
  echo "---- diff resumido antes de commit ----"
  git --no-pager diff --stat -- \
    AdminVideos/static/AdminVideos/css/mi-css.css \
    AdminVideos/templates/AdminVideos/base.html

  echo ""
  echo "---- add ----"
  git add \
    AdminVideos/static/AdminVideos/css/mi-css.css \
    AdminVideos/templates/AdminVideos/base.html

  echo ""
  echo "---- staged diff resumido ----"
  git --no-pager diff --cached --stat

  echo ""
  echo "---- commit ----"
  if git diff --cached --quiet; then
    echo "AVISO: no hay cambios staged para comitear."
  else
    git commit -m "Ajusta sidebar gris en modo oscuro"
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
    echo "Puede ser conexión/DNS si aparece algo como 'Could not resolve host: github.com'."
    echo "El commit local queda hecho; podés reintentar luego con: git push"
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
