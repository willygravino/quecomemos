#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

python - <<'PY'
from datetime import datetime
from pathlib import Path
from shutil import copy2
import re

formulario = Path("AdminVideos/templates/AdminVideos/plato_form_inner.html")
css = Path("AdminVideos/static/AdminVideos/css/mi-css.css")
base = Path("AdminVideos/templates/AdminVideos/base.html")

faltantes = [str(ruta) for ruta in (formulario, css, base) if not ruta.is_file()]
if faltantes:
    raise SystemExit("DETENIDO: faltan archivos necesarios:\n- " + "\n- ".join(faltantes))

texto_formulario = formulario.read_text(encoding="utf-8")
texto_css = css.read_text(encoding="utf-8")
texto_base = base.read_text(encoding="utf-8")


# 1. Retirar por completo el encabezado fijo de la prueba anterior.
texto_formulario, cantidad = re.subn(
    r'''\n\s*<header class="plato-form-sticky-header".*?</header>\n''',
    "\n",
    texto_formulario,
    count=1,
    flags=re.S,
)
if cantidad != 1:
    raise SystemExit(
        f"DETENIDO: se esperaba 1 encabezado fijo y se encontraron {cantidad}. "
        "No se modificó ningún archivo."
    )


# 2. Retirar todo el CSS perteneciente a esa prueba.
texto_css, cantidad = re.subn(
    r'''\n/\* ===== QC: encabezado fijo del formulario de platos ===== \*/.*\Z''',
    "\n",
    texto_css,
    count=1,
    flags=re.S,
)
if cantidad != 1:
    raise SystemExit(
        f"DETENIDO: se esperaba 1 bloque CSS del encabezado fijo y se encontraron {cantidad}. "
        "No se modificó ningún archivo."
    )


# 3. Quitar la X superior, que quedaría redundante con Volver.
patron_cerrar = re.compile(
    r'''\n\s*<!-- CERRAR -->\s*<a href="\{\{ request\.GET\.return_to\|default:'/' \}\}"\s*class="plato-action-btn text-muted js-close-plato-form"\s*title="Cerrar">\s*<i class="fa-solid fa-xmark"></i>\s*</a>''',
    re.S,
)
texto_formulario, cantidad = patron_cerrar.subn("", texto_formulario, count=1)
if cantidad not in (0, 1):
    raise SystemExit(
        f"DETENIDO: se esperaba como máximo 1 control superior Cerrar y se encontraron {cantidad}. "
        "No se modificó ningún archivo."
    )


# 4. Agregar Volver a la izquierda, alineado con el primer título del formulario.
marcador = '''                <section class="plato-form-section plato-form-section-principal">
                  <div class="plato-form-section-header">
                    <span class="plato-form-section-icon" aria-hidden="true">'''

nuevo = '''                <section class="plato-form-section plato-form-section-principal">
                  <div class="plato-form-section-header">
                    <a href="{{ request.GET.return_to|default:'/' }}"
                       class="plato-form-back-btn js-close-plato-form"
                       title="Volver"
                       aria-label="Volver">
                      <i class="fa-solid fa-arrow-left" aria-hidden="true"></i>
                      <span>Volver</span>
                    </a>
                    <span class="plato-form-section-icon" aria-hidden="true">'''

if texto_formulario.count(marcador) != 1:
    raise SystemExit(
        f"DETENIDO: se esperaba 1 sección principal y se encontraron {texto_formulario.count(marcador)}. "
        "No se modificó ningún archivo."
    )
texto_formulario = texto_formulario.replace(marcador, nuevo, 1)


css_volver = r'''

/* ===== QC: volver desde el formulario de platos ===== */
.plato-form-back-btn {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  gap: .32rem;
  min-height: 2.1rem;
  padding: .32rem .55rem;
  color: var(--bs-secondary-color);
  font-size: .74rem;
  font-weight: 700;
  line-height: 1;
  text-decoration: none;
  background: var(--bs-body-bg);
  border: 1px solid var(--bs-border-color);
  border-radius: 999rem;
  transition: color .15s ease, background-color .15s ease, border-color .15s ease;
}

.plato-form-back-btn:hover,
.plato-form-back-btn:focus {
  color: var(--bs-body-color);
  background: var(--bs-secondary-bg);
  border-color: var(--bs-secondary-color);
}

@media (max-width: 575.98px) {
  .plato-form-section-header {
    gap: .5rem;
  }

  .plato-form-back-btn {
    width: 2rem;
    height: 2rem;
    min-height: 2rem;
    padding: 0;
  }

  .plato-form-back-btn span {
    display: none;
  }
}
'''
texto_css = texto_css.rstrip() + css_volver.rstrip() + "\n"


# 5. Renovar caché del CSS.
version = datetime.now().strftime("%Y%m%d%H%M%S")
texto_base, cantidad = re.subn(
    r"(AdminVideos/css/mi-css\.css' %\}\?v=)[^\"']+",
    rf"\g<1>{version}",
    texto_base,
    count=1,
)
if cantidad != 1:
    raise SystemExit("DETENIDO: no se pudo actualizar la versión del CSS. No se modificó ningún archivo.")


# 6. Validar que no quedó nada del encabezado fijo.
if "plato-form-sticky" in texto_formulario or "plato-form-sticky" in texto_css:
    raise SystemExit("DETENIDO: quedaron referencias al encabezado fijo. No se modificó ningún archivo.")


# 7. Respaldo y escritura final.
respaldo = Path.home() / "Desktop" / f"respaldo_boton_volver_formulario_{version}"
for ruta in (formulario, css, base):
    destino = respaldo / ruta
    destino.parent.mkdir(parents=True, exist_ok=True)
    copy2(ruta, destino)

formulario.write_text(texto_formulario, encoding="utf-8")
css.write_text(texto_css, encoding="utf-8")
base.write_text(texto_base, encoding="utf-8")

print("OK: se retiró completamente el encabezado fijo.")
print("OK: se retiró la X superior redundante.")
print("OK: Volver quedó alineado a la izquierda con Datos principales.")
print("Los botones finales Cancelar y Guardar plato se conservaron.")
print(f"Versión nueva del CSS: {version}")
print(f"Respaldo: {respaldo}")
PY

python manage.py check
python manage.py makemigrations --check
git --no-pager diff --check

echo
echo "=== ARCHIVOS MODIFICADOS ==="
git status --short

echo
echo "Listo para probar. No se hizo commit ni push."
