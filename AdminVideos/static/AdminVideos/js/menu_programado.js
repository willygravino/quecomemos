/* ============================================================
   MENÚ PROGRAMADO
   - Refresca el bloque del menú sin recargar la página.
   - Envía el modal "Asignar plato" por AJAX.
   - Fija / desfija hábitos desde el pin por AJAX.
   ============================================================ */

(function () {
  /* ============================================================
     REFRESCAR MENÚ PROGRAMADO
     ============================================================ */
  function refrescarMenuProgramado() {
    console.log("[QC-DEBUG] REFRESH-START", {
      anyShow: document.querySelectorAll(".modal.show").length,
      anyDblock: document.querySelectorAll(".modal.d-block").length,
    });
    const contenedor = document.getElementById("contenedor-menu-programado-dias");
    const tabsDias = document.getElementById("diasTab");
    const accionesMenu = document.getElementById("menuProgramadoAcciones");

    if (!contenedor || !window.fetch || !window.DOMParser) {
      return Promise.resolve();
    }

    const url = new URL(window.location.href);
    url.searchParams.set("_menu_refresh", Date.now().toString());
    const diaSeleccionado = document.getElementById("diaSeleccionado");
    const diaActivo = (
      (window.QCDiaActivo && window.QCDiaActivo.get()) ||
      (diaSeleccionado && diaSeleccionado.value) ||
      ""
    );

    if (diaActivo) {
      url.searchParams.set("dia_activo", diaActivo);
    }

    return fetch(url.toString(), {
      method: "GET",
      headers: {
        "X-Requested-With": "XMLHttpRequest"
      },
      credentials: "same-origin",
      cache: "no-store"
    })
    .then(function (response) {
      if (!response.ok) {
        throw new Error("Error al refrescar menú programado");
      }

      return response.text();
    })
    .then(function (html) {
      const doc = new DOMParser().parseFromString(html, "text/html");
      const nuevoContenedor = doc.getElementById("contenedor-menu-programado-dias");
      const nuevosTabsDias = doc.getElementById("diasTab");
      const nuevasAccionesMenu = doc.getElementById("menuProgramadoAcciones");
      const carritoListaCompras = document.getElementById("botonListaComprasFlotanteWrap");
      const nuevoCarritoListaCompras = doc.getElementById("botonListaComprasFlotanteWrap");

      if (!nuevoContenedor) {
        throw new Error("No se encontró el menú programado actualizado");
      }

      if (tabsDias && nuevosTabsDias) {
        tabsDias.innerHTML = nuevosTabsDias.innerHTML;
      }

      if (accionesMenu && nuevasAccionesMenu) {
        accionesMenu.innerHTML = nuevasAccionesMenu.innerHTML;
      }

      if (carritoListaCompras && nuevoCarritoListaCompras) {
        carritoListaCompras.innerHTML = nuevoCarritoListaCompras.innerHTML;
      }

      contenedor.innerHTML = nuevoContenedor.innerHTML;

      if (window.QCDiaActivo) {
        window.QCDiaActivo.syncFromDom({
          actualizarUrl: true
        });
      }
    });
  }

  window.refrescarMenuProgramado = refrescarMenuProgramado;

    /* ============================================================
     CSRF PARA REQUESTS POST
     ============================================================ */
  function getCookie(nombre) {
    const cookies = document.cookie ? document.cookie.split(";") : [];

    for (const cookie of cookies) {
      const cookieLimpia = cookie.trim();

      if (cookieLimpia.startsWith(nombre + "=")) {
        return decodeURIComponent(cookieLimpia.slice(nombre.length + 1));
      }
    }

    return "";
  }

  function getCSRFToken() {
    return getCookie("csrftoken");
  }

  /* §31 E7: helpers de modales — versión simplificada.
     Regla de oro: NO limpiar backdrops mientras haya modales en
     transición (el watchdog de E6 corría en el gap entre show() y
     .show y borraba el backdrop del modal nuevo).

     Solo dos operaciones:
     - _qcPrepararModalAntesDeAbrir: si nadie está abriendo/abierto,
       limpiar huérfanos de sesiones anteriores.
     - _qcCerrarModalLimpiamente: hide + onHidden en hidden.bs.modal.
       SIN timeout, SIN watchdog, SIN cleanup blanket. */

  function _qcPrepararModalAntesDeAbrir(modalEl) {
    var _inst = modalEl ? bootstrap.Modal.getInstance(modalEl) : null;
    console.log("[QC-DEBUG] PREPARAR", {
      targetId: modalEl ? modalEl.id : null,
      targetShow: modalEl ? modalEl.classList.contains("show") : null,
      targetDblock: modalEl ? modalEl.classList.contains("d-block") : null,
      bodyOpen: document.body.classList.contains("modal-open"),
      backdrops: document.querySelectorAll(".modal-backdrop").length,
      anyShow: document.querySelectorAll(".modal.show").length,
      anyDblock: document.querySelectorAll(".modal.d-block").length,
      instIsShown: _inst ? _inst._isShown : null,
      instIsTrans: _inst ? _inst._isTransitioning : null,
    });
    if (modalEl && modalEl.classList.contains("show")) return;
    // Si hay otro modal visible, no tocar.
    if (document.querySelector(".modal.show")) return;
    // Si hay uno en transición (.d-block sin .show), no tocar.
    if (document.querySelector(".modal.d-block")) return;
    // Nadie está abriendo/cerrando: limpiar huérfanos.
    document.querySelectorAll(".modal-backdrop").forEach(function (b) {
      try { b.remove(); } catch (e) {}
    });
    document.body.classList.remove("modal-open");
    document.body.style.removeProperty("overflow");
    document.body.style.removeProperty("padding-right");
  }

  function _qcCerrarModalLimpiamente(modalEl, onHidden) {
    var _instC = modalEl ? bootstrap.Modal.getInstance(modalEl) : null;
    console.log("[QC-DEBUG] CERRAR", {
      targetId: modalEl ? modalEl.id : null,
      instExists: !!_instC,
      instIsShown: _instC ? _instC._isShown : null,
      instIsTrans: _instC ? _instC._isTransitioning : null,
      bodyOpen: document.body.classList.contains("modal-open"),
      backdrops: document.querySelectorAll(".modal-backdrop").length,
    });
    if (!modalEl) { if (onHidden) onHidden(); return; }
    var inst = null;
    try { inst = bootstrap.Modal.getInstance(modalEl); } catch (e) {}
    if (!inst) { if (onHidden) onHidden(); return; }
    var fired = false;
    var handler = function () {
      if (fired) return;
      fired = true;
      console.log("[QC-DEBUG] HIDDEN-FIRED", {
        targetId: modalEl.id,
        bodyOpen: document.body.classList.contains("modal-open"),
        backdrops: document.querySelectorAll(".modal-backdrop").length,
      });
      modalEl.removeEventListener("hidden.bs.modal", handler);
      if (onHidden) onHidden();
    };
    modalEl.addEventListener("hidden.bs.modal", handler);
    try { inst.hide(); } catch (e) {}
  }

  /* ============================================================
        QUITAR ITEM PROGRAMADO POR AJAX
        ============================================================ */
    document.addEventListener("click", function (event) {
        const link = event.target.closest(".js-eliminar-programado");

        if (!link) {
        return;
        }

        const contenedorMenuProgramado = document.getElementById("contenedor-menu-programado-dias");
        const ajaxUrl = link.dataset.ajaxUrl;

        // Fallback seguro: si falta algo esencial, dejamos el link clásico.
        if (!contenedorMenuProgramado || !ajaxUrl || !window.fetch) {
        return;
        }

        event.preventDefault();

        const body = new URLSearchParams({
        es_lugar: link.dataset.esLugar || "",
        objeto_id: link.dataset.objetoId || "",
        comida: link.dataset.comida || "",
        fecha: link.dataset.fecha || ""
        });

        fetch(ajaxUrl, {
        method: "POST",
        body: body.toString(),
        headers: {
            "X-CSRFToken": getCSRFToken(),
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
        },
        credentials: "same-origin"
        })
        .then(function (response) {
        if (!response.ok) {
            throw new Error("Error al quitar item programado");
        }

        return response.json();
        })
        .then(function (data) {
        if (!data.ok) {
            throw new Error("Respuesta inválida al quitar item programado");
        }

        return refrescarMenuProgramado();
        })
        .catch(function (error) {
        console.error(error);
        });
    }, true);


  /* ============================================================
     ASIGNAR PLATO / LUGAR POR AJAX
     ============================================================ */
  const asignarPlatoForm = document.getElementById("asignarPlatoForm");

  if (asignarPlatoForm) {
    asignarPlatoForm.addEventListener("submit", function (e) {
      const url = asignarPlatoForm.action;

      // Fallback seguro: si falta algo esencial, dejamos el submit clásico.
      if (!url || !window.fetch) {
        return;
      }

      e.preventDefault();

      const submitBtn = asignarPlatoForm.querySelector("button[type='submit']");
      if (submitBtn) {
        submitBtn.disabled = true;
      }

      fetch(url, {
        method: "POST",
        body: new FormData(asignarPlatoForm),
        headers: {
          "X-Requested-With": "XMLHttpRequest"
        },
        credentials: "same-origin"
      })
      .then(function (response) {
        if (!response.ok) {
          throw new Error("Error al asignar plato");
        }

        return response.json();
      })
      .then(function (data) {
        if (!data.ok) {
          throw new Error("Respuesta inválida al asignar plato");
        }

        const modalEl = document.getElementById("asignarPlatoModal");

        if (modalEl && window.bootstrap) {
          const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
          modal.hide();
        }

        return refrescarMenuProgramado();
      })
      .catch(function (error) {
        console.error(error);
      })
      .finally(function () {
        if (submitBtn) {
          submitBtn.disabled = false;
        }
      });
    });
  }


  /* ============================================================
     FIJAR / DESFIJAR HÁBITO POR AJAX
     ============================================================ */
  document.addEventListener("click", function (e) {
    const link = e.target.closest(".js-toggle-habito");

    if (!link) {
      return;
    }

    const ajaxUrl = link.dataset.ajaxUrl || link.href;

    // Fallback seguro: si falta algo esencial, dejamos el link clásico.
    if (!ajaxUrl || !window.fetch) {
      return;
    }

    e.preventDefault();

    link.classList.add("pe-none");

    fetch(ajaxUrl, {
      method: "GET",
      headers: {
        "X-Requested-With": "XMLHttpRequest"
      },
      credentials: "same-origin"
    })
    .then(function (response) {
      if (!response.ok) {
        throw new Error("Error al fijar o eliminar hábito");
      }

      return response.json();
    })
    .then(function (data) {
      if (!data.ok) {
        throw new Error("Respuesta inválida al fijar o eliminar hábito");
      }

      return refrescarMenuProgramado();
    })
    .catch(function (error) {
      console.error(error);
    })
    .finally(function () {
      link.classList.remove("pe-none");
    });
  }, true);

  /* ============================================================
     ASIGNAR EXTRA DESDE EL MENÚ (+ Salsa / + Guarnición)
     Abre el modal existente con el plato precargado y la fila
     del extra ya agregada.
     ============================================================ */
  document.addEventListener("click", async function (event) {
    const btn = event.target.closest(".js-asignar-extra");
    if (!btn) return;
    event.preventDefault();

    const tipoExtra = btn.dataset.extraTipo || "";
    const platoId = btn.dataset.extraPlatoId || "";
    const platoNombre = btn.dataset.extraPlatoNombre || "";
    const dia = btn.dataset.extraDia || "";
    const comida = btn.dataset.extraComida || "";

    if (!tipoExtra || !platoId) return;

    const modalEl = document.getElementById("asignarPlatoModal");
    if (!modalEl) return;

    // Setear día y comida en el modal
    const diaInput = document.getElementById("diaSeleccionado");
    if (diaInput) diaInput.value = dia;

    const comidaSel = document.getElementById("comidaSeleccionada");
    if (comidaSel) comidaSel.value = comida;

    // Preparar el modal (carga tipos, muestra bloqueExtras si es Principal)
    if (typeof window.setPlatoInfo === "function") {
      await window.setPlatoInfo(platoId, "plato", platoNombre);
    }

    // Agregar la fila del extra clickeado (Salsa o Guarnicion)
    if (typeof window.addExtraRow === "function") {
      window.addExtraRow(tipoExtra);
    }

    // Abrir el modal
    if (window.bootstrap && bootstrap.Modal) {
      bootstrap.Modal.getOrCreateInstance(modalEl).show();
    }
  }, true);
  /* ============================================================
     SLOTS SEMANALES: crear slot desde el menú
     ============================================================ */

  // Click "+ Slot" → abre el modal de presets con día/momento precargados
  document.addEventListener("click", function (event) {
    const btn = event.target.closest(".js-crear-slot");
    if (!btn) return;
    event.preventDefault();

    const dia = btn.dataset.dia || "";
    const momento = btn.dataset.momento || "";
    const diaInput = document.getElementById("slotDiaInput");
    const momentoInput = document.getElementById("slotMomentoInput");
    const modalEl = document.getElementById("crearSlotModal");

    if (!dia || !momento || !diaInput || !momentoInput || !modalEl) return;

    diaInput.value = dia;
    momentoInput.value = momento;

    if (window.bootstrap && bootstrap.Modal) {
      _qcPrepararModalAntesDeAbrir(modalEl);
      var _instBefore = bootstrap.Modal.getInstance(modalEl);
      console.log("[QC-DEBUG] SHOW-CALL", {
        targetId: modalEl.id,
        instExists: !!_instBefore,
        instIsShown: _instBefore ? _instBefore._isShown : null,
        instIsTrans: _instBefore ? _instBefore._isTransitioning : null,
      });
      bootstrap.Modal.getOrCreateInstance(modalEl).show();
    }
  }, true);

  // Click preset en el modal → POST crear slot + refresh + close
  document.addEventListener("click", function (event) {
    const btn = event.target.closest(".js-elegir-preset");
    if (!btn) return;
    event.preventDefault();

    const preset = btn.dataset.preset || "";
    const diaInput = document.getElementById("slotDiaInput");
    const momentoInput = document.getElementById("slotMomentoInput");
    const modalEl = document.getElementById("crearSlotModal");

    if (!preset || !diaInput || !momentoInput || !modalEl) return;

    const dia = diaInput.value;
    const momento = momentoInput.value;
    if (!dia || !momento) return;

    const url = modalEl.dataset.crearSlotUrl || "";
    if (!url || !window.fetch) return;

    // Convertir YYYY-MM-DD → dia_semana Django (0=lunes ... 6=domingo)
    const partes = dia.split("-");
    const fecha = new Date(Number(partes[0]), Number(partes[1]) - 1, Number(partes[2]));
    const jsDay = fecha.getDay();            // 0=domingo, 1=lunes, ..., 6=sábado
    const diaSemanaDjango = (jsDay + 6) % 7; // 0=lunes, ..., 6=domingo

    btn.disabled = true;

    const body = new URLSearchParams({
      dia_semana: String(diaSemanaDjango),
      momento: momento,
      preset: preset
    });

    fetch(url, {
      method: "POST",
      body: body.toString(),
      headers: {
        "X-CSRFToken": getCSRFToken(),
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
      },
      credentials: "same-origin"
    })
    .then(function (response) {
      if (!response.ok) throw new Error("Error al crear slot");
      return response.json();
    })
    .then(function (data) {
      if (!data.ok) throw new Error("Respuesta inválida al crear slot");
      _qcCerrarModalLimpiamente(modalEl, refrescarMenuProgramado);
    })
    .catch(function (error) {
      console.error(error);
    })
    .finally(function () {
      btn.disabled = false;
    });
  }, true);

  /* ============================================================
     SLOTS SEMANALES: elegir plato para un slot pendiente
     ============================================================ */

  // Click en chip "Pendiente: X" → abre modal con platos filtrados
  document.addEventListener("click", function (event) {
    const btn = event.target.closest(".js-abrir-elegir-plato");
    if (!btn) return;
    event.preventDefault();

    const slotId = btn.dataset.slotId || "";
    const slotLabel = btn.dataset.slotLabel || "";
    const dia = btn.dataset.menuDia || "";
    const comida = btn.dataset.menuComida || "";
    const modalEl = document.getElementById("elegirPlatoSlotModal");

    if (!slotId || !modalEl || !window.fetch) return;

    const urlTemplate = modalEl.dataset.platosUrlTemplate || "";
    if (!urlTemplate) return;
    // Reemplazar "/0/" (pk=0 dummy) por el id real
    const url = urlTemplate.replace("/0/", "/" + slotId + "/");

    document.getElementById("elegirPlatoSlotIdInput").value = slotId;
    document.getElementById("elegirPlatoSlotDiaInput").value = dia;
    document.getElementById("elegirPlatoSlotComidaInput").value = comida;
    document.getElementById("elegirPlatoSlotPreset").textContent = slotLabel || "slot";

    const lista = document.getElementById("elegirPlatoSlotLista");
    lista.innerHTML = '<p class="text-muted small mb-0">Cargando...</p>';

    if (window.bootstrap && bootstrap.Modal) {
      _qcPrepararModalAntesDeAbrir(modalEl);
      var _instBefore = bootstrap.Modal.getInstance(modalEl);
      console.log("[QC-DEBUG] SHOW-CALL", {
        targetId: modalEl.id,
        instExists: !!_instBefore,
        instIsShown: _instBefore ? _instBefore._isShown : null,
        instIsTrans: _instBefore ? _instBefore._isTransitioning : null,
      });
      bootstrap.Modal.getOrCreateInstance(modalEl).show();
    }

    fetch(url, {
      method: "GET",
      headers: { "X-Requested-With": "XMLHttpRequest" },
      credentials: "same-origin"
    })
    .then(function (response) {
      if (!response.ok) throw new Error("Error al cargar platos del slot");
      return response.json();
    })
    .then(function (data) {
      if (!data.ok) throw new Error("Respuesta inválida");
      if (!data.platos || data.platos.length === 0) {
        lista.innerHTML = '<p class="text-muted small mb-0">No hay platos que matcheen este filtro. Probá con otro slot.</p>';
        return;
      }
      lista.innerHTML = "";
      data.platos.forEach(function (p) {
        const b = document.createElement("button");
        b.type = "button";
        b.className = "list-group-item list-group-item-action js-elegir-plato-slot d-flex justify-content-between align-items-center";
        b.dataset.platoId = p.id;
        b.dataset.platoNombre = p.nombre;
        b.innerHTML = '<span>' + p.nombre + '</span>'
          + (p.tipo ? ' <small class="text-muted">' + p.tipo + '</small>' : '');
        lista.appendChild(b);
      });
    })
    .catch(function (error) {
      console.error(error);
      lista.innerHTML = '<p class="text-danger small mb-0">Error al cargar platos.</p>';
    });
  }, true);

  // Click en un plato del modal → POST /asignar/plato con slot_origen_id
  document.addEventListener("click", function (event) {
    const btn = event.target.closest(".js-elegir-plato-slot");
    if (!btn) return;
    event.preventDefault();

    const platoId = btn.dataset.platoId || "";
    const slotId = document.getElementById("elegirPlatoSlotIdInput").value;
    const dia = document.getElementById("elegirPlatoSlotDiaInput").value;
    const comida = document.getElementById("elegirPlatoSlotComidaInput").value;
    const modalEl = document.getElementById("elegirPlatoSlotModal");

    if (!platoId || !slotId || !dia || !comida || !modalEl) return;

    const asignarUrl = modalEl.dataset.asignarUrl || "";
    if (!asignarUrl || !window.fetch) return;

    btn.disabled = true;

    const body = new URLSearchParams({
      tipo_elemento: "plato",
      plato_id: platoId,
      dia: dia,
      comida: comida,
      slot_origen_id: slotId
    });

    fetch(asignarUrl, {
      method: "POST",
      body: body.toString(),
      headers: {
        "X-CSRFToken": getCSRFToken(),
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
      },
      credentials: "same-origin"
    })
    .then(function (response) {
      if (!response.ok) throw new Error("Error al asignar plato al slot");
      return response.json();
    })
    .then(function (data) {
      if (!data.ok) throw new Error("Respuesta inválida al asignar plato");
      _qcCerrarModalLimpiamente(modalEl, refrescarMenuProgramado);
    })
    .catch(function (error) {
      console.error(error);
    })
    .finally(function () {
      btn.disabled = false;
    });
  }, true);

  /* ============================================================
     SLOTS SEMANALES: borrar slot con confirmación
     ============================================================ */

  document.addEventListener("click", async function (event) {
    const btn = event.target.closest(".js-borrar-slot");
    if (!btn) return;
    event.preventDefault();
    event.stopPropagation();

    const slotId = btn.dataset.slotId || "";
    const slotLabel = btn.dataset.slotLabel || "";
    const borrarUrl = btn.dataset.borrarUrl || "";

    if (!slotId || !borrarUrl || !window.fetch) return;

    const mensaje = '¿Borrar el slot "' + slotLabel + '"?';
    const confirmar = window.confirmDialog
      ? await window.confirmDialog({
          title: "Borrar slot",
          body: mensaje,
          confirmText: "Borrar",
          confirmClass: "btn-danger"
        })
      : window.confirm(mensaje);

    if (!confirmar) return;

    btn.disabled = true;

    fetch(borrarUrl, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCSRFToken(),
        "X-Requested-With": "XMLHttpRequest"
      },
      credentials: "same-origin"
    })
    .then(function (response) {
      if (!response.ok) throw new Error("Error al borrar slot");
      return response.json();
    })
    .then(function (data) {
      if (!data.ok) throw new Error("Respuesta inválida al borrar slot");
      return refrescarMenuProgramado();
    })
    .catch(function (error) {
      console.error(error);
    })
    .finally(function () {
      btn.disabled = false;
    });
  }, true);

  /* ============================================================
     §31 E3: editar slot (lápiz en el chip)
     - Click lápiz → GET → precargar modal → show.
     - Change preset → autocompletar tiempos/medios desde JSON.
     - Submit → POST → close → refresh.
     ============================================================ */

  var _editarSlotPresets = null;
  function _getEditarSlotPresets() {
    if (_editarSlotPresets !== null) return _editarSlotPresets;
    var tag = document.getElementById("editarSlotPresetsData");
    if (!tag) { _editarSlotPresets = {}; return _editarSlotPresets; }
    try { _editarSlotPresets = JSON.parse(tag.textContent || "{}"); }
    catch (e) { _editarSlotPresets = {}; }
    return _editarSlotPresets;
  }

  function _aplicarCriterioAlModal(criterio) {
    // Medios
    var medios = (criterio && criterio.medios) || [];
    document.querySelectorAll('#editarSlotForm input[name="medios"]').forEach(function (cb) {
      cb.checked = medios.indexOf(cb.value) !== -1;
    });
    // Tiempos
    var elab = document.getElementById("editarSlotElabInput");
    if (elab) elab.value = (criterio && criterio.elaboracion_max != null) ? criterio.elaboracion_max : "";
    var cocc = document.getElementById("editarSlotCoccInput");
    if (cocc) cocc.value = (criterio && criterio.coccion_max != null) ? criterio.coccion_max : "";
  }

  // Click lápiz
  document.addEventListener("click", function (event) {
    var btn = event.target.closest(".js-editar-slot");
    if (!btn) return;
    event.preventDefault();
    event.stopPropagation();

    var slotId = btn.dataset.slotId || "";
    var modalEl = document.getElementById("editarSlotModal");
    if (!slotId || !modalEl || !window.fetch) return;

    var getUrlTemplate = modalEl.dataset.getSlotUrlTemplate || "";
    if (!getUrlTemplate) return;
    var getUrl = getUrlTemplate.replace("/0/", "/" + slotId + "/");

    document.getElementById("editarSlotIdInput").value = slotId;

    // Reset visual mientras carga
    document.getElementById("editarSlotPresetSelect").value = "";
    _aplicarCriterioAlModal({});

    if (window.bootstrap && bootstrap.Modal) {
      _qcPrepararModalAntesDeAbrir(modalEl);
      var _instBefore = bootstrap.Modal.getInstance(modalEl);
      console.log("[QC-DEBUG] SHOW-CALL", {
        targetId: modalEl.id,
        instExists: !!_instBefore,
        instIsShown: _instBefore ? _instBefore._isShown : null,
        instIsTrans: _instBefore ? _instBefore._isTransitioning : null,
      });
      bootstrap.Modal.getOrCreateInstance(modalEl).show();
    }

    fetch(getUrl, {
      method: "GET",
      headers: { "X-Requested-With": "XMLHttpRequest" },
      credentials: "same-origin"
    })
    .then(function (response) {
      if (!response.ok) throw new Error("Error al cargar slot");
      return response.json();
    })
    .then(function (data) {
      if (!data.ok) throw new Error("Respuesta inválida");
      var slot = data.slot;
      document.getElementById("editarSlotPresetSelect").value = slot.preset || "";
      _aplicarCriterioAlModal(slot.criterio || {});
    })
    .catch(function (error) {
      console.error(error);
    });
  }, true);

  // Change preset → autocompletar tiempos/medios
  document.addEventListener("change", function (event) {
    var sel = event.target.closest("#editarSlotPresetSelect");
    if (!sel) return;
    var key = sel.value || "";
    var presets = _getEditarSlotPresets();
    if (!key || !presets[key]) return;
    _aplicarCriterioAlModal(presets[key].criterio || {});
  });

  // Submit del form
  document.addEventListener("submit", function (event) {
    var form = event.target.closest("#editarSlotForm");
    if (!form) return;
    event.preventDefault();

    var slotId = document.getElementById("editarSlotIdInput").value || "";
    var modalEl = document.getElementById("editarSlotModal");
    if (!slotId || !modalEl || !window.fetch) return;

    var editUrlTemplate = modalEl.dataset.editarSlotUrlTemplate || "";
    if (!editUrlTemplate) return;
    var editUrl = editUrlTemplate.replace("/0/", "/" + slotId + "/");

    var saveBtn = document.getElementById("editarSlotSaveBtn");
    if (saveBtn) saveBtn.disabled = true;

    // Armar body con preset + tiempos + medios
    var body = new URLSearchParams();
    body.set("preset", document.getElementById("editarSlotPresetSelect").value || "");
    body.set("elaboracion_max", document.getElementById("editarSlotElabInput").value || "");
    body.set("coccion_max", document.getElementById("editarSlotCoccInput").value || "");
    form.querySelectorAll('input[name="medios"]:checked').forEach(function (cb) {
      body.append("medios", cb.value);
    });

    fetch(editUrl, {
      method: "POST",
      body: body.toString(),
      headers: {
        "X-CSRFToken": getCSRFToken(),
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
      },
      credentials: "same-origin"
    })
    .then(function (response) {
      if (!response.ok) {
        return response.json().then(function (d) {
          throw new Error(d.error || "Error al editar slot");
        });
      }
      return response.json();
    })
    .then(function (data) {
      if (!data.ok) throw new Error("Respuesta inválida");
      _qcCerrarModalLimpiamente(modalEl, function () {
        if (window.refrescarMenuProgramado) window.refrescarMenuProgramado();
      });
    })
    .catch(function (error) {
      console.error(error);
      alert(error.message || "Error al editar slot");
    })
    .finally(function () {
      if (saveBtn) saveBtn.disabled = false;
    });
  });

})();
