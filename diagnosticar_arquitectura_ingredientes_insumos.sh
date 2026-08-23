#!/usr/bin/env bash
set -u

ROOT="${1:-.}"
STAMP="$(date +"%Y%m%d_%H%M%S")"
OUT="diagnostico_arquitectura_ingredientes_insumos_${STAMP}.txt"

EXCLUDES=(
  --exclude-dir=.git
  --exclude-dir=.venv
  --exclude-dir=venv
  --exclude-dir=env
  --exclude-dir=node_modules
  --exclude-dir=__pycache__
  --exclude-dir=staticfiles
  --exclude-dir=media
  --exclude-dir=dist
  --exclude-dir=build
  --exclude='*.min.js'
  --exclude='*.map'
)

CODE_INCLUDES=(
  --include='*.py'
  --include='*.html'
  --include='*.js'
  --include='*.css'
  --include='*.scss'
)

section () {
  echo
  echo "================================================================"
  echo "$1"
  echo "================================================================"
}

{
  echo "DIAGNÓSTICO DE ARQUITECTURA: INGREDIENTES -> POSIBLES INSUMOS"
  echo "Generado: $(date)"
  echo "Raíz analizada: $(cd "$ROOT" 2>/dev/null && pwd || echo "$ROOT")"
  echo
  echo "OBJETIVO:"
  echo "Determinar si la arquitectura existente de ingredientes puede reutilizarse"
  echo "para implementar Insumos con:"
  echo "- catálogo/base de insumos"
  echo "- posibilidad de crear insumos"
  echo "- selector"
  echo "- autocomplete"
  echo "- asociación simple con plato/receta, inicialmente sin cantidad ni unidad"
  echo
  echo "SEGURIDAD:"
  echo "- No modifica archivos."
  echo "- No incluye .env ni carpetas virtualenv."
  echo "- Aun así, revisá el TXT antes de compartirlo por si existen secretos"
  echo "  escritos directamente dentro de archivos .py/.js/.html."
  echo

  section "1) ESTRUCTURA RELEVANTE DEL PROYECTO"
  find "$ROOT" \
    \( -path '*/.git' -o -path '*/.venv' -o -path '*/venv' -o -path '*/env' \
       -o -path '*/node_modules' -o -path '*/__pycache__' -o -path '*/staticfiles' \
       -o -path '*/media' -o -path '*/dist' -o -path '*/build' \) -prune \
    -o -type f \
    \( -name 'manage.py' -o -name 'models.py' -o -name 'forms.py' \
       -o -name 'views.py' -o -name 'urls.py' -o -name '*.html' \
       -o -name '*.js' \) \
    -print 2>/dev/null | sort

  section "2) TODAS LAS REFERENCIAS A INGREDIENTE / INGREDIENTES"
  grep -RIn -C 8 \
    "${EXCLUDES[@]}" \
    "${CODE_INCLUDES[@]}" \
    -E 'Ingrediente|ingrediente|Ingredientes|ingredientes' \
    "$ROOT" 2>/dev/null || echo "No se encontraron referencias."

  section "3) MODELOS RELACIONADOS CON INGREDIENTES, RECETAS O PLATOS"
  while IFS= read -r file; do
    if grep -qiE 'ingrediente|receta|plato' "$file" 2>/dev/null; then
      echo
      echo "################ ARCHIVO: $file ################"
      sed -n '1,700p' "$file"
    fi
  done < <(
    find "$ROOT" \
      \( -path '*/.git' -o -path '*/.venv' -o -path '*/venv' -o -path '*/env' \
         -o -path '*/node_modules' -o -path '*/__pycache__' \) -prune \
      -o -type f -name 'models.py' -print 2>/dev/null
  )

  section "4) FORMULARIOS RELACIONADOS CON INGREDIENTES / PLATOS / RECETAS"
  while IFS= read -r file; do
    if grep -qiE 'ingrediente|receta|plato' "$file" 2>/dev/null; then
      echo
      echo "################ ARCHIVO: $file ################"
      sed -n '1,800p' "$file"
    fi
  done < <(
    find "$ROOT" \
      \( -path '*/.git' -o -path '*/.venv' -o -path '*/venv' -o -path '*/env' \
         -o -path '*/node_modules' -o -path '*/__pycache__' \) -prune \
      -o -type f -name 'forms.py' -print 2>/dev/null
  )

  section "5) VISTAS RELACIONADAS CON INGREDIENTES / CREACIÓN / AUTOCOMPLETE"
  while IFS= read -r file; do
    if grep -qiE 'ingrediente|autocomplete|select2|receta|plato' "$file" 2>/dev/null; then
      echo
      echo "################ ARCHIVO: $file ################"
      grep -n -C 25 -iE \
        'ingrediente|autocomplete|select2|receta|plato' \
        "$file" 2>/dev/null || true
    fi
  done < <(
    find "$ROOT" \
      \( -path '*/.git' -o -path '*/.venv' -o -path '*/venv' -o -path '*/env' \
         -o -path '*/node_modules' -o -path '*/__pycache__' \) -prune \
      -o -type f -name 'views.py' -print 2>/dev/null
  )

  section "6) URLS RELACIONADAS CON INGREDIENTES / AUTOCOMPLETE / PLATOS"
  while IFS= read -r file; do
    if grep -qiE 'ingrediente|autocomplete|select2|receta|plato' "$file" 2>/dev/null; then
      echo
      echo "################ ARCHIVO: $file ################"
      sed -n '1,600p' "$file"
    fi
  done < <(
    find "$ROOT" \
      \( -path '*/.git' -o -path '*/.venv' -o -path '*/venv' -o -path '*/env' \
         -o -path '*/node_modules' -o -path '*/__pycache__' \) -prune \
      -o -type f -name 'urls.py' -print 2>/dev/null
  )

  section "7) TEMPLATES QUE MANEJAN INGREDIENTES"
  MATCHING_TEMPLATES="$(
    grep -RIl \
      "${EXCLUDES[@]}" \
      --include='*.html' \
      -E 'Ingrediente|ingrediente|Ingredientes|ingredientes' \
      "$ROOT" 2>/dev/null || true
  )"

  if [ -z "$MATCHING_TEMPLATES" ]; then
    echo "No se encontraron templates relacionados."
  else
    while IFS= read -r file; do
      [ -z "$file" ] && continue
      echo
      echo "################ TEMPLATE: $file ################"
      sed -n '1,900p' "$file"
    done <<< "$MATCHING_TEMPLATES"
  fi

  section "8) JAVASCRIPT DE SELECTORES / AUTOCOMPLETE / CREACIÓN DINÁMICA"
  MATCHING_JS="$(
    grep -RIl \
      "${EXCLUDES[@]}" \
      --include='*.js' \
      -E 'ingrediente|autocomplete|select2|tom-select|choices|selectize|fetch\(|XMLHttpRequest|htmx|modal' \
      "$ROOT" 2>/dev/null || true
  )"

  if [ -z "$MATCHING_JS" ]; then
    echo "No se encontraron archivos JS relacionados."
  else
    while IFS= read -r file; do
      [ -z "$file" ] && continue
      echo
      echo "################ JAVASCRIPT: $file ################"
      sed -n '1,1200p' "$file"
    done <<< "$MATCHING_JS"
  fi

  section "9) LIBRERÍAS / WIDGETS DE AUTOCOMPLETE DETECTADOS"
  grep -RIn -C 5 \
    "${EXCLUDES[@]}" \
    "${CODE_INCLUDES[@]}" \
    -E 'django-autocomplete-light|dal\.|autocomplete\.ModelSelect2|ModelSelect2|select2|Select2|tom-select|TomSelect|choices\.js|Choices\(|selectize|Selectize' \
    "$ROOT" 2>/dev/null || echo "No se detectó una librería conocida de autocomplete/select."

  section "10) FORMSETS / INLINE FORMSETS / PREFIJOS DINÁMICOS"
  grep -RIn -C 10 \
    "${EXCLUDES[@]}" \
    "${CODE_INCLUDES[@]}" \
    -E 'formset|inlineformset|modelformset|TOTAL_FORMS|INITIAL_FORMS|empty_form|management_form|prefix=' \
    "$ROOT" 2>/dev/null || echo "No se detectaron formsets."

  section "11) CREACIÓN RÁPIDA: MODALES, ENDPOINTS JSON, FETCH, AJAX, HTMX"
  grep -RIn -C 12 \
    "${EXCLUDES[@]}" \
    "${CODE_INCLUDES[@]}" \
    -E 'JsonResponse|fetch\(|XMLHttpRequest|hx-|htmx|modal|data-bs-toggle|data-bs-target|create.*ingred|crear.*ingred|nuevo.*ingred|add.*ingred' \
    "$ROOT" 2>/dev/null || echo "No se detectó claramente creación rápida/dinámica."

  section "12) MIGRACIONES QUE MENCIONAN INGREDIENTES"
  find "$ROOT" \
    \( -path '*/.git' -o -path '*/.venv' -o -path '*/venv' -o -path '*/env' \
       -o -path '*/node_modules' -o -path '*/__pycache__' \) -prune \
    -o -type f -path '*/migrations/*.py' -print 2>/dev/null |
  while IFS= read -r file; do
    if grep -qiE 'ingrediente' "$file" 2>/dev/null; then
      echo
      echo "---------- $file ----------"
      grep -n -C 15 -iE 'ingrediente' "$file" 2>/dev/null || true
    fi
  done

  section "13) SETTINGS / INSTALLED_APPS RELEVANTES (SIN SECRET_KEY)"
  SETTINGS_FILES="$(
    find "$ROOT" \
      \( -path '*/.git' -o -path '*/.venv' -o -path '*/venv' -o -path '*/env' \
         -o -path '*/node_modules' -o -path '*/__pycache__' \) -prune \
      -o -type f \( -name 'settings.py' -o -name 'base.py' \) -print 2>/dev/null
  )"

  if [ -n "$SETTINGS_FILES" ]; then
    while IFS= read -r file; do
      [ -z "$file" ] && continue
      if grep -qiE 'INSTALLED_APPS|autocomplete|dal|select2' "$file" 2>/dev/null; then
        echo
        echo "---------- $file ----------"
        grep -n -C 15 -E 'INSTALLED_APPS|autocomplete|dal|select2' "$file" 2>/dev/null \
          | sed -E \
              -e "s/(SECRET_KEY[[:space:]]*=[[:space:]]*).*/\1'***OCULTO***'/" \
              -e "s/(PASSWORD[[:space:]]*[:=][[:space:]]*).*/\1'***OCULTO***'/" \
              -e "s/(API_KEY[[:space:]]*[:=][[:space:]]*).*/\1'***OCULTO***'/"
      fi
    done <<< "$SETTINGS_FILES"
  fi

  section "FIN DEL DIAGNÓSTICO"
  echo "Archivo generado: $OUT"

} > "$OUT"

echo
echo "Listo."
echo "Se generó:"
echo "  $OUT"
echo
echo "Revisalo rápidamente y adjuntalo en el chat."
