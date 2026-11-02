# CONTEXTO_IA.md — Qué Comemos

> Este archivo es la fuente de verdad del proyecto para trabajar con IA.
> **Cualquier IA o colaborador DEBE leerlo completo antes de proponer o ejecutar cambios.**
> Última actualización: 2026-10-25 (sesión doble-submit + confirmDialog + inventario).

## 1. Identidad del proyecto

- Nombre: **Qué Comemos**
- Tipo: app web de gestión de platos, ingredientes, menús programados, lista de compras y red social gastronómica.
- Estado: **en producción** (deploy en Railway). Los cambios NO son libres.
- Dueño del producto: yo. La IA es asistente, no decide.
- Local: Mac, VS Code, entorno `.venv`.

## 2. Stack

- Django 5, Python 3.12
- Templates Django (no React/Vue)
- JavaScript vanilla (no frameworks)
- CSS propio + Bootstrap
- Deploy: Railway

## 3. Estructura

- App principal: `AdminVideos/`
- Templates: `AdminVideos/templates/AdminVideos/`
- Partiales: `AdminVideos/templates/AdminVideos/partials/`
- CSS: `AdminVideos/static/AdminVideos/css/`
- JS: `AdminVideos/static/AdminVideos/js/`
- Vendor (NO tocar): `AdminVideos/static/AdminVideos/vendor/`

## 4. Mapa de archivos (inventario 2026-10-25)

> Total ~176k líneas, de las cuales **~130k son librerías vendorizadas** (jQuery, Bootstrap, FontAwesome, Chart.js, DataTables). **El código propio es ~46k líneas.**

### Backend Python (top)
| Archivo | Líneas | Notas |
|---|---|---|
| `views.py` | **4.955** | Archivo enorme, candidato a refactor futuro |
| `models.py` | 932 | |
| `services/pantry.py` | 471 | Capa de servicios (buena arquitectura) |
| `forms.py` | 342 | |
| `admin.py` | 178 | |
| `navigation.py` | 41 | |
| `context_processors.py` | 24 | |
| `signals.py` | 16 | |
| `tests.py` | **3** | Casi sin tests |

### Templates principales
| Archivo | Líneas |
|---|---|
| `base.html` | **2.041** |
| `video_list_base.html` | 1.294 |
| `plato_form_inner.html` | 985 |
| `lista_filtrada.html` | 812 |
| `_menu_programado_dias.html` | 403 |
| `_confirm_action_modal.html` | 314 |
| `_plato_card_detalle.html` | 292 |
| `lista_de_compras.html` | 264 |
| `compartir_lista.html` | 225 |

### JS propios (sin vendor)
| Archivo | Líneas | Rol |
|---|---|---|
| `form_init.js` | **1.541** | Init form plato + guardado AJAX + variedades |
| `filtros_platos.js` | 839 | Filtros del listado |
| `menu_print_sheet.js` | 618 | Hoja imprimible del menú |
| `partes_receta.js` | 609 | Partes de receta |
| `overlay_ui.js` | 421 | Swipe/wheel dismiss, UI |
| `insumos_form.js` | 399 | Insumos del form |
| `plato_create_sheet.js` | 371 | Sheet crear/editar plato |
| `lo_que_tengo.js` | 365 | Control de disponibilidad |
| `menu_programado.js` | 275 | Menú semanal |
| `pantry_bind.js` | 250 | Binding de pantry |
| `shopping_panel.js` | 241 | Panel de lista de compras |
| `lista_super/idb_cola_offline.js` | 141 | Cola offline (IndexedDB) |
| `lista_super/sync_offline_lista_super.js` | 131 | Sync offline |
| `lista_super/sw_lista_super.js` | 72 | Service Worker |
| `lista_de_compras.js` | 90 | |
| `navigation.js` | 67 | |

### CSS propios
| Archivo | Líneas |
|---|---|
| `mi-css.css` | **2.824** |
| `menu_print_sheet.css` | 368 |
| `mobile_action_bar.css` | 154 |
| `shopping_panel.css` | 118 |
| `plato_create_sheet.css` | 117 |

## 5. Dominios funcionales

1. **Platos** — crear, editar, categorizar, variedades, ingredientes, insumos, partes de receta, imágenes.
2. **Menús programados** — semanal, días, impresión, estados.
3. **Lista de compras** — con soporte **offline** (IndexedDB + service worker + sync).
4. **Lugares** — listado, detalle, compartir.
5. **Amigues / chat** — panel, solicitudes, chat modal.
6. **Pantry** — control de "lo que tengo", servicio en `services/pantry.py`.
7. **Auth** — signup, login, forgot password.
8. **Historial**.
9. **Delivery / comer afuera** — vistas propias.

## 6. Reglas NO negociables

1. **Modo oscuro**: cada cambio visual se verifica en claro Y oscuro. Sin colores hardcodeados.
2. **Responsive**: cada cambio se verifica en desktop y mobile. No romper breakpoints.
3. **No romper JS**: si un template depende de `id`, `class` o `data-attribute` que consume JS, NO renombrarlo sin actualizar el JS en el mismo cambio.
4. **No duplicar componentes**: si existe un partial (`_*.html`), reutilizarlo.
5. **Reutilizar lógica existente**: antes de escribir código nuevo, buscar si ya está implementado.
6. **Cambios quirúrgicos**: diff mínimo. No reescribir archivos completos salvo pedido explícito.
7. **No tocar `vendor/`** salvo actualización explícita de librería.
8. **Prohibido en producción sin rama y backup**: migraciones, cambios de modelos, refactors de `base.html`.

## 7. Reglas de versionado de JS y CSS (obligatorio)

**Cada vez que se modifica un `.js`, hay que bumpear su versión en `base.html`.**

- Formato: `?v=YYYYMMDD_HHMMSS`
- Ubicación: `AdminVideos/templates/AdminVideos/base.html`, en el `<script src="{% static '...' %}?v=...">`.
- **Si no se bumpea, el navegador usa el JS viejo cacheado** y los cambios "no se ven" en producción.
- En local, `Cmd+Shift+R` fuerza recarga. Para producción, el bump es obligatorio.
- Los **templates `.html`** y los **partials `_*.html`** NO se cachean: no hace falta bumpear.
- Al bumpear varios JS en el mismo cambio, usar el **mismo timestamp** para todos.
- Localizar las líneas exactas con `grep -n "\.js' %}" AdminVideos/templates/AdminVideos/base.html`.
- **CSS también se cachea**: cada vez que se modifica un `.css` propio, hay que bumpear su `?v=` en `base.html`. Los navegadores cachean CSS agresivamente y los cambios "no se ven".
- **Trampa del `{% static %}`**: el `?v=` va **afuera** del tag. 
  - ✅ Correcto: `<link href="{% static 'css/mi-css.css' %}?v=123">`
  - ❌ Incorrecto: `<link href="{% static 'css/mi-css.css?v=123' %}">` (Django busca un archivo con ese nombre y falla o sirve mal).
- **Excepción importante**: algunos JS no se cargan desde `base.html`, sino desde el template que los usa. Ejemplo: `filtros_platos.js` y `lo_que_tengo.js` se bumpean en `lista_filtrada.html`. Buscar siempre con `grep -rn "\.js' %}" AdminVideos/templates/` antes de asumir que está en `base.html`.

## 8. Filosofía: sin parches, causa raíz

- Si un fix "tapa" el síntoma sin explicar **por qué** falla, **no se aplica**.
- Flujo obligatorio ante un bug no trivial:
  1. **Instrumentar** (logs, `console.table`) para ver el estado real.
  2. **Reproducir** en el navegador con DevTools abierto.
  3. **Leer el log**: entender qué pasa exactamente.
  4. **Identificar la causa raíz** (no el síntoma).
  5. **Diseñar el fix** sobre la causa raíz.
  6. **Quitar la instrumentación** antes de commitear.
- Ejemplo real (2026-10-25): "el modal pregunta aunque no toqué nada". Se iba a resolver con un flag `_formDirty` (parche). Al instrumentar `hayCambios()`, se vio que había **colisión de claves por `name`** en checkboxes múltiples (`name="tipos"`). El fix correcto fue `_fieldKey(el)` con clave única por elemento, sin flags.
- Si una solución requiere "una bandera más" o "un caso especial más", probablemente no es la solución.

## 9. Reutilización: buscar antes de crear

- Antes de crear un componente nuevo, **buscar si ya existe** algo parecido.
- Si existe algo 80% útil, **extenderlo**. Si es inservible, crear nuevo y documentar por qué.
- Buscar con `grep -rn "palabra_clave" AdminVideos/templates/AdminVideos/partials/ AdminVideos/static/AdminVideos/js/`.

### Componentes reutilizables existentes
- **`_confirm_action_modal.html`** → modal genérico de confirmación.
  - API declarativa: botón con `data-bs-toggle="modal"` + `data-confirm-*`.
  - API programática: `await window.confirmDialog({title, body, hint, confirmText, cancelText, confirmClass}) -> Promise<boolean>`.
  - **Usar SIEMPRE este para preguntar sí/no. No crear otro.**
- **`_toast_msg.html`** → toast para **informar** (`?msg=...&level=success|danger|warning|info`).
  - Autohide 2.5s, **no bloquea**, no tiene botones de acción.
  - **NO sirve para confirmar.** Solo para notificar.

## 10. Flujo de trabajo con IA (obligatorio)

