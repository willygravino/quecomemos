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
  

### 28.8 Regex peligroso en CSS (lección 2026-10-26)

- **Nunca usar `[\s\S]*?` en regex para "encontrar bloques" de CSS.** Un regex como `/* =+[\s\S]*?filtro-keyword-clear...` puede matchear desde el **PRIMER** `/* ===` del archivo hasta el bloque buscado, borrando **TODO el CSS intermedio**.
- **Síntoma**: `git --no-pager diff --stat` muestra "~2900 líneas borradas" en `mi-css.css`. La página se rompe con layout caótico (inputs superpuestos, colores mal, todo desalineado).
- **Regla**: cuando se modifica un `.css` grande, **append al final** (seguro) o **reemplazo por bloque exacto** con `s.count(anchor) == 1`. **Nunca** regex con wildcards amplios.
- **Rollback inmediato**: `git checkout HEAD -- <archivo>`. Vuelve al estado del último commit sin perder cambios ya commiteados.
