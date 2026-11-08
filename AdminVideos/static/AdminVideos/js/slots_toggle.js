/* ============================================================
   §31 D1: toggle "Slots on/off"
   - Persiste en localStorage (por navegador).
   - Aplica/remueve body.qc-slots-off.
   - Default: ON (slots visibles).
   - El CSS oculta chips, "+ Slot", borde magenta del plato, y
     neutraliza el título magenta de comida solo-slot.
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
    var input = document.getElementById("qcSlotsToggle");
    if (input) input.checked = enabled;
  }

  function init() {
    var enabled = leerEstado();
    aplicar(enabled);

    var input = document.getElementById("qcSlotsToggle");
    if (input) {
      input.addEventListener("change", function () {
        var nuevo = !!input.checked;
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
