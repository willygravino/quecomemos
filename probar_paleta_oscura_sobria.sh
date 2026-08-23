#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

python - <<'PY'
from datetime import datetime
from pathlib import Path
from shutil import copy2
import re

css = Path("AdminVideos/static/AdminVideos/css/mi-css.css")
base = Path("AdminVideos/templates/AdminVideos/base.html")

if not css.is_file() or not base.is_file():
    raise SystemExit("DETENIDO: ejecutá este archivo desde la carpeta raíz de quecomemos.")

texto_css = css.read_text(encoding="utf-8")
texto_base = base.read_text(encoding="utf-8")

inicio = "/* ===== QC: paleta oscura sobria (inicio) ===== */"
fin = "/* ===== QC: paleta oscura sobria (fin) ===== */"

if inicio in texto_css or fin in texto_css:
    raise SystemExit("DETENIDO: la paleta de prueba ya está instalada.")

patron_version = re.compile(r"(mi-css\.css'\s*%\}\?v=)(\d+)")
if len(patron_version.findall(texto_base)) != 1:
    raise SystemExit("DETENIDO: no se pudo identificar de forma única la versión de mi-css.css en base.html.")

# Limpia un fragmento accidental detectado en el diagnóstico.
texto_css = texto_css.replace(".album,git p", ".album")

