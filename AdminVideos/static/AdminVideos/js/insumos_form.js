(function () {
  "use strict";

  if (window.__INSUMOS_FORM_STANDALONE_LOADED__) return;
  window.__INSUMOS_FORM_STANDALONE_LOADED__ = true;

  function getCookie(name) {
    const cookies = document.cookie ? document.cookie.split(";") : [];

    for (const raw of cookies) {
      const cookie = raw.trim();

      if (cookie.startsWith(name + "=")) {
        return decodeURIComponent(cookie.substring(name.length + 1));
      }
    }

    return "";
  }

  function getSelectFormulario() {
    return document.getElementById("id_insumos");
  }

  function getErrorBox() {
    return document.getElementById("nuevo-insumo-error");
  }

  function mostrarError(mensaje) {
    const box = getErrorBox();

    if (box) {
      box.textContent = mensaje;
      box.classList.remove("d-none");
    }

    console.warn("[Insumos]", mensaje);
  }

  function limpiarError() {
    const box = getErrorBox();

    if (box) {
      box.textContent = "";
      box.classList.add("d-none");
    }
  }

  function refrescarEstadoVacio() {
    const select = getSelectFormulario();
    const empty = document.getElementById("insumos-empty");

    if (!select || !empty) return;

    const cantidad = Array.from(select.options).filter(
      (option) => option.selected
    ).length;

    const lista = document.getElementById("insumos-ul");
    const hayInsumos = cantidad > 0;

    if (lista) lista.classList.toggle("d-none", !hayInsumos);
    empty.classList.toggle("d-none", hayInsumos);
  }

  function agregarALista(insumo) {
    const select = getSelectFormulario();
    const lista = document.getElementById("insumos-ul");

    if (!select || !lista) {
      throw new Error("No se encontró la lista de insumos del formulario.");
    }

    const id = String(insumo.id || "");
    const nombre = String(insumo.text || insumo.nombre || "").trim();

    if (!id || !nombre) {
      throw new Error("El insumo recibido no tiene ID o nombre.");
    }

    let option = Array.from(select.options).find(
      (op) => String(op.value) === id
    );

    if (!option) {
      option = new Option(nombre, id, true, true);
      select.appendChild(option);
    }

    option.selected = true;

    let fila = lista.querySelector(
      '[data-insumo-row][data-insumo-id="' +
      CSS.escape(id) +
      '"]'
    );

    if (!fila) {
      fila = document.createElement("li");
      fila.className = "list-group-item ingrediente-compact-item";
      fila.setAttribute("data-insumo-row", "");
      fila.dataset.insumoId = id;

      const summary = document.createElement("div");
      summary.className =
        "d-flex align-items-center gap-1 ingrediente-compact-summary";

      const textoBtn = document.createElement("button");
      textoBtn.type = "button";
      textoBtn.className =
        "btn btn-link btn-sm p-0 text-start ingrediente-summary-btn";
      textoBtn.tabIndex = -1;
      textoBtn.setAttribute("aria-label", nombre);

      const texto = document.createElement("span");
      texto.className = "fw-semibold ingrediente-summary-nombre";
      texto.textContent = nombre;

      const quitar = document.createElement("button");
      quitar.type = "button";
      quitar.className =
        "btn btn-sm btn-outline-danger py-0 px-2 eliminar-insumo";
      quitar.title = "Quitar insumo";
      quitar.setAttribute("aria-label", "Quitar " + nombre);
      quitar.textContent = "×";

      textoBtn.appendChild(texto);
      summary.appendChild(textoBtn);
      summary.appendChild(quitar);
      fila.appendChild(summary);
      lista.appendChild(fila);
    }

    refrescarEstadoVacio();
  }

  function quitarDeLista(btn) {
    const fila = btn.closest("[data-insumo-row]");
    if (!fila) return;

    const id = String(fila.dataset.insumoId || "");
    const select = getSelectFormulario();

    if (select && id) {
      const option = Array.from(select.options).find(
        (op) => String(op.value) === id
      );

      if (option) option.remove();
    }

    fila.remove();
    refrescarEstadoVacio();
  }

  function limpiarModal() {
    const nuevo = document.getElementById("nuevo-insumo-nombre");

    if (nuevo) nuevo.value = "";

    limpiarError();

    if (window.jQuery) {
      const $select = window.jQuery("#modal-insumo");

      if ($select.length && $select.data("select2")) {
        $select.val(null).trigger("change");
      }
    }
  }

  function inicializarSelectorModal(modalEl) {
    if (!window.jQuery || !window.jQuery.fn.select2) {
      mostrarError("Select2 no está disponible.");
      return;
    }

    const $ = window.jQuery;
    const $select = $("#modal-insumo");

    if (!$select.length) {
      mostrarError("No se encontró el selector de insumos existentes.");
      return;
    }

    if (!$select.data("select2")) {
      $select.select2({
        dropdownParent: $(modalEl),
        placeholder: "Seleccioná un insumo",
        minimumInputLength: 0,
        allowClear: true,
        width: "100%",
        ajax: {
          url: "/api/insumos/",
          dataType: "json",
          delay: 250,
          data: function (params) {
            return { q: params.term || "" };
          },
          processResults: function (data) {
            return {
              results:
                data && Array.isArray(data.results)
                  ? data.results
                  : []
            };
          },
          cache: true
        }
      });
    }
  }

  async function resolverInsumo() {
    const nuevo = (
      document.getElementById("nuevo-insumo-nombre")?.value || ""
    ).trim();

    if (nuevo) {
      const response = await fetch("/api/insumos/", {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken")
        },
        body: JSON.stringify({ nombre: nuevo })
      });

      let data = {};

      try {
        data = await response.json();
      } catch (_) {
        throw new Error(
          "La API de insumos devolvió una respuesta inválida."
        );
      }

      if (!response.ok) {
        const mensaje =
          data?.errors?.nombre?.[0] ||
          data?.error ||
          "No se pudo crear el insumo.";

        throw new Error(mensaje);
      }

      return {
        id: data.id,
        text: data.nombre
      };
    }

    if (!window.jQuery) {
      throw new Error("jQuery no está disponible.");
    }

    const $select = window.jQuery("#modal-insumo");

    if (!$select.length || !$select.data("select2")) {
      throw new Error("El selector de insumos no está inicializado.");
    }

    const elegido = $select.select2("data")[0] || {};

    if (!elegido.id) {
      throw new Error(
        "Seleccioná un insumo existente o escribí uno nuevo."
      );
    }

    return {
      id: elegido.id,
      text: elegido.text
    };
  }

  // Se ejecuta aunque el formulario se cargue luego por AJAX.
  document.addEventListener(
    "click",
    async function (event) {
      const target =
        event.target instanceof Element ? event.target : null;

      if (!target) return;

      const quitar = target.closest(".eliminar-insumo");

      if (quitar) {
        event.preventDefault();
        event.stopImmediatePropagation();
        quitarDeLista(quitar);
        return;
      }

      const guardar = target.closest("#guardarInsumo");

      if (!guardar) return;

      // Capturamos antes de handlers antiguos de form_init.js.
      event.preventDefault();
      event.stopImmediatePropagation();

      if (guardar.dataset.guardando === "1") return;

      guardar.dataset.guardando = "1";
      guardar.disabled = true;

      const textoOriginal = guardar.textContent;
      guardar.textContent = "Guardando…";
      limpiarError();

      try {
        const insumo = await resolverInsumo();

        agregarALista(insumo);
        limpiarModal();

        const modalEl = document.getElementById("insumoModal");

        if (modalEl && window.bootstrap?.Modal) {
          window.bootstrap.Modal
            .getOrCreateInstance(modalEl)
            .hide();
        }
      } catch (error) {
        mostrarError(
          error?.message || "No se pudo agregar el insumo."
        );
      } finally {
        guardar.dataset.guardando = "0";
        guardar.disabled = false;
        guardar.textContent = textoOriginal;
      }
    },
    true
  );

  document.addEventListener(
    "shown.bs.modal",
    function (event) {
      if (event.target?.id !== "insumoModal") return;

      limpiarModal();
      inicializarSelectorModal(event.target);

      if (window.jQuery) {
        const $select = window.jQuery("#modal-insumo");

        if ($select.length && $select.data("select2")) {
          $select.select2("open");
        }
      }
    },
    true
  );

  document.addEventListener(
    "input",
    function (event) {
      const target =
        event.target instanceof Element ? event.target : null;

      const input = target?.closest("#nuevo-insumo-nombre");

      if (!input || !input.value.trim()) return;

      limpiarError();

      if (window.jQuery) {
        const $select = window.jQuery("#modal-insumo");

        if ($select.length && $select.data("select2")) {
          $select.val(null).trigger("change");
        }
      }
    },
    true
  );

  if (window.jQuery) {
    window.jQuery(document).on(
      "select2:select.insumosStandalone",
      "#modal-insumo",
      function () {
        const nuevo =
          document.getElementById("nuevo-insumo-nombre");

        if (nuevo) nuevo.value = "";

        limpiarError();
      }
    );
  }

  // Refrescar estado inicial si el formulario ya existe.
  refrescarEstadoVacio();
})();
