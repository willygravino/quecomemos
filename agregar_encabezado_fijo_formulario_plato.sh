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

if "plato-form-sticky-header" in texto_formulario:
    raise SystemExit("DETENIDO: el encabezado fijo ya existe. No se modificó ningún archivo.")

if texto_formulario.count('id="platoForm"') != 1:
    raise SystemExit("DETENIDO: no se encontró de forma única #platoForm. No se modificó ningún archivo.")


# Insertar justo después del CSRF, dentro del formulario real.
marcador = "                {% csrf_token %}"
if texto_formulario.count(marcador) != 1:
    raise SystemExit("DETENIDO: no se encontró de forma única el CSRF del formulario. No se modificó ningún archivo.")

encabezado = r'''

                <header class="plato-form-sticky-header" aria-label="Acciones principales del formulario">
                  <div class="plato-form-sticky-context">
                    <span class="plato-form-sticky-eyebrow">
                      {% if form.instance.pk %}Editando plato{% else %}Nuevo plato{% endif %}
                    </span>
                    <h1 class="plato-form-sticky-title">
                      {% if form.instance.pk %}
                        {{ form.instance.nombre_plato|default:"Plato" }}
                      {% else %}
                        {% if tipopag == "Principal" %}Plato principal
                        {% elif tipopag == "Guarnicion" %}Guarnición
                        {% elif tipopag == "Ingrediente de picada" %}Ingrediente de picada
                        {% elif tipopag == "Comerafuera" %}Lugar para comer afuera
                        {% elif tipopag == "Delivery" %}Delivery
                        {% else %}{{ tipopag|default:"Plato" }}{% endif %}
                      {% endif %}
                    </h1>
                  </div>

                  <div class="plato-form-sticky-actions">
                    <a href="{{ request.GET.return_to|default:'/' }}"
                       class="btn btn-sm btn-outline-secondary js-close-plato-form">
                      <i class="fa-solid fa-xmark me-1" aria-hidden="true"></i>
                      <span class="d-none d-sm-inline">Cancelar</span>
                    </a>
                    <button type="submit" class="btn btn-sm btn-success">
                      <i class="fa-solid fa-floppy-disk me-1" aria-hidden="true"></i>
                      Guardar
                    </button>
                  </div>
                </header>
'''

texto_formulario = texto_formulario.replace(marcador, marcador + encabezado, 1)


css_encabezado = r'''

/* ===== QC: encabezado fijo del formulario de platos ===== */
.plato-form-sticky-header {
  position: sticky;
  top: .5rem;
  z-index: 1020;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin: -.15rem 0 1rem;
  padding: .58rem .7rem;
  color: var(--bs-body-color);
  background: color-mix(in srgb, var(--bs-body-bg) 94%, transparent);
  border: 1px solid var(--bs-border-color);
  border-radius: .75rem;
  box-shadow: 0 .28rem .8rem rgba(0, 0, 0, .10);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.plato-form-sticky-context {
  min-width: 0;
}

.plato-form-sticky-eyebrow {
  display: block;
  margin-bottom: .08rem;
  color: var(--bs-secondary-color);
  font-size: .62rem;
  font-weight: 750;
  letter-spacing: .075em;
  line-height: 1.1;
  text-transform: uppercase;
}

.plato-form-sticky-title {
  max-width: 42rem;
  margin: 0;
  overflow: hidden;
  color: var(--bs-body-color);
  font-size: 1rem;
  font-weight: 750;
  line-height: 1.2;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.plato-form-sticky-actions {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  gap: .4rem;
}

.plato-form-sticky-actions .btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 2.15rem;
}

@media (max-width: 575.98px) {
  .plato-form-page {
    margin-top: .6rem !important;
  }

  .plato-form-sticky-header {
    top: .25rem;
    gap: .45rem;
    margin-inline: -.25rem;
    padding: .48rem .5rem;
    border-radius: .6rem;
  }

  .plato-form-sticky-eyebrow {
    font-size: .56rem;
  }

  .plato-form-sticky-title {
    max-width: 9.5rem;
    font-size: .84rem;
  }

  .plato-form-sticky-actions {
    gap: .25rem;
  }

  .plato-form-sticky-actions .btn {
    min-height: 2rem;
    padding-inline: .55rem;
  }
}
'''

texto_css = texto_css.rstrip() + css_encabezado.rstrip() + "\n"


# Renovar caché del CSS.
version = datetime.now().strftime("%Y%m%d%H%M%S")
texto_base, cantidad = re.subn(
    r"(AdminVideos/css/mi-css\.css' %\}\?v=)[^\"']+",
    rf"\g<1>{version}",
    texto_base,
    count=1,
)
if cantidad != 1:
    raise SystemExit("DETENIDO: no se pudo actualizar la versión del CSS. No se modificó ningún archivo.")


# Respaldo y escritura final.
respaldo = Path.home() / "Desktop" / f"respaldo_encabezado_formulario_{version}"
for ruta in (formulario, css, base):
    destino = respaldo / ruta
    destino.parent.mkdir(parents=True, exist_ok=True)
    copy2(ruta, destino)

formulario.write_text(texto_formulario, encoding="utf-8")
css.write_text(texto_css, encoding="utf-8")
base.write_text(texto_base, encoding="utf-8")

print("OK: el formulario ahora tiene encabezado fijo.")
print("OK: muestra si se está creando o editando y el tipo/nombre del plato.")
print("OK: Cancelar y Guardar permanecen accesibles durante el desplazamiento.")
print("No se modificaron rutas, vistas, validaciones ni modales internos.")
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
