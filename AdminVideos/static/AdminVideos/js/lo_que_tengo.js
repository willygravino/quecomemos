(function () {
  function getCookie(nombre) {
    const cookies = document.cookie ? document.cookie.split(";") : [];

    for (const cookie of cookies) {
      const cookieLimpia = cookie.trim();

      if (cookieLimpia.startsWith(nombre + "=")) {
        return decodeURIComponent(cookieLimpia.slice(nombre.length + 1));
      }
    }

    return "";
  }

  function getCSRFToken() {
    return getCookie("csrftoken");
  }

  function getModal() {
    return document.getElementById("loQueTengoModal");
  }

  function getConfig() {
    const modal = getModal();

    if (!modal) {
      return null;
    }

    return {
      modal,
      palabrasUrl: modal.dataset.palabrasUrl,
      agregarUrl: modal.dataset.agregarUrl,
      sugerenciasUrl: modal.dataset.sugerenciasUrl || "/api/ingredientes/",
    };
  }

  function actualizarDisponibilidadFiltro(palabras, confirmado) {
    const linkFiltro = document.querySelector(".js-filtro-lo-que-tengo");

    if (!linkFiltro) {
      return;
    }

    const cantidad = Array.isArray(palabras) ? palabras.length : 0;
    const disponible = confirmado && cantidad > 0;

    if (!linkFiltro.dataset.tituloDisponibleLoQueTengo) {
      linkFiltro.dataset.tituloDisponibleLoQueTengo =
        linkFiltro.getAttribute("title") || "Activar Con lo que tengo";
    }

    linkFiltro.dataset.tienePalabrasLoQueTengo = confirmado
      ? (disponible ? "1" : "0")
      : "cargando";
    linkFiltro.classList.toggle("disabled", !disponible);
    linkFiltro.setAttribute("aria-disabled", disponible ? "false" : "true");
    linkFiltro.tabIndex = disponible ? 0 : -1;

    if (disponible) {
      linkFiltro.style.removeProperty("opacity");
      linkFiltro.style.removeProperty("cursor");
      linkFiltro.setAttribute(
        "title",
        linkFiltro.dataset.tituloDisponibleLoQueTengo
      );
    } else {
      linkFiltro.style.setProperty("opacity", "0.45");
      linkFiltro.style.setProperty("cursor", "not-allowed");
      linkFiltro.setAttribute(
        "title",
        confirmado
          ? "Agregá al menos una palabra con el lápiz para activar este filtro"
          : "Comprobando palabras de Lo que tengo"
      );
    }

    if (confirmado) {
      window.dispatchEvent(new CustomEvent("loQueTengo:disponibilidad", {
        detail: {
          disponible,
          cantidad,
        },
      }));
    }
  }

  function renderPalabras(palabras) {
    actualizarDisponibilidadFiltro(palabras, true);

    const lista = document.getElementById("loQueTengoLista");

    if (!lista) {
      return;
    }

    if (!palabras || !palabras.length) {
      lista.innerHTML = `
        <li class="list-group-item text-muted small">
          Todavía no agregaste palabras.
        </li>
      `;
      return;
    }

    lista.innerHTML = palabras.map(function (item) {
      return `
        <li class="list-group-item d-flex justify-content-between align-items-center">
          <span>${escapeHtml(item.palabra)}</span>

          <button
            type="button"
            class="btn btn-sm btn-outline-danger js-lo-que-tengo-eliminar"
            data-id="${item.id}">
            X
          </button>
        </li>
      `;
    }).join("");
  }

  function escapeHtml(value) {
    return String(value || "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  async function cargarPalabras() {
    const config = getConfig();

    if (!config || !config.palabrasUrl || !window.fetch) {
      return;
    }

    const response = await fetch(config.palabrasUrl, {
      method: "GET",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
      },
      credentials: "same-origin",
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error("No se pudieron cargar las palabras de Lo que tengo.");
    }

    const data = await response.json();

    if (!data.ok) {
      throw new Error("Respuesta inválida al cargar Lo que tengo.");
    }

    renderPalabras(data.palabras);
  }

  function inicializarSelect2() {
    const config = getConfig();
    const select = document.getElementById("loQueTengoSelect");

    if (!config || !select || !window.jQuery || !jQuery.fn.select2) {
      return;
    }

    const $select = jQuery(select);

    if ($select.data("select2")) {
      return;
    }

    $select.select2({
      placeholder: "Ej: tomate, arroz, pollo",
      dropdownParent: jQuery(config.modal),
      width: "100%",
      tags: true,
      allowClear: true,
      minimumInputLength: 0,
      ajax: {
        url: config.sugerenciasUrl,
        dataType: "json",
        delay: 250,
        data: function (params) {
          return {
            q: params.term || "",
          };
        },
        processResults: function (data) {
          if (data && Array.isArray(data.results)) {
            return {
              results: data.results,
            };
          }

          return {
            results: [],
          };
        },
        cache: true,
      },
      createTag: function (params) {
        const term = (params.term || "").trim();

        if (!term) {
          return null;
        }

        return {
          id: term,
          text: term,
          newTag: true,
        };
      },
    });
  }

  function obtenerPalabraSeleccionada() {
    const select = document.getElementById("loQueTengoSelect");

    if (!select || !window.jQuery || !jQuery.fn.select2) {
      return "";
    }

    const data = jQuery(select).select2("data")[0] || null;

    if (!data) {
      return "";
    }

    return String(data.text || data.id || "").trim();
  }

  function limpiarSeleccion() {
    const select = document.getElementById("loQueTengoSelect");

    if (select && window.jQuery && jQuery.fn.select2) {
      jQuery(select).val(null).trigger("change");
    }
  }

  async function agregarPalabra() {
    const config = getConfig();
    const errorBox = document.getElementById("loQueTengoError");

    if (errorBox) {
      errorBox.classList.add("d-none");
      errorBox.textContent = "";
    }

    if (!config || !config.agregarUrl) {
      return;
    }

    const palabra = obtenerPalabraSeleccionada();

    if (!palabra) {
      if (errorBox) {
        errorBox.textContent = "Elegí o escribí una palabra.";
        errorBox.classList.remove("d-none");
      }
      return;
    }

    const formData = new FormData();
    formData.append("palabra", palabra);

    const response = await fetch(config.agregarUrl, {
      method: "POST",
      body: formData,
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": getCSRFToken(),
      },
      credentials: "same-origin",
    });

    const data = await response.json();

    if (!response.ok || !data.ok) {
      if (errorBox) {
        errorBox.textContent = data.error || "No se pudo agregar la palabra.";
        errorBox.classList.remove("d-none");
      }
      return;
    }

    limpiarSeleccion();
    renderPalabras(data.palabras);
  }

  async function eliminarPalabra(id) {
    if (!id) {
      return;
    }

    const response = await fetch(`/ajax/lo-que-tengo/${id}/eliminar/`, {
      method: "POST",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": getCSRFToken(),
      },
      credentials: "same-origin",
    });

    const data = await response.json();

    if (!response.ok || !data.ok) {
      throw new Error("No se pudo eliminar la palabra.");
    }

    renderPalabras(data.palabras);
  }

  document.addEventListener("DOMContentLoaded", function () {
    actualizarDisponibilidadFiltro([], false);

    const modal = getModal();

    if (!modal) {
      return;
    }

    modal.addEventListener("shown.bs.modal", function () {
      inicializarSelect2();

      cargarPalabras().catch(function (error) {
        console.error(error);
      });
    });

    cargarPalabras().catch(function (error) {
      console.error(error);
    });

    document.addEventListener("click", function (event) {
      const agregarBtn = event.target.closest("#loQueTengoAgregarBtn");

      if (agregarBtn) {
        event.preventDefault();

        agregarPalabra().catch(function (error) {
          console.error(error);
        });

        return;
      }

      const eliminarBtn = event.target.closest(".js-lo-que-tengo-eliminar");

      if (eliminarBtn) {
        event.preventDefault();

        eliminarPalabra(eliminarBtn.dataset.id).catch(function (error) {
          console.error(error);
        });
      }
    });

});
})();