1. **Investigar**: decir en qué archivo(s) está implementada la funcionalidad y qué se ve afectado.
2. **Proponer plan**: enumerar pasos (3-6). Si es grande, cómo partirlo.
3. **Esperar aprobación** del plan (no escribir código todavía).
4. **Ejecutar en pasos pequeños**: un cambio por paso.
5. **Verificar**: `python manage.py check` después de cada paso.
6. **Probar en navegador** con `Cmd+Shift+R` antes de commitear.
7. **Commit sugerido** al cerrar cada paso.

Si la IA no puede seguir este flujo, debe decirlo y detenerse.

## 11. Comandos de verificación

```bash
source .venv/bin/activate
python manage.py check
python manage.py test AdminVideos -v 2   # cuando existan tests

## 12. Lecciones de bash y edición de archivos

- **`>>` para agregar, `>` para sobrescribir**. Nunca `>` si el archivo puede existir. Verificar con `cat archivo` o `ls` antes.
- **Backup antes de cada cambio quirúrgico**: `cp archivo backups_XXX/archivo.antes_descripcion`.
- **Scripts con asserts** (`assert s.count(anchor) == 1`) que abortan si el ancla no existe o no es única. Si el script falla, **no escribe nada** — nunca deja archivos a medio modificar.
- Usar `python3 - <<'PY'` con pathlib para cambios quirúrgicos, no `sed -i` ni regex amplios.
- **Dry-run antes de borrar**: `git clean -nd` antes de `git clean -fd`; `git stash list` antes de `git stash drop`.

## 13. Lecciones de git

- **`git stash` en vez de `git reset --hard`** cuando puede haber cambios recuperables. Es reversible.
- **`git reset --hard` NO borra untracked**: para esos, `git clean`. Comandos distintos.
- **Commits chiquitos**, un fix por commit. Si algo falla, revertir solo ese commit.
- **`python manage.py check`** antes de cada commit.
- **Probar en navegador ANTES de commitear**, con `Cmd+Shift+R`.
- **Backups en `backups_*/`**: agregar al `.gitignore`, no borrar hasta confirmar que el fix anda.

## 14. Lecciones de debugging

- **Instrumentar antes de arreglar**: `console.table(diffs)` para ver qué campos difieren.
- **Reproducir el bug en el navegador con DevTools abierto** antes de hipotetizar.
- **Quitar la instrumentación al commitear**.
- **No asumir "no lo vi fallar = no puede fallar"**. El código sin protección puede fallar aunque el timing lo oculte.
- Un bug de "falso positivo" casi siempre es un problema de **comparación** o **estado inicial**, no del feature en sí.

## 15. Puntos críticos del sistema (mapa de intervención)

> Líneas aproximadas al 2026-10-25. Verificar con `grep` antes de tocar.

| Archivo | Punto | Qué hace |
|---|---|---|
| `plato_create_sheet.js` | `cerrar()` (~L133) | Punto único de cierre del sheet. `async`, consulta cambios. |
| `plato_create_sheet.js` | `_fieldKey()` (~L107) | Clave única por elemento (checkbox/radio: `name::value`; resto: `name`). |
| `plato_create_sheet.js` | `snapshotForm()`, `hayCambios()` (~L112-155) | Detección de cambios. |
| `plato_create_sheet.js` | `renderForm()` (~L162) | Inyecta form y llama `snapshotForm()`. |
| `plato_create_sheet.js` | `beforeunload` (~L323) | Aviso al cerrar pestaña/volver. |
| `form_init.js` | `setFormSubmitting(form, bool)` (~L33) | Deshabilita/habilita submit (anti-doble-submit). |
| `form_init.js` | `setupAjaxSave()` (~L1201) | Handler del form principal (alta/edición). |
| `form_init.js` | Handler async de variedades (~L1330) | Guardado AJAX de variedades. |
| `_confirm_action_modal.html` | `window.confirmDialog(opts)` (~L143) | Modal genérico de confirmación. Promise<boolean>. |
| `_toast_msg.html` | `bootstrap.Toast` | Solo informar (no confirmar). |
| `base.html` | `<script ... ?v=YYYYMMDD_HHMMSS>` | Versionado de JS. |
| `base.html` | `{% include "_confirm_action_modal.html" %}` (~L1309) | Inclusión del modal genérico. |
| `base.html` | `{% include "_toast_msg.html" %}` (~L1714) | Inclusión del toast. |
| `views.py` | `obtener_estado_filtros_platos` (~L2982) | Lee `ver_cotidiano`/`ver_especial` de POST/GET. Default: ambos `True`. |
| `views.py` | `filtrar_platos` (~L2313) | Filtro de categoría con `categoria__in` incluyendo `Ambos` en ambos modos. |
| `filtros_platos.js` | Bloqueo toggles categoría (~L670) | Impide dejar 0 categorías marcadas (revierte + aviso 2.5s). |


## 16. Categorías del dominio

- Platos principales
- Guarniciones
- Picadas
- Ingredientes de picada
- Delivery
- Comer afuera

## 17. Entidades del dominio

- **Plato**: nombre, ingredientes, insumos, preparación, imágenes, categoría, tipos.
- **Menú programado**: asignación de platos a días, organización semanal, impresión, eliminación.
- **Lista de compras**: con soporte offline.
- **Lugar**: punto de venta/compra, con compartir.

## 18. Estados visuales que NUNCA se deben romper

- Día con menú
- Día sin menú
- Día activo
- Modo claro
- Modo oscuro

Cada estado debe verse bien en desktop y mobile.

## 19. Cosas que NO hacer

- No pegar grandes bloques de código en la terminal (usar scripts `.sh` o heredocs **chicos**, o editar en VS Code).
- No modificar `.venv/`, `migrations/` ni archivos de deploy sin pedido explícito.
- No instalar dependencias nuevas sin justificar y preguntar.
- No "limpiar" código por iniciativa propia: si ves algo raro, reportarlo, no borrarlo.
- No reescribir un archivo entero para cambiar 3 líneas.
- No asumir: si no encuentra dónde está algo, decir "no lo encontré" en lugar de inventar.
- **No tocar `vendor/`**.
- **No crear un segundo modal de confirmación**: usar `_confirm_action_modal.html`.
- **No usar el toast para confirmar**: solo informar.
- **No aplicar parches**: buscar causa raíz (ver sección 8).

## 20. Pendiente de explorar (no inventariado aún)

- Interior de `views.py` (4.955 líneas) — vistas por dominio, AJAX vs HTML.
- `models.py` (932 líneas) — entidades, relaciones, migraciones pendientes.
- `forms.py` (342 líneas) — formsets y validaciones.
- Sistema offline de `lista_super/` (IndexedDB, service worker, sync).
- `services/pantry.py` — lógica de "lo que tengo".
- Sistema de amigos/chat (`_panel_amigues.html`, `_chat_modal_content.html`).
- Sistema de lugares (`lugar_detail.html`, `_listado_lugares.html`).
- Sistema de historial.
- `video_list_base.html` (1.294 líneas) — base de listados.
- `filtros_platos.js` (839 líneas) — filtros.
- `menu_print_sheet.js` (618 líneas) — flujo de impresión.
- **Tests**: prácticamente no hay (`tests.py` = 3 líneas). **Deuda técnica.**

## 21. Estado actual / próximos pasos

### Completado (sesión 2026-10-25)
- [x] Fix doble submit en form principal (Commit `ee5b45d`)
- [x] Fix doble submit en variedades (Commit `cbe5352`)
- [x] `_confirm_action_modal.html` extendido con `window.confirmDialog()` (Commit `6905e0b`)
- [x] Confirmación al cerrar sheet con cambios sin guardar (Commit `8be9a97`)
- [x] `beforeunload` para cierre de pestaña/volver
- [x] `_fieldKey` para soportar checkboxes múltiples (bug de `tipos`)
- [x] `CONTEXTO_IA.md` (este archivo)
- [x] Filtro Cotidianos/Especiales (2 checkboxes independientes, default ambos ON = ver todo)
- [x] Backend `categoria__in` respeta `Ambos` en ambos modos; bloqueo del último en JS; URL persistente

### Próximos pasos posibles
- [ ] Recorrer `views.py` y mapear vistas por dominio (candidato a refactor).
- [ ] Escribir los primeros tests de caracterización.
- [ ] Recorrer el sistema offline de `lista_super/`.
- [ ] Recorrer el sistema de menús (programado + print).
- [ ] Ir completando la sección 20 con hallazgos.

- [x] Fix búsqueda: word boundary + unaccent (pollo no trae repollo, atun trae atún)
- [x] Fix bulk delete con AJAX previo (form desconectado por innerHTML del listado)

## 22. Notas de diseño

- Los partials `_*.html` se incluyen desde templates mayores; no son páginas completas.
- Los JS de menú (`menu_programado.js`, `menu_print_sheet.js`) comparten estado; cambios en uno suelen requerir revisar el otro.
- El sheet de crear/editar plato NO es un Bootstrap Modal: es un sheet custom con clase `is-open`. Todos los cierres pasan por `cerrar()`.
- El form de variedades SÍ es un Bootstrap Modal, anidado dentro del sheet.
- `#modalPlato` es el sheet custom. El form de variedades está en `#variedadModal` (Bootstrap).
## 23. Actualización post-sesión (25/10 - tarde/noche)

### Cambios estructurales realizados
- **`nombre_plato` ampliado**: de `max_length=30` a `100` (migración `0102_alter_nombre_plato_100`). *Nota: Railway corre las migraciones mediante el **Pre-Deploy Command** configurado en el panel, no por `nixpacks.toml`.*
- **Limpieza masiva**: se eliminaron 68 archivos residuales (scripts `.sh`, reportes `.txt`, backups viejos) que estaban trackeados en git. Todo recuperable por git o en el tarball local.

