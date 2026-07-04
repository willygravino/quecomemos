
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
    if (tipopag === "Guarnicion") {
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
    actualizarListadoPlatos();
  });

  // ============================================================
  // 4.b Buscar por palabra clave mientras se escribe
  // ============================================================
  const inputPalabraClave = form.querySelector('input[name="palabra_clave"]');
  let timeoutBusquedaPalabraClave = null;

  if (inputPalabraClave) {
    inputPalabraClave.addEventListener("input", function () {
      clearTimeout(timeoutBusquedaPalabraClave);

      timeoutBusquedaPalabraClave = setTimeout(function () {
        actualizarListadoPlatos();
      }, 400);
    });
  }

  // ============================================================
  // 5. Filtrar por checkboxes sin recargar
  // ============================================================
  form.querySelectorAll("input[type='checkbox']").forEach(function (checkbox) {
    checkbox.addEventListener("change", function () {
      actualizarListadoPlatos();
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

    const nuevaUrl = new URL(link.href);
    window.history.pushState({ tipopag: tipopag }, "", nuevaUrl.toString());

    actualizarBotonCrearPlato(tipopag);

    const dropdown = link.closest(".dropdown");
    const dropdownToggle = dropdown ? dropdown.querySelector('[data-bs-toggle="dropdown"]') : null;

    if (dropdownToggle && window.bootstrap && bootstrap.Dropdown) {
      bootstrap.Dropdown.getOrCreateInstance(dropdownToggle).hide();
    }

    actualizarListadoPlatos();  
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
    actualizarBotonCrearPlato(tipopag);
    actualizarListadoPlatos();

  });
});