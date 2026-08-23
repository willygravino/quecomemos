(function () {
  "use strict";

  if (window.QCOverlayUI) return;

  function createCache(ttlMs) {
    const ttl = Number(ttlMs) > 0 ? Number(ttlMs) : 20000;
    const entries = new Map();

    function fresh(entry) {
      return (
        entry &&
        entry.value !== undefined &&
        Date.now() - entry.savedAt < ttl
      );
    }

    async function fetchAndStore(url, loader) {
      const current = entries.get(url);

      if (current && current.promise) {
        return current.promise;
      }

      const promise = Promise.resolve()
        .then(function () {
          return loader(url);
        })
        .then(function (value) {
          entries.set(url, {
            value: value,
            savedAt: Date.now(),
            promise: null,
          });
          return value;
        })
        .catch(function (error) {
          const old = entries.get(url);

          if (old && old.value !== undefined) {
            entries.set(url, {
              value: old.value,
              savedAt: old.savedAt,
              promise: null,
            });
          } else {
            entries.delete(url);
          }

          throw error;
        });

      entries.set(url, {
        value: current ? current.value : undefined,
        savedAt: current ? current.savedAt : 0,
        promise: promise,
      });

      return promise;
    }

    return {
      peek: function (url) {
        const entry = entries.get(url);
        return fresh(entry) ? entry.value : undefined;
      },

      get: function (url, loader) {
        const entry = entries.get(url);

        if (fresh(entry)) {
          return Promise.resolve(entry.value);
        }

        return fetchAndStore(url, loader);
      },

      refresh: function (url, loader) {
        entries.delete(url);
        return fetchAndStore(url, loader);
      },

      prefetch: function (url, loader) {
        if (!url) return Promise.resolve(undefined);

        return this.get(url, loader).catch(function () {
          return undefined;
        });
      },

      invalidate: function (url) {
        if (url) entries.delete(url);
        else entries.clear();
      },
    };
  }

  function bindSwipeDismiss(options) {
    const element = options && options.element;
    const direction = options && options.direction;
    const onDismiss = options && options.onDismiss;

    if (!element || typeof onDismiss !== "function") {
      return function () {};
    }

    if (direction !== "right" && direction !== "down") {
      throw new Error("Dirección de swipe no soportada: " + direction);
    }

    const threshold = Number(options.threshold) || 72;
    const axisRatio = Number(options.axisRatio) || 1.2;
    const maxOffset = Number(options.maxOffset) || 260;
    const ignoreSelector =
      options.ignoreSelector ||
      "input, textarea, select, button, a, [contenteditable='true'], " +
        ".select2-container, .modal, [data-bs-toggle]";

    let startX = 0;
    let startY = 0;
    let offset = 0;
    let tracking = false;
    let dragging = false;

    function canStart(event) {
      if (
        event.target &&
        event.target.closest &&
        event.target.closest(ignoreSelector)
      ) {
        return false;
      }

      if (typeof options.canStart === "function") {
        return options.canStart(event) !== false;
      }

      return true;
    }

    function primaryDelta(touch) {
      return direction === "right"
        ? touch.clientX - startX
        : touch.clientY - startY;
    }

    function crossDelta(touch) {
      return direction === "right"
        ? touch.clientY - startY
        : touch.clientX - startX;
    }

    function resetVisual(animated) {
      element.classList.remove("qc-swipe-dragging");

      if (animated) {
        element.style.setProperty("--qc-swipe-offset", "0px");

        window.setTimeout(function () {
          if (!element.classList.contains("qc-swipe-dragging")) {
            element.style.removeProperty("--qc-swipe-offset");
          }
        }, 280);
      } else {
        element.style.removeProperty("--qc-swipe-offset");
      }
    }

    function finish(shouldDismiss) {
      if (!tracking) return;

      tracking = false;

      if (!dragging) {
        offset = 0;
        return;
      }

      if (shouldDismiss) {
        resetVisual(false);
        onDismiss();
      } else {
        resetVisual(true);
      }

      dragging = false;
      offset = 0;
    }

    element.addEventListener(
      "touchstart",
      function (event) {
        if (event.touches.length !== 1 || !canStart(event)) return;

        const touch = event.touches[0];
        startX = touch.clientX;
        startY = touch.clientY;
        offset = 0;
        tracking = true;
        dragging = false;
      },
      { passive: true }
    );

    element.addEventListener(
      "touchmove",
      function (event) {
        if (!tracking || event.touches.length !== 1) return;

        const touch = event.touches[0];
        const primary = primaryDelta(touch);
        const cross = Math.abs(crossDelta(touch));

        if (primary <= 0) {
          if (!dragging && Math.abs(primary) > 18) tracking = false;
          return;
        }

        if (!dragging) {
          if (primary < 12) return;

          if (primary < cross * axisRatio) {
            if (cross > 18) tracking = false;
            return;
          }

          dragging = true;
          element.classList.add("qc-swipe-dragging");
        }

        event.preventDefault();
        offset = Math.min(primary, maxOffset);

        element.style.setProperty(
          "--qc-swipe-offset",
          Math.round(offset) + "px"
        );
      },
      { passive: false }
    );

    element.addEventListener(
      "touchend",
      function () {
        finish(dragging && offset >= threshold);
      },
      { passive: true }
    );

    element.addEventListener(
      "touchcancel",
      function () {
        finish(false);
      },
      { passive: true }
    );

    return function () {
      resetVisual(false);
    };
  }


  function bindWheelDismiss(options) {
    const element = options && options.element;
    const direction = options && options.direction;
    const onDismiss = options && options.onDismiss;

    if (!element || typeof onDismiss !== "function") {
      return function () {};
    }

    if (direction !== "right" && direction !== "down") {
      throw new Error(
        "Dirección de trackpad no soportada: " + direction
      );
    }

    const threshold = Number(options.threshold) || 96;
    const axisRatio = Number(options.axisRatio) || 1.35;
    const physicalSign =
      Number(options.physicalSign) === 1 ? 1 : -1;

    const ignoreSelector =
      options.ignoreSelector ||
      "input, textarea, select, button, a, [contenteditable='true'], " +
        ".select2-container, .modal, [data-bs-toggle]";

    let accumulated = 0;
    let finishTimer = null;
    let lastEventAt = 0;
    let dismissed = false;

    function canStart(event) {
      if (
        event.target &&
        event.target.closest &&
        event.target.closest(ignoreSelector)
      ) {
        return false;
      }

      if (typeof options.canStart === "function") {
        return options.canStart(event) !== false;
      }

      return true;
    }

    function deltas(event) {
      const primaryRaw =
        direction === "right" ? event.deltaX : event.deltaY;

      const cross =
        direction === "right"
          ? Math.abs(event.deltaY)
          : Math.abs(event.deltaX);

      return {
        primary: primaryRaw * physicalSign,
        cross: cross,
      };
    }

    function reset() {
      window.clearTimeout(finishTimer);
      finishTimer = null;
      accumulated = 0;
      lastEventAt = 0;
      dismissed = false;
    }

    function scheduleReset() {
      window.clearTimeout(finishTimer);

      finishTimer = window.setTimeout(function () {
        accumulated = 0;
        lastEventAt = 0;
      }, 150);
    }

    function onWheel(event) {
      // Trackpads modernos suelen reportar píxeles.
      // Mouse wheels tradicionales suelen usar líneas/páginas.
      if (event.deltaMode !== 0) return;
      if (dismissed || !canStart(event)) return;

      const values = deltas(event);
      const primary = values.primary;
      const cross = values.cross;

      // No interferir con el scroll del eje contrario.
      if (Math.abs(primary) < cross * axisRatio) {
        return;
      }

      // Ignorar gesto opuesto.
      if (primary <= 0) {
        accumulated = 0;
        return;
      }

      const now = performance.now();

      // Una pausa perceptible separa un gesto del siguiente.
      if (lastEventAt && now - lastEventAt > 180) {
        accumulated = 0;
      }

      lastEventAt = now;

      // Ya reconocimos un gesto horizontal/vertical dominante dentro
      // de nuestro overlay: evitar que el navegador lo interprete además
      // como Back/Forward u overscroll de la página.
      event.preventDefault();

      // No movemos el panel evento por evento:
      // sólo acumulamos intención y dejamos que CSS haga el cierre.
      accumulated += primary;

      if (accumulated >= threshold) {
        dismissed = true;
        window.clearTimeout(finishTimer);
        onDismiss();

        window.setTimeout(reset, 320);
        return;
      }

      scheduleReset();
    }

    element.addEventListener("wheel", onWheel, {
      passive: false,
    });

    return function () {
      window.clearTimeout(finishTimer);
      element.removeEventListener("wheel", onWheel);
      reset();
    };
  }

  function whenIdle(callback, timeout) {
    if (typeof window.requestIdleCallback === "function") {
      window.requestIdleCallback(callback, {
        timeout: Number(timeout) || 1600,
      });
      return;
    }

    window.setTimeout(callback, 500);
  }

  window.QCOverlayUI = {
    createCache: createCache,
    bindSwipeDismiss: bindSwipeDismiss,
    bindWheelDismiss: bindWheelDismiss,
    whenIdle: whenIdle,
  };
})();
