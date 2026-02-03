/* static/js/form_init.js */
/* global bootstrap, $ */

(function () {
  "use strict";

  // ===========================
  // PLATO INGREDIENTES (modal): guardar comentarios (debounce)
  // ===========================
  if (!document.__platoIngredientesComentarioBound) {
    let t = null;

    document.addEventListener("input", (ev) => {
      const inp = ev.target.closest("input[type='text'][data-ing-nombre]");
      if (!inp) return;

      const modal = inp.closest("#platoIngredientesModal");
      if (!modal) return;

      const api = modal.getAttribute("data-api-toggle");
      if (!api) return;

      const nombre = (inp.dataset.ingNombre || "").trim();
      const comentario = (inp.value || "").trim();

      // debounce simple para no postear cada tecla
      clearTimeout(t);
      t = setTimeout(async () => {
        try {
          const res = await fetch(api, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ nombre, comentario })
          });

          const data = await res.json().catch(() => ({}));
          if (!res.ok || data.ok === false) {
            console.error("API error (comentario):", res.status, data);
          }
        } catch (e) {
          console.error("No se pudo persistir el comentario", e);
        }
      }, 400);
    });

    document.__platoIngredientesComentarioBound = true;
  }


    // ===========================
  // PLATO INGREDIENTES (modal): guardar checks
  // checked en este modal = "hay que comprar" => no-tengo
  // Endpoint api-toggle-item usa checked = "tengo"
  // Por eso invertimos.
  // ===========================
  if (!document.__platoIngredientesToggleBound) {
    console.log("✅ platoIngredientesToggleBound cargado");

    document.addEventListener("change", async (ev) => {
      const chk = ev.target.closest("input[type='checkbox'][name='ingrediente_a_comprar_id']");
      if (!chk) return;

      const modal = chk.closest("#platoIngredientesModal");
      if (!modal) return;

      const api = modal.getAttribute("data-api-toggle");
      if (!api) {
        console.error("Falta data-api-toggle en #platoIngredientesModal");
        return;
      }

      const li = chk.closest("li");
      const nombre = (li?.querySelector("label")?.textContent || "").trim();
      if (!nombre) {
        console.error("No pude leer el nombre del ingrediente");
        return;
      }

      const checkedComprar = chk.checked;   // checked => comprar => no-tengo
      const checkedTengo = !checkedComprar; // invertimos para el endpoint

      try {
        const res = await fetch(api, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ nombre, checked: checkedTengo })
        });

        const data = await res.json().catch(() => ({}));
        if (!res.ok || data.ok === false) {
          console.error("API error:", res.status, data);
        }
      } catch (e) {
        console.error("No se pudo persistir el cambio", e);
      }
    });

    document.__platoIngredientesToggleBound = true;
  }


  // ===========================
  // PLATO: Ver / compartir ingredientes (modal)
  // Apila modales (no oculta modalPlato)
  // ===========================
  if (!document.__platoIngredientesBound) {

    // ---- Helper: stack de modales (Bootstrap 5)
    // Hace que cada modal nuevo quede arriba del anterior, con backdrop correcto.
    function stackModal(modalEl) {
      const openModals = document.querySelectorAll(".modal.show").length; // cuántos ya están abiertos
      const baseZ = 1055;                 // Bootstrap modal z-index base
      const step = 20;                    // separación segura
      const z = baseZ + (openModals * step);

      modalEl.style.zIndex = z;

      // Cuando Bootstrap cree el backdrop, lo ajustamos también
      setTimeout(() => {
        const backdrops = document.querySelectorAll(".modal-backdrop");
        const backdrop = backdrops[backdrops.length - 1];
        if (backdrop) {
          backdrop.style.zIndex = z - 1;
        }
      }, 0);
    }

    async function openPlatoIngredientesModal(url) {
      const res = await fetch(url, {
        headers: { "X-Requested-With": "XMLHttpRequest" },
        credentials: "same-origin",
      });

      const html = await res.text();

      if (!res.ok) {
        console.error("❌ Error HTTP", res.status, "al cargar modal ingredientes");
        console.error(html);
        return;
      }


      const root = document.getElementById("modal-root");
      if (!root) {
        console.error("Falta #modal-root en el HTML base");
        return;
      }

      root.innerHTML = html;

      const modalEl = document.getElementById("platoIngredientesModal");
      if (!modalEl) {
        console.error("No llegó #platoIngredientesModal en el HTML del endpoint");
        return;
      }

      // que viva en body para z-index correcto
      if (modalEl.parentElement !== document.body) {
        document.body.appendChild(modalEl);
      }

      // IMPORTANTE: al apilar, conviene desactivar el "focus trap" del modal superior
      // para que no rompa interacción con el de abajo (Bootstrap 5 soporta focus:false)
      const modal =
        bootstrap.Modal.getInstance(modalEl) ||
        new bootstrap.Modal(modalEl, { focus: false });

      // antes de mostrar, ajustamos stack
      stackModal(modalEl);
      modal.show();

      modalEl.addEventListener(
        "hidden.bs.modal",
        () => {
          root.innerHTML = "";
        },
        { once: true }
      );
    }

    document.addEventListener("click", (e) => {
      const btn = e.target.closest(".js-plato-ingredientes");
      if (!btn) return;

      e.preventDefault();

      const url = btn.dataset.url;
      if (!url) {
        console.error("Falta data-url en .js-plato-ingredientes");
        return;
      }

      openPlatoIngredientesModal(url).catch((err) =>
        console.error("Error abriendo ingredientes:", err)
      );
    });

    document.__platoIngredientesBound = true;
  }


  
  // ===========================
// FIX BOOTSTRAP MODALS STACKING
// ===========================
// Cuando se abre un modal (ej: Variedad) y desde ahí se abre otro
// (ej: Ingrediente), Bootstrap deja ambos con el mismo z-index (1050)
// y el segundo queda visualmente "detrás".
//
// La causa es que algunos modales se renderizan dentro de otros
// contenedores (por ejemplo, dentro del modal de variedad).
//
// Solución:
// - Forzar que ciertos modales vivan directamente en <body>
// - Bootstrap calcula correctamente z-index y backdrop desde ahí
//
// ⚠️ Esto se ejecuta UNA SOLA VEZ al cargar el script
// ===========================

  function ensureModalAtBody(id) {
    const el = document.getElementById(id);
    if (!el) return;
    if (el.parentElement !== document.body) {
      document.body.appendChild(el);
    }
  }

  // al iniciar el script (después de definir funciones básicas)
  ensureModalAtBody("ingredienteModal");
  ensureModalAtBody("confirmDeleteVariedadModal");
  ensureModalAtBody("successModal");

  


  // Evita redefinir si el archivo se carga más de una vez
  if (window.__PLATO_FORM_INIT_LOADED__) return;

  function getCookie(name) {
    const cookies = document.cookie ? document.cookie.split(";") : [];
    for (let i = 0; i < cookies.length; i++) {
      const c = cookies[i].trim();
      if (c.startsWith(name + "=")) return decodeURIComponent(c.substring(name.length + 1));
    }
    return null;
  }


  const CSRF_TOKEN = getCookie("csrftoken");
  window.__PLATO_FORM_INIT_LOADED__ = true;

    


  // ===== Utils =====
  function log() {
    if (window && window.console && console.log) {
      console.log.apply(console, arguments);
    }
  }


  // ===== Select2 helpers =====
  function buildSelect2Config(dropdownParent /* jQuery or null */) {
    const cfg = {
      placeholder: "Selecciona un ingrediente",
      ajax: {
        url: "/api/ingredientes/",
        dataType: "json",
        delay: 250,
        data: (params) => ({ q: params.term || "" }),



        

        processResults: (data) => {
          // Caso 1: API estilo Select2 => { results: [{id, text}, ...] }
          if (data && Array.isArray(data.results)) {
            return { results: data.results };
          }

          // Caso 2: tu API vieja => [{id, nombre}, ...]
          if (Array.isArray(data)) {
            return {
              results: data.map((item) => ({ id: item.id, text: item.nombre })),
            };
          }

          return { results: [] };
        },





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

   // ✅ Pre-cargar valor inicial (data-attributes o fallback desde hidden)
    let initId = $select.data("initial-id");
    let initText = $select.data("initial-text");

    // Si no vienen data-initial-* (a veces en HTML cargado por AJAX),
    // tomar valor desde los hidden del mismo <li>
    if ((!initId || !initText)) {
      const li = selectEl.closest("li");
      if (li) {
        const hidId = li.querySelector('input[name$="-ingrediente"]');
        const hidText = li.querySelector('input[name$="-nombre_ingrediente"]');
        if (!initId && hidId) initId = (hidId.value || "").trim();
        if (!initText && hidText) initText = (hidText.value || "").trim();
      }
    }

    if (initId && initText) {
      const option = new Option(initText, initId, true, true);
      $select.append(option).trigger("change");
    }


    // Inicializar Select2 (lista del form, fuera del modal => sin dropdownParent)
    const modalRoot = $select.closest(".modal");
    const dropdownParent = modalRoot.length ? modalRoot : null;

    $select.select2(buildSelect2Config(dropdownParent));

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

      <input type="checkbox" name="${prefix}-${totalForms}-DELETE" class="d-none delete-flag" value="">


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

    
  // Evita doble init SOLO en página completa.
  // En modal se reemplaza HTML (AJAX), así que necesitamos re-init siempre.
  const isModalContext = !!(context.closest && context.closest("#modalPlato"));
  if (!isModalContext) {
    if (context.__platoFormInitialized) {
      log("ℹ️ initPlatoForm: ya estaba inicializado para este context");
      return;
    }
    context.__platoFormInitialized = true;
  }



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


    // ===== Modal ingredientes → Select2 del modal-nombre (delegado) =====
    if (!document.__ingredienteModalSelect2Bound) {
      document.addEventListener("shown.bs.modal", function (e) {
        if (!e.target || e.target.id !== "ingredienteModal") return;

        const $modal = $(e.target);
        const $sel = $modal.find("#modal-nombre");
        if (!$sel.length) return;

        if (!$sel.data("select2")) {
          $sel.select2(buildSelect2Config($modal));
        }
        $sel.select2("open");
      });

      document.__ingredienteModalSelect2Bound = true;
    }







    // ===== Botón "Guardar" del modal ingredientes
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

  // // ===== Asegurar que el form tenga action correcto =====
  // const formEl = context.querySelector("#platoForm") || context.querySelector("form[method='post']");
  // if (formEl) {
    
    
  //   const isUpdateMode = formEl.dataset.mode === "update";

  //   // 👉 Si es edición, NO tocar el action
  //   if (isUpdateMode) {
  //     log("✏️ Modo edición detectado, action preservado:", formEl.action);
  //   } else {
  //     // 👉 Si es creación (modal)




  //     let tipopag = "Principal";
  //     const tipoInput = context.querySelector("input[name='tipos']:checked");
  //     if (tipoInput) {
  //       tipopag = tipoInput.value;
  //     }

  //     formEl.action = `/videos/create/?tipopag=${encodeURIComponent(tipopag)}`;
  //     log("🆕 Modo creación, action forzado:", formEl.action);
  //   }
  // }
 


        // ===== Guardado AJAX dentro del modal principal =====
    function setupAjaxSave(modalBody) {
      const form = modalBody.querySelector("form");
      if (!form) return;

      form.addEventListener("submit", function (e) {
        // Solo interceptar si el form está dentro del modal
      if (!form.closest("#modalPlato")) return;

        e.preventDefault();

        // 🔹 Crear FormData con todos los inputs visibles y ocultos del modal
        const formData = new FormData(form);

        // // 🔹 Asegurar que el formset de ingredientes se incluya aunque esté fuera del <form>
        // document.querySelectorAll("[name^='ingredientes_en_plato-']").forEach(el => {
        //   if (!formData.has(el.name)) {
        //     formData.append(el.name, el.value);
        //   }
        // });
          modalBody.querySelectorAll("[name^='ingredientes_en_plato-'], #id_ingredientes_en_plato-TOTAL_FORMS, #id_ingredientes_en_plato-INITIAL_FORMS, #id_ingredientes_en_plato-MIN_NUM_FORMS, #id_ingredientes_en_plato-MAX_NUM_FORMS")
        .forEach(el => {
          if (el.type === "checkbox") {
            if (el.checked) formData.set(el.name, el.value || "on");
            else formData.delete(el.name);
          } else {
            formData.set(el.name, el.value);
          }
        });



    fetch(form.action, {
        method: "POST",
        body: formData,
        headers: {
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": CSRF_TOKEN || ""
        },
      })
      .then(async response => {
        const contentType = response.headers.get("content-type") || "";

        if (contentType.includes("application/json")) {
          const data = await response.json();

          if (data.success) {

            const modal = bootstrap.Modal.getInstance(form.closest("#modalPlato"));

            modal.hide();
            location.reload(); // refresca lista de platos
          } else if (data.html) {
            modalBody.innerHTML = data.html;
            initPlatoForm(modalBody);
          } else {
            console.error("⚠️ Respuesta JSON inesperada:", data);
          }

        } else {
          const text = await response.text();
          console.error("❌ La respuesta no es JSON. Posible error en el backend:");
          console.error(text); // Mostramos el HTML que causó el fallo
          alert("Error inesperado del servidor. Revisa la consola para más información.");
        }
      })
      .catch(err => {
        console.error("❌ Error en el fetch:", err);
        alert("Ocurrió un error al intentar guardar. Revisá la consola para más detalles.");
      });
          



      });
    }

    // Llamar a setupAjaxSave cuando se inicializa el form
    setupAjaxSave(context);
    log("✅ initPlatoForm completado para el contexto:", context);
  } // ← cierre de la función initPlatoForm

  // Exponer globalmente
  window.initPlatoForm = initPlatoForm;


    // ===========================
  // VARIEDADES: modal siempre (create/update)
  // ===========================
  if (!document.__variedadModalBound) {

    function ensureVariedadModalExists() {
      let modalEl = document.getElementById("variedadModal");
      if (modalEl) return modalEl;

      // Crear modal si no existe (por si el template no lo incluye)
      const wrapper = document.createElement("div");
      wrapper.innerHTML = `
        <div class="modal fade" id="variedadModal" tabindex="-1" aria-hidden="true">
          <div class="modal-dialog modal-lg modal-dialog-scrollable">
            <div class="modal-content">
              <div class="modal-header">
                <h5 class="modal-title">Agregar variedad</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button>
              </div>
              <div class="modal-body" id="variedadModalBody">
                <div class="text-muted">Cargando…</div>
              </div>
            </div>
          </div>
        </div>
      `;
      document.body.appendChild(wrapper.firstElementChild);
      return document.getElementById("variedadModal");
    }

    async function openVariedadModal(url) {
      const modalEl = ensureVariedadModalExists();
      const modalBody = modalEl.querySelector("#variedadModalBody");
      modalBody.innerHTML = '<div class="text-muted">Cargando…</div>';

      const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
      modal.show();

      const res = await fetch(url, {
        headers: { "X-Requested-With": "XMLHttpRequest" },
        credentials: "same-origin",
      });
      const data = await res.json();

      modalBody.innerHTML = data.html;

      // Re-init de todo lo del form (select2 + formset + etc.) en el HTML nuevo
      // OJO: tu initPlatoForm detecta modal por #modalPlato, así que acá va a
      // comportarse como "page". Está bien porque el HTML se reemplaza.
      if (window.initPlatoForm) window.initPlatoForm(modalBody);

      // Además, interceptamos submit dentro de este modal (variedadModal),
      // porque tu setupAjaxSave actual solo engancha #modalPlato.
      const innerForm = modalBody.querySelector("form");
      if (innerForm && !innerForm.__ajaxBound) {
        innerForm.addEventListener("submit", async function (e) {
          e.preventDefault();

          const formData = new FormData(innerForm);

          // Asegurar formset ingredientes dentro del modal de variedad
          modalBody
            .querySelectorAll(
              "[name^='ingredientes_en_plato-'], #id_ingredientes_en_plato-TOTAL_FORMS, #id_ingredientes_en_plato-INITIAL_FORMS, #id_ingredientes_en_plato-MIN_NUM_FORMS, #id_ingredientes_en_plato-MAX_NUM_FORMS"
            )
            .forEach((el) => {
              if (el.type === "checkbox") {
                if (el.checked) formData.set(el.name, el.value || "on");
                else formData.delete(el.name);
              } else {
                formData.set(el.name, el.value);
              }
            });

          const resp = await fetch(innerForm.action, {
            method: "POST",
            body: formData,
            headers: {
              "X-Requested-With": "XMLHttpRequest",
              "X-CSRFToken": CSRF_TOKEN || "",
            },
            credentials: "same-origin",
          });

          const ct = resp.headers.get("content-type") || "";
          if (!ct.includes("application/json")) {
            const text = await resp.text();
            console.error("❌ Respuesta no JSON en variedad:", text);
            alert("Error inesperado del servidor (variedad). Revisá la consola.");
            return;
          }

          const payload = await resp.json();

          if (payload.success) {
            const modalEl2 = modalEl; // el mismo modal del principio
            const inst = bootstrap.Modal.getInstance(modalEl2);

            // cerrar
            if (inst) inst.hide();

            // recargar cuando el modal terminó de cerrarse
            modalEl2.addEventListener(
              "hidden.bs.modal",
              () => window.location.reload(),
              { once: true }
            );
            return;
          }


          if (payload.html) {
            modalBody.innerHTML = payload.html;
            if (window.initPlatoForm) window.initPlatoForm(modalBody);
          }
        });

        innerForm.__ajaxBound = true;
      }
    }

    // Delegación: cualquier botón/link con .js-open-variedad-modal
    document.addEventListener("click", function (e) {
      const btn = e.target.closest(".js-open-variedad-modal");
      if (!btn) return;

      e.preventDefault();

      const url = btn.getAttribute("data-url") || btn.getAttribute("href");
      if (!url) return;

      openVariedadModal(url).catch((err) => {
        console.error("❌ Error abriendo modal variedad:", err);
        alert("No se pudo cargar el formulario de variedad. Revisá la consola.");
      });
    });

    document.__variedadModalBound = true;
  }


  // Auto-init en páginas normales (cuando hay formulario ya presente en el DOM)
  document.addEventListener("DOMContentLoaded", function () {
    const formInPage =
      document.querySelector("#platoForm") || document.querySelector("form[method='post']");
    if (formInPage) {
      initPlatoForm(document);
    }
  });
})(); // ← cierre final del IIFE principal