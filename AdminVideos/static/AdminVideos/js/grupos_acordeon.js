(function () {
  "use strict";
  var STORAGE_KEY = "qc_grupos_abiertos";

  function leerEstado() {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}"); }
    catch (e) { return {}; }
  }

  function guardarEstado(estado) {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(estado)); }
    catch (e) {}
  }

  function aplicarA(d) {
    if (d.__acordeonBound) return;
    d.__acordeonBound = true;
    var codigo = d.dataset.grupo;
    if (!codigo) return;
    var estado = leerEstado();
    if (Object.prototype.hasOwnProperty.call(estado, codigo)) {
      d.open = !!estado[codigo];
    }
    d.addEventListener("toggle", function () {
      var e = leerEstado();
      e[codigo] = d.open;
      guardarEstado(e);
    });
  }

  function aplicar() {
    document.querySelectorAll("details[data-grupo]").forEach(aplicarA);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", aplicar);
  } else {
    aplicar();
  }

  var observado = false;
  function observarContenedor(intentos) {
    intentos = intentos || 0;
    if (observado) return;
    var cont = document.getElementById("contenedor-listado-platos");
    if (!cont) {
      if (intentos < 20) {
        setTimeout(function () { observarContenedor(intentos + 1); }, 100);
      }
      return;
    }
    observado = true;
    var mo = new MutationObserver(function () {
      requestAnimationFrame(aplicar);
    });
    mo.observe(cont, { childList: true });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () { observarContenedor(0); });
  } else {
    observarContenedor(0);
  }
})();
