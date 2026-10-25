
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

  // Un único canal de render para listado + carousel + lugares.
  // Si cambia el filtro mientras hay un request en vuelo, sólo el último
  // puede pintar la pantalla.
  let listadoAbortController = null;
  let listadoRequestSeq = 0;
  let filtroBarridoSeq = 0;

  // Sincronizar el botón de creación con la vista inicial.
  actualizarBotonCrearPlato(
    form.querySelector('input[name="tipopag"]')?.value || "Principal"
  );

  // Impedir crear platos desde la vista Todos.
  document.addEventListener("click", function (event) {
    const botonCrear = event.target.closest("#botonCrearPlatoFlotante");
    if (!botonCrear) return;

    const tipopagFormulario =
      form.querySelector('input[name="tipopag"]')?.value || "";
    const tipopagUrl =
      new URLSearchParams(window.location.search).get("tipopag") || "";

    if (tipopagFormulario === "Todos" || tipopagUrl === "Todos") {
      event.preventDefault();
      event.stopImmediatePropagation();
    }
  }, true);
// ============================================================
  // 2. Refrescar listado, carousel y lugares por AJAX
  // ============================================================
  function actualizarListadoPlatos() {
    const url = form.dataset.listadoUrl;
    const formData = new FormData(form);

    const tabDiaActivo = document.querySelector(
      "#diasTab .nav-link.active[data-dia-activo]"
    );
    const diaActivo = (
      (window.QCDiaActivo && window.QCDiaActivo.get()) ||
      (tabDiaActivo && tabDiaActivo.dataset.diaActivo) ||
      ""
    );

    if (diaActivo) {
      formData.set("dia_activo", diaActivo);
    }

    formData.set("return_to", window.location.pathname + window.location.search);

    const requestSeq = ++listadoRequestSeq;

    if (listadoAbortController) {
      listadoAbortController.abort();
    }

    const controller = new AbortController();
    listadoAbortController = controller;

    // IMPORTANTE: devolver la Promise. El controlador de barrido necesita
    // esperar el AJAX real, no sólo la animación.
    return fetch(url, {
      method: "POST",
      body: formData,
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-QC-Stateless-Filters": "1"
      },
      credentials: "same-origin",
      cache: "no-store",
      signal: controller.signal
    })
      .then(function (response) {
        if (!response.ok) {
          throw new Error("Error al cargar el listado");
        }

        return response.json();
      })
      .then(function (data) {
        // Un response viejo jamás puede sobrescribir un filtro más nuevo.
        if (requestSeq !== listadoRequestSeq) {
          return {
            ignored: true,
            reason: "stale-response"
          };
        }

        contenedor.innerHTML = data.html_listado || "";

        const contenedorCarousel = document.getElementById("contenedor-carousel-platos");
        if (contenedorCarousel) {
          contenedorCarousel.innerHTML = data.html_carousel || "";
          inicializarCarouselesPlatos(contenedorCarousel);
        }

        const contenedorLugares = document.getElementById("contenedor-listado-lugares");
        if (contenedorLugares) {
          contenedorLugares.innerHTML = data.html_lugares || "";
        }

        if (typeof initListadoPlatos === "function") {
          initListadoPlatos();
        }

        return data;
      })
      .catch(function (error) {
        if (error && error.name === "AbortError") {
          return {
            ignored: true,
            reason: "aborted"
          };
        }

        console.error(error);
        throw error;
      })
      .finally(function () {
        if (listadoAbortController === controller) {
          listadoAbortController = null;
        }
      });
  }

  // ============================================================
  // 3. Sincronizar selector horizontal y filtro global
  // ============================================================
  function estaActivoLoQueTengo() {
    const input = form.querySelector('input[name="lo_que_tengo_activo"]');
    return Boolean(input && input.value === "1");
  }

  function actualizarEstadoLoQueTengo(activo, tipopag) {
    const input = form.querySelector('input[name="lo_que_tengo_activo"]');
    const linksFiltro = document.querySelectorAll(".js-filtro-lo-que-tengo");

    document.querySelectorAll(".js-lo-que-tengo-state-root").forEach(function (root) {
      root.classList.toggle("lo-que-tengo-activo", activo);
    });

    if (input) {
      input.value = activo ? "1" : "0";
    }

    linksFiltro.forEach(function (linkFiltro) {
      linkFiltro.classList.toggle("is-active", activo);
      linkFiltro.dataset.loQueTengoActivo = activo ? "1" : "0";
      linkFiltro.setAttribute("aria-pressed", activo ? "true" : "false");
      linkFiltro.setAttribute("aria-checked", activo ? "true" : "false");

      const urlFiltro = new URL(linkFiltro.href, window.location.href);
      urlFiltro.searchParams.set("tipopag", tipopag || "Principal");
      urlFiltro.searchParams.set("lo_que_tengo", activo ? "0" : "1");
      linkFiltro.href = urlFiltro.toString();
    });

    document.querySelectorAll(".js-filtro-tipopag").forEach(function (link) {
      link.classList.toggle(
        "is-filtered-lo-que-tengo",
        activo && link.dataset.tipopag === tipopag
      );
    });
  }

  window.addEventListener("loQueTengo:disponibilidad", function (event) {
    const disponible = Boolean(event.detail && event.detail.disponible);

    if (disponible || !estaActivoLoQueTengo()) {
      return;
    }

    const inputTipopag = form.querySelector('input[name="tipopag"]');
    const inputLoQueTengo = form.querySelector('input[name="lo_que_tengo_activo"]');

    if (!inputTipopag || !inputLoQueTengo) {
      return;
    }

    const tipopag = inputTipopag.value || "Principal";
    inputLoQueTengo.value = "0";
    actualizarEstadoLoQueTengo(false, tipopag);

    const nuevaUrl = new URL(window.location.href);
    nuevaUrl.searchParams.set("tipopag", tipopag);
    nuevaUrl.searchParams.set("lo_que_tengo", "0");

    window.history.replaceState(
      { tipopag: tipopag, loQueTengoActivo: false },
      "",
      nuevaUrl.toString()
    );

    actualizarSelectorHorizontalActivo(tipopag);
    actualizarListadoPlatosConBarrido();
  });

  function actualizarSelectorHorizontalActivo(tipopag) {
    document.querySelectorAll(".js-filtro-tipopag").forEach(function (link) {
      const activo = link.dataset.tipopag === tipopag;
      link.classList.toggle("is-active", activo);
      link.classList.toggle("active", activo);
      link.setAttribute("aria-current", activo ? "page" : "false");
    });

    actualizarEstadoLoQueTengo(estaActivoLoQueTengo(), tipopag);
    centrarCategoriaHorizontalActiva(tipopag);
  }

  function centrarCategoriaHorizontalActiva(tipopag) {
    const rail = document.getElementById("selectorPlatosRail");
    if (!rail) {
      return;
    }

    const activo = Array.from(rail.querySelectorAll(".js-filtro-tipopag")).find(
      function (link) {
        return link.dataset.tipopag === tipopag;
      }
    );

    if (!activo) {
      return;
    }

    window.requestAnimationFrame(function () {
      const destino = activo.offsetLeft - ((rail.clientWidth - activo.offsetWidth) / 2);
      rail.scrollTo({
        left: Math.max(0, destino),
        behavior: "smooth"
      });
    });
  }

  // ============================================================

  // ============================================================
  // 3.a Actualizar título "Sugerencias de..." según tipopag actual
  // ============================================================
  function etiquetaSugerenciasTipopag(tipopag) {
    const etiquetas = {
      "Principal": "Platos principales",
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
      "Todos": "Todos los platos",
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
  let filtroBarridoInicio = 0;

  const FILTRO_BARRIDO_MIN_MS = 320;
  const FILTRO_BARRIDO_MAX_MS = 5000;
  const FILTRO_BARRIDO_DOM_QUIETO_MS = 180;

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
      "#contenedor-listado-lugares",
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

  function obtenerNodosRenderCambioFiltro() {
    const selectores = [
      "#contenedor-carousel-platos",
      "#contenedor-listado-platos",
      "#contenedor-listado-lugares",
      "#contenedor-lugares",
      "#contenedor-delivery",
      "#contenedor-comer-afuera",
      "[data-listado-url]",
    ];

    const nodos = [];

    selectores.forEach((selector) => {
      document.querySelectorAll(selector).forEach((nodo) => {
        if (!nodos.includes(nodo)) {
          nodos.push(nodo);
        }
      });
    });

    return nodos.filter((nodo) => nodo.isConnected);
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

    filtroBarridoInicio = Date.now();
    document.body.classList.add("filtro-platos-cambiando");

    const overlay = posicionarBarridoCambioFiltro();
    overlay.classList.remove("is-hiding");

    requestAnimationFrame(() => {
      posicionarBarridoCambioFiltro();
      overlay.classList.add("is-active");
    });
  }

  function esperarRenderCambioFiltro() {
    const nodos = obtenerNodosRenderCambioFiltro();

    if (!nodos.length || typeof MutationObserver === "undefined") {
      return new Promise((resolve) => {
        window.setTimeout(resolve, 650);
      });
    }

    return new Promise((resolve) => {
      let finalizado = false;
      let quietTimer = null;

      const finalizar = () => {
        if (finalizado) {
          return;
        }

        finalizado = true;
        window.clearTimeout(quietTimer);
        window.clearTimeout(maxTimer);
        observer.disconnect();
        resolve();
      };

      const observer = new MutationObserver(() => {
        window.clearTimeout(quietTimer);
        posicionarBarridoCambioFiltro();

        quietTimer = window.setTimeout(() => {
          finalizar();
        }, FILTRO_BARRIDO_DOM_QUIETO_MS);
      });

      const maxTimer = window.setTimeout(() => {
        finalizar();
      }, FILTRO_BARRIDO_MAX_MS);

      nodos.forEach((nodo) => {
        observer.observe(nodo, {
          childList: true,
          subtree: true,
          attributes: true,
          characterData: true,
        });
      });
    });
  }

  function desactivarBarridoCambioFiltro() {
    const overlay = document.getElementById("filtroPlatosBarridoOverlay");
    const elapsed = Date.now() - filtroBarridoInicio;
    const delay = Math.max(0, FILTRO_BARRIDO_MIN_MS - elapsed);

    window.setTimeout(() => {
      document.body.classList.remove("filtro-platos-cambiando");

      if (!overlay) {
        return;
      }

      overlay.classList.add("is-hiding");
      overlay.classList.remove("is-active");

      filtroBarridoHideTimer = window.setTimeout(() => {
        overlay.remove();
      }, 180);
    }, delay);
  }

  function actualizarListadoPlatosConBarrido() {
    const barridoSeq = ++filtroBarridoSeq;
    activarBarridoCambioFiltro();

    const esperaRender = esperarRenderCambioFiltro();
    let resultado = null;

    try {
      resultado = actualizarListadoPlatos();
    } catch (error) {
      if (barridoSeq === filtroBarridoSeq) {
        desactivarBarridoCambioFiltro();
      }
      throw error;
    }

    const esperaAjax = resultado && typeof resultado.finally === "function"
      ? resultado
      : Promise.resolve();

    Promise.allSettled([esperaAjax, esperaRender]).then(function () {
      // Un request abortado/viejo no puede apagar el overlay del request nuevo.
      if (barridoSeq !== filtroBarridoSeq) {
        return;
      }

      desactivarBarridoCambioFiltro();
    });

    return resultado;
  }


  // 3.b Actualizar botón flotante de crear según tipopag actual
  // ============================================================
  function actualizarBotonCrearPlato(tipopag) {
    const boton = document.getElementById("botonCrearPlatoFlotante");

    if (!boton) {
      return;
    }

    const esVistaTodos = tipopag === "Todos";

    // En Todos se muestra el botón, pero queda gris y sin acción.
    boton.style.removeProperty("display");
    boton.classList.toggle("disabled", esVistaTodos);
    boton.classList.toggle("btn-secondary", esVistaTodos);
    boton.classList.toggle("btn-success", !esVistaTodos);
    boton.setAttribute("aria-disabled", esVistaTodos ? "true" : "false");
    boton.tabIndex = esVistaTodos ? -1 : 0;

    const textoBoton = boton.querySelector(".boton-crear-plato-texto");

    if (esVistaTodos) {
      boton.removeAttribute("href");
      const aviso = "Seleccioná un tipo de plato para crear uno nuevo";
      boton.title = aviso;
      boton.setAttribute("aria-label", aviso);
      if (textoBoton) {
        textoBoton.textContent = "Elegí una categoría";
      }
      return;
    }


    const esLugar = tipopag === "Delivery" || tipopag === "Comerafuera";
    const urlBase = esLugar ? boton.dataset.urlCrearLugar : boton.dataset.urlCrearPlato;

    if (!urlBase) {
      return;
    }

    const params = new URLSearchParams();

    if (tipopag && tipopag !== "Todos") {
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
    } else if (
      tipopag &&
      tipopag !== "Principal" &&
      tipopag !== "Todos" &&
      tipopag !== "Dash"
    ) {
      titulo = `Agregar receta de ${tipopag.toLowerCase()}`;
    }

    boton.title = titulo;
    boton.setAttribute("aria-label", titulo);
    if (textoBoton) {
      textoBoton.textContent = titulo
        .replace("Agregar receta de ", "Agregar ")
        .replace("Agregar ingrediente de picada", "Agregar ingrediente");
    }
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

  // 5.a Impedir que queden los dos toggles de categoría destildados.
  // Se corre en fase capture para adelantarse al listener genérico y no
  // disparar un fetch inútil con la lista vacía.
  const checkboxesCategoria = form.querySelectorAll(
    'input[name="ver_cotidiano"], input[name="ver_especial"]'
  );
  let avisoCategoriaTimer = null;

  function mostrarAvisoCategoriaVacia() {
    const grupo = form.querySelector('[aria-label="Categorías visibles"]');
    if (!grupo) return;

    let aviso = document.getElementById("aviso-categoria-vacia");
    if (!aviso) {
      aviso = document.createElement("div");
      aviso.id = "aviso-categoria-vacia";
      aviso.className = "small text-danger mt-1";
      aviso.textContent = "Tenés que elegir al menos una categoría.";
      grupo.parentNode.insertBefore(aviso, grupo.nextSibling);
    }

    aviso.style.display = "";
    window.clearTimeout(avisoCategoriaTimer);
    avisoCategoriaTimer = window.setTimeout(function () {
      aviso.style.display = "none";
    }, 2500);
  }

  checkboxesCategoria.forEach(function (checkbox) {
    checkbox.addEventListener("change", function (event) {
      const algunoMarcado = Array.from(checkboxesCategoria).some(function (c) {
        return c.checked;
      });

      if (!algunoMarcado) {
        checkbox.checked = true;
        mostrarAvisoCategoriaVacia();
        event.stopImmediatePropagation();
      }
    }, true);
  });

  // ============================================================
  // 5.b Desplazar el selector horizontal con sus flechas
  // ============================================================
  document.addEventListener("click", function (event) {
    const boton = event.target.closest("[data-selector-platos-scroll]");
    if (!boton) {
      return;
    }

    const rail = document.getElementById("selectorPlatosRail");
    if (!rail) {
      return;
    }

    const direccion = Number(boton.dataset.selectorPlatosScroll) || 0;
    rail.scrollBy({
      left: direccion * Math.max(260, rail.clientWidth * 0.72),
      behavior: "smooth"
    });
  });

  // ============================================================
  // 6. Filtrar desde cualquier selector sin recargar
  // ============================================================
  document.addEventListener("click", function (event) {
    const linkFiltro = event.target.closest(".js-filtro-lo-que-tengo");

    if (!linkFiltro || !window.fetch) {
      return;
    }

    const inputTipopag = form.querySelector('input[name="tipopag"]');
    const inputLoQueTengo = form.querySelector('input[name="lo_que_tengo_activo"]');

    if (!inputTipopag || !inputLoQueTengo) {
      return;
    }

    event.preventDefault();

    if (linkFiltro.dataset.tienePalabrasLoQueTengo !== "1") {
      return;
    }

    const tipopag = inputTipopag.value || "Principal";
    const activar = !estaActivoLoQueTengo();

    inputLoQueTengo.value = activar ? "1" : "0";
    actualizarSelectorHorizontalActivo(tipopag);

    const nuevaUrl = new URL(window.location.href);
    nuevaUrl.searchParams.set("tipopag", tipopag);

    if (activar) {
      nuevaUrl.searchParams.set("lo_que_tengo", "1");
    } else {
      nuevaUrl.searchParams.set("lo_que_tengo", "0");
    }

    const cbCat1 = form.querySelector('input[name="ver_cotidiano"]');
    const cbEsp1 = form.querySelector('input[name="ver_especial"]');
    if (cbCat1) nuevaUrl.searchParams.set("ver_cotidiano", cbCat1.checked ? "1" : "0");
    if (cbEsp1) nuevaUrl.searchParams.set("ver_especial", cbEsp1.checked ? "1" : "0");

    window.history.pushState(
      { tipopag: tipopag, loQueTengoActivo: activar },
      "",
      nuevaUrl.toString()
    );

    actualizarBotonCrearPlato(tipopag);
    actualizarListadoPlatosConBarrido();
  });

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
    actualizarSelectorHorizontalActivo(tipopag);
    actualizarTituloSugerencias(tipopag);

    const nuevaUrl = new URL(link.href, window.location.href);
    nuevaUrl.searchParams.set("tipopag", tipopag);

    if (estaActivoLoQueTengo()) {
      nuevaUrl.searchParams.set("lo_que_tengo", "1");
    } else {
      nuevaUrl.searchParams.set("lo_que_tengo", "0");
    }

    const cbCat2 = form.querySelector('input[name="ver_cotidiano"]');
    const cbEsp2 = form.querySelector('input[name="ver_especial"]');
    if (cbCat2) nuevaUrl.searchParams.set("ver_cotidiano", cbCat2.checked ? "1" : "0");
    if (cbEsp2) nuevaUrl.searchParams.set("ver_especial", cbEsp2.checked ? "1" : "0");

    window.history.pushState(
      { tipopag: tipopag, loQueTengoActivo: estaActivoLoQueTengo() },
      "",
      nuevaUrl.toString()
    );

    actualizarBotonCrearPlato(tipopag);

    const dropdown = link.closest(".dropdown");
    const dropdownToggle = dropdown
      ? dropdown.querySelector('[data-bs-toggle="dropdown"]')
      : null;

    if (dropdownToggle && window.bootstrap && bootstrap.Dropdown) {
      bootstrap.Dropdown.getOrCreateInstance(dropdownToggle).hide();
    }

    actualizarListadoPlatosConBarrido();
  });

  // 7. Soportar botón atrás / adelante del navegador
  // ============================================================
  window.addEventListener("popstate", function () {
    const params = new URLSearchParams(window.location.search);
    let tipopag = params.get("tipopag") || "Principal";
    let loQueTengoActivo = params.get("lo_que_tengo") === "1";

    // Compatibilidad con enlaces o entradas antiguas del historial.
    if (tipopag === "LoQueTengo") {
      tipopag = "Todos";
      loQueTengoActivo = true;
    }

    // No reactivar desde el historial un filtro sin palabras.
    const linkFiltroLoQueTengo = document.querySelector(
      ".js-filtro-lo-que-tengo"
    );
    if (
      linkFiltroLoQueTengo &&
      linkFiltroLoQueTengo.dataset.tienePalabrasLoQueTengo !== "1"
    ) {
      loQueTengoActivo = false;
    }

    const inputTipopag = form.querySelector('input[name="tipopag"]');
    const inputLoQueTengo = form.querySelector('input[name="lo_que_tengo_activo"]');

    if (!inputTipopag || !inputLoQueTengo) {
      return;
    }

    inputTipopag.value = tipopag;
    inputLoQueTengo.value = loQueTengoActivo ? "1" : "0";

    const vcUrl = params.get("ver_cotidiano");
    const veUrl = params.get("ver_especial");
    const cbCatPop = form.querySelector('input[name="ver_cotidiano"]');
    const cbEspPop = form.querySelector('input[name="ver_especial"]');
    if (cbCatPop) cbCatPop.checked = vcUrl === null ? true : vcUrl !== "0";
    if (cbEspPop) cbEspPop.checked = veUrl === null ? true : veUrl !== "0";

    actualizarSelectorHorizontalActivo(tipopag);
    actualizarTituloSugerencias(tipopag);
    actualizarBotonCrearPlato(tipopag);
    actualizarListadoPlatosConBarrido();
  });

  const tipopagInicial = (
    form.querySelector('input[name="tipopag"]')?.value || "Principal"
  );
  actualizarSelectorHorizontalActivo(tipopagInicial);

});
