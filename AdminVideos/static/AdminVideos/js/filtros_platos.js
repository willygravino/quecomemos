
function inicializarCarouselesPlatos(contexto) {
  if (!window.bootstrap || !bootstrap.Carousel) return;

  const root = contexto || document;

  root.querySelectorAll(".carousel").forEach(function (carouselEl) {
    carouselEl.setAttribute("data-bs-touch", "true");

    bootstrap.Carousel.getOrCreateInstance(carouselEl, {
      interval: false,
      touch: true,
      wrap: true,
    });
  });
}

document.addEventListener("DOMContentLoaded", function () {
  // ============================================================
  // 1. Elementos base de la pantalla
  // ============================================================
  const form = document.getElementById("form-filtros-platos");
  const contenedor = document.getElementById("contenedor-listado-platos");

  if (!form || !contenedor) return;

  let estadoAntesDeLoQueTengo = null;

  function aplicarModoLoQueTengo(tipopag) {
    const usarLoQueTengo = form.querySelector('input[name="usar_lo_que_tengo"]');
    const quecomemos = form.querySelector('input[name="quecomemos"]');
    const misplatos = form.querySelector('input[name="misplatos"]');

    if (tipopag === "LoQueTengo") {
      if (!estadoAntesDeLoQueTengo) {
        estadoAntesDeLoQueTengo = {
          usarLoQueTengo: usarLoQueTengo ? usarLoQueTengo.checked : false,
          quecomemos: quecomemos ? quecomemos.checked : false,
          misplatos: misplatos ? misplatos.checked : false,
        };
      }

      if (usarLoQueTengo) {
        usarLoQueTengo.checked = true;
      }

      if (quecomemos && misplatos && !quecomemos.checked && !misplatos.checked) {
        quecomemos.checked = true;
        misplatos.checked = true;
      }

      return;
    }

    if (estadoAntesDeLoQueTengo) {
      if (usarLoQueTengo) {
        usarLoQueTengo.checked = estadoAntesDeLoQueTengo.usarLoQueTengo;
      }

      if (quecomemos) {
        quecomemos.checked = estadoAntesDeLoQueTengo.quecomemos;
      }

      if (misplatos) {
        misplatos.checked = estadoAntesDeLoQueTengo.misplatos;
      }

      estadoAntesDeLoQueTengo = null;
    }
  }

  // ============================================================
  // 2. Refrescar listado, carousel y lugares por AJAX
  // ============================================================
  function actualizarListadoPlatos() {
    const url = form.dataset.listadoUrl;
    const formData = new FormData(form);

    formData.set("return_to", window.location.pathname + window.location.search);

    fetch(url, {
      method: "POST",
      body: formData,
      headers: {
        "X-Requested-With": "XMLHttpRequest"
      }
    })
      .then(function (response) {
        if (!response.ok) {
          throw new Error("Error al cargar el listado");
        }

        return response.json();
      })
      .then(function (data) {
        contenedor.innerHTML = data.html_listado;

        const contenedorCarousel = document.getElementById("contenedor-carousel-platos");
        if (contenedorCarousel) {
          contenedorCarousel.innerHTML = data.html_carousel;
          inicializarCarouselesPlatos(contenedorCarousel);
        }

        const contenedorLugares = document.getElementById("contenedor-listado-lugares");
        if (contenedorLugares) {
          contenedorLugares.innerHTML = data.html_lugares;
        }

        if (typeof initListadoPlatos === "function") {
          initListadoPlatos();
        }
      })
      .catch(function (error) {
        console.error(error);
      });
  }

  // ============================================================
  // 3. Marcar activo el item actual del menú lateral
  // ============================================================
  function marcarMenuItem(link, activo) {
    link.classList.toggle("is-active", activo);

    const item = link.closest(".nav-item");
    if (item) {
      item.classList.toggle("active", activo);
    }

    const texto = link.querySelector(".item-text");
    if (texto) {
      texto.classList.toggle("text-white", activo);
      texto.classList.toggle("fw-bold", activo);
      texto.classList.toggle("text-white-50", !activo);
    }

    const icono = link.querySelector(".icon-wrap i");
    if (icono) {
      icono.classList.toggle("text-white-50", !activo);
    }
  }

  function actualizarMenuLateralActivo(tipopag) {
    document.querySelectorAll("#accordionSidebar .nav-item").forEach(function (item) {
      item.classList.remove("active");
    });

    document.querySelectorAll(".js-filtro-tipopag").forEach(function (link) {
      const activo = link.dataset.tipopag === tipopag;

      link.classList.toggle("is-active", activo);
      link.classList.toggle("active", activo);

      if (activo) {
        const item = link.closest(".nav-item");
        if (item) {
          item.classList.add("active");
        }
      }
    });

    document.querySelectorAll(".js-filtro-tipopag-grupo").forEach(function (link) {
      const valores = (link.dataset.tipopagValues || "")
        .split(",")
        .map(function (valor) {
          return valor.trim();
        })
        .filter(Boolean);

      marcarMenuItem(link, valores.includes(tipopag));
    });

    document.querySelectorAll(".js-filtro-tipopag:not(.dropdown-item)").forEach(function (link) {
      marcarMenuItem(link, link.dataset.tipopag === tipopag);
    });
  }

  // ============================================================

  // ============================================================
  // 3.a Actualizar título "Sugerencias de..." según tipopag actual
  // ============================================================
  function etiquetaSugerenciasTipopag(tipopag) {
    const etiquetas = {
      "Principal": "Plato principal",
      "Entrada": "Entradas",
      "Guarnicion": "Guarniciones",
      "Dip": "Dips",
      "Salsa": "Salsas",
      "Picada": "Picadas armadas",
      "Ingrediente de picada": "Ingredientes de picada",
      "Postre": "Postres",
      "Trago": "Bebidas / tragos",
      "Delivery": "delivery",
      "Comerafuera": "lugares para comer afuera",
      "LoQueTengo": "lo que tengo",
    };

    return etiquetas[tipopag] || tipopag || "Plato principal";
  }

  function actualizarTituloSugerencias(tipopag) {
    const target = document.getElementById("sugerenciasPlatosTituloTipo");

    if (!target) {
      return;
    }

    target.textContent = etiquetaSugerenciasTipopag(tipopag);
    target.dataset.tipopagActual = tipopag || "Principal";
  }


  // ============================================================
  // 3.a.1 Barrido visual mientras cambia el filtro por AJAX
  // ============================================================
  let filtroBarridoHideTimer = null;

  function obtenerNodosBarridoCambioFiltro() {
    const selectores = [
      ".sugerencias-platos-titulo-bar",
      "#filtrosPlatosForm",
      "#filtros-platos-form",
      ".filtros-platos-panel",
      ".filtros-platos-wrapper",
      ".filtros-activos-wrap",
      "[data-listado-url]",
      "#contenedor-carousel-platos",
      "#contenedor-listado-platos",
      "#contenedor-lugares",
      "#contenedor-delivery",
      "#contenedor-comer-afuera",
    ];

    const nodos = [];

    selectores.forEach((selector) => {
      document.querySelectorAll(selector).forEach((nodo) => {
        if (!nodos.includes(nodo)) {
          nodos.push(nodo);
        }
      });
    });

    return nodos.filter((nodo) => {
      const rect = nodo.getBoundingClientRect();
      return rect.width > 0 && rect.height > 0;
    });
  }

  function calcularRectBarridoCambioFiltro() {
    const nodos = obtenerNodosBarridoCambioFiltro();

    if (!nodos.length) {
      return null;
    }

    const rects = nodos.map((nodo) => nodo.getBoundingClientRect());

    const top = Math.min(...rects.map((rect) => rect.top));
    const left = Math.min(...rects.map((rect) => rect.left));
    const right = Math.max(...rects.map((rect) => rect.right));
    const bottom = Math.max(...rects.map((rect) => rect.bottom));

    const margen = 6;
    const viewportWidth = window.innerWidth || document.documentElement.clientWidth;
    const viewportHeight = window.innerHeight || document.documentElement.clientHeight;

    return {
      top: Math.max(0, top - margen),
      left: Math.max(0, left - margen),
      width: Math.min(viewportWidth, right + margen) - Math.max(0, left - margen),
      height: Math.min(viewportHeight, bottom + margen) - Math.max(0, top - margen),
    };
  }

  function obtenerOverlayBarridoCambioFiltro() {
    let overlay = document.getElementById("filtroPlatosBarridoOverlay");

    if (!overlay) {
      overlay = document.createElement("div");
      overlay.id = "filtroPlatosBarridoOverlay";
      overlay.className = "filtro-platos-barrido-overlay";
      overlay.setAttribute("aria-hidden", "true");
      document.body.appendChild(overlay);
    }

    return overlay;
  }

  function posicionarBarridoCambioFiltro() {
    const overlay = obtenerOverlayBarridoCambioFiltro();
    const rect = calcularRectBarridoCambioFiltro();

    if (!rect) {
      return overlay;
    }

    overlay.style.top = `${rect.top}px`;
    overlay.style.left = `${rect.left}px`;
    overlay.style.width = `${rect.width}px`;
    overlay.style.height = `${rect.height}px`;

    return overlay;
  }

  function activarBarridoCambioFiltro() {
    window.clearTimeout(filtroBarridoHideTimer);

    document.body.classList.add("filtro-platos-cambiando");

    const overlay = posicionarBarridoCambioFiltro();
    overlay.classList.remove("is-hiding");

    requestAnimationFrame(() => {
      posicionarBarridoCambioFiltro();
      overlay.classList.add("is-active");
    });
  }

  function desactivarBarridoCambioFiltro() {
    const overlay = document.getElementById("filtroPlatosBarridoOverlay");

    document.body.classList.remove("filtro-platos-cambiando");

    if (!overlay) {
      return;
    }

    overlay.classList.add("is-hiding");
    overlay.classList.remove("is-active");

    filtroBarridoHideTimer = window.setTimeout(() => {
      overlay.remove();
    }, 180);
  }

  function actualizarListadoPlatosConBarrido() {
    activarBarridoCambioFiltro();

    let resultado = null;

    try {
      resultado = actualizarListadoPlatos();
    } catch (error) {
      desactivarBarridoCambioFiltro();
      throw error;
    }

    if (resultado && typeof resultado.finally === "function") {
      resultado.finally(() => {
        desactivarBarridoCambioFiltro();
      });
    } else {
      window.setTimeout(() => {
        desactivarBarridoCambioFiltro();
      }, 650);
    }

    return resultado;
  }

  // 3.b Actualizar botón flotante de crear según tipopag actual
  // ============================================================
  function actualizarBotonCrearPlato(tipopag) {
    const boton = document.getElementById("botonCrearPlatoFlotante");

    if (!boton) {
      return;
    }

    const esLugar = tipopag === "Delivery" || tipopag === "Comerafuera";
    const urlBase = esLugar ? boton.dataset.urlCrearLugar : boton.dataset.urlCrearPlato;

    if (!urlBase) {
      return;
    }

    const params = new URLSearchParams();

    if (tipopag) {
      params.set("tipopag", tipopag);
    }

    params.set("return_to", window.location.pathname + window.location.search);

    boton.href = `${urlBase}?${params.toString()}`;

    
    let titulo = "Agregar receta de plato principal";
    if (tipopag === "Picada") {
      titulo = "Armar picada";
    } else if (tipopag === "Ingrediente de picada") {
      titulo = "Agregar ingrediente de picada";
    } else if (tipopag === "Guarnicion") {
      titulo = "Agregar receta de guarnición";
    } else if (tipopag === "Comerafuera") {
      titulo = "Agregar lugar para comer afuera";
    } else if (tipopag === "Delivery") {
      titulo = "Agregar delivery";
    } else if (tipopag && tipopag !== "Principal" && tipopag !== "Dash") {
      titulo = `Agregar receta de ${tipopag.toLowerCase()}`;
    }

    boton.title = titulo;
    boton.setAttribute("aria-label", titulo);
  }

  // ============================================================
  // 4. Buscar por palabra clave sin recargar
  // ============================================================
  form.addEventListener("submit", function (event) {
    event.preventDefault();
    actualizarListadoPlatosConBarrido();
  });

  // ============================================================
  // 4.b Buscar por palabra clave mientras se escribe
  // ============================================================
  const inputPalabraClave = form.querySelector('input[name="palabra_clave"]');
  let timeoutBusquedaPalabraClave = null;

  function actualizarVisualPalabraClave() {
    if (!inputPalabraClave) {
      return;
    }

    const grupo = inputPalabraClave.closest(".filtro-keyword-box");
    const activo = inputPalabraClave.value.trim().length > 0;

    if (grupo) {
      grupo.classList.toggle("filtro-keyword-activo", activo);
    }

    inputPalabraClave.classList.toggle("text-danger", activo);
    inputPalabraClave.classList.toggle("fw-semibold", activo);
  }

  if (inputPalabraClave) {
    inputPalabraClave.addEventListener("input", function () {
      actualizarVisualPalabraClave();
      clearTimeout(timeoutBusquedaPalabraClave);

      timeoutBusquedaPalabraClave = setTimeout(function () {
        actualizarListadoPlatosConBarrido();
      }, 400);
    });

    actualizarVisualPalabraClave();
  }

  // ============================================================
  // 5. Filtrar por checkboxes sin recargar
  // ============================================================
  form.querySelectorAll("input[type='checkbox']").forEach(function (checkbox) {
    checkbox.addEventListener("change", function () {
      actualizarListadoPlatosConBarrido();
    });
  });

  // ============================================================
  // 6. Filtrar desde el menú lateral sin recargar
  // ============================================================
  document.addEventListener("click", function (event) {
    const link = event.target.closest(".js-filtro-tipopag");

    if (!link) {
      return;
    }

    const tipopag = link.dataset.tipopag;

    // Fallback seguro: si falta algo, dejamos navegar normal.
    if (!tipopag || !window.fetch) {
      return;
    }

    const inputTipopag = form.querySelector('input[name="tipopag"]');

    if (!inputTipopag) {
      return;
    }

    event.preventDefault();

    inputTipopag.value = tipopag;
    aplicarModoLoQueTengo(tipopag);

    actualizarMenuLateralActivo(tipopag);
    actualizarTituloSugerencias(tipopag);

    const nuevaUrl = new URL(link.href);
    window.history.pushState({ tipopag: tipopag }, "", nuevaUrl.toString());

    actualizarBotonCrearPlato(tipopag);

    const dropdown = link.closest(".dropdown");
    const dropdownToggle = dropdown ? dropdown.querySelector('[data-bs-toggle="dropdown"]') : null;

    if (dropdownToggle && window.bootstrap && bootstrap.Dropdown) {
      bootstrap.Dropdown.getOrCreateInstance(dropdownToggle).hide();
    }

    actualizarListadoPlatosConBarrido();
  });

  // ============================================================
  // 7. Soportar botón atrás / adelante del navegador
  // ============================================================
  window.addEventListener("popstate", function () {
    const params = new URLSearchParams(window.location.search);
    const tipopag = params.get("tipopag");

    if (!tipopag) {
      return;
    }

    const inputTipopag = form.querySelector('input[name="tipopag"]');

    if (!inputTipopag) {
      return;
    }
    inputTipopag.value = tipopag;
    actualizarMenuLateralActivo(tipopag);
    actualizarTituloSugerencias(tipopag);
    actualizarBotonCrearPlato(tipopag);
    actualizarListadoPlatosConBarrido();

  });
});
