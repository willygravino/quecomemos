#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
cd "$ROOT"

if [ ! -f manage.py ] || [ ! -d .git ]; then
  echo "ERROR: ejecutá este script desde la raíz del repo Django."
  exit 1
fi

if [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
elif command -v python >/dev/null 2>&1; then
  PY="python"
else
  PY="python3"
fi

BASE="AdminVideos/templates/AdminVideos/base.html"
LISTA="AdminVideos/templates/AdminVideos/lista_de_compras.html"
FORM="AdminVideos/templates/AdminVideos/plato_form_inner.html"
VIEWS="AdminVideos/views.py"
NAVPY="AdminVideos/navigation.py"
NAVJS="AdminVideos/static/AdminVideos/js/navigation.js"

for f in "$BASE" "$LISTA" "$FORM" "$VIEWS"; do
  [ -f "$f" ] || { echo "ERROR: falta $f"; exit 1; }
done

STAMP="$(date +"%Y%m%d_%H%M%S")"
BACKUP_DIR=".backup_limpieza_navegacion_v2_${STAMP}"
for f in "$BASE" "$LISTA" "$FORM" "$VIEWS"; do
  mkdir -p "$BACKUP_DIR/$(dirname "$f")"
  cp "$f" "$BACKUP_DIR/$f"
done
for f in "$NAVPY" "$NAVJS"; do
  if [ -f "$f" ]; then
    mkdir -p "$BACKUP_DIR/$(dirname "$f")"
    cp "$f" "$BACKUP_DIR/$f"
  fi
done
git diff > "$BACKUP_DIR/pre_patch.diff" || true
git status --short > "$BACKUP_DIR/pre_patch_status.txt" || true

"$PY" - <<'PY'
from pathlib import Path
import re

base_path = Path("AdminVideos/templates/AdminVideos/base.html")
lista_path = Path("AdminVideos/templates/AdminVideos/lista_de_compras.html")
form_path = Path("AdminVideos/templates/AdminVideos/plato_form_inner.html")
views_path = Path("AdminVideos/views.py")
navpy_path = Path("AdminVideos/navigation.py")
navjs_path = Path("AdminVideos/static/AdminVideos/js/navigation.js")

base = base_path.read_text(encoding="utf-8")
lista = lista_path.read_text(encoding="utf-8")
form = form_path.read_text(encoding="utf-8")
views = views_path.read_text(encoding="utf-8")

# ------------------------------------------------------------
# Helpers para editar sólo una clase concreta.
# ------------------------------------------------------------
def class_bounds(text, class_name):
    start_match = re.search(rf"(?m)^class {re.escape(class_name)}\b", text)
    if not start_match:
        raise RuntimeError(f"No encuentro class {class_name}.")
    next_match = re.search(r"(?m)^class \w+", text[start_match.end():])
    end = start_match.end() + next_match.start() if next_match else len(text)
    return start_match.start(), end

def replace_in_class(text, class_name, old, new, *, label):
    start, end = class_bounds(text, class_name)
    block = text[start:end]
    if new in block:
        return text
    if old not in block:
        raise RuntimeError(f"No encuentro {label} dentro de {class_name}.")
    block = block.replace(old, new, 1)
    return text[:start] + block + text[end:]

# ============================================================
# 1) Contenido final de los dos helpers nuevos.
#    Se escribe recién al FINAL si todo valida.
# ============================================================
navpy = """from __future__ import annotations

from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme


def get_safe_return_to(
    request,
    *,
    fallback_url_name: str | None = None,
    include_referer: bool = True,
) -> str:
    \"\"\"Resuelve un destino interno seguro para volver después de una acción.

    Prioridad: POST return_to -> GET return_to -> Referer opcional -> fallback.
    Nunca devuelve una URL perteneciente a otro host.
    \"\"\"
    candidates = [
        request.POST.get("return_to"),
        request.GET.get("return_to"),
    ]

    if include_referer:
        candidates.append(request.META.get("HTTP_REFERER"))

    for candidate in candidates:
        candidate = (candidate or "").strip()
        if not candidate:
            continue

        if url_has_allowed_host_and_scheme(
            candidate,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return candidate

    if fallback_url_name:
        return reverse(fallback_url_name)

    return ""
"""

navjs = """/* Navegación efímera entre pantallas.

   data-nav-store-current=\"clave\" guarda la URL actual antes de navegar.
   data-nav-return=\"clave\" vuelve a esa URL.
   El href del enlace de retorno queda siempre como fallback.
*/
(function () {
  "use strict";

  const PREFIX = "qc_nav_origin:";

  function storageKey(name) {
    return PREFIX + name;
  }

  function setOrigin(name) {
    try {
      sessionStorage.setItem(storageKey(name), window.location.href);
    } catch (error) {
      // Sin storage, el enlace sigue funcionando normalmente.
    }
  }

  function consumeOrigin(name) {
    try {
      const key = storageKey(name);
      const value = sessionStorage.getItem(key) || "";
      sessionStorage.removeItem(key);
      return value;
    } catch (error) {
      return "";
    }
  }

  document.addEventListener("click", function (event) {
    const storeLink = event.target.closest("[data-nav-store-current]");
    if (storeLink) {
      const name = (storeLink.dataset.navStoreCurrent || "").trim();
      if (name) setOrigin(name);
      return;
    }

    const returnLink = event.target.closest("[data-nav-return]");
    if (!returnLink) return;

    const name = (returnLink.dataset.navReturn || "").trim();
    if (!name) return;

    const rawOrigin = consumeOrigin(name);
    if (!rawOrigin) return;

    try {
      const destination = new URL(rawOrigin, window.location.origin);
      if (destination.origin !== window.location.origin) return;
      if (destination.href === window.location.href) return;

      event.preventDefault();
      window.location.assign(destination.href);
    } catch (error) {
      // href del enlace = fallback seguro.
    }
  });
})();
"""

# ============================================================
# 2) base.html: convertir navegación inline en declarativa.
# ============================================================
old_inline = ' onclick="try{sessionStorage.setItem(\'qc_lista_compras_origen\', window.location.href);}catch(e){}"'
if old_inline in base:
    base = base.replace(old_inline, ' data-nav-store-current="lista-compras"', 1)
elif 'data-nav-store-current="lista-compras"' not in base:
    raise RuntimeError("No encuentro ni el onclick viejo ni el atributo nuevo del carrito.")

nav_include = '<script src="{% static \'AdminVideos/js/navigation.js\' %}"></script>'
if nav_include not in base:
    if "</body>" not in base:
        raise RuntimeError("No encuentro </body> en base.html.")
    base = base.replace("</body>", "  " + nav_include + "\n</body>", 1)

# ============================================================
# 3) Lista de compras: sólo atributo declarativo, sin script.
# ============================================================
if 'data-nav-return="lista-compras"' not in lista:
    old_href = 'href="{% url \'filtro-de-platos\' %}"'
    marker = 'id="btn-volver-lista-compras"'
    pos = lista.find(marker)
    if pos == -1:
        raise RuntimeError("No encuentro el botón Volver.")
    href_pos = lista.find(old_href, pos)
    if href_pos == -1:
        raise RuntimeError("No encuentro el href fallback de Volver.")
    lista = lista[:href_pos] + old_href + ' data-nav-return="lista-compras"' + lista[href_pos + len(old_href):]

lista = re.sub(
    r'\s*<script id="volver-lista-compras-origen">[\s\S]*?</script>\s*',
    "\n",
    lista,
    count=1,
)

# ============================================================
# 4) views.py: importar helper común.
# ============================================================
import_line = "from AdminVideos.navigation import get_safe_return_to\n"
if import_line not in views:
    marker = "from django.utils.http import url_has_allowed_host_and_scheme\n"
    if marker not in views:
        raise RuntimeError("No encuentro el import actual del validador de URL.")
    views = views.replace(marker, marker + import_line, 1)

# eliminar_plato: seguro + fallback conocido.
old_delete = '    return_to = request.POST.get("return_to") or request.GET.get("return_to")\n'
new_delete = (
    '    return_to = get_safe_return_to(\n'
    '        request,\n'
    '        fallback_url_name="filtro-de-platos",\n'
    '        include_referer=False,\n'
    '    )\n'
)
if new_delete not in views:
    if old_delete not in views:
        raise RuntimeError("No encuentro return_to de eliminar_plato.")
    views = views.replace(old_delete, new_delete, 1)

old_delete_redirect = (
    '    if return_to:\n'
    '        return redirect(return_to)\n\n'
    '    return redirect("filtro-de-platos")\n'
)
new_delete_redirect = '    return redirect(return_to)\n'
if old_delete_redirect in views:
    # sólo el primero posterior a eliminar_plato según el código auditado
    delete_start = views.find("def eliminar_plato(")
    delete_end = views.find("\nclass ", delete_start)
    delete_block = views[delete_start:delete_end]
    if old_delete_redirect not in delete_block:
        raise RuntimeError("El redirect esperado no pertenece a eliminar_plato.")
    delete_block = delete_block.replace(old_delete_redirect, new_delete_redirect, 1)
    views = views[:delete_start] + delete_block + views[delete_end:]

# ============================================================
# 5) PlatoCreate: misma semántica actual (sin fallback forzado).
# ============================================================
old_create_return = (
    '        return_to = (\n'
    '            self.request.POST.get("return_to")\n'
    '            or self.request.GET.get("return_to")\n'
    '            or self.request.META.get("HTTP_REFERER")\n'
    '            or ""\n'
    '        )\n\n'
    '        if return_to and not url_has_allowed_host_and_scheme(return_to, allowed_hosts={self.request.get_host()}):\n'
    '            return_to = ""\n'
)
new_create_return = '        return_to = get_safe_return_to(self.request)\n'
views = replace_in_class(
    views,
    "PlatoCreate",
    old_create_return,
    new_create_return,
    label="bloque return_to de Create",
)

# Contexto seguro para Cancelar / hidden / variedades.
create_context_anchor = "        context = super().get_context_data(**kwargs)\n"
create_context_new = (
    create_context_anchor
    + '        context["return_to_url"] = get_safe_return_to(\n'
    + '            self.request,\n'
    + '            fallback_url_name="filtro-de-platos",\n'
    + '        )\n'
)
start, end = class_bounds(views, "PlatoCreate")
block = views[start:end]
if 'context["return_to_url"] = get_safe_return_to(' not in block:
    if create_context_anchor not in block:
        raise RuntimeError("No encuentro get_context_data de PlatoCreate.")
    block = block.replace(create_context_anchor, create_context_new, 1)
    views = views[:start] + block + views[end:]

# ============================================================
# 6) PlatoUpdate: fallback explícito a la pantalla principal.
# ============================================================
old_update_return = (
    '        return_to = (\n'
    '            self.request.POST.get("return_to")\n'
    '            or self.request.GET.get("return_to")\n'
    '            or self.request.META.get("HTTP_REFERER")\n'
    '            or "/"\n'
    '        )\n\n'
    '        # Seguridad: evitar redirecciones a otro dominio\n'
    '        if return_to and not url_has_allowed_host_and_scheme(return_to, allowed_hosts={self.request.get_host()}):\n'
    '            return_to = "/"\n'
)
new_update_return = (
    '        return_to = get_safe_return_to(\n'
    '            self.request,\n'
    '            fallback_url_name="filtro-de-platos",\n'
    '        )\n'
)
views = replace_in_class(
    views,
    "PlatoUpdate",
    old_update_return,
    new_update_return,
    label="bloque return_to de Update",
)

start, end = class_bounds(views, "PlatoUpdate")
block = views[start:end]
if 'context["return_to_url"] = get_safe_return_to(' not in block:
    if create_context_anchor not in block:
        raise RuntimeError("No encuentro get_context_data de PlatoUpdate.")
    block = block.replace(create_context_anchor, create_context_new, 1)
    views = views[:start] + block + views[end:]

# ============================================================
# 7) AJAX de filtros/listado: validar return_to antes de propagar.
# ============================================================
old_ajax_return = '    return_to_url = request.POST.get("return_to") or reverse("filtro-de-platos")\n'
new_ajax_return = (
    '    return_to_url = get_safe_return_to(\n'
    '        request,\n'
    '        fallback_url_name="filtro-de-platos",\n'
    '        include_referer=False,\n'
    '    )\n'
)
if new_ajax_return not in views:
    if old_ajax_return not in views:
        raise RuntimeError("No encuentro return_to_url del listado AJAX.")
    views = views.replace(old_ajax_return, new_ajax_return, 1)

# Si centralizamos los dos únicos usos, sacar import directo.
if "url_has_allowed_host_and_scheme(" not in views:
    views = views.replace("from django.utils.http import url_has_allowed_host_and_scheme\n", "", 1)
else:
    raise RuntimeError("Quedó algún uso directo de url_has_allowed_host_and_scheme en views.py.")

# ============================================================
# 8) plato_form_inner: consumir sólo return_to ya saneado.
# ============================================================
form = form.replace("{{ request.GET.return_to|default:'/' }}", "{{ return_to_url }}")
form = form.replace("{{ request.GET.return_to|urlencode }}", "{{ return_to_url|urlencode }}")
form = form.replace(
    "{% firstof request.POST.return_to request.GET.return_to '/' %}",
    "{{ return_to_url }}",
)
form = form.replace(
    '<a class="btn btn-secondary" href="/">Ir a Home</a>',
    '<a class="btn btn-secondary" href="{% url \'filtro-de-platos\' %}">Volver</a>',
)

# ============================================================
# 9) VALIDAR TODO ANTES DE ESCRIBIR.
# ============================================================
errors = []

if "qc_lista_compras_origen" in base or "qc_lista_compras_origen" in lista:
    errors.append("quedó la clave vieja qc_lista_compras_origen")
if 'onclick="try{sessionStorage' in base:
    errors.append("quedó navegación inline en base.html")
if 'data-nav-store-current="lista-compras"' not in base:
    errors.append("falta data-nav-store-current en carrito")
if 'data-nav-return="lista-compras"' not in lista:
    errors.append("falta data-nav-return en Volver")
if 'id="volver-lista-compras-origen"' in lista:
    errors.append("quedó el script inline viejo de Volver")
if nav_include not in base:
    errors.append("navigation.js no quedó incluido en base")
if "request.GET.return_to" in form or "request.POST.return_to" in form:
    errors.append("plato_form_inner todavía consume return_to crudo")
if views.count("get_safe_return_to(") < 6:
    errors.append("hay menos usos de get_safe_return_to de los esperados")
if "url_has_allowed_host_and_scheme(" in views:
    errors.append("views.py todavía valida URLs por su cuenta")
if old_create_return in views:
    errors.append("quedó bloque viejo de return_to en PlatoCreate")
if old_update_return in views:
    errors.append("quedó bloque viejo de return_to en PlatoUpdate")

# Compilar Python transformado antes de escribir.
try:
    compile(navpy, "AdminVideos/navigation.py", "exec")
    compile(views, "AdminVideos/views.py", "exec")
except SyntaxError as exc:
    errors.append(f"Python inválido tras transformación: {exc}")

if errors:
    raise RuntimeError("Validación previa falló: " + "; ".join(errors))

# ============================================================
# 10) ESCRIBIR RECIÉN AHORA.
# ============================================================
navpy_path.write_text(navpy, encoding="utf-8")
navjs_path.parent.mkdir(parents=True, exist_ok=True)
navjs_path.write_text(navjs, encoding="utf-8")
base_path.write_text(base, encoding="utf-8")
lista_path.write_text(lista, encoding="utf-8")
form_path.write_text(form, encoding="utf-8")
views_path.write_text(views, encoding="utf-8")

print("OK: todas las transformaciones validaron antes de escribir.")
print("OK: return_to centralizado en navigation.py.")
print("OK: navegación efímera centralizada en navigation.js.")
PY

echo
echo "============================================================"
echo "CHECKS"
echo "============================================================"
git diff --check
"$PY" manage.py check
"$PY" manage.py makemigrations --check --dry-run

"$PY" manage.py shell <<'PY'
from django.template.loader import get_template
from django.test import RequestFactory
from AdminVideos.navigation import get_safe_return_to

for template in (
    "AdminVideos/base.html",
    "AdminVideos/lista_de_compras.html",
    "AdminVideos/plato_form_inner.html",
):
    get_template(template)
    print("Template OK:", template)

rf = RequestFactory()

interno = rf.get("/prueba/", {"return_to": "/videos/list/filtro/?tipopag=Guarnicion"})
assert get_safe_return_to(interno) == "/videos/list/filtro/?tipopag=Guarnicion"

externo = rf.get("/prueba/", {"return_to": "https://example.com/afuera"})
assert get_safe_return_to(
    externo,
    fallback_url_name="filtro-de-platos",
    include_referer=False,
) == "/videos/list/filtro/"

print("get_safe_return_to: OK")
PY

if command -v node >/dev/null 2>&1; then
  node --check "$NAVJS"
  echo "navigation.js: OK"
fi

echo
echo "============================================================"
echo "AUDITORÍA POST-LIMPIEZA"
echo "============================================================"

echo "-- navegación declarativa --"
grep -RInE "data-nav-store-current|data-nav-return|qc_nav_origin" "$BASE" "$LISTA" "$NAVJS" || true

echo
echo "-- return_to crudo en plato_form_inner --"
if grep -nE "request\.(GET|POST)\.return_to" "$FORM"; then
  echo "ERROR: quedó return_to crudo en plato_form_inner."
  exit 1
else
  echo "OK"
fi

echo
echo "-- validación URL centralizada --"
COUNT_VALIDATOR="$(grep -RIl "url_has_allowed_host_and_scheme" AdminVideos --exclude-dir=__pycache__ | wc -l | tr -d " ")"
if [ "$COUNT_VALIDATOR" -ne 1 ]; then
  echo "ERROR: url_has_allowed_host_and_scheme aparece en $COUNT_VALIDATOR archivos; esperaba 1."
  grep -RIn "url_has_allowed_host_and_scheme" AdminVideos --exclude-dir=__pycache__ || true
  exit 1
fi
grep -n "url_has_allowed_host_and_scheme" "$NAVPY"

echo
echo "-- restos del mecanismo viejo de Compras --"
if grep -nE "qc_lista_compras_origen|volver-lista-compras-origen|onclick=\"try\{sessionStorage" "$BASE" "$LISTA"; then
  echo "ERROR: quedaron restos del mecanismo viejo."
  exit 1
else
  echo "OK"
fi

echo
echo "============================================================"
echo "CAMBIOS"
echo "============================================================"
git diff --stat
echo
git status --short

echo
echo "============================================================"
echo "PRUEBA MANUAL"
echo "============================================================"
echo "1. Guarniciones -> carrito -> Volver."
echo "2. Otra categoría/filtros -> carrito -> Volver."
echo "3. Abrir Lista de compras directamente -> Volver al principal."
echo "4. Crear plato -> cancelar y luego crear/guardar."
echo "5. Editar plato -> cancelar y luego editar/guardar."
echo "6. En Crear/Editar/Compras, Agregar y carrito siguen ocultos."
echo
echo "No hace commit."
echo "Backup: $BACKUP_DIR"
