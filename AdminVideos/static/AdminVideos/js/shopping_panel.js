(function () {
  "use strict";

  const panel = document.getElementById("shoppingPanel");
  const body = document.getElementById("shoppingPanelBody");
  const backdrop = document.getElementById("shoppingPanelBackdrop");
  const UI = window.QCOverlayUI;

  if (!panel || !body || !backdrop) return;

  const cache = UI ? UI.createCache(20000) : null;

  let lastTrigger = null;
  let currentUrl = "";
  let loading = false;

  function triggers() {
    return document.querySelectorAll("[data-shopping-panel-open]");
  }

  function setExpanded(value) {
    triggers().forEach(function (trigger) {
      trigger.setAttribute("aria-expanded", value ? "true" : "false");
    });
  }

  function setOpen(open) {
    document.body.classList.toggle("shopping-panel-open", open);
    panel.classList.toggle("is-open", open);
    backdrop.classList.toggle("is-open", open);
    backdrop.hidden = !open;
    panel.setAttribute("aria-hidden", open ? "false" : "true");
    setExpanded(open);

    if (open) {
      panel
        .querySelector("[data-shopping-panel-close]")
        ?.focus({ preventScroll: true });
    } else if (lastTrigger && document.contains(lastTrigger)) {
      lastTrigger.focus({ preventScroll: true });
    }
  }

  function loadingMarkup() {
    return (
      '<div class="shopping-panel-placeholder text-muted">' +
      "Cargando lista…" +
      "</div>"
    );
  }

  async function fetchContent(url) {
    const response = await fetch(url, {
      method: "GET",
      headers: { "X-Requested-With": "XMLHttpRequest" },
      credentials: "same-origin",
    });

    if (!response.ok) throw new Error("HTTP " + response.status);

    const html = await response.text();
    const doc = new DOMParser().parseFromString(html, "text/html");
    const content = doc.querySelector("#lista-compras-contenido");

    if (!content) {
      throw new Error("No se encontró el contenido de Lista de compras.");
    }

    return content.outerHTML;
  }

  function renderContent(html) {
    body.innerHTML = html;
    body.scrollTop = 0;
  }

  async function loadPanel(url, options) {
    const force = options && options.force;
    const cached = !force && cache ? cache.peek(url) : undefined;

    if (cached !== undefined) {
      renderContent(cached);

      cache
        .refresh(url, fetchContent)
        .then(function (freshHtml) {
          if (
            panel.classList.contains("is-open") &&
            currentUrl === url &&
            freshHtml !== cached
          ) {
            const scrollTop = body.scrollTop;
            renderContent(freshHtml);
            body.scrollTop = scrollTop;
          }
        })
        .catch(function () {});

      return;
    }

    if (loading) return;

    loading = true;
    body.innerHTML = loadingMarkup();

    try {
      const html = cache
        ? await (force
            ? cache.refresh(url, fetchContent)
            : cache.get(url, fetchContent))
        : await fetchContent(url);

      if (currentUrl === url) renderContent(html);
    } catch (error) {
      console.warn(
        "No se pudo abrir Lista de compras como panel.",
        error
      );
      window.location.href = url;
    } finally {
      loading = false;
    }
  }

  async function openPanel(trigger) {
    const url = trigger.getAttribute("href");

    if (!url) return;

    lastTrigger = trigger;
    currentUrl = url;
    setOpen(true);

    await loadPanel(url);
  }

  function closePanel() {
    setOpen(false);
    currentUrl = "";
    body.innerHTML = loadingMarkup();
  }

  function prefetchCurrent() {
    if (!cache) return;

    const trigger = document.querySelector(
      "[data-shopping-panel-open]"
    );
    const url = trigger && trigger.getAttribute("href");

    if (url) cache.prefetch(url, fetchContent);
  }

  document.addEventListener("click", function (event) {
    const opener = event.target.closest(
      "[data-shopping-panel-open]"
    );

    if (opener) {
      event.preventDefault();
      openPanel(opener);
      return;
    }

    if (event.target.closest("[data-shopping-panel-close]")) {
      event.preventDefault();
      closePanel();
    }
  });

  document.addEventListener(
    "pointerenter",
    function (event) {
      const opener = event.target.closest?.(
        "[data-shopping-panel-open]"
      );

      if (!opener || !cache) return;

      cache.prefetch(opener.getAttribute("href"), fetchContent);
    },
    true
  );

  document.addEventListener(
    "touchstart",
    function (event) {
      const opener = event.target.closest?.(
        "[data-shopping-panel-open]"
      );

      if (!opener || !cache) return;

      cache.prefetch(opener.getAttribute("href"), fetchContent);
    },
    { passive: true, capture: true }
  );

  backdrop.addEventListener("click", closePanel);

  document.addEventListener("keydown", function (event) {
    if (
      event.key === "Escape" &&
      panel.classList.contains("is-open")
    ) {
      closePanel();
    }
  });

  document.addEventListener(
    "shopping-panel:refresh",
    function () {
      if (panel.classList.contains("is-open") && currentUrl) {
        if (cache) cache.invalidate(currentUrl);
        loadPanel(currentUrl, { force: true });
      }
    }
  );

  if (UI) {
    UI.bindSwipeDismiss({
      element: panel,
      direction: "right",
      threshold: 72,
      maxOffset: Math.min(window.innerWidth * 0.72, 320),
      onDismiss: closePanel,
    });

    UI.bindWheelDismiss({
      element: panel,
      direction: "right",
      threshold: 96,
      maxOffset: Math.min(window.innerWidth * 0.72, 320),
      physicalSign: -1,
      onDismiss: closePanel,
    });

    UI.whenIdle(prefetchCurrent, 1400);
  }
})();
