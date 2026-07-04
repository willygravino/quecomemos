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

  function actualizarContador(palabras) {
    const contador = document.getElementById("loQueTengoContador");
    const cantidad = Array.isArray(palabras) ? palabras.length : 0;

    if (contador) {
      contador.textContent = cantidad ? `(${cantidad})` : "";
    }
  }

  function renderPalabras(palabras) {
    const lista = document.getElementById("loQueTengoLista");

    if (!lista) {
      return;
    }

    actualizarContador(palabras);

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
  
  const filtroBox = document.getElementById("loQueTengoFiltroBox");
  const usarLoQueTengoCheckbox = document.getElementById("usarLoQueTengo");

  function actualizarEstadoFiltroBox() {
    if (!filtroBox || !usarLoQueTengoCheckbox) {
      return;
    }

    filtroBox.classList.toggle("is-active", usarLoQueTengoCheckbox.checked);
  }

  if (usarLoQueTengoCheckbox) {
    usarLoQueTengoCheckbox.addEventListener("change", actualizarEstadoFiltroBox);
    actualizarEstadoFiltroBox();
  }

});
})();
