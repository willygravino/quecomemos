#!/usr/bin/env bash
# Diagnostico dirigido del estado "Con lo que tengo".
# SOLO LECTURA del codigo del proyecto. Unicamente crea el reporte TXT.
set -euo pipefail

if [[ ! -f manage.py ]]; then
  echo 'ERROR: Ejecuta este script desde la carpeta donde esta manage.py.' >&2
  exit 1
fi

OUT="reporte_estado_con_lo_que_tengo_detallado.txt"

mostrar_rango() {
  local archivo="$1" inicio="$2" fin="$3"
  printf '\n==================== %s (%s-%s) ====================\n' "$archivo" "$inicio" "$fin"
  if [[ -f "$archivo" ]]; then
    nl -ba "$archivo" | sed -n "${inicio},${fin}p"
  else
    printf 'ARCHIVO NO ENCONTRADO\n'
  fi
}

mostrar_coincidencias() {
  local archivo="$1"
  printf '\n==================== COINCIDENCIAS: %s ====================\n' "$archivo"
  if [[ -f "$archivo" ]]; then
    grep -n -C 2 -E 'lo_que_tengo|LoQueTengo|loQueTengo|usarLoQueTengo|usar_lo_que_tengo|js-filtro-lo-que-tengo' "$archivo" || true
  else
    printf 'ARCHIVO NO ENCONTRADO\n'
  fi
}

{
  printf 'REPORTE DIRIGIDO - REACTIVACION DE "CON LO QUE TENGO"\n'
  printf 'Fecha: %s\n' "$(date -Iseconds)"
  printf 'Proyecto: %s\n' "$PWD"
  printf 'Alcance: solamente archivos ACTIVOS (se omiten directorios de backup).\n'
  printf 'No se realizaron cambios en archivos de la aplicacion.\n'

  # La fuente persistida y la compatibilidad con URLs antiguas.
  mostrar_rango 'AdminVideos/views.py' 2935 3010
  mostrar_rango 'AdminVideos/views.py' 3320 3380
  mostrar_rango 'AdminVideos/views.py' 3435 3505

  # Inicio, refresco AJAX, estado visual, apagado, links y popstate.
  mostrar_rango 'AdminVideos/static/AdminVideos/js/filtros_platos.js' 1 255
  mostrar_rango 'AdminVideos/static/AdminVideos/js/filtros_platos.js' 650 830

  # Checkbox, form, boton, JS embebido e imports reales.
  mostrar_coincidencias 'AdminVideos/templates/AdminVideos/lista_filtrada.html'
  mostrar_rango 'AdminVideos/templates/AdminVideos/lista_filtrada.html' 580 715

  # Control global y navegacion que pueden reintroducir el parametro.
  mostrar_coincidencias 'AdminVideos/templates/AdminVideos/partials/_control_lo_que_tengo_global.html'
  mostrar_coincidencias 'AdminVideos/templates/AdminVideos/partials/_selector_horizontal_platos.html'
  mostrar_coincidencias 'AdminVideos/templates/AdminVideos/base.html'
  mostrar_coincidencias 'AdminVideos/templates/AdminVideos/pre-base.html'
  mostrar_coincidencias 'AdminVideos/static/AdminVideos/js/navigation.js'
  mostrar_rango 'AdminVideos/static/AdminVideos/js/lo_que_tengo.js' 1 110

  printf '\nFIN. Si algun fragmento queda fuera de rango, adjuntar el archivo original.\n'
} > "$OUT"

printf 'Reporte generado: %s\n' "$OUT"
