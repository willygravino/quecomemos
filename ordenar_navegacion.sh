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
BACKUP_DIR=".backup_limpieza_navegacion_${STAMP}"
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

# ============================================================
# 1) Helper Django: una sola regla para return_to seguro.
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
    \"\"\"Devuelve un destino interno seguro para volver después de una acción.

    Prioridad: POST return_to -> GET return_to -> Referer opcional -> fallback.
    Nunca devuelve una URL de otro host.
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
navpy_path.write_text(navpy, encoding="utf-8")

# ============================================================
# 2) JS genérico para navegación efímera "ir y volver".
# ============================================================
navjs = """/* Navegación efímera entre pantallas.
   data-nav-store-current=\"clave\" guarda la URL actual antes de navegar.
   data-nav-return=\"clave\" vuelve a esa URL; el href queda como fallback.
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
navjs_path.parent.mkdir(parents=True, exist_ok=True)
navjs_path.write_text(navjs, encoding="utf-8")

# ============================================================
# 3) base.html: sin JS inline; sólo semántica declarativa.
# ============================================================
base = re.sub(
    r'\s+onclick="try\{sessionStorage\.setItem\(\'qc_lista_compras_origen\', window\.location\.href\);\}catch\(e\)\{\}"',
    ' data-nav-store-current="lista-compras"',
    base,
    count=1,
)

if 'data-nav-store-current="lista-compras"' not in base:
    cart_pat = r'(<a\s+href="\{% url \'menu-elegido\' %\}"[\s\S]*?aria-label="Lista de compras")'
    base, n = re.subn(cart_pat, r'\1 data-nav-store-current="lista-compras"', base, count=1)
    if n != 1:
        raise RuntimeError("No pude agregar el atributo de origen al carrito.")

navjs_include = '<script src="{% static \'AdminVideos/js/navigation.js\' %}"></script>'
if navjs_include not in base:
    if "</body>" not in base:
        raise RuntimeError("No encuentro </body> en base.html.")
    base = base.replace("</body>", "  " + navjs_include + "\n</body>", 1)

# ============================================================
# 4) Lista de compras: botón declarativo; quitar script inline.
# ============================================================
lista = re.sub(
    r'(<a\s+id="btn-volver-lista-compras"[\s\S]*?href="\{% url \'filtro-de-platos\' %\}")',
    r'\1 data-nav-return="lista-compras"',
    lista,
    count=1,
) if 'data-nav-return="lista-compras"' not in lista else lista

lista, removed = re.subn(
    r'\s*<script id="volver-lista-compras-origen">[\s\S]*?</script>\s*',
    "\n",
    lista,
    count=1,
)

if 'id="volver-lista-compras-origen"' in lista:
    raise RuntimeError("Quedó el script inline viejo de Volver.")
if 'data-nav-return="lista-compras"' not in lista:
    raise RuntimeError("Volver no quedó conectado al helper JS.")

# ============================================================
# 5) views.py: usar helper único para return_to.
# ============================================================
import_line = "from AdminVideos.navigation import get_safe_return_to\n"
if import_line not in views:
    # Insertar junto a imports locales, antes de helpers/definiciones.
    marker = "from django.utils.http import url_has_allowed_host_and_scheme\n"
    if marker in views:
        views = views.replace(marker, marker + import_line, 1)
    else:
        # fallback tras imports de servicios pantry
        pos = views.find("\n\n", views.find("from AdminVideos."))
        if pos == -1:
            raise RuntimeError("No encuentro zona de imports en views.py.")
        views = views[:pos+2] + import_line + views[pos+2:]

# eliminar_plato: resolver return_to seguro y sin Referer implícito.
views = views.replace(
    '    return_to = request.POST.get("return_to") or request.GET.get("return_to")\n',
    '    return_to = get_safe_return_to(request, include_referer=False)\n',
    1,
)

# Create / Update: reemplazar bloques duplicados de resolución+validación.
pattern = re.compile(
    r'        return_to = \(\n'
    r'            self\.request\.POST\.get\("return_to"\)\n'
    r'            or self\.request\.GET\.get\("return_to"\)\n'
    r'            or self\.request\.META\.get\("HTTP_REFERER"\)\n'
    r'            or (?:""|"/")\n'
    r'        \)\n\n'
    r'        (?:# Seguridad: evitar redirecciones a otro dominio\n)?'
    r'        if return_to and not url_has_allowed_host_and_scheme\(return_to, allowed_hosts=\{self\.request\.get_host\(\)\}\):\n'
    r'            return_to = (?:""|"/")\n'
)
views, n_safe = pattern.subn(
    '        return_to = get_safe_return_to(self.request)\n',
    views,
)

if n_safe < 2:
    raise RuntimeError(f"Esperaba centralizar Create y Update; reemplacé {n_safe} bloques.")

# AJAX listado: no propagar return_to sin validar.
views = views.replace(
    '    return_to_url = request.POST.get("return_to") or reverse("filtro-de-platos")\n',
    '    return_to_url = get_safe_return_to(\n'
    '        request,\n'
    '        fallback_url_name="filtro-de-platos",\n'
    '        include_referer=False,\n'
    '    )\n',
    1,
)

# Ya no debe importarse el validador directamente en views.
if "url_has_allowed_host_and_scheme(" not in views:
    views = views.replace("from django.utils.http import url_has_allowed_host_and_scheme\n", "", 1)

# Contexto seguro para links/hidden del formulario.
# Agregar en get_context_data de PlatoCreate y PlatoUpdate justo después de super().
classes = ["PlatoCreate", "PlatoUpdate"]
for class_name in classes:
    class_match = re.search(rf"(?m)^class {class_name}\b[\s\S]*?(?=^class |\Z)", views)
    if not class_match:
        raise RuntimeError(f"No encuentro {class_name}.")
    block = class_match.group(0)
    if 'context["return_to_url"] =' not in block:
        anchor = "        context = super().get_context_data(**kwargs)\n"
        if anchor not in block:
            raise RuntimeError(f"No encuentro get_context_data de {class_name}.")
        replacement = (
            anchor
            + '        context["return_to_url"] = get_safe_return_to(\n'
            + '            self.request,\n'
            + '            fallback_url_name="filtro-de-platos",\n'
            + '        )\n'
        )
        block = block.replace(anchor, replacement, 1)
        views = views[:class_match.start()] + block + views[class_match.end():]

# ============================================================
# 6) Template de formulario: no leer return_to crudo del request.
# ============================================================
form = form.replace(
    '{{ request.GET.return_to|default:\'/\' }}',
    '{{ return_to_url }}',
)
form = form.replace(
    '{{ request.GET.return_to|urlencode }}',
    '{{ return_to_url|urlencode }}',
)
form = form.replace(
    '{% firstof request.POST.return_to request.GET.return_to \'/\' %}',
    '{{ return_to_url }}',
)
form = form.replace(
    '<a class="btn btn-secondary" href="/">Ir a Home</a>',
    '<a class="btn btn-secondary" href="{% url \'filtro-de-platos\' %}">Volver</a>',
)

# ============================================================
# 7) Validaciones estáticas antes de escribir.
# ============================================================
if "qc_lista_compras_origen" in base or "qc_lista_compras_origen" in lista:
    raise RuntimeError("Quedó la clave vieja de storage en templates.")

if 'onclick="try{sessionStorage' in base:
    raise RuntimeError("Quedó navegación inline en base.html.")

if "request.GET.return_to" in form or "request.POST.return_to" in form:
    raise RuntimeError("plato_form_inner todavía lee return_to crudo.")

if "url_has_allowed_host_and_scheme(" in views:
    raise RuntimeError("views.py todavía valida return_to por su cuenta.")

base_path.write_text(base, encoding="utf-8")
lista_path.write_text(lista, encoding="utf-8")
form_path.write_text(form, encoding="utf-8")
views_path.write_text(views, encoding="utf-8")

print("OK: navegación efímera centralizada en navigation.js.")
print("OK: return_to centralizado en AdminVideos/navigation.py.")
print("OK: formulario ya no consume return_to crudo.")
print("OK: eliminar_plato deja de redirigir a return_to sin validar.")
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
r = rf.get("/prueba/", {"return_to": "/videos/list/filtro/?tipopag=Guarnicion"})
assert get_safe_return_to(r) == "/videos/list/filtro/?tipopag=Guarnicion"

r = rf.get("/prueba/", {"return_to": "https://example.com/afuera"})
assert get_safe_return_to(r, fallback_url_name="filtro-de-platos") == "/videos/list/filtro/"

print("safe return_to: OK")
PY

if command -v node >/dev/null 2>&1; then
  node --check "$NAVJS"
  echo "navigation.js: OK"
fi

echo
echo "============================================================"
echo "AUDITORÍA POST-LIMPIEZA"
echo "============================================================"

echo "-- storage de navegación --"
grep -RIn "qc_nav_origin\|data-nav-store-current\|data-nav-return" \
  "$BASE" "$LISTA" "$NAVJS" || true

echo
echo "-- return_to crudo en plato_form_inner (debe estar vacío) --"
if grep -nE "request\.(GET|POST)\.return_to" "$FORM"; then
  echo "ERROR: todavía hay return_to crudo en el formulario."
  exit 1
else
  echo "OK"
fi

echo
echo "-- validador de URL: debe vivir sólo en navigation.py --"
grep -RIn "url_has_allowed_host_and_scheme" AdminVideos --exclude-dir=__pycache__ || true

echo
echo "-- navegación inline nueva: no debe existir --"
if grep -n "qc_lista_compras_origen\|onclick=\"try{sessionStorage" "$BASE" "$LISTA"; then
  echo "ERROR: quedó navegación inline vieja."
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
echo "1. Guarniciones -> carrito -> Volver: vuelve a Guarniciones."
echo "2. Otra categoría/filtros -> carrito -> Volver: vuelve exactamente allí."
echo "3. Lista de compras directa -> Volver: fallback a la pantalla principal."
echo "4. Crear plato -> cancelar/guardar: vuelve al origen."
echo "5. Editar plato -> cancelar/guardar: vuelve al origen."
echo "6. Crear/Editar/Compras: los flotantes deben seguir ocultos."
echo
echo "No hace commit."
echo "Backup: $BACKUP_DIR"