### Reglas nuevas en el formulario de platos
- **Sincronización de Tipos**: el backend (`PlatoCreate.get_form`) y el frontend (`get_context_data -> items`) ahora usan exactamente la misma fuente: el diccionario `TIPOS_POR_TEMPLATE` en `views.py`. **Regla**: si agregás un tipo a un template, modificalo *solo* en ese diccionario; ambos lados se actualizan solos.
- **Validación AJAX (form_invalid)**: `PlatoCreate` y `PlatoUpdate` ahora tienen `form_invalid`. Si el request es AJAX y el form falla, devuelven `{"success": false, "html": "..."}` con `status=400`. Esto evita el `alert()` genérico y muestra los errores inline. El JS (`form_init.js`) ya sabe manejar esta respuesta.
- **Al menos un tipo**: `form_init.js` tiene un listener `change` global que impide destildar el último checkbox de `tipos`. Si el usuario lo intenta, se revierte y muestra un mensaje inline por 2.5s.

### Puntos críticos actualizados (reemplaza la sección 15 para estos archivos)
| Archivo | Punto | Qué hace |
|---|---|---|
| `views.py` | `PlatoCreate.get_form` | Filtra tipos según `TIPOS_POR_TEMPLATE`. |
| `views.py` | `PlatoCreate.get_context_data` | Pasa `items` filtrado igual que el form. |
| `views.py` | `PlatoCreate.form_invalid` | Maneja errores AJAX devolviendo JSON. |
| `views.py` | `PlatoUpdate.form_invalid` | Ídem para edición. |
| `form_init.js` | Listener `tipos` (~L1290) | Impide dejar cero tipos marcados. |

### Pendiente de explorar (actualizado)
- **`views.py`** sigue siendo un candidato a refactor (ahora ~5.000 líneas).
- **El bug del `alert()` genérico** que ocultaba errores de validación ya está resuelto. Ahora los errores se ven inline.


## 24. Sesión 2026-10-25 (tarde) — filtros Cotidianos/Especiales

### Implementado
- **Dos checkboxes independientes**: `ver_cotidiano`, `ver_especial`. Default al abrir pantalla: **ambos tildados** (= ver todo: cotidianos + especiales + ambos).
- **Backend**: `filtrar_platos` recibe los flags. Aplica `categoria__in=[COTIDIANO, INDISTINTO]` si solo cotidiano; `[ESPECIAL, INDISTINTO]` si solo especial. Los `Ambos` aparecen siempre.
- **Bloqueo client-side**: no se pueden destildar los dos. Revierte y muestra aviso inline 2.5s. Patrón idéntico al de `tipos` en el form de plato (§23).
- **`popstate` + `pushState`**: la URL persiste `ver_cotidiano=0/1` y `ver_especial=0/1`. Atrás/adelante sincroniza los checkboxes.

### Lección de diseño
- Toggles de **estados combinables** (Cotidiano + Especial pueden estar los dos activos): usar **checkboxes independientes con bloqueo del último**, NO un solo radio. El radio no puede representar "los dos a la vez" ni "ninguno".
- **Ojo con el `?v=`**: el de `filtros_platos.js` y `lo_que_tengo.js` vive en `lista_filtrada.html`, no en `base.html`. La regla de §7 aplica al archivo que **realmente carga** el JS.

### Deuda visual pendiente (no funcional, NO tocar hasta que se pida)
- Alineación / borde rojo al `:checked` / color de los 2 checkboxes nuevos, para que igualen a los otros botones de la barra.
- Legibilidad del icono en modo oscuro.
- Encaje en mobile dentro del modal Filtros (los 2 checkboxes nuevos).

### Pendiente funcional (próximas sesiones, los irá marcando el usuario)
- `palabra_clave`, `quecomemos`, `misplatos` **no** se persisten en la URL (solo `tipopag`, `lo_que_tengo`, `ver_cotidiano`, `ver_especial` sí).
- `medios`, `dificultad`, `categoria` como campos libres en `PlatoFilterForm` no tienen UI (posible legacy).
- Aplicar el toggle Cotidianos/Especiales en otras pantallas (menú, historial) cuando el usuario lo pida.


## 25. Actualización de dependencias (2026-10-25, sesión seguridad)

### Qué se actualizó
| Paquete | Antes | Después | Motivo |
|---|---|---|---|
| Django | 5.0.3 | **5.2.18** | LTS. Corrige SQL injection críticas (CVE-2026-1207/1285/1287) + DoS |
| Pillow | 9.5.0 | **13.0.0** | DoS + memory corruption |
| requests | 2.28.2 | **2.33.0** | CVE-2026-25645 |
| urllib3 | 1.26.15 | **2.8.0** | CVE-2026-44431 |
| asgiref | 3.7.2 | **3.13.0** | Requerido por Django 5.2 |
| certifi | 2022.12.7 | **2026.10.23** | Requerido por requests 2.33 |

### Resultado
- **Dependabot: 74 → 12 vulnerabilidades** (0 critical, 6 high, 6 moderate).
- Las 4 críticas originales (SQL injection Django x2, DoS, memory corruption Pillow) resueltas.
- `STORAGES` ya estaba configurado en `nuestrotubo/settings.py` (Django 4.2+ style) → **no hubo que migrar** el viejo `DEFAULT_FILE_STORAGE`/`STATICFILES_STORAGE`.
- `pip check` + `manage.py check` limpios. Sin migraciones pendientes.

### Deuda explícita (importante)
- **Pillow 13 NO se probó con subida real de imágenes** (el usuario no usa esa feature actualmente). Cuando se empiece a usar, **probar crear plato con imagen** antes de dar por cerrado. Si falla, sospechosos típicos:
  - `Image.ANTIALIAS` removido (deprecado en 9.x, eliminado en 10.x) — buscar en `views.py` o donde se procesen imágenes.
  - Cambios en `ImageOps` / `Image.Resampling`.
  - Fallback: bajar a `Pillow==11.3.0` (sigue parcheado contra las CVEs críticas, con menos cambios de API).
- **12 vulnerabilidades restantes** (6 high, 6 moderate) son de dependencias transitivas y vendorizadas. Candidatos para una sesión futura:
  - Bumps de bajo riesgo: `babel`, `charset-normalizer`, `idna`, `packaging`, `gunicorn`, `whitenoise`, `django-cors-headers`.
  - **Riesgo medio**: `dj-database-url 0.5.0 → 3.1.2` (cambió API entre versiones, revisar parseo de `DATABASE_URL` en Railway).
  - jQuery/Bootstrap vendorizados: actualización manual (bajar versión nueva y reemplazar en `vendor/`).

### Verificación en producción
- Deploy a Railway OK (commit `512e35f`).
- Dependabot recalculó a **12 vulnerabilidades** en el push.
- Login + listado + filtros verificados manualmente.
- **No verificado**: subida de imagen (ver deuda arriba).

### Regla nueva
- **Al actualizar Django de versión menor** (ej. 5.0 → 5.2): correr `pip install -r requirements.txt` y luego `pip check`, `manage.py check`, y arrancar el server. Los conflictos más comunes son pins viejos de **dependencias transitivas** (`asgiref`, `certifi`, `sqlparse`) que Django nuevo exige más nuevos. Actualizar el pin conflictivo uno por uno hasta que `pip install` pase.


## 26. Feature flags activos (funcionalidades ocultas temporalmente)

> Registro de features **implementadas y funcionales** pero **ocultas en la UI** deliberadamente. El código sigue vivo, los datos se siguen procesando, solo no se muestra el control. Cuando se necesiten, se reactivan siguiendo las instrucciones de cada una.

### 26.1 Toggles "Sugerencias Quecomemos" y "Mis platos"

**Estado**: ocultos desde 2026-10-25 (sesión de filtros responsive).

**Motivo**: el usuario no usa esas dos fuentes de platos actualmente. Se ocultan para simplificar la barra de filtros, sin remover el mecanismo.

**Qué hace cada uno** (cuando están visibles):
- **Mis platos**: muestra solo los platos del usuario logueado (`propietario=usuario`).
- **Sugerencias Quecomemos**: muestra los platos del usuario `quecomemos` (catálogo curado), filtrando los "descartados" del usuario.
- Se pueden combinar: los dos tildados = unión de ambos.
- **Regla del backend**: si ninguno está tildado, `filtrar_platos` devuelve lista vacía. Por eso el feature flag fuerza `misplatos`.

**Cómo están ocultos** (2 lugares, hay que revertir ambos):

1. **HTML** en `AdminVideos/templates/AdminVideos/lista_filtrada.html` (~L429):
   ```html
   <!-- FEATURE FLAG: Toggles ocultos. Para reactivar, quitar la clase "d-none" -->
   <div class="d-none" id="toggles-quecomemos-misplatos">
     <input ... name="quecomemos" ...>
     <label ... for="quecomemos">...</label>
     <input ... name="misplatos" ...>
     <label ... for="misplatos">...</label>
   </div>
```


## 27. Deudas tecnicas de filtros (no urgentes, para atacar en sesion aparte)

> Identificadas en la sesion 2026-10-25 (responsive + limpieza del filtro). No son urgentes, pero conviene atacarlas antes de que el sistema crezca.

### 27.1 Triplicacion del texto del boton "crear plato"

**Problema**: la logica de "si tipopag es X, mostrar texto Y" esta escrita en 4 lugares sincronizados:
- `base.html` -> atributo `title` (tooltip)
- `base.html` -> atributo `aria-label`
- `base.html` -> `<span class="boton-crear-plato-texto">` (visible desktop)
- `base.html` -> `<span class="qc-mobile-action-label">` (visible mobile)
- `filtros_platos.js` -> funcion `actualizarBotonCrearPlato()` (actualiza en AJAX)

