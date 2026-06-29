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

    if (!contenedor || !window.fetch || !window.DOMParser) {
      return Promise.resolve();
    }

    const url = new URL(window.location.href);
    url.searchParams.set("_menu_refresh", Date.now().toString());
    const diaSeleccionado = document.getElementById("diaSeleccionado");

    if (diaSeleccionado && diaSeleccionado.value) {
      url.searchParams.set("dia_activo", diaSeleccionado.value);
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

      if (!nuevoContenedor) {
        throw new Error("No se encontró el menú programado actualizado");
      }

      if (tabsDias && nuevosTabsDias) {
        tabsDias.innerHTML = nuevosTabsDias.innerHTML;
      }

      contenedor.innerHTML = nuevoContenedor.innerHTML;
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
})();