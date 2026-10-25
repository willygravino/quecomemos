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

  // === Deteccion de cambios sin guardar ===
  let _formSnapshot = null;

  function _snapshotValue(el) {
    if (el.type === "checkbox" || el.type === "radio") {
      return el.checked ? "1" : "0";
    }
    if (el.tagName === "SELECT" && el.multiple) {
      return Array.from(el.selectedOptions)
        .map(function (o) { return o.value; })
        .sort()
        .join("\u0001");
    }
    return el.value == null ? "" : String(el.value);
  }

  function _fieldKey(el) {
    if (el.type === "checkbox" || el.type === "radio") {
      return el.name + "::" + (el.value || "");
    }
    return el.name;
  }

  function snapshotForm() {
    _formSnapshot = {};
    const form = body.querySelector("form");
    if (!form) return;
    form.querySelectorAll("input, textarea, select").forEach(function (el) {
      if (!el.name) return;
      if (el.type === "submit" || el.type === "button" || el.type === "file") return;
      _formSnapshot[_fieldKey(el)] = _snapshotValue(el);
    });
    window.__platoFormSaved = false;
  }

  function hayCambios() {
    if (!_formSnapshot) return false;
    const form = body.querySelector("form");
    if (!form) return false;
    let changed = false;
    form.querySelectorAll("input, textarea, select").forEach(function (el) {
      if (changed) return;
      if (!el.name) return;
      if (el.type === "submit" || el.type === "button" || el.type === "file") return;
      const key = _fieldKey(el);
      const curr = _snapshotValue(el);
      const prev = Object.prototype.hasOwnProperty.call(_formSnapshot, key)
        ? _formSnapshot[key]
        : undefined;
      if (prev !== curr) {
        changed = true;
      }
    });
    return changed;
  }

  async function cerrar() {
    if (hayCambios() && !window.__platoFormSaved) {
      const ok = await window.confirmDialog({
        title: "Salir sin guardar",
        body: "Vas a perder los cambios del formulario.",
        hint: "",
        confirmText: "Salir sin guardar",
        cancelText: "Seguir editando",
        confirmClass: "btn-warning"
      });
      if (!ok) return;
    }
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

    snapshotForm();

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

  window.addEventListener("beforeunload", function (e) {
    if (!sheet.classList.contains("is-open")) return;
    if (window.__platoFormSaved) return;
    if (!hayCambios()) return;
    e.preventDefault();
    e.returnValue = "";
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