bloque = r'''

/* ===== QC: paleta oscura sobria (inicio) ===== */
/*
  Paleta exclusiva del modo oscuro.
  Conserva el significado de éxito, advertencia y peligro,
  pero elimina la saturación predeterminada de Bootstrap.
*/
[data-bs-theme="dark"] {
  --qc-primary: #68758c;
  --qc-primary-hover: #78869e;
  --qc-primary-soft: #2b303a;
  --qc-primary-border: #77839a;

  --qc-secondary: #555d69;
  --qc-secondary-hover: #656e7b;

  --qc-success: #477c62;
  --qc-success-hover: #568d70;
  --qc-success-soft: #20352b;

  --qc-info: #52798a;
  --qc-info-hover: #628b9d;
  --qc-info-soft: #22343c;

  --qc-warning: #a57d3e;
  --qc-warning-hover: #b88d49;
  --qc-warning-soft: #3d3220;

  --qc-danger: #a65353;
  --qc-danger-hover: #ba6262;
  --qc-danger-soft: #402728;

  --qc-control-text: #f3f4f6;
  --qc-focus-ring: rgba(120, 134, 158, .28);

  --bs-primary: var(--qc-primary);
  --bs-primary-rgb: 104, 117, 140;
  --bs-secondary: var(--qc-secondary);
  --bs-secondary-rgb: 85, 93, 105;
  --bs-success: var(--qc-success);
  --bs-success-rgb: 71, 124, 98;
  --bs-info: var(--qc-info);
  --bs-info-rgb: 82, 121, 138;
  --bs-warning: var(--qc-warning);
  --bs-warning-rgb: 165, 125, 62;
  --bs-danger: var(--qc-danger);
  --bs-danger-rgb: 166, 83, 83;
}

/* Primary: acciones principales, enlaces, fondos y bordes. */
[data-bs-theme="dark"] .btn-primary {
  color: var(--qc-control-text) !important;
  background-color: var(--qc-primary) !important;
  border-color: var(--qc-primary) !important;
}

[data-bs-theme="dark"] .btn-primary:hover,
[data-bs-theme="dark"] .btn-primary:focus,
[data-bs-theme="dark"] .btn-primary:active,
[data-bs-theme="dark"] .btn-primary.active,
[data-bs-theme="dark"] .show > .btn-primary.dropdown-toggle {
  color: #fff !important;
  background-color: var(--qc-primary-hover) !important;
  border-color: var(--qc-primary-hover) !important;
}

[data-bs-theme="dark"] .btn-primary:focus,
[data-bs-theme="dark"] .btn-primary:focus-visible {
  box-shadow: 0 0 0 .2rem var(--qc-focus-ring) !important;
}

[data-bs-theme="dark"] .btn-outline-primary {
  color: #aeb8ca !important;
  border-color: var(--qc-primary-border) !important;
}

[data-bs-theme="dark"] .btn-outline-primary:hover,
[data-bs-theme="dark"] .btn-outline-primary:focus,
[data-bs-theme="dark"] .btn-outline-primary:active,
[data-bs-theme="dark"] .btn-outline-primary.active {
  color: #fff !important;
  background-color: var(--qc-primary) !important;
  border-color: var(--qc-primary) !important;
}

[data-bs-theme="dark"] .bg-primary,
[data-bs-theme="dark"] .text-bg-primary {
  color: #fff !important;
  background-color: var(--qc-primary) !important;
}

[data-bs-theme="dark"] .text-primary,
[data-bs-theme="dark"] .link-primary {
  color: #aeb8ca !important;
}

[data-bs-theme="dark"] .border-primary {
  border-color: var(--qc-primary-border) !important;
}

[data-bs-theme="dark"] .alert-primary,
[data-bs-theme="dark"] .list-group-item-primary,
[data-bs-theme="dark"] .table-primary {
  color: #d9dee7 !important;
  background-color: var(--qc-primary-soft) !important;
  border-color: #414957 !important;
}

/* Secondary: gris neutro y menos azulado. */
[data-bs-theme="dark"] .btn-secondary {
  color: var(--qc-control-text) !important;
  background-color: var(--qc-secondary) !important;
  border-color: var(--qc-secondary) !important;
}

[data-bs-theme="dark"] .btn-secondary:hover,
[data-bs-theme="dark"] .btn-secondary:focus,
[data-bs-theme="dark"] .btn-secondary:active {
  color: #fff !important;
  background-color: var(--qc-secondary-hover) !important;
  border-color: var(--qc-secondary-hover) !important;
}

/* Colores semánticos suavizados: conservan su función. */
[data-bs-theme="dark"] .btn-success,
[data-bs-theme="dark"] .bg-success,
[data-bs-theme="dark"] .text-bg-success {
  color: #fff !important;
  background-color: var(--qc-success) !important;
  border-color: var(--qc-success) !important;
}

[data-bs-theme="dark"] .btn-success:hover,
[data-bs-theme="dark"] .btn-success:focus,
[data-bs-theme="dark"] .btn-success:active {
  background-color: var(--qc-success-hover) !important;
  border-color: var(--qc-success-hover) !important;
}

[data-bs-theme="dark"] .text-success { color: #7fb797 !important; }
[data-bs-theme="dark"] .border-success { border-color: #609174 !important; }
[data-bs-theme="dark"] .alert-success,
[data-bs-theme="dark"] .list-group-item-success {
  color: #bcd9c8 !important;
  background-color: var(--qc-success-soft) !important;
  border-color: #355843 !important;
}

[data-bs-theme="dark"] .btn-info,
[data-bs-theme="dark"] .bg-info,
[data-bs-theme="dark"] .text-bg-info {
  color: #fff !important;
  background-color: var(--qc-info) !important;
  border-color: var(--qc-info) !important;
}

[data-bs-theme="dark"] .btn-info:hover,
[data-bs-theme="dark"] .btn-info:focus,
[data-bs-theme="dark"] .btn-info:active {
  background-color: var(--qc-info-hover) !important;
  border-color: var(--qc-info-hover) !important;
}

[data-bs-theme="dark"] .text-info { color: #86adbd !important; }
[data-bs-theme="dark"] .alert-info,
[data-bs-theme="dark"] .list-group-item-info {
  color: #c0d7df !important;
  background-color: var(--qc-info-soft) !important;
  border-color: #395662 !important;
}

[data-bs-theme="dark"] .btn-warning,
[data-bs-theme="dark"] .bg-warning,
[data-bs-theme="dark"] .text-bg-warning {
  color: #fff !important;
  background-color: var(--qc-warning) !important;
  border-color: var(--qc-warning) !important;
}

[data-bs-theme="dark"] .btn-warning:hover,
[data-bs-theme="dark"] .btn-warning:focus,
[data-bs-theme="dark"] .btn-warning:active {
  background-color: var(--qc-warning-hover) !important;
  border-color: var(--qc-warning-hover) !important;
}

[data-bs-theme="dark"] .text-warning { color: #d4ad70 !important; }
[data-bs-theme="dark"] .alert-warning,
[data-bs-theme="dark"] .list-group-item-warning {
  color: #ead3ab !important;
  background-color: var(--qc-warning-soft) !important;
  border-color: #66512e !important;
}

[data-bs-theme="dark"] .btn-danger,
[data-bs-theme="dark"] .bg-danger,
[data-bs-theme="dark"] .text-bg-danger {
  color: #fff !important;
  background-color: var(--qc-danger) !important;
  border-color: var(--qc-danger) !important;
}

[data-bs-theme="dark"] .btn-danger:hover,
[data-bs-theme="dark"] .btn-danger:focus,
[data-bs-theme="dark"] .btn-danger:active {
  background-color: var(--qc-danger-hover) !important;
  border-color: var(--qc-danger-hover) !important;
}

[data-bs-theme="dark"] .text-danger { color: #d17b7b !important; }
[data-bs-theme="dark"] .border-danger { border-color: #b46161 !important; }
[data-bs-theme="dark"] .alert-danger,
[data-bs-theme="dark"] .list-group-item-danger {
  color: #edc1c1 !important;
  background-color: var(--qc-danger-soft) !important;
  border-color: #704040 !important;
}

/* Los controles deshabilitados continúan siendo legibles. */
[data-bs-theme="dark"] .btn:disabled,
[data-bs-theme="dark"] .btn.disabled {
  opacity: .48 !important;
}
/* ===== QC: paleta oscura sobria (fin) ===== */
'''

texto_css = texto_css.rstrip() + "\n" + bloque.strip() + "\n"
nueva_version = datetime.now().strftime("%Y%m%d%H%M%S")
texto_base = patron_version.sub(rf"\g<1>{nueva_version}", texto_base, count=1)

respaldo = Path.home() / "Desktop" / f"respaldo_paleta_oscura_{datetime.now():%Y%m%d_%H%M%S}"
respaldo.mkdir(parents=True, exist_ok=False)
copy2(css, respaldo / css.name)
copy2(base, respaldo / base.name)

css.write_text(texto_css, encoding="utf-8")
base.write_text(texto_base, encoding="utf-8")

print("OK: se instaló la paleta oscura sobria de prueba.")
print("Se conservaron los colores semánticos, pero con menor saturación.")
print("Se corrigió el fragmento accidental «git p» si estaba presente.")
print(f"Versión nueva del CSS: {nueva_version}")
print(f"Respaldo: {respaldo}")
PY

python manage.py check
git --no-pager diff --check

echo
echo "=== ARCHIVOS MODIFICADOS ==="
git status --short

echo
echo "Listo para probar. No se hizo commit ni push."
