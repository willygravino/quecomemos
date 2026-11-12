
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
  // §45: helper dinámico. El form se resuelve en cada uso, así sobrevive
  // si el DOM lo reemplaza (bug confirmado: tras asignar un plato, el form
  // del closure quedaba stale y todos los handlers escribían en el viejo).
  function getForm() {
    return document.getElementById("form-filtros-platos");
  }

  // Referencia mutable por compatibilidad con handlers existentes.
  // Se mantiene actualizada por MutationObserver al final del IIFE.
  let form = getForm();

  const contenedor = document.getElementById("contenedor-listado-platos");

  if (!form || !contenedor) return;

  // Un único canal de render para listado + carousel + lugares.
  // Si cambia el filtro mientras hay un request en vuelo, sólo el último
  // puede pintar la pantalla.
  let listadoAbortController = null;
  let listadoRequestSeq = 0;

  // Sincronizar el botón de creación con la vista inicial.
  actualizarBotonCrearPlato(
    form.querySelector('input[name="tipopag"]')?.value || "Principal"
  );

  // Impedir crear platos desde la vista Todos.
  document.addEventListener("click", function (event) {
    const botonCrear = event.target.closest("#botonCrearPlatoFlotante");
    if (!botonCrear) return;

    const form = getForm();
    if (!form) return;
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
    const form = getForm();
    if (!form) return Promise.resolve();
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

    // IMPORTANTE: devolver la Promise. El spinner de carga necesita saber cuándo termina.
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
    const form = getForm();
    if (!form) return false;
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
    const form = getForm();
    if (!form) return;
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
    actualizarListadoPlatosConSpinner();
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

    const activo = Array.from(document.querySelectorAll(".js-filtro-tipopag")).find(
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
  // 3.a.1 Spinner de carga al cambiar el filtro por AJAX
  // ============================================================
  function mostrarSpinnerCarga() {
    document.body.classList.add("filtro-platos-cambiando");
    let back = document.getElementById("filtrosLoadingBackdrop");
    if (!back) {
      back = document.createElement("div");
      back.id = "filtrosLoadingBackdrop";
      back.className = "filtros-loading-backdrop";
      back.setAttribute("aria-hidden", "true");
      back.innerHTML = '<span class="spinner-border text-primary" role="status" aria-label="Cargando"></span>';
      document.body.appendChild(back);
    }
  }

  function ocultarSpinnerCarga() {
    document.body.classList.remove("filtro-platos-cambiando");
    const back = document.getElementById("filtrosLoadingBackdrop");
    if (back) back.remove();
  }

  function actualizarListadoPlatosConSpinner() {
    mostrarSpinnerCarga();

    let resultado = null;
    try {
      resultado = actualizarListadoPlatos();
    } catch (error) {
      ocultarSpinnerCarga();
      throw error;
    }

    const esperaAjax = resultado && typeof resultado.finally === "function"
      ? resultado
      : Promise.resolve();

    Promise.resolve(esperaAjax).then(function () {
      ocultarSpinnerCarga();
    }).catch(function () {
      ocultarSpinnerCarga();
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
      titulo = "Agregar receta de picada armada";
    } else if (tipopag === "Ingrediente de picada") {
      titulo = "Agregar receta de ingrediente de picada";
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
      textoBoton.textContent = titulo;
    }

    // El label mobile tambien tiene que reflejar el tipo actual.
    const textoBotonMobile = boton.querySelector(".qc-mobile-action-label");
    if (textoBotonMobile) {
      textoBotonMobile.textContent = titulo;
    }
  }

  // ============================================================
  // 4. Buscar por palabra clave sin recargar
  // ============================================================
  // §45: submit delegado en document (sobrevive al reemplazo del form).
  document.addEventListener("submit", function (event) {
    if (event.target !== getForm()) return;
    event.preventDefault();
    actualizarListadoPlatosConSpinner();
  });

  // ============================================================
  // 4.b Buscar por palabra clave mientras se escribe
  // ============================================================
  let timeoutBusquedaPalabraClave = null;

  function actualizarVisualPalabraClave(inputKwParam) {
    let inp = inputKwParam;
    if (!inp) {
      const _f = getForm();
      inp = _f ? _f.querySelector('input[name="palabra_clave"]') : null;
    }
    if (!inp) return;

    const grupo = inp.closest(".filtro-keyword-box");
    const activo = inp.value.trim().length > 0;

    if (grupo) {
      grupo.classList.toggle("filtro-keyword-activo", activo);
    }

    inp.classList.toggle("text-danger", activo);
    inp.classList.toggle("fw-semibold", activo);
  }

  // §45: input delegado en document. Resuelve el input dinámicamente cada vez.
  document.addEventListener("input", function (event) {
    if (!event.target.matches('#form-filtros-platos input[name="palabra_clave"]')) return;

    const inputKw = event.target;
    actualizarVisualPalabraClave(inputKw);
    clearTimeout(timeoutBusquedaPalabraClave);

    timeoutBusquedaPalabraClave = setTimeout(function () {
      actualizarListadoPlatosConSpinner();

      // Persistir palabra_clave en URL (replaceState: no llena historial)
      const urlKw = new URL(window.location.href);
      const kw = (inputKw.value || "").trim();
      if (kw) urlKw.searchParams.set("palabra_clave", kw);
      else urlKw.searchParams.delete("palabra_clave");
      window.history.replaceState(window.history.state || {}, "", urlKw.toString());
    }, 400);
  });

  // Inicializar visual al cargar (si el input existe)
  (function _initVisualKw() {
    var _f = getForm();
    var _inp = _f ? _f.querySelector('input[name="palabra_clave"]') : null;
    if (_inp) actualizarVisualPalabraClave(_inp);
  })();

  // ============================================================
  // 5. Filtrar por checkboxes sin recargar
  // ============================================================
  // §45: change delegado en document. Resuelve el form dinámicamente.
  document.addEventListener("change", function (event) {
    const cb = event.target;
    if (!cb.matches || !cb.matches('#form-filtros-platos input[type="checkbox"]')) return;

    const _f = getForm();
    if (!_f) return;

    actualizarListadoPlatosConSpinner();

    // Persistir todos los filtros en URL (pushState)
    const urlCb = new URL(window.location.href);
    const fdCb = new FormData(_f);
    const kwCb = fdCb.get("palabra_clave") || "";
    if (kwCb) urlCb.searchParams.set("palabra_clave", kwCb);
    else urlCb.searchParams.delete("palabra_clave");
    if (fdCb.get("quecomemos")) urlCb.searchParams.set("quecomemos", "quecomemos");
    else urlCb.searchParams.delete("quecomemos");
    if (fdCb.get("misplatos")) urlCb.searchParams.set("misplatos", "misplatos");
    else urlCb.searchParams.delete("misplatos");
    urlCb.searchParams.set("ver_cotidiano", fdCb.get("ver_cotidiano") ? "1" : "0");
    urlCb.searchParams.set("ver_especial", fdCb.get("ver_especial") ? "1" : "0");
    window.history.pushState(window.history.state || {}, "", urlCb.toString());
  });

  // 5.a Toggle cruzado: al apagar uno de los dos checkboxes de categoría,
  // se enciende el otro automáticamente. Se permite tener ambos ON (ver todo)
  // o uno solo, pero nunca ambos OFF (lista vacía).
  // Se corre en fase capture para que el toggle ocurra ANTES de que el
  // listener genérico lea el estado del form y dispare el fetch.
  // §45: toggle cruzado delegado en document con capture, para que corra
  // antes del listener change genérico que dispara el fetch.
  document.addEventListener("change", function (event) {
    const cb = event.target;
    if (!cb.matches || !cb.matches('#form-filtros-platos input[name="ver_cotidiano"], #form-filtros-platos input[name="ver_especial"]')) return;
    if (cb.checked) return;

    const _f = getForm();
    if (!_f) return;

    _f.querySelectorAll('input[name="ver_cotidiano"], input[name="ver_especial"]').forEach(function (otro) {
      if (otro !== cb) otro.checked = true;
    });
  }, true);

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

    const form = getForm();
    if (!form) return;

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

    // Persistir tambien palabra_clave / quecomemos / misplatos
    const fdLqt = new FormData(form);
    const kwLqt = fdLqt.get("palabra_clave") || "";
    if (kwLqt) nuevaUrl.searchParams.set("palabra_clave", kwLqt);
    else nuevaUrl.searchParams.delete("palabra_clave");
    if (fdLqt.get("quecomemos")) nuevaUrl.searchParams.set("quecomemos", "quecomemos");
    else nuevaUrl.searchParams.delete("quecomemos");
    if (fdLqt.get("misplatos")) nuevaUrl.searchParams.set("misplatos", "misplatos");
    else nuevaUrl.searchParams.delete("misplatos");

    window.history.pushState(
      { tipopag: tipopag, loQueTengoActivo: activar },
      "",
      nuevaUrl.toString()
    );

    actualizarBotonCrearPlato(tipopag);
    actualizarListadoPlatosConSpinner();
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

    // §45c: resolver form dinámicamente (fix stale form post-asignar plato)
    const form = getForm();
    if (!form) return;

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

    // Persistir tambien palabra_clave / quecomemos / misplatos
    const fdTyp = new FormData(form);
    const kwTyp = fdTyp.get("palabra_clave") || "";
    if (kwTyp) nuevaUrl.searchParams.set("palabra_clave", kwTyp);
    else nuevaUrl.searchParams.delete("palabra_clave");
    if (fdTyp.get("quecomemos")) nuevaUrl.searchParams.set("quecomemos", "quecomemos");
    else nuevaUrl.searchParams.delete("quecomemos");
    if (fdTyp.get("misplatos")) nuevaUrl.searchParams.set("misplatos", "misplatos");
    else nuevaUrl.searchParams.delete("misplatos");

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

    actualizarListadoPlatosConSpinner();
  });

  // 7. Soportar botón atrás / adelante del navegador
  // ============================================================
  window.addEventListener("popstate", function () {
    const form = getForm();
    if (!form) return;
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

    // Restaurar palabra_clave
    const palabraPop = params.get("palabra_clave") || "";
    if (inputPalabraClave && inputPalabraClave.value !== palabraPop) {
      inputPalabraClave.value = palabraPop;
      actualizarVisualPalabraClave();
    }

    // Restaurar quecomemos / misplatos
    const cbQuePop = form.querySelector('input[name="quecomemos"]');
    const cbMisPop = form.querySelector('input[name="misplatos"]');
    if (cbQuePop) cbQuePop.checked = params.get("quecomemos") === "quecomemos";
    if (cbMisPop) cbMisPop.checked = params.get("misplatos") === "misplatos";

    actualizarSelectorHorizontalActivo(tipopag);
    actualizarTituloSugerencias(tipopag);
    actualizarBotonCrearPlato(tipopag);
    actualizarListadoPlatosConSpinner();
  });

  const _formInicial = getForm();
  const tipopagInicial = (
    _formInicial?.querySelector('input[name="tipopag"]')?.value || "Principal"
  );
  actualizarSelectorHorizontalActivo(tipopagInicial);

  // §45: MutationObserver mantiene 'form' actualizado cuando el DOM lo
  // reemplaza (ej. tras asignar un plato). Con debounce vía requestAnimationFrame.
  let _formRefreshScheduled = false;
  if (typeof MutationObserver !== "undefined") {
    const _obs = new MutationObserver(function () {
      if (_formRefreshScheduled) return;
      _formRefreshScheduled = true;
      window.requestAnimationFrame(function () {
        _formRefreshScheduled = false;
        const nuevoForm = getForm();
        if (nuevoForm && nuevoForm !== form) {
          form = nuevoForm;
          // Resincronizar visuales que dependen del form
          try { actualizarVisualPalabraClave(); } catch (e) {}
        }
      });
    });
    _obs.observe(document.body, { childList: true, subtree: true });
  }

});

// ============================================================
// BOTÓN X PARA LIMPIAR LA BÚSQUEDA (2026-11-02)
// - Aparece solo cuando el input de palabra clave tiene texto.
// - Click limpia el input y dispara el filtro automáticamente.
// - Funciona en mobile (donde el navegador no muestra el X nativo).
// ============================================================
(function () {
  function initClearSearch() {
    const form = document.getElementById("form-filtros-platos");
    if (!form) return;

    const input = form.querySelector('input[name="palabra_clave"]');
    const btn = form.querySelector(".btn-clear-search");
    if (!input || !btn || btn.__clearBound) return;

    function updateVisibility() {
      const hasValue = (input.value || "").trim().length > 0;
      btn.classList.toggle("is-visible", hasValue);
    }

    input.addEventListener("input", updateVisibility);

    btn.addEventListener("click", function (e) {
      e.preventDefault();
      input.value = "";
      input.dispatchEvent(new Event("input", { bubbles: true }));
      updateVisibility();
      input.focus();
    });

    updateVisibility();
    btn.__clearBound = true;
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initClearSearch);
  } else {
    initClearSearch();
  }
})();