**Riesgo**: si cambia un texto (ej. "picada armada"), hay que editar 4 lugares o queda inconsistente. Es el mismo tipo de bug que se resolvio con `TIPOS_POR_TEMPLATE` en §23, pero aca no se aplico.

**Solucion propuesta**: custom template tag que devuelva el texto, y que el JS lo lea de un `data-*` en el boton. Una sola fuente.

### 27.2 Mapa de etiquetas de tipos duplicado en JS

**Problema**: `filtros_platos.js` tiene `etiquetaSugerenciasTipopag()` con un objeto hardcodeado con las etiquetas de cada tipo ("Platos principales", "Guarniciones", etc.). Esto repite `TIPOS_POR_TEMPLATE` del backend (`views.py`).

**Riesgo**: si se agrega un tipo nuevo (ej. "Snack"), el backend lo conoce pero el JS no -> el titulo queda desactualizado sin error visible.

**Solucion propuesta**: pasar el mapa completo desde el contexto del backend como JSON embebido en el HTML, y que el JS lo lea.

### 27.3 Persistencia en URL
**RESUELTO el 2026-10-26**. Ahora persisten en la URL todos los filtros:
`tipopag`, `lo_que_tengo`, `ver_cotidiano`, `ver_especial`, `palabra_clave`, `quecomemos`, `misplatos`.
- Implementado en `filtros_platos.js` (debounce `replaceState` para palabra clave, `pushState` para el resto).
- `popstate` restaura el estado completo.
---

### Lo que NO vale la pena tocar (dejarlo como esta)

- Partir `filtros_platos.js` en varios archivos: no agrega valor.
- Sistema de barrido visual: es elegante, nadie nota si se simplifica. Dejarlo.
- `!important` en CSS: es feo pero no rompe. Esperar a una sesion de limpieza general.
- Header `X-QC-Stateless-Filters: 1`: misterioso. Investigar solo si se confirma que alguien lo lee.
- Tests: es una deuda separada (§20), no de esta sesion.


### Prioridad recomendada (cuando se ataquen)

1. ~~§27.3 Persistencia URL~~ (completado 2026-10-26).
2. §27.1 Template tag del boton crear (~30 min, evita bugs futuros).
3. §27.2 Mapa de tipos desde backend (~20 min, identico al fix de §23).

### 27.4 Búsqueda por palabra: word boundary + sin acentos
**RESUELTO el 2026-10-26**. Bug: "pollo" traía "repollo" (substring sin boundary) y "atun" no encontraba "atún".
- **Fix**: `django.contrib.postgres` + `UnaccentExtension` (migración `0103`) + lookup `__unaccent__iregex`.
- **Patrón**: `_patron_busqueda(texto)` en `views.py` — normaliza tildes con `unicodedata`, escapa con `re.escape`, prefija con `\m` (word boundary al inicio).
- **Aplicado en**: `filtrar_platos`, `filtrar_platos_por_lo_que_tengo`, `obtener_resultados_principales` (Delivery y Comerafuera).
- **Comportamiento**: `\mpollo` matchea Pollo/Pollos/Pollería; NO repollo. Permite plurales y derivados. Frase exacta (no AND de palabras).
- **Tests pasados**: pollo→7 platos sin repollo; atun→atún; POLLO==pollo; atún==atun.

### 27.5 Bug detectado: `bulk-delete-form` ID duplicado
**DETECTADO el 2026-10-26**. Hay 2 `<form id="bulk-delete-form">` en la misma página:
- `_listado_platos.html:83` (endpoint `eliminar-platos-masivo`)
- `_listado_lugares.html:111` (endpoint `eliminar-lugares-masivo`)
- `getElementById` devuelve el primero (platos). **Borrado masivo en Lugares/Delivery probablemente usa endpoint equivocado.**
- **Verificar** si al borrar lugares desde el listado falla. Si sí: renombrar IDs a `bulk-delete-form-platos` y `bulk-delete-form-lugares`, actualizar `data-confirm-submit-form` en `initListadoPlatos` y en `_confirm_action_modal.html`.



### 27.6 Postres faltaba en el contexto del modal `#asignarPlatoModal`
**RESUELTO el 2026-10-27**. El botón "+ Postre" abría el modal con el `<select id="tplPostre">` vacío.
- **Causa**: `FiltroDePlatos` pasaba `salsas` y `guarniciones` al contexto, pero no `postres`.
- **Fix**: nueva función `obtener_postres(usuario)` + cálculo en `FiltroDePlatos` + `"postres": postres` en el dict del contexto.
- **Deuda futura**: el modal vive en `base.html` (todas las vistas) pero solo `FiltroDePlatos` pasa `postres`/`salsas`/`guarniciones`. En otras vistas los `<select>` quedan vacíos. Fix arquitectónico: mover a `context_processor`.

### 27.7 Botones "+ Salsa", "+ Guarnición", "+ Postre" en menú programado
**IMPLEMENTADO el 2026-10-27**. En cada plato Principal del menú programado (por comida), hay 3 botones que abren `#asignarPlatoModal` con el plato precargado + la fila del extra ya agregada.
- **`_menu_programado_item.html`**: botones con `data-extra-tipo`, `data-extra-plato-id`, `data-extra-plato-nombre`, `data-extra-dia`, `data-extra-comida` (sin `id=` para evitar duplicados en almuerzo/cena).
- **`_menu_programado_comida.html`**: pasa `dia=dia` al include.
- **`menu_programado.js`**: handler `.js-asignar-extra` que setea hidden inputs del modal, hace `await setPlatoInfo(...)`, `addExtraRow(tipo)` y abre el modal.
- **Reutiliza**: el modal, `addExtraRow`, y el view `AsignarPlato` (que ya procesa `extra_tipo`/`extra_id`).
- **Sin migración**. Bump de `menu_programado.js` en el template que lo carga.

### 27.8 Muteo de comidas vacías en menú programado
**IMPLEMENTADO el 2026-10-27**. Comidas sin platos se ven atenuadas.
- **`_menu_programado_comida.html`**: wrapper `.menu-programado-comida-wrapper` con clase `.menu-programado-comida-vacia` si `not platos`.
- **`mi-css.css`**: `.menu-programado-comida-wrapper.menu-programado-comida-vacia` → `opacity: 0.45`, `h6` gris con `--bs-secondary-bg`. Hover sube a `0.7`.
- **JS intacto**: `data-menu-dia`/`data-menu-comida` siguen en el `<div>` interno.
- Solo apaga, no oculta.

## 28. Reglas de comunicación y trabajo con el dueño

> Reglas de formato y comunicación acordadas por el dueño. **Aplican siempre, sin excepción.**

### 28.1 Terminal: un solo bloque por paso
- **Todos los comandos que se pidan van en UN SOLO bloque de código**, no en varios mensajes.
- Si son pasos múltiples, van separados con `echo "=== Paso X ==="` dentro del mismo bloque.
- El dueño copia una vez y ejecuta.

### 28.2 `--no-pager` obligatorio en comandos git
- Todo comando `git` debe llevar `--no-pager` (`log`, `diff`, `show`, `status`).
- **Razón**: sin `--no-pager`, la terminal abre `less` y hay que apretar `q`, rompiendo el flujo.

### 28.3 Bump del `?v=` también para CSS
- Cada vez que se modifica un `.css` propio, **bumpear el `?v=`** en el template que lo carga.
- Buscar con: `grep -rn "\.css' %}" AdminVideos/templates/ | grep -v backup`
- Misma lógica que §7 para JS.

### 28.4 Código extenso: archivos `.sh` o `.py` (no heredoc)
- **Nunca** pasar más de ~20 líneas de Python/bash/markdown directo a la terminal.
- Los heredocs con `<<'PY'` o `<<EOF` se rompen con backticks, `<div>`, markdown o bloques de código. **Es el problema más recurrente.**
- **En cambio**: escribir el script en un archivo (`.sh` o `.py`) en VS Code y ejecutarlo con `bash script.sh` o `python3 script.py`.
- **Excepción**: cambios chicos de Python (1-2 anchors, sin backticks), heredoc con `<<'PY'` es aceptable.

