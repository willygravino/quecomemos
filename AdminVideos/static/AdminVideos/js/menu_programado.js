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
      if (window.bootstrap && bootstrap.Modal) {
        bootstrap.Modal.getOrCreateInstance(modalEl).hide();
      }
      return refrescarMenuProgramado();
    })
    .catch(function (error) {
      console.error(error);
    })
    .finally(function () {
      btn.disabled = false;
    });
  }, true);

})();
