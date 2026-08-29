/* PLATO FORM SHEET: Crear + Editar comparten la misma hoja. */
(function () {
  "use strict";

  const sheet = document.getElementById("modalPlato");
  const body = document.getElementById("platoCreateSheetBody");
  const backdrop = document.getElementById(
    "platoCreateSheetBackdrop"
  );
  const UI = window.QCOverlayUI;

  if (!sheet || !body || !backdrop) return;

  const cache = UI ? UI.createCache(30000) : null;

  let triggerActivo = null;
  let cargando = false;

  function placeholder(texto) {
    return (
      '<div class="plato-create-sheet-placeholder text-muted">' +
      texto +
      "</div>"
    );
  }

  function esFormularioPlato(trigger) {
    if (!trigger) return false;

    const esCrear = trigger.id === "botonCrearPlatoFlotante";
    const esEditar = trigger.hasAttribute("data-plato-sheet-open");

    if (!esCrear && !esEditar) return false;

    if (trigger.classList.contains("disabled")) return false;
    if (trigger.getAttribute("aria-disabled") === "true") {
      return false;
    }

    const href = trigger.getAttribute("href") || "";
    if (!href) return false;

    try {
      const destino = new URL(href, window.location.origin);

      if (destino.origin !== window.location.origin) {
        return false;
      }

      if (esEditar) {
        return true;
      }

      const createBase = trigger.dataset.urlCrearPlato || "";
      if (!createBase) return false;

      const crear = new URL(createBase, window.location.origin);

      return (
        destino.origin === crear.origin &&
        destino.pathname === crear.pathname
      );
    } catch (error) {
      return false;
    }
  }

  function setOpen(open) {
    document.body.classList.toggle(
      "plato-create-sheet-open",
      open
    );
    sheet.classList.toggle("is-open", open);
    backdrop.classList.toggle("is-open", open);
    backdrop.hidden = !open;
    sheet.setAttribute("aria-hidden", open ? "false" : "true");

    if (
      !open &&
      triggerActivo &&
      document.contains(triggerActivo)
    ) {
      triggerActivo.focus({ preventScroll: true });
    }
  }

  function limpiar() {
    body.innerHTML = placeholder("Cargando formulario…");
  }

  function cerrar() {
    setOpen(false);

    window.setTimeout(function () {
      if (!sheet.classList.contains("is-open")) limpiar();
    }, 280);
  }

  async function fetchFormHtml(url) {
    const response = await fetch(url, {
      method: "GET",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
      },
      credentials: "same-origin",
    });

    if (!response.ok) {
      throw new Error("HTTP " + response.status);
    }

    const payload = await response.json();

    if (!payload || !payload.html) {
      throw new Error("La respuesta no contiene el formulario.");
    }

    return payload.html;
  }

  function renderForm(html, url, focusName) {
    body.innerHTML = html;
    body.scrollTop = 0;

    if (typeof window.initPlatoForm === "function") {
      window.initPlatoForm(body);
    }

    document.dispatchEvent(
      new CustomEvent("plato-form:loaded", {
        detail: { root: body, url: url },
      })
    );

    if (!focusName) return;

    const nombre = body.querySelector(
      '#platoForm input[name="nombre_plato"]'
    );

    if (nombre) {
      window.setTimeout(function () {
        try {
          nombre.focus({ preventScroll: true });
        } catch (error) {}
      }, 40);
    }
  }

  async function cargar(url) {
    const cached = cache ? cache.peek(url) : undefined;

    if (cached !== undefined) {
      renderForm(cached, url, true);
      return;
    }

    if (cargando) return;

    cargando = true;
    body.innerHTML = placeholder("Cargando formulario…");

    try {
      const html = cache
        ? await cache.get(url, fetchFormHtml)
        : await fetchFormHtml(url);

      renderForm(html, url, true);
    } catch (error) {
      console.warn(
        "No se pudo abrir el formulario de plato como hoja. Uso la página normal.",
        error
      );
      window.location.href = url;
    } finally {
      cargando = false;
    }
  }

  async function abrir(trigger) {
    const url = trigger.getAttribute("href");

    if (!url) return;

    triggerActivo = trigger;
    setOpen(true);

    await cargar(url);
  }

  function prefetchTrigger(trigger) {
    if (!cache || !esFormularioPlato(trigger)) return;

    const url = trigger.getAttribute("href");

    if (url) cache.prefetch(url, fetchFormHtml);
  }

  function prefetchCurrent() {
    prefetchTrigger(
      document.getElementById("botonCrearPlatoFlotante")
    );
  }

  document.addEventListener("click", function (event) {
    const platoTrigger = event.target.closest(
      "#botonCrearPlatoFlotante, [data-plato-sheet-open]"
    );

    if (platoTrigger && esFormularioPlato(platoTrigger)) {
      event.preventDefault();
      // CAPTURE: los links de edición pueden frenar el bubbling para no activar la fila.
      if (platoTrigger.hasAttribute("data-plato-sheet-open")) {
        event.stopPropagation();
      }
      abrir(platoTrigger);
      return;
    }

    const closeLink = event.target.closest(
      "#modalPlato .js-close-plato-form"
    );

    if (closeLink) {
      event.preventDefault();
      cerrar();
    }
  }, true);
  document.addEventListener(
    "pointerenter",
    function (event) {
      const trigger = event.target.closest?.(
        "#botonCrearPlatoFlotante, [data-plato-sheet-open]"
      );

      if (trigger && esFormularioPlato(trigger)) prefetchTrigger(trigger);
    },
    true
  );

  document.addEventListener(
    "touchstart",
    function (event) {
      const trigger = event.target.closest?.(
        "#botonCrearPlatoFlotante, [data-plato-sheet-open]"
      );

      if (trigger && esFormularioPlato(trigger)) prefetchTrigger(trigger);
    },
    { passive: true, capture: true }
  );

  backdrop.addEventListener("click", cerrar);

  document.addEventListener("keydown", function (event) {
    if (
      event.key !== "Escape" ||
      !sheet.classList.contains("is-open")
    ) {
      return;
    }

    if (document.querySelector(".modal.show")) return;

    cerrar();
  });

  if (UI) {
    UI.bindSwipeDismiss({
      element: sheet,
      direction: "down",
      threshold: 78,
      maxOffset: Math.min(window.innerHeight * 0.55, 360),
      canStart: function () {
        return body.scrollTop <= 1;
      },
      onDismiss: cerrar,
    });

    UI.bindWheelDismiss({
      element: sheet,
      direction: "down",
      threshold: 105,
      maxOffset: Math.min(window.innerHeight * 0.55, 360),
      physicalSign: -1,
      canStart: function () {
        return body.scrollTop <= 1;
      },
      onDismiss: cerrar,
    });

    UI.whenIdle(prefetchCurrent, 1700);
  }
})();
