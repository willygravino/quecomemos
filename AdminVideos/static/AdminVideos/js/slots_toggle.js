/* ============================================================
   §31 D2k: toggle "Slots on/off" (botón circular con ícono filtro)
   - Persiste en localStorage (por navegador). Default: ON.
   - Aplica/remueve body.qc-slots-off.
   - Handler DELEGADO en document (sobrevive al innerHTML reemplazado
     por refrescarMenuProgramado() de menu_programado.js).
   - MutationObserver re-sincroniza aria-pressed/title del botón nuevo
     después de cada refresh (evita que el botón re-renderizado quede con
     aria-pressed desactualizado).
   ============================================================ */
(function () {
  var STORAGE_KEY = "qc_slots_enabled";
  var _observer = null;
  var _aplicando = false;

  function leerEstado() {
    try {
      var v = localStorage.getItem(STORAGE_KEY);
      if (v === null) return true;
      return v === "1";
    } catch (e) {
      return true;
    }
  }

  function guardarEstado(enabled) {
    try {
      localStorage.setItem(STORAGE_KEY, enabled ? "1" : "0");
    } catch (e) {}
  }

  function aplicar(enabled) {
    if (!document.body) return;
    document.body.classList.toggle("qc-slots-off", !enabled);
    var btn = document.getElementById("qcSlotsToggle");
    if (!btn) return;
    var estadoStr = enabled ? "true" : "false";
    var dataStr = enabled ? "1" : "0";
    var titulo = enabled ? "Ocultar slots" : "Mostrar slots";
    if (btn.getAttribute("aria-pressed") !== estadoStr) {
      btn.setAttribute("aria-pressed", estadoStr);
    }
    if (btn.dataset.slotsEnabled !== dataStr) {
      btn.dataset.slotsEnabled = dataStr;
    }
    if (btn.title !== titulo) {
      btn.title = titulo;
    }
  }

  // Handler delegado: funciona aunque el botón sea reemplazado.
  document.addEventListener("click", function (event) {
    var btn = event.target.closest("#qcSlotsToggle");
    if (!btn) return;
    event.preventDefault();
    var actual = btn.getAttribute("aria-pressed") === "true";
    var nuevo = !actual;
    aplicar(nuevo);
    guardarEstado(nuevo);
  });

  // Observer: si el botón es re-renderizado por un refresh del menú,
  // re-aplicar el estado del localStorage. Flag _aplicando evita loop.
  function observar() {
    if (_observer || typeof MutationObserver === "undefined") return;
    _observer = new MutationObserver(function () {
      if (_aplicando) return;
      _aplicando = true;
      try {
        aplicar(leerEstado());
      } finally {
        _aplicando = false;
      }
    });
    _observer.observe(document.body, { childList: true, subtree: true });
  }

  function init() {
    aplicar(leerEstado());
    observar();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // Expuesto por si hace falta re-aplicar manualmente.
  window.qcAplicarSlotsToggle = aplicar;
})();
