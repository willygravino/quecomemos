document.addEventListener("DOMContentLoaded", function () {
  // ============================================================
  // 1. Elementos base de la pantalla
  // ============================================================
  const form = document.getElementById("form-filtros-platos");
  const contenedor = document.getElementById("contenedor-listado-platos");

  if (!form || !contenedor) return;

  // ============================================================
  // 2. Refrescar listado, carousel y lugares por AJAX
  // ============================================================
  function actualizarListadoPlatos() {
    const url = form.dataset.listadoUrl;
    const formData = new FormData(form);

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
  function actualizarMenuLateralActivo(tipopag) {
    document.querySelectorAll(".js-filtro-tipopag").forEach(function (link) {
      const activo = link.dataset.tipopag === tipopag;

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
    });
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
    actualizarMenuLateralActivo(tipopag);

    const nuevaUrl = new URL(link.href);
    window.history.pushState({ tipopag: tipopag }, "", nuevaUrl.toString());

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
    actualizarListadoPlatos();
  });
});