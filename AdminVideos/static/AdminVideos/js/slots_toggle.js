/* ============================================================
   §31 D1c: toggle "Slots on/off" (botón circular "S")
   - Persiste en localStorage (por navegador).
   - Aplica/remueve body.qc-slots-off.
   - Default: ON (slots visibles).
   - aria-pressed="true" = slots ON, "false" = slots OFF.
   ============================================================ */
(function () {
  var STORAGE_KEY = "qc_slots_enabled";

  function leerEstado() {
    try {
      var v = localStorage.getItem(STORAGE_KEY);
      if (v === null) return true;      // default ON
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
    if (btn) {
      btn.setAttribute("aria-pressed", enabled ? "true" : "false");
      btn.dataset.slotsEnabled = enabled ? "1" : "0";
      btn.title = enabled ? "Ocultar slots" : "Mostrar slots";
    }
  }

  function init() {
    var enabled = leerEstado();
    aplicar(enabled);

    var btn = document.getElementById("qcSlotsToggle");
    if (btn) {
      btn.addEventListener("click", function () {
        var nuevo = btn.getAttribute("aria-pressed") !== "true";
        aplicar(nuevo);
        guardarEstado(nuevo);
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // Expuesto por si un refresh AJAX necesita reaplicar el estado
  window.qcAplicarSlotsToggle = aplicar;
})();
