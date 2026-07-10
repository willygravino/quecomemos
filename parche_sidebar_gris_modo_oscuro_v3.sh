#!/usr/bin/env bash
set -euo pipefail

LOG="parche_sidebar_gris_modo_oscuro_v3_$(date +%Y%m%d_%H%M%S).txt"

{
  echo "=================================================="
  echo "Parche sidebar gris en modo oscuro v3"
  echo "Fecha: $(date)"
  echo "Directorio: $(pwd)"
  echo "=================================================="

  echo ""
  echo "---- estado inicial ----"
  git --no-pager status --short || true

  echo ""
  echo "---- limpieza segura de logs/scripts sidebar anteriores no versionados ----"
  python - <<'PY'
from pathlib import Path
import subprocess

result = subprocess.run(
    ["git", "ls-files", "--others", "--exclude-standard"],
    check=True,
    text=True,
    capture_output=True,
)

prefixes = (
    "parche_sidebar_gris_modo_oscuro_v1",
    "parche_sidebar_gris_modo_oscuro_v2",
)

deleted = []
for raw in result.stdout.splitlines():
    p = Path(raw)
    if p.suffix.lower() not in {".sh", ".txt"}:
        continue
    if p.name.startswith(prefixes):
        try:
            p.unlink()
            deleted.append(str(p))
        except FileNotFoundError:
            pass

if deleted:
    for item in deleted:
        print(f"BORRADO: {item}")
else:
    print("OK: no había temporales v1/v2 para borrar")
PY

  python - <<'PY'
from pathlib import Path
import re
from datetime import datetime

base_path = Path("AdminVideos/templates/AdminVideos/base.html")
css_path = Path("AdminVideos/static/AdminVideos/css/mi-css.css")

for path in [base_path, css_path]:
    if not path.exists():
        raise SystemExit(f"No existe {path}")

base = base_path.read_text()
css = css_path.read_text()
stamp = datetime.now().strftime("%Y%m%d%H%M%S")

markers = [
    "/* ===== QC Bootstrap-first: sidebar gris modo oscuro ===== */",
    "/* ===== QC Bootstrap-first: sidebar gris modo oscuro v2 ===== */",
    "/* ===== QC Bootstrap-first: sidebar gris modo oscuro v3 ===== */",
]

for marker in markers:
    if marker in css:
        css = css.split(marker, 1)[0].rstrip() + "\n"
        print(f"OK: bloque previo removido desde: {marker}")

marker = "/* ===== QC Bootstrap-first: sidebar gris modo oscuro v3 ===== */"

block = r'''

/* ===== QC Bootstrap-first: sidebar gris modo oscuro v3 ===== */
/*
  Sólo modo oscuro.
  Sidebar gris, sin franja completa para el activo.
  Diferencia más clara:
  - no seleccionados más apagados;
  - hover intermedio;
  - activo mucho más brillante y redondel más marcado.
*/
[data-bs-theme="dark"] .sidebar,
[data-bs-theme="dark"] .sidebar.sidebar-dark,
[data-bs-theme="dark"] .bg-gradient-primary {
  background-color: var(--bs-tertiary-bg) !important;
  background-image: linear-gradient(180deg, #212529 0%, #16181b 100%) !important;
  color: var(--bs-body-color) !important;
}

[data-bs-theme="dark"] .sidebar .sidebar-brand,
[data-bs-theme="dark"] .sidebar .sidebar-brand:hover,
[data-bs-theme="dark"] .sidebar .sidebar-brand:focus,
[data-bs-theme="dark"] .sidebar .sidebar-brand-icon,
[data-bs-theme="dark"] .sidebar .sidebar-brand-text {
  color: var(--bs-emphasis-color) !important;
  background: transparent !important;
}

[data-bs-theme="dark"] .sidebar .sidebar-divider {
  border-top-color: rgba(255, 255, 255, .12) !important;
}

[data-bs-theme="dark"] .sidebar .sidebar-heading {
  color: rgba(255, 255, 255, .42) !important;
}

/* Links normales: más apagados para que el activo se note */
[data-bs-theme="dark"] .sidebar .nav-item .nav-link,
[data-bs-theme="dark"] .sidebar .nav-item .nav-link span,
[data-bs-theme="dark"] .sidebar .nav-item .nav-link i,
[data-bs-theme="dark"] .sidebar .menu-item,
[data-bs-theme="dark"] .sidebar .menu-item .item-text,
[data-bs-theme="dark"] .sidebar .menu-item .icon-wrap,
[data-bs-theme="dark"] .sidebar .menu-item .icon-wrap i {
  color: rgba(255, 255, 255, .50) !important;
}

/* Nunca pintar toda la fila */
[data-bs-theme="dark"] .sidebar .nav-item .nav-link,
[data-bs-theme="dark"] .sidebar .menu-item,
[data-bs-theme="dark"] .sidebar .nav-item.active .nav-link,
[data-bs-theme="dark"] .sidebar .menu-item.is-active {
  background-color: transparent !important;
  background-image: none !important;
  box-shadow: none !important;
}

/* Hover: sube, pero sigue por debajo del activo */
[data-bs-theme="dark"] .sidebar .nav-item .nav-link:hover,
[data-bs-theme="dark"] .sidebar .nav-item .nav-link:focus,
[data-bs-theme="dark"] .sidebar .menu-item:not(.is-active):hover {
  background-color: transparent !important;
  color: rgba(255, 255, 255, .78) !important;
}

[data-bs-theme="dark"] .sidebar .nav-item .nav-link:hover span,
[data-bs-theme="dark"] .sidebar .nav-item .nav-link:hover i,
[data-bs-theme="dark"] .sidebar .nav-item .nav-link:focus span,
[data-bs-theme="dark"] .sidebar .nav-item .nav-link:focus i,
[data-bs-theme="dark"] .sidebar .menu-item:not(.is-active):hover .item-text,
[data-bs-theme="dark"] .sidebar .menu-item:not(.is-active):hover .icon-wrap,
[data-bs-theme="dark"] .sidebar .menu-item:not(.is-active):hover .icon-wrap i {
  color: rgba(255, 255, 255, .78) !important;
}

/* Activo: claramente más brillante, sin franja */
[data-bs-theme="dark"] .sidebar .nav-item.active .nav-link,
[data-bs-theme="dark"] .sidebar .nav-item.active .nav-link span,
[data-bs-theme="dark"] .sidebar .nav-item.active .nav-link i,
[data-bs-theme="dark"] .sidebar .menu-item.is-active,
[data-bs-theme="dark"] .sidebar .menu-item.is-active .item-text,
[data-bs-theme="dark"] .sidebar .menu-item.is-active .icon-wrap,
[data-bs-theme="dark"] .sidebar .menu-item.is-active .icon-wrap i {
  color: rgba(255, 255, 255, .96) !important;
  font-weight: 600 !important;
}

/* Círculos/iconos custom del menú */
[data-bs-theme="dark"] .sidebar .icon-wrap {
  background-color: rgba(255, 255, 255, .045) !important;
  border-color: rgba(255, 255, 255, .10) !important;
}

/* Hover sólo intensifica el redondel, todavía suave */
[data-bs-theme="dark"] .sidebar .menu-item:not(.is-active):hover .icon-wrap,
[data-bs-theme="dark"] .sidebar .nav-item .nav-link:hover .icon-wrap {
  background-color: rgba(255, 255, 255, .12) !important;
  border-color: rgba(255, 255, 255, .25) !important;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, .04) !important;
}

/* Activo: redondel más brillante, sin franja de fondo */
[data-bs-theme="dark"] .sidebar .menu-item.is-active .icon-wrap,
[data-bs-theme="dark"] .sidebar .nav-item.active .icon-wrap {
  background-color: rgba(255, 255, 255, .28) !important;
  border-color: rgba(255, 255, 255, .56) !important;
  box-shadow:
    0 0 0 2px rgba(255, 255, 255, .12),
    0 .25rem .75rem rgba(0, 0, 0, .32) !important;
}

/* Si hay activos SB Admin sin icon-wrap, sólo texto/icono brillante; sin franja */
[data-bs-theme="dark"] .sidebar .nav-item.active {
  background-color: transparent !important;
}

/* Dropdowns/collapses internos de la sidebar */
[data-bs-theme="dark"] .sidebar .collapse-inner,
[data-bs-theme="dark"] .sidebar .dropdown-menu,
[data-bs-theme="dark"] .sidebar .sidebar-dropdown-menu {
  background-color: #1f2328 !important;
  border: 1px solid var(--bs-border-color) !important;
  box-shadow: 0 .6rem 1.25rem rgba(0, 0, 0, .38) !important;
}

[data-bs-theme="dark"] .sidebar .collapse-item,
[data-bs-theme="dark"] .sidebar .dropdown-item,
[data-bs-theme="dark"] .sidebar .sidebar-dropdown-menu .dropdown-item {
  color: rgba(255, 255, 255, .55) !important;
  background-color: transparent !important;
}

[data-bs-theme="dark"] .sidebar .collapse-item:hover,
[data-bs-theme="dark"] .sidebar .collapse-item:focus,
[data-bs-theme="dark"] .sidebar .dropdown-item:hover,
[data-bs-theme="dark"] .sidebar .dropdown-item:focus,
[data-bs-theme="dark"] .sidebar .sidebar-dropdown-menu .dropdown-item:hover,
[data-bs-theme="dark"] .sidebar .sidebar-dropdown-menu .dropdown-item:focus {
  color: rgba(255, 255, 255, .88) !important;
  background-color: rgba(255, 255, 255, .08) !important;
}

[data-bs-theme="dark"] .sidebar .collapse-item.active,
[data-bs-theme="dark"] .sidebar .dropdown-item.active,
[data-bs-theme="dark"] .sidebar .sidebar-dropdown-menu .dropdown-item.active {
  color: rgba(255, 255, 255, .96) !important;
  background-color: rgba(255, 255, 255, .12) !important;
}

/* Toggle de sidebar */
[data-bs-theme="dark"] #sidebarToggle,
[data-bs-theme="dark"] #sidebarToggleTop {
  color: rgba(255, 255, 255, .56) !important;
  background-color: rgba(255, 255, 255, .07) !important;
  border-color: rgba(255, 255, 255, .12) !important;
}

[data-bs-theme="dark"] #sidebarToggle:hover,
[data-bs-theme="dark"] #sidebarToggleTop:hover {
  color: rgba(255, 255, 255, .92) !important;
  background-color: rgba(255, 255, 255, .16) !important;
}
'''

css = css.rstrip() + block + "\n"

base, count_bust = re.subn(
    r"\{% static 'AdminVideos/css/mi-css\.css' %\}(?:\?v=[0-9A-Za-z_.-]+)?",
    "{% static 'AdminVideos/css/mi-css.css' %}?v=" + stamp,
    base,
    count=1,
)

if count_bust != 1:
    raise SystemExit("No pude actualizar cache bust de mi-css.css en base.html.")

css = css.rstrip() + "\n"

base_path.write_text(base)
css_path.write_text(css)

print("OK: bloque sidebar gris modo oscuro v3 agregado")
print(f"OK: cache bust mi-css.css actualizado a {stamp}")

base_now = base_path.read_text()
css_now = css_path.read_text()

checks = [
    ("Bootstrap 5.3.3 sigue cargado", "bootstrap@5.3.3" in base_now),
    ("data-bs-theme sigue en html", "data-bs-theme" in re.search(r"<html\b[^>]*>", base_now).group(0)),
    ("toggle topbar sigue", "qcBootstrapThemeToggle" in base_now),
    ("bloque sidebar v3 presente", marker in css_now),
    ("bloque sidebar v2 ausente", "QC Bootstrap-first: sidebar gris modo oscuro v2" not in css_now),
    ("sin franja activa", ".menu-item.is-active {\n  background-color: transparent" in css_now),
    ("no seleccionados apagados", "rgba(255, 255, 255, .50)" in css_now),
    ("activo brillante", "rgba(255, 255, 255, .96)" in css_now and "font-weight: 600" in css_now),
    ("activo icon-wrap más marcado", "rgba(255, 255, 255, .28)" in css_now and "rgba(255, 255, 255, .56)" in css_now),
    ("cache bust actualizado", f"mi-css.css' %}}?v={stamp}" in base_now),
]

ok = True
for name, result in checks:
    print(("OK: " if result else "ERROR: ") + name)
    ok = ok and result

if not ok:
    raise SystemExit("Fallaron validaciones.")

print("OK: validaciones completas")
PY

  echo ""
  echo "---- grep sidebar gris v3 ----"
  grep -n -A210 -B5 "QC Bootstrap-first: sidebar gris modo oscuro v3" \
    AdminVideos/static/AdminVideos/css/mi-css.css \
    | sed -n '1,290p' || true

  echo ""
  echo "---- checks ----"
  python -m py_compile AdminVideos/views.py AdminVideos/forms.py AdminVideos/models.py
  python manage.py check
  git --no-pager diff --check

  echo ""
  echo "---- diff resumido ----"
  git --no-pager diff --stat -- \
    AdminVideos/static/AdminVideos/css/mi-css.css \
    AdminVideos/templates/AdminVideos/base.html

  echo ""
  echo "---- git status ----"
  git --no-pager status --short

  echo ""
  echo "=================================================="
  echo "Archivo generado: $LOG"
  echo "=================================================="

} > "$LOG" 2>&1

cat "$LOG"

echo ""
echo "---- archivo generado ----"
ls -lh "$LOG"