### 28.5 Diagnósticos: archivos `.txt` en vez de pegar output
- Dar **un solo comando** que redirija el output a un `.txt`:
  ```bash
  { echo "=== A ==="; grep -rn "algo" dir/; echo "=== B ==="; sed -n 'X,Yp' file; } > diagnostico.txt


### 28.6 Cierre: un solo bloque para todo el paso
- Si un paso incluye **script + verificación + commit + push** → va todo en **un bloque**.
- Excepción: si requiere **decisión del dueño entre medio**, se parte en 2 bloques.

### 28.7 Regla general
> El dueño copia, pega, ejecuta. **Minimizar la fricción** es la regla de oro.


### 28.8 Regex peligroso en CSS (lección 2026-10-26)

- **Nunca usar `[\s\S]*?` en regex para "encontrar bloques" de CSS.** Un regex como `/* =+[\s\S]*?filtro-keyword-clear...` puede matchear desde el **PRIMER** `/* ===` del archivo hasta el bloque buscado, borrando **TODO el CSS intermedio**.
- **Síntoma**: `git --no-pager diff --stat` muestra "~2900 líneas borradas" en `mi-css.css`. La página se rompe con layout caótico (inputs superpuestos, colores mal, todo desalineado).
- **Regla**: cuando se modifica un `.css` grande, **append al final** (seguro) o **reemplazo por bloque exacto** con `s.count(anchor) == 1`. **Nunca** regex con wildcards amplios.
- **Rollback inmediato**: `git checkout HEAD -- <archivo>`. Vuelve al estado del último commit sin perder cambios ya commiteados.


## 29. Carta de restaurante (subtipo_carta + agrupación)

### Motivación
El listado de platos estaba mezclado, ordenado por historial de programación (bueno para "¿qué cocino?", malo para "leer una carta"). El dueño pidió un sistema que agrupe los platos como una carta real.

### Modelo (migración 0104)
- **Campo nuevo** `Plato.subtipo_carta` (CharField, choices, blank, default="").
- **Choices** (`SUBTIPO_CARTA_CHOICES` en `models.py`): `carnes_rojas`, `aves`, `cerdo`, `pescados`, `embutidos`, `pastas`, `masas`, `guisos`, `vegetarianos`, `otros`, `""`.
- **Orden de aparición** (`SUBTIPO_CARTA_ORDEN` en `models.py`): lista con el orden de la carta.
- **Solo aplica a "Principal"**. Otras tabs siguen sin subtipo.

### Form (crear/editar plato)
- `PlatoForm.fields` incluye `subtipo_carta`.
- `<select>` visible en la sección "Clasificación" del form, debajo de "Categoría".
- Guía visual: "(solo para platos principales)".

### Orden en `filtrar_platos`
- **Tab Principal**: `order_by` por `subtipo_orden` (Case/When con `SUBTIPO_CARTA_ORDEN`) + `nombre_plato` (alfabético).
- **Otras tabs**: order_by por historial de programación (sin cambios).

### Agrupación (`agrupar_platos_para_carta`)
- Función en `views.py` que devuelve `[{codigo, titulo, platos}, ...]` respetando el orden de la carta.
- Platos sin subtipo: al final en un grupo "Sin clasificar".
- Se calcula en `FiltroDePlatos` y `ajax_listado_platos`, se pasa como `platos_agrupados_carta`.

### Template (`_listado_platos.html`)
- Nuevo bloque `{% elif platos_agrupados_carta %}`:
  - Header: `<div class="plato-grupo-header">` con nombre + contador.
  - Iteración de platos del grupo (reusa `_plato_row_gmail.html`).

### CSS
- `.plato-grupo-header`: borde izquierdo violeta, fondo `--bs-tertiary-bg`, uppercase + letter-spacing.
- `.plato-grupo-count`: pill con cantidad de platos.
- Dark mode: fondo violeta suave, borde primario.
- Estilos al final de `mi-css.css` (regla §28.8).

### Clasificación masiva inicial
- Script one-shot aplicó subtipo a los 67 principales por palabras clave del nombre.
- Resultado: 69/69 principales clasificados.
- Para platos nuevos: usar el `<select>` en el form.

### Deudas futuras (no urgentes)
- **Clasificaciones imperfectas**: "Mondongo" → guisos, "Torre de panqueques" duplicado.
- **Aplicar subtipo a Guarniciones y Postres**. Hoy solo Principal.
- **Color por subtipo** en el header.
- **Colapsar/expandir grupos** con click.
- **Bulk edit**: reasignar subtipo a varios platos a la vez.

## 30. Sesión 2026-10-31 — Refactor variedades cerrado + Feature "Duplicar plato"

### 30.1 Refactor "remove-variedades" — cerrado y deployado

**Estado**: mergeado a `main` (`ebc74d7`) y **deployado a Railway**. Producción sin variedades.

**Lo que se eliminó** (modelo + vistas + UI):
- `Plato.plato_padre`, `Plato.nombre_grupo`, `Plato.nombre_para_front`, `Plato.es_variedad()`.
- `ElegirPlatoForm` completa.
- `PlatoVariedadCreate/Update/Delete` + 3 URLs.
- UI de "Variedades" en `plato_form_inner.html`, `plato_detail_content.html`, `_plato_row_gmail.html`, `_plato_card_detalle.html`.
- Modal `#variedadModal` (template + inyección dinámica en `form_init.js`).
- Migración `0106_remove_variedades_fields` (2 `RemoveField`).
- ~750 líneas propias netas.

**Backup**: `backups_variedades/platos_campos_variedades.json` (121 platos, 7 con `nombre_grupo`).
**Histórico**: migraciones `0065`, `0068`, `0074` NO se tocan (historia).

### 30.2 Intentó "Carpetas de variedades" — DESCARTADO, rama de respaldo

**Idea inicial**: agrupar platos como "Milanesas" con viñetas adentro. Se implementó (modelo `Carpeta`, FK `Plato.carpeta`, endpoint "crear variedad", agrupación en menú programado). **Se revirtió** por:
- El feature agregaba complejidad sin resolver un problema real.
- "No es lo mismo una milanesa que otra" (carne ≠ berenjena ≠ pollo).
- `subtipo_carta` (§29) ya agrupa mejor (Carnes rojas, Vegetarianos, Aves).
- El Paso 5 modificó el **menú programado** por error, cuando el pedido era el **listado tipo Gmail**.

**Rama de respaldo**: `carpetas-wip` (5 commits). Si en el futuro se retoma, `git checkout carpetas-wip`. **No está deployada**. Prod sigue en `ebc74d7`.

**Lección**: cuando el dueño dice "menú", preguntar si es "menú programado" o "listado". Y no construir agrupaciones sobre `subtipo_carta` sin validar que no dupliquen la funcionalidad.

### 30.3 Feature "Duplicar plato" — implementado (commit `dd1a26f`)

**Objetivo**: hacer visible la función "duplicar plato" en el listado Gmail y en el card detalle. Sacarla del form (ruido). Fixear bug de `descartar-sugerido`.

**Cambios**:

1. **Fix bug `agregar_a_mi_lista`** (`views.py`):
   - **Antes**: duplicar un plato propio lo marcaba como `sugerido_importado` y hacía `descartar-sugerido`. Efecto: el original desaparecía del listado.
   - **Ahora**: si `plato_original.propietario == request.user` → duplicado normal, `messages.success("Plato duplicado como «X (copia)»")`, redirect a `return_to`. El original **sigue visible**.
   - Si `propietario != request.user` → flujo original de importación (marca `sugeridos_importados`, descarta sugerido).
   - **Formato del nombre**: `"{nombre_original} (copia)"` (antes era `"Copia de {nombre}"`). El nuevo formato ordena alfabéticamente junto al original: "Milanesa", "Milanesa (copia)", "Milanesa de pollo".

2. **Botón "Duplicar"** en `_plato_row_gmail.html` (listado Gmail):
   - Ícono `fa-clone` (`fa-regular`), clase `plato-gmail-action-btn`.
   - Solo si `plato.propietario == request.user`.
   - Link GET a `{% url 'agregar-a-mi-lista' plato.id %}?duplicar=true`.
   - Sin confirmación.

3. **Botón "Duplicar"** en `_plato_card_detalle.html` (card + carousel):
   - `btn-sm btn-outline-secondary` con texto "Duplicar".
   - Al lado de "Editar". Solo si propio.

4. **Limpieza del form** (`plato_form_inner.html`):
   - **Sacado** el botón "Duplicar" (provocaba confusión: "¿se cierra el form actual? ¿se abre otro?").
   - **Sacado** el botón "Ingredientes" (redundante: ya está en listado Gmail con `fa-list-check` y en card detalle con `js-plato-ingredientes`).
   - El `<div aria-label="Acciones del plato">` que los contenía se eliminó completo.

5. **El botón "Duplicar" del detalle** (`plato_detail_content.html`) **se mantiene** — no tiene el problema del form y es un lugar natural.

**Sin migración. Sin JS nuevo. Sin bump de CSS.**

**Puntos críticos actualizados** (§15):
| Archivo | Punto | Qué hace |
|---|---|---|
| `views.py` | `agregar_a_mi_lista` (~L4120) | Duplicar plato propio vs importar ajeno. Formato `"{nombre} (copia)"`. |
| `_plato_row_gmail.html` | `plato-gmail-action-duplicar` (~L46) | Ícono `fa-clone`. Solo propio. |
| `_plato_card_detalle.html` | botón "Duplicar" (~L170) | Al lado de Editar. Solo propio. |
| `plato_form_inner.html` | `Datos principales` (~L113) | Ya no tiene botones "Duplicar" ni "Ingredientes". |

### 30.4 Deuda pendiente

- `git config --global user.email/name`: el warning de commits sin identidad persiste. No bloquea. Arreglar cuando se quiera.
- `.DS_Store` untracked en varios directorios: ruido macOS. Considerar agregar a `.gitignore` en una sesión de limpieza.
- Rama `carpetas-wip`: borrar (`git branch -D carpetas-wip`) o conservar. Si se conserva, no molesta.
- `backups_variedades/` en `.gitignore`: los archivos están untracked, sin riesgo. Deuda de limpieza.


### 30.5 Sesión 2026-10-31 (continuación) — Botones completos en listado Gmail + muteo de carousel

**Commits**: `dd1a26f` (botones Gmail + fix bug) y `44ed2b3` (muteo carousel). Deployados a Railway.

#### 30.5.1 Botones en `_plato_row_gmail.html` (listado tipo Gmail)

Antes había 2-4 botones según caso. Ahora hay **hasta 7** en este orden:

| Botón | Cuándo aparece | Ícono | Acción |
|---|---|---|---|
| Ver enlace | `plato.enlace` | `fa-arrow-up-right-from-square` | Link externo, pestaña nueva |
| Programar | Siempre | `fa-calendar-plus` | Abre `#asignarPlatoModal` |
| Ingredientes | Siempre | `fa-list-check` | Abre modal ingredientes (AJAX) |
| Compartir | `amigues` | `fa-share-nodes` | Abre `#compartirModal` (sin dropdown de historial) |
| Editar | `propietario` | `fa-pen-to-square` | Abre sheet de edición |
| Duplicar | `propietario` | `fa-clone` | Crea copia (ver §30.3) |
| Eliminar | `propietario` | `fa-trash-can` | `confirmDialog` + `eliminar-plato` |

**Importante:** todos los botones tienen `onclick="event.stopPropagation();"` para **no disparar el click del row** (que abre el detalle).

**El dropdown de historial de compartidos NO se replica en el listado** — son ~90 líneas HTML por plato × 121 platos = ~11k de HTML extra. Se accede desde el card detalle. Si en el futuro se necesita, evaluar alternativa (lazy load, ajax, etc.).

**CSS**: reutiliza `.plato-gmail-action-btn` (no se agregó CSS nuevo). Sin bump de JS.

#### 30.5.2 Muteo de indicadores del carousel (`_menu_programado_dias.html` + `mi-css.css`)

**Motivación**: en el carousel mobile de comidas (Desayuno · Almuerzo · Merienda · Cena), los indicadores de comidas sin plato programado se veían igual que los que sí tenían. El dueño pidió atenuarlos, igual que §27.8 (wrapper de comida vacía).

**Cambios:**
- **Eliminado**: la regla `.meal-link.has-plato::after` que dibujaba un **tilde verde** (`✓`) al lado del link. Redundante: el contraste apagado/activo ya es suficiente.
- **Agregado** al final de `mi-css.css`:
  ```css
  .meal-link:not(.has-plato) {
    opacity: 0.45;
  }
  .meal-link:not(.has-plato):hover,
  .meal-link:not(.has-plato):focus-visible {
    opacity: 0.7;
  }
  ```

- **HTML**: sin cambios. La clase `has-plato` ya existía en `_menu_programado_dias.html` (`{% if dia_plato.1.X %}has-plato{% endif %}`).
- **Modo oscuro**: las reglas `[data-bs-theme="dark"] .meal-link` ya existentes cubren el color. La opacidad aplica en ambos modos.
- **Bump**: `mi-css.css` → `?v=20261031_220000` en `base.html` L49.

#### 30.5.3 Puntos críticos actualizados (§15)

| Archivo | Punto | Qué hace |
|---|---|---|
| `_plato_row_gmail.html` | bloque `.plato-gmail-actions` (~L25-100) | 7 botones en orden. Cada uno con `stopPropagation`. |
| `mi-css.css` | `.meal-link:not(.has-plato)` (~L3029) | Muteo de indicadores de comida sin programar. |
| `mi-css.css` | `[data-bs-theme="dark"] .meal-link` (~L1213) | Color en modo oscuro. |

#### 30.5.4 Deuda nueva / consideraciones

- **Dropdown de historial de compartir en el listado**: no replicado (§30.5.1). Si se necesita, es un mini-proyecto aparte (lazy load o modal).
- **`_plato_card_detalle.html` (card/carousel del listado)**: tiene los mismos 7 botones pero con **texto** (`btn-sm btn-outline-secondary`), no solo íconos. Estilos diferentes entre listado y card por diseño. No unificar sin pedido explícito.
- **Ver enlace en el card** solo aparece si `plato.enlace`; el card lo muestra con texto "Ver enlace" y el listado con ícono. Coherente con el resto.

#### 30.5.5 Fix barrido que se despegaba al scrollear (`5f3d8c5`)

**Bug reportado**: el overlay shimmer del filtro (`.filtro-platos-barrido-overlay`) se posicionaba una sola vez con `getBoundingClientRect()`. Al scrollear durante la carga, el listado se movía pero el overlay quedaba en el `top/left` viejo → visualmente despegado.

**Fix** (`filtros_platos.js`, ~15 líneas): listener `scroll` + `resize` que, solo si el overlay tiene `.is-active`, recalcula la posición vía `requestAnimationFrame` (con flag para evitar doble rAF por frame).

**Punto crítico nuevo (§15)**:
| Archivo | Punto | Qué hace |
|---|---|---|
| `filtros_platos.js` | `reposicionarBarridoEnScroll` | Reposiciona el overlay shimmer al scrollear/resizear. rAF con debounce natural. |

**Alternativa evaluada y descartada**: reemplazar el shimmer por un spinner centrado (overlay con ícono `fa-spinner fa-spin`). Se descartó porque el shimmer gustaba y el costo del fix era menor. Si en algún momento se quiere migrar a spinner, la función a reemplazar es `activarBarridoCambioFiltro` / `desactivarBarridoCambioFiltro` + el bloque CSS `.filtro-platos-barrido-overlay*` en `mi-css.css`.

### 30.6 Selector de categorías rediseñado (`3dbcc56`)

**Motivación**: el dueño reportó sobrecarga visual del estado activo (fondo + borde + glow + redondel en el ícono + desplazamiento) y pidió integrar el selector al bloque de platos.

**Cambios aplicados:**

1. **Consolidación de reglas `.is-active`**: había 2 reglas duplicadas (light) + 2 (dark) que se contradecían. Ahora:
   - **Light**: fondo azul suave `rgba(78,115,223,0.14)` + texto/ícono `var(--bs-primary)`. Sin borde, sin glow.
   - **Dark**: fondo `rgba(78,115,223,0.20)` + texto `#a3b8f0`. Sin borde, sin glow.
   - **Rojo "lo que tengo"**: mismo esquema con `#dc3545` (light) y `#ff7f8c` (dark). Se eliminó la duplicada.

2. **Redondel del ícono eliminado**: `.selector-platos-item .icon-wrap` ya no tiene `background` ni `border`. Solo el ícono centrado. El único caso que conserva redondel es el activo rojo (visualmente necesario).

3. **Hover simplificado**: sin `border-color`, sin `transform: translateY(-1px)`, sin `text-decoration`. Solo `background: var(--bs-secondary-bg)` + `color: var(--bs-body-color)`.

4. **Shell transparente (opción B)**: `.selector-platos-shell` ya no tiene `background`, `border`, `box-shadow`, `border-radius`. Ahora flota integrado al bloque de platos. Se eliminó `[data-bs-theme="dark"] .selector-platos-shell`.

5. **Agrupación semántica + separadores**:
   - Grupos visuales: `[Todos] | [Principales] [Entradas] [Guarniciones] | [Dips] [Salsas] | [Picadas] [Ingredientes de picada] | [Postres] | [Bebidas y tragos] | [Delivery] [Comer afuera]`.
   - `.selector-platos-sep`: línea vertical 1px entre grupos (`var(--bs-border-color)` light, `rgba(255,255,255,.15)` dark).
   - `.selector-platos-sep-fuerte`: 2px + `var(--bs-secondary-color)` después de "Todos" para destacarlo.
   - Guarniciones se movió de "Extras" al grupo "Platos" (es importante, cerca de Entradas).

**Puntos críticos nuevos (§15)**:
| Archivo | Punto | Qué hace |
|---|---|---|
| `_selector_horizontal_platos.html` | `<span class="selector-platos-sep">` | Separadores entre grupos. 1 fuerte (después de Todos) + 5 sutiles. |
| `mi-css.css` | `.selector-platos-shell` (~L1690) | Ahora transparente, sin borde/sombra. |
| `mi-css.css` | `.selector-platos-item:hover` | Solo `background: var(--bs-secondary-bg)`, sin borde/transform/underline. |
| `mi-css.css` | `.selector-platos-item.is-active` | Fondo suave + texto primary. Sin glow/redondel. |
| `mi-css.css` | `.selector-platos-sep` + `-fuerte` | Separadores verticales con dark mode. |

**Deuda pendiente**:
- **Probar Opción C**: mover el selector adentro del wrapper del bloque de platos. Requiere tocar `pre-base.html` (wrapper nuevo) + `mi-css.css` (mover fondo del listado al wrapper). No urgente — la opción B ya integra visualmente.
- **Ajuste fino del gap** entre selector y bloque de platos (hoy `m-2` en el wrapper del listado). Se puede ajustar a `mt-0` si se siente mucho.

**Rollback**: si en el futuro se quiere volver al diseño anterior del selector, `git revert 3dbcc56` revierte todo el rediseño (sin migraciones, solo CSS + HTML de tabs).

### 30.7 Sesión 2026-11-01 (cont.) — Jerarquía tipo carta + acordeón en "Todos"

#### Cambios principales

**Tab "Todos" ahora tiene 3 niveles jerárquicos:**

1. **Nivel 1** (tipo): `Platos Principales`, `Entradas`, `Guarniciones`, `Dips y Salsas`, `Picadas`, `Ingredientes de picada`, `Postres / Reposterías`, `Bebidas / Tragos`.
   - Banda con `background: var(--bs-secondary-bg)`, texto bold uppercase con tracking.
   - Chevron + badge count + acordeón colapsable (persistente en localStorage).
2. **Nivel 2** (subtipo_carta, solo en Principal/Postre): `Carnes rojas`, `Aves`, `Pastas`, etc.
   - Susurro tipográfico: texto muted, chico, sin fondo.
3. **Items**: indentados bajo subgrupo, sin líneas verticales.

**Persistencia del acordeón:**
- `localStorage.qc_grupos_abiertos` = `{codigo: bool}`.
- `MutationObserver` en `#contenedor-listado-platos` re-aplica el estado después de cada AJAX (crítico: el refresco por filtros reemplaza todo el DOM).

**Defensa en código:**
- `tiene_subtipo` solo se evalúa si `codigo in ("Principal", "Postre")` (evita que un dato sucio como "salsa roja" con `subtipo=carnes_rojas` genere un "Carnes rojas" espurio).
- Dato limpiado: id=347 "salsa roja" perdió `subtipo_carta="carnes_rojas"` (deuda del script one-shot de §29).

**Limpieza CSS:**
- `.plato-row` sin `border-left` (raya de procedencia) ni `border-top`.
- `.plato-row.is-carousel-active` sin `box-shadow: inset` (era la "raya" entre header y primer plato).
- `.plato-grupo-acordeon` con `margin: 0; padding: 0` (details por defecto del browser).

**Puntos críticos nuevos (§15):**
| Archivo | Punto | Qué hace |
|---|---|---|
| `views.py` | `ORDEN_GRUPOS_LO_QUE_TENGO` | 8 grupos: Principal, Entrada, Guarnicion, Dip, Picada, Ingrediente de picada, Postre, Trago. |
| `views.py` | `agrupar_platos_para_lo_que_tengo` | Subgrupos por `subtipo_carta` SOLO en Principal/Postre. |
| `grupos_acordeon.js` | `observarContenedor` | MutationObserver que re-aplica localStorage después de cada AJAX. |
| `mi-css.css` | `.plato-grupo-nivel1` (~L####) | Banda nivel 1 con `secondary-bg`. |
| `mi-css.css` | `.plato-grupo-header` | Nivel 2 susurro, sin border. |
| `mi-css.css` | `.plato-subgrupo-bloque` | Wrapper de anidación de items. |

**Deuda pendiente:**
- Limpiar `backups_variedades/` (untracked, no molesta).
- `rm -rf backups_variedades/` está en `.gitignore`.



### 30.8 Sesión 2026-11-01 (cont.) — Carrusel sticky, spinner, limpieza de filas

**Commits**: `622f268` (el commit final de esta iteración, -493 líneas).

#### 30.8.1 Carrusel de platos sticky

**Objetivo**: la card de detalle (imagen + botones Programar/Ingredientes/Editar/Duplicar/Eliminar) queda **fija arriba** al scrollear; el listado se desliza debajo.

**Implementación**:
- `#contenedor-carousel-platos` con `position: sticky; top: 0; z-index: 10; background: var(--bs-body-bg)`.
- **Mobile** (`max-width: 767.98px`): `max-height: 60vh; overflow-y: auto` (para no tapar todo el listado).

#### 30.8.2 Fix del `overflow` que rompía sticky

**Problema**: `position: sticky` no funciona si algún ancestro tiene `overflow-x: hidden` (comportamiento viejo de `#content-wrapper`).

**Solución**:
```css
#content-wrapper {
  overflow: clip !important;
}


### 30.9 Sesión 2026-11-02 — Eliminación total del sistema de acciones masivas

**Motivación**: El dueño notó que la cantidad de platos en el sistema nunca va a justificar "seleccionar varios para borrar en masa". Es complejidad innecesaria. Si se necesita más adelante, se reinstala.

#### 30.9.1 Qué se eliminó
- **Backend**: `eliminar_platos_masivo` y `eliminar_lugares_masivo` (`views.py`) + sus URLs.
- **Templates Platos y Lugares**: barras superiores con checkbox master, badge "N seleccionados", iconos de bulk, y forms ocultos (`bulk-delete-form`).
- **Filas**: checkboxes individuales en `_plato_row_gmail.html` y `_listado_lugares.html`.
- **JS**: función `initListadoPlatos` + todos sus helpers (`getSelectedIds`, `updateSelectedCount`, handlers de checkboxes). **-5569 chars** en `video_list_base.html`. Además se eliminaron **3 scripts huérfanos** (uno de ellos roto, con `DOMContentLoaded, );`).
- **CSS**: `.platos-acciones-bar`.

#### 30.9.2 Cómo se hacen ahora las acciones individuales
- Como las filas son limpias y el carrusel sticky siempre está visible arriba, las acciones se hacen **haciendo click en la fila** (que cambia el carrusel al plato correspondiente) y luego usando los botones grandes del carrusel (Programar, Ingredientes, Editar, Duplicar, Eliminar).

#### 30.9.3 Puntos críticos actualizados
- `_listado_platos.html`: ya no tiene `platos-acciones-bar` ni `checkbox`.
- `video_list_base.html`: mucho más liviano (-5.5k chars).
- `_confirm_action_modal.html`: limpio, ya no tiene lógica para `submitMode === "bulk-delete"`.
- **Deuda técnica saldada**: se arregló el bug histórico (§27.5) de IDs duplicados en `bulk-delete-form` entre Platos y Lugares, simplemente eliminándolos.

#### 30.9.4 Limpieza de `.DS_Store`
- Los archivos `.DS_Store` (basura de macOS) se colaron en el commit `01ced8a`.
- **Acción**: `git rm --cached` para todos y agregar al `.gitignore` global para que no vuelvan a entrar.



### 30.10 Sesión 2026-11-02 — Carrusel sticky, spinner de carga, viñeta y limpieza

#### 30.10.1 Carrusel de platos sticky + dots

- **Sticky**: `#contenedor-carousel-platos` con `position: sticky; top: 0; z-index: 10; background: var(--bs-body-bg)`.
- **Fix crítico para que sticky funcione**: `#content-wrapper { overflow: clip !important }`. El vendor `sb-admin-2` ponía `overflow-x: hidden` que rompe sticky. `overflow: clip` resuelve y evita el artifact de "puntitos" que aparecía con `clip visible`.
- **Dots minimalistas**: 5px, `var(--bs-secondary-color)` con 0.35 opacidad, activo `var(--bs-primary)`.
- **Dots ocultos en mobile**: con 20+ slides son inútiles en touch. Navegación: swipe + flechas prev/next.
- **Dots al final del card con flexbox** (importante): el HTML tiene `.carousel-indicators` ANTES de `.carousel-inner`. Para que aparezcan abajo: `.carousel { display: flex; flex-direction: column }`, `.carousel-inner { order: 1 }`, `.carousel-indicators { order: 2; position: static }`.
- **Imagen en mobile**: `height: 70px; object-fit: cover` (era 225px).


#### 30.10.2 Spinner de carga (reemplazo del barrido/shimmer)

- **Problema**: el barrido del filtro (overlay con animación shimmer) se "despegaba" al scrollear.
- **Solución**: spinner de Bootstrap creado dinámicamente por JS en `<body>`.
- **`mostrarSpinnerCarga()`** → crea `<div id="filtrosLoadingBackdrop">` con `<span class="spinner-border">`. Lo agrega al body.
- **`ocultarSpinnerCarga()`** → lo elimina.
- **CSS**: `.filtros-loading-backdrop { position: fixed; inset: 0; z-index: 1045; background: rgba(0,0,0,0.15); display: flex; align-items: center; justify-content: center }`.
- **Eliminado completamente**: `.filtro-platos-barrido-overlay`, `@keyframes filtroPlatosBarrido`, `reposicionarBarridoEnScroll`, todos los helpers `*Barrido*` (~-2000 líneas de JS).

**Importante**: el spinner se crea en `<body>`, no en el template, porque el AJAX reemplaza `#contenedor-listado-platos` con `innerHTML`. Si estuviera en el template, desaparecería en cada refresh.

#### 30.10.3 Viñeta azul en cada plato

- `.plato-row-nombre::before { content: "•"; color: var(--bs-primary); margin-right: 0.45rem; font-weight: bold }`.
- Punto azul a la izquierda de cada plato. Simple, sin tocar HTML.


#### 30.10.4 Filtros: layout mobile + íconos

- **Input full-width** en mobile (fila 1).
- **Íconos alineados en fila 2** con wrapper `.filtros-iconos-row`: casa + lápiz + tazón + estrella, todos centrados.
- **Ícono "Con lo que tengo"**: cambiado de `fa-basket-shopping` (canasto → remitía a "comprar") a **`fa-house`** (casa → remite a "lo que tengo en casa").
- **Casa + lápiz agrupados en píldora** con divisor: `[🏠|✏️]` como un solo control (la casa activa, el lápiz edita).
- **Altura uniforme** de los 4 íconos: `height: 2.25rem; padding: 0.375rem 0.5rem; align-items: center; line-height: 1`.

#### 30.10.5 Shell suave alrededor del panel

- `.filtro-platos-inline-shell { background: var(--bs-tertiary-bg); border-radius: 0.75rem; padding: 0.5rem 0.75rem; margin-bottom: 0.5rem }`.
- Card adentro transparente (`bg-transparent` en HTML) → una sola caja visual.
- Eliminado `mb-2` del `<form>` para padding simétrico arriba/abajo.


#### 30.10.6 Fix puntas negras (bug histórico)

**Síntoma**: en las esquinas redondeadas del `.filtros-platos-card` aparecían triángulos oscuros.

**Causa**: `<div class="shadow bg-dark p-0">` en `pre-base.html:52` (envolviendo `{% block filtro %}`). El `bg-dark` de Bootstrap pintaba el fondo gris oscuro (`rgb(90,92,105)`), que asomaba por las esquinas donde el card (con `border-radius: 8px`) no lo cubría.

**Diagnóstico**: `document.elementsFromPoint()` en las 4 esquinas exactas del card. Los últimos elementos de la pila revelaron el wrapper oscuro.

**Fix**: eliminado el wrapper completo en `pre-base.html`. Sin CSS nuevo, sin `!important`.

#### 30.10.7 Deudas técnicas pendientes

1. **502 `!important`** en `mi-css.css`. Muchos de esta sesión. Candidatos a limpieza.
2. **5 bloques duplicados** de `.modo-desktop.lo-que-tengo-global` (L2536, 2591, 3431, 3546, 3559).
3. **35 bloques `@media`** dispersos. Consolidar.
4. **Rama `carpetas-wip`** (feature descartado, decidir borrar o conservar).

### 30.11 Sesión 2026-11-02 (cont.) — Fix dark mode filtro + shell transparente

#### 30.11.1 Bug del doble contenedor en dark mode

**Síntoma**: en light mode el filtro se veía con 1 sola caja (shell suave). En dark mode aparecían 2 cajas superpuestas (shell gris + card oscuro adentro).

**Causa raíz**: en mi-css.css (L1007-1020) hay una regla global:

[data-bs-theme="dark"] .card,
[data-bs-theme="dark"] .card-body,
... {
  background-color: var(--bs-body-bg) !important;
}

Esa regla pisaba el bg-transparent del card (que sí funcionaba en light porque no hay regla equivalente). Por eso en dark volvía el fondo oscuro del card → doble caja.

**Diagnóstico preciso**: document.elementsFromPoint() + getComputedStyle en cada nivel. Se identificó:
- Shell: rgb(43,48,53) (gris oscuro, el fondito suave)
- Card: rgb(33,37,41) (casi negro, debería ser transparente)
- Card-body: rgb(33,37,41) (idem)
- Form: rgba(0,0,0,0) (OK)

Y una regla [data-bs-theme="dark"] .card, .card-body, ... con !important que ganaba por especificidad.

#### 30.11.2 Fix aplicado

**Modificar la regla global** (no agregar parches):

Antes:
[data-bs-theme="dark"] .card,
[data-bs-theme="dark"] .card-body,
... { background-color: var(--bs-body-bg) !important; }

Después:
[data-bs-theme="dark"] .card:not(.filtros-platos-card),
[data-bs-theme="dark"] .card-body:not(.filtros-platos-card > .card-body),
... { background-color: var(--bs-body-bg) !important; }

**Por qué funciona**: al excluir .filtros-platos-card (y su .card-body directo), la regla global deja de aplicar sobre el filtro. El shell queda como único contenedor visual → 1 sola caja en light y dark.

**Bonus**: se corrigió un typo histórico en la misma regla (.album,git p → .album,). El selector inválido era ignorado por el navegador, sin efecto funcional.

**Riesgo**: la regla global afecta a modales, dropdowns, list-groups, etc. Se verificó que ningún otro componente dependa del fondo del .card del filtro específicamente. En dark mode el resto sigue igual.

#### 30.11.3 Deuda nueva

- .filtros-platos-card > .card-body ahora depende de la regla :not(.filtros-platos-card > .card-body). Si en el futuro se agrega otro .card-body dentro del filtro (anidado), NO estará excluido (porque el selector es para hijos directos). A tener en cuenta.

### 31. Idea futura: Plantillas de menú semanal (2026-11-02)

> **Estado**: idea capturada, no implementada. Pendiente de diseño detallado y aprobación. Idea del dueño, discutida al final de la sesión del 2026-11-02.

#### 31.1 Motivación

El menú semanal actual (lun-dom) requiere que el usuario **cargue plato por plato** cada comida, cada día. Es tedioso. La idea es permitir **plantillas**: semanas pre-armadas con **slots tipados** que describen el **tipo** de plato que va en cada comida, no el plato concreto.

El usuario elige una plantilla → la app muestra la semana con **filtros** en lugar de platos → el usuario recorre item por item eligiendo de entre las opciones que matchean → la semana queda armada.


#### 31.2 Modelo conceptual

Cada **slot** de la plantilla (día + comida) tiene un **criterio/filtro** que describe qué tipo de plato va ahí:

| Ejemplo de slot | Interpretación del criterio |
|---|---|
| "Un plato de carne roja" | `subtipo_carta=carnes_rojas` |
| "Plato vegetariano" | `subtipo_carta=vegetarianos` |
| "Rápida preparación" | `(elaboracion + coccion) <= 30` |
| "Guarnición vegetariana" | `tipos incluye Guarnicion AND subtipo_carta=vegetarianos` |
| "Guiso con legumbres" | combinación de `tipo` + ingredientes |
| "Comida liviana para la noche" | combinación de `categoria` + `medios` + `estacionalidad` |

El usuario elige un plato de entre los que matchean, y el slot queda materializado.

#### 31.3 Campos del modelo que ya sirven como filtro

Casi todo el "filtro" ya está en `Plato`:
- `tipos` (CSV de tipos: Principal, Guarnicion, Entrada, etc.)
- `categoria` (Cotidiano / Especial / Ambos)
- `subtipo_carta` (Carnes rojas, Aves, Vegetarianos, Pastas, etc.)
- `elaboracion` + `coccion` (minutos, para "rápida preparación")
- `medios` (Horno, Cocina, Parrilla, Wok, Sin cocción)
- `estacionalidad` (Todo el año, Verano, Invierno, etc.)
- `ingredientes_en_plato` (relación con `Ingrediente`, para "con legumbres")

**Falta definir**: cómo se **combinan** esos campos en un criterio. Opciones:
- **Simple**: campo `CriterioSlot.tipo` (uno solo de los anteriores) + valor.
- **Complejo**: `CriterioSlot.filtros_json` (JSON con condiciones AND/OR).
- **Medio**: campos explícitos (`tipos`, `subtipos`, `categoria`) que se ANDean.


#### 31.4 Decisiones arquitectónicas pendientes

**1. ¿Plantilla vive en un modelo paralelo o en `MenuDia` directo?**

- **Opción A**: modelo `PlantillaSemana` + `PlantillaSlot` + `MenuItem.plato` nullable. El slot vacío indica "sin elegir". No se materializa hasta que el usuario elige.
  - Pro: no ensucia `MenuDia`.
  - Con: hay que sincronizar plantilla con la semana real.

- **Opción B**: `MenuDia` con `MenuItem.plato` nullable + `MenuItem.criterio`. La semana ya es la plantilla, sin modelo intermedio.
  - Pro: más simple.
  - Con: `MenuItem` mezcla "elegido" con "pendiente".

- **Opción C**: la plantilla vive aparte (`PlantillaSemana`), y al elegirla se **copia** a `MenuDia` (con `plato=null` y `criterio`). El usuario va eligiendo platos y los `MenuItem` se van completando.
  - Pro: separa "plantilla" de "semana en curso".
  - Con: duplicación (¿se re-sincroniza si la plantilla cambia?).

**Mi voto (anotado, no decidido): Opción A**. La plantilla es un objeto separado; se materializa en `MenuDia` cuando el usuario elige cada slot.

**2. ¿Cómo se materializa?**

- Opción A: cada click del usuario crea un `MenuItem` en la semana real (`plato=<id>`).
- Opción B: la semana muestra los slots pendientes con dropdowns, y recién al elegir todos se "confirma" la semana y se crea `MenuDia`.
- Opción C: mixto — al elegir la plantilla se crea `MenuDia` con `MenuItem.plato=null`; cada click llena uno.

**Mi voto: C**. La semana ya existe apenas se elige la plantilla (visible en el menú), y cada slot se va llenando.

**3. Plantillas del sistema vs plantillas del usuario**

Ya existe el patrón para `Plato`:
- `propietario` (FK User) + `proviene_de` (string, marca de origen si se importó).
- Platos del user "quecomemos" son "sugerencias" del sistema.

Reusar el mismo patrón:
- `PlantillaSemana.propietario` (FK User nullable).
- Plantillas del sistema: `propietario=quecomemos` (o `NULL` con flag `es_sistema=True`).
- Plantillas del usuario: `propietario=<user>`.

**Mi voto: reusar el patrón existente.**


#### 31.5 Ejemplos de plantillas

- **"Semana de platos especiales"** — todos los almuerzos/cenas con `categoria=Especial`.
- **"Semana vegetariana"** — todos los platos con `subtipo_carta=vegetarianos`.
- **"Comidas livianas a la noche"** — cenas con `medios` en (Wok, Sin cocción) o con `elaboracion+coccion <= 20`.
- **"Semana sin harinas"** — filtro por ingredientes excluyentes (no trigo, no arroz, no pastas).
- **"Semana sin repeticiones"** — el usuario elige el plato en cada slot, pero la app **no permite repetir** un plato que ya está en otro slot.

**Filtros más complejos** (a definir si se implementan en fase 1 o después):
- Rangos de ingredientes específicos.
- Combinaciones AND/OR.
- Orden por estacionalidad (preferir platos de la estación actual).

#### 31.6 Estado actual

**Nada implementado**. Esto es una idea capturada para retomar en una sesión futura.

**Antes de implementar, hace falta:**
1. **Decidir las 3 arquitecturas de §31.4.**
2. **Diseñar el modelo de datos** (`PlantillaSemana` + `CriterioSlot`).
3. **Diseñar la UI**: cómo se ve una semana con slots pendientes.
4. **Diseñar el flujo**: elegir plantilla → llenar slots → confirmar.

**No empezar a codear hasta tener un plan aprobado.** Es un feature grande (~1000+ líneas entre modelo, migración, vistas, templates, JS). Requiere el flujo de §10 (investigar → plan → aprobación → ejecutar) paso a paso.

#### 31.7 Consideraciones extra

- **Interacción con `carpetas-wip`** (feature descartado): sin relación directa.
- **Interacción con `subtipo_carta`** (§29): es el filtro más natural, ya está implementado.
- **Interacción con "Lo que tengo"** (§30): una plantilla podría filtrar también por lo que tiene el usuario. Sería poderoso pero suma complejidad.

