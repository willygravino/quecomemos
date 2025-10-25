/* static/js/form_init.js */
/* global bootstrap, $ */

(function () {
  "use strict";

  // Evita redefinir si el archivo se carga más de una vez
  if (window.__PLATO_FORM_INIT_LOADED__) return;
  window.__PLATO_FORM_INIT_LOADED__ = true;

  // ===== Utils =====
  function log() {
    if (window && window.console && console.log) {
      console.log.apply(console, arguments);
    }
  }

  function getCookie(name) {
    const cookies = document.cookie ? document.cookie.split(";") : [];
    for (let i = 0; i < cookies.length; i++) {
      const c = cookies[i].trim();
      if (c.startsWith(name + "=")) {
        return decodeURIComponent(c.substring(name.length + 1));
      }
    }
    return null;
  }

  const CSRF_TOKEN = getCookie("csrftoken");

  // ===== Select2 helpers =====
  function buildSelect2Config(dropdownParent /* jQuery or null */) {
    const cfg = {
      placeholder: "Selecciona un ingrediente",
      ajax: {
        url: "/api/ingredientes/",
        dataType: "json",
        delay: 250,
        data: (params) => ({ q: params.term || "" }),
        processResults: (data) => ({
          results: (data || []).map((item) => ({ id: item.id, text: item.nombre })),
        }),
        cache: true,
      },
      minimumInputLength: 0,
      allowClear: true,
      width: "style",
    };
    if (dropdownParent) cfg.dropdownParent = dropdownParent;
    return cfg;
  }

  // Inicializa un <select.ingrediente-select> dentro de un <li>
  // y sincroniza su valor con los inputs hidden (...-ingrediente y ...-nombre_ingrediente)
  function initIngredienteSelect(selectEl) {
    if (!selectEl) return;
    const $select = $(selectEl);

    // Idempotencia: si ya tiene Select2, no reiniciar
    if ($select.data("select2")) return;

    // Pre-cargar valor inicial si viene de la base
    const initId = $select.data("initial-id");
    const initText = $select.data("initial-text");
    if (initId && initText) {
      const option = new Option(initText, initId, true, true);
      $select.append(option).trigger("change");
    }

    // Inicializar Select2 (lista del form, fuera del modal => sin dropdownParent)
    $select.select2(buildSelect2Config(null));

    // Vincular cambios al par de hidden
    $select.on("select2:select select2:clear change", function () {
      const li = selectEl.closest("li");
      if (!li) return;
      const hiddenId = li.querySelector('input[name$="-ingrediente"]');
      const hiddenNombre = li.querySelector('input[name$="-nombre_ingrediente"]');
      const data = $select.select2("data")[0] || null;
      if (hiddenId) hiddenId.value = data ? data.id ?? "" : "";
      if (hiddenNombre) hiddenNombre.value = data ? data.text ?? "" : "";
    });
  }

  // ===== Subcategorías por tipo =====
  const DETALLE_OPCIONES = {
    verduleria: [
      ["verdura", "Verdura"],
      ["fruta", "Fruta"],
      ["tuberculo", "Tubérculo"],
      ["hierba_fresca", "Hierba fresca"],
    ],
    carniceria: [
      ["carne_roja", "Carne roja"],
      ["ave", "Ave"],
      ["cerdo", "Cerdo"],
      ["cordero", "Cordero"],
      ["achuras", "Achuras"],
    ],
    pescaderia: [
      ["pescado", "Pescado"],
      ["marisco", "Marisco"],
    ],
    panaderia: [["pan", "Pan"]],
    almacen: [
      ["legumbre", "Legumbre"],
      ["cereal", "Cereal"],
      ["harina_blanca", "Harina Blanca"],
      ["aceite", "Aceite"],
      ["conserva", "Conserva"],
      ["azucar", "Azúcar"],
      ["especia", "Especia"],
    ],
    fiambreria: [
      ["fiambre", "Fiambre"],
      ["queso", "Queso"],
      ["embutido", "Embutido"],
    ],
    otro: [["otro", "Otro"]],
    lacteos: [],
    bebidas: [],
  };

  function cargarDetallePorTipo(tipoSelEl, detalleSelEl) {
    if (!tipoSelEl || !detalleSelEl) return;
    const tipo = tipoSelEl.value;
    detalleSelEl.innerHTML = '<option value="">— (opcional)</option>';
    (DETALLE_OPCIONES[tipo] || []).forEach(([val, label]) => {
      const opt = document.createElement("option");
      opt.value = val;
      opt.textContent = label;
      detalleSelEl.appendChild(opt);
    });
  }

  // ===== Crear ingrediente si hace falta (POST a /api/ingredientes/) =====
  async function crearIngredienteSiHaceFalta(context) {
    const nombreNuevo = (context.querySelector("#nuevo-nombre")?.value || "").trim();

    // Si el usuario digitó un nombre, damos de alta el ingrediente:
    if (nombreNuevo !== "") {
      const tipo = context.querySelector("#nuevo-tipo")?.value || "";
      const detalle = context.querySelector("#nuevo-detalle")?.value || "";
      if (!tipo) throw new Error("Elegí el tipo del nuevo ingrediente.");

      const resp = await fetch("/api/ingredientes/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": CSRF_TOKEN || "",
        },
        body: JSON.stringify({ nombre: nombreNuevo, tipo, detalle }),
        credentials: "same-origin",
      });

      if (!resp.ok) {
        const erroresBox = context.querySelector("#nuevo-ingrediente-errores");
        if (erroresBox) {
          erroresBox.innerHTML = "No se pudo crear el ingrediente.";
          erroresBox.classList.remove("d-none");
        }
        throw new Error("Error al crear ingrediente");
      }

      const creado = await resp.json();
      // limpiar campos del nuevo
      const nombreEl = context.querySelector("#nuevo-nombre");
      const tipoEl = context.querySelector("#nuevo-tipo");
      const detalleEl = context.querySelector("#nuevo-detalle");
      if (nombreEl) nombreEl.value = "";
      if (tipoEl) tipoEl.value = "otro";
      if (detalleEl) detalleEl.innerHTML = '<option value="">— (opcional)</option>';

      return { id: creado.id, text: creado.nombre };
    }

    // Si no hay nombre nuevo, usar ingrediente existente del select del modal
    const $sel = $("#modal-nombre");
    const sel = $sel.select2("data")[0] || {};
    if (!sel.id) {
      throw new Error("Seleccioná un ingrediente existente o completá el nombre de uno nuevo.");
    }
    return { id: sel.id, text: sel.text };
  }

  // ===== Eliminar ingrediente (marca DELETE y oculta fila) =====
  function eliminarIngrediente(target) {
    const btn = target?.closest(".eliminar-ingrediente") || target;
    if (!btn) return false;

    const li = btn.closest("li");
    if (!li) return false;

    let del = li.querySelector('input[name$="-DELETE"]');
    if (!del) {
      const anyField = li.querySelector(
        'input[name^="ingredientes_en_plato-"], select[name^="ingredientes_en_plato-"]'
      );
      if (anyField?.name) {
        const base = anyField.name.replace(
          /-(nombre_ingrediente|cantidad|unidad|ingrediente|id)$/,
          ""
        );
        del = document.createElement("input");
        del.type = "checkbox";
        del.name = `${base}-DELETE`;
        del.className = "delete-flag d-none";
        li.appendChild(del);
      }
    }
    if (del) del.checked = true;

    li.querySelectorAll("[required]").forEach((el) => el.removeAttribute("required"));
    li.style.setProperty("display", "none", "important");
    li.setAttribute("aria-hidden", "true");

    return false;
  }

  // ===== Agregar ingrediente (desde el modal al formset) =====
  function agregarIngrediente(context) {
    const totalFormsInput = context.querySelector("#id_ingredientes_en_plato-TOTAL_FORMS");
    const ul = context.querySelector("#ingredientes-ul");
    const proto = context.querySelector("#unidad-prototype");

    if (!totalFormsInput || !ul || !proto) {
      console.error("Falta TOTAL_FORMS, #ingredientes-ul o #unidad-prototype");
      return;
    }

    const prefix = "ingredientes_en_plato";
    const totalForms = parseInt(totalFormsInput.value, 10);

    // Datos desde el modal:
    const sel = $("#modal-nombre").select2("data")[0] || {};
    const idIngrediente = sel?.id || "";
    const nombre = sel?.text || "";
    const cantidad = (context.querySelector("#modal-cantidad")?.value || "").replace(",", ".");
    const unidadElegida = context.querySelector("#modal-unidad")?.value || "";

    // Clonar prototype de unidad con el índice correcto
    let unidadHtml = proto.innerHTML.replace(/__prefix__/g, totalForms);

    // Construir <li>
    const li = document.createElement("li");
    li.className =
      "list-group-item d-flex flex-column flex-sm-row align-items-stretch align-items-sm-center gap-2";
    li.innerHTML = `
      <input type="hidden" name="${prefix}-${totalForms}-ingrediente" value="${idIngrediente}">
      <input type="hidden" name="${prefix}-${totalForms}-nombre_ingrediente" value="${nombre}">

      <select class="form-select form-select-sm ingrediente-select w-100 w-sm-auto flex-fill"
              data-initial-id="${idIngrediente}"
              data-initial-text="${nombre}"></select>

      <input type="text" name="${prefix}-${totalForms}-cantidad"
             value="${cantidad}"
             class="form-control form-control-sm w-100 w-sm-auto"
             placeholder="Cantidad">

      <div class="w-100 w-sm-auto">
        ${unidadHtml}
      </div>

      <input type="checkbox" name="${prefix}-${totalForms}-DELETE" class="d-none delete-flag">

      <button type="button" class="btn btn-sm btn-danger ms-sm-auto eliminar-ingrediente">X</button>
    `;

    ul.appendChild(li);

    // Actualizar TOTAL_FORMS
    totalFormsInput.value = totalForms + 1;

    // Inicializar select de INGREDIENTE
    const newSelectIngrediente = li.querySelector(".ingrediente-select");
    initIngredienteSelect(newSelectIngrediente);

    // Activar el SELECT de UNIDAD clonado y setear valor elegido en el modal
    const unidadSelect = li.querySelector(`select[name="${prefix}-${totalForms}-unidad"]`);
    if (unidadSelect) {
      unidadSelect.disabled = false;
      unidadSelect.value = unidadElegida || "";
    }

    // Limpiar modal
    $("#modal-nombre").val(null).trigger("change");
    const cantEl = context.querySelector("#modal-cantidad");
    const uniEl = context.querySelector("#modal-unidad");
    if (cantEl) cantEl.value = "";
    if (uniEl) uniEl.selectedIndex = 0;

    // Cerrar modal
    const modalEl = context.querySelector("#ingredienteModal");
    const modal = modalEl
      ? bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl)
      : null;
    if (modal) modal.hide();
  }

  // ===== Inicializador principal =====
  // context: `document` (página completa) o un contenedor dentro del modal (e.g., modalBody)
  function initPlatoForm(context) {
    if (!context) context = document;

    // Evita doble init sobre el mismo root
    if (context.__platoFormInitialized) {
      log("ℹ️ initPlatoForm: ya estaba inicializado para este context");
      return;
    }
    context.__platoFormInitialized = true;

    const form = context.querySelector("#platoForm") || context.querySelector("form[method='post']");
    if (!form) {
      log("ℹ️ initPlatoForm: no se encontró el formulario en este context. Nada que hacer.");
      return;
    }

    // ===== Inicializar selects existentes en la lista
    context.querySelectorAll("#ingredientes-ul .ingrediente-select").forEach(initIngredienteSelect);

    // ===== Delegación: eliminar ingrediente
    const ul = context.querySelector("#ingredientes-ul");
    if (ul && !ul.__deleteDelegationBound) {
      ul.addEventListener("click", function (ev) {
        const btn = ev.target.closest(".eliminar-ingrediente");
        if (btn) {
          ev.preventDefault();
          eliminarIngrediente(btn);
        }
      });
      ul.__deleteDelegationBound = true;
    }

    // ===== Subcategorías por tipo (nuevo ingrediente)
    const tipoSel = context.querySelector("#nuevo-tipo");
    const detalleSel = context.querySelector("#nuevo-detalle");
    if (tipoSel && detalleSel) {
      cargarDetallePorTipo(tipoSel, detalleSel);
      tipoSel.addEventListener("change", function () {
        cargarDetallePorTipo(tipoSel, detalleSel);
      });
    }

    // ===== Modal ingredientes → Select2 del modal-nombre
    const ingredienteModal = context.querySelector("#ingredienteModal");
    if (ingredienteModal && !ingredienteModal.__shownHandlerBound) {
      ingredienteModal.addEventListener("shown.bs.modal", function () {
        const $modal = $(ingredienteModal);
        $("#modal-nombre")
          .select2(buildSelect2Config($modal))
          .select2("open");
        // Si querés Select2 para #modal-unidad, podés habilitarlo:
        // $("#modal-unidad").select2({ dropdownParent: $modal, width: "style" });
      });
      ingredienteModal.__shownHandlerBound = true;
    }

    // ===== Botón "Guardar" del modal ingredientes
    const guardarBtn = context.querySelector("#guardarIngrediente");
    if (guardarBtn && !guardarBtn.__bound) {
      guardarBtn.addEventListener("click", async function () {
        try {
          const elegido = await crearIngredienteSiHaceFalta(context);
          const $modalSel = $("#modal-nombre");
          $modalSel.empty();
          const opt = new Option(elegido.text, elegido.id, true, true);
          $modalSel.append(opt).trigger("change");
          agregarIngrediente(context);
        } catch (err) {
          if (err?.message) console.warn(err.message);
        }
      });
      guardarBtn.__bound = true;
    }

    log("✅ initPlatoForm completado para el contexto:", context);
  }

  // Exponer globalmente
  window.initPlatoForm = initPlatoForm;

  // Auto-init en páginas normales (cuando hay formulario ya presente en el DOM)
  document.addEventListener("DOMContentLoaded", function () {
    const formInPage = document.querySelector("#platoForm") || document.querySelector("form[method='post']");
    if (formInPage) {
      initPlatoForm(document);
    }
  });
})();
