/* global bootstrap */

(function () {
  "use strict";

  if (window.__PARTES_RECETA_LOADED__) return;
  window.__PARTES_RECETA_LOADED__ = true;

  const estados = new WeakMap();

  function obtenerCampoPartes(form) {
    return form.querySelector('[name="partes_receta_json"]');
  }

  function leerPartes(form) {
    const campo = obtenerCampoPartes(form);
    if (!campo || !campo.value) return [];

    try {
      const partes = JSON.parse(campo.value);
      return Array.isArray(partes) ? partes : [];
    } catch (error) {
      console.warn("No se pudieron leer las partes de la receta.", error);
      return [];
    }
  }

  function guardarPartes(form, partes) {
    const campo = obtenerCampoPartes(form);
    if (!campo) return;

    campo.value = JSON.stringify(
      partes.map(function (parte, indice) {
        return {
          clave: String(parte.clave || "").trim(),
          nombre: String(parte.nombre || "").trim(),
          instrucciones: String(parte.instrucciones || "").trim(),
          orden: indice,
        };
      })
    );
  }

  function crearClaveParte() {
    if (window.crypto && typeof window.crypto.randomUUID === "function") {
      return "parte_" + window.crypto.randomUUID().replace(/-/g, "");
    }

    return (
      "parte_" +
      Date.now().toString(36) +
      "_" +
      Math.random().toString(36).slice(2, 12)
    );
  }

  function obtenerEstado(form) {
    let estado = estados.get(form);

    if (!estado) {
      estado = {
        parteObjetivo: "",
        activandoIngredienteDeParte: false,
      };
      estados.set(form, estado);
    }

    return estado;
  }

  function obtenerPrefijoFila(fila) {
    const campo = fila.querySelector(
      'input[name^="ingredientes_en_plato-"], select[name^="ingredientes_en_plato-"]'
    );
    const coincidencia = campo?.name?.match(/^(ingredientes_en_plato-\d+)-/);
    return coincidencia ? coincidencia[1] : "";
  }

  function obtenerCampoParteFila(fila, crearSiFalta) {
    let campo = fila.querySelector('input[name$="-parte_clave"]');
    if (campo || !crearSiFalta) return campo;

    const prefijo = obtenerPrefijoFila(fila);
    if (!prefijo) return null;

    campo = document.createElement("input");
    campo.type = "hidden";
    campo.name = prefijo + "-parte_clave";

    const contenedor = fila.querySelector(".ingrediente-formset-fields") || fila;
    contenedor.appendChild(campo);
    return campo;
  }

  function obtenerClaveFila(fila) {
    return (obtenerCampoParteFila(fila, false)?.value || "").trim();
  }

  function asignarClaveFila(fila, clave) {
    const campo = obtenerCampoParteFila(fila, true);
    if (campo) campo.value = clave || "";
  }

  function crearBoton(texto, clases, icono) {
    const boton = document.createElement("button");
    boton.type = "button";
    boton.className = clases;

    if (icono) {
      const i = document.createElement("i");
      i.className = icono;
      i.setAttribute("aria-hidden", "true");
      boton.appendChild(i);
      boton.appendChild(document.createTextNode(" "));
    }

    boton.appendChild(document.createTextNode(texto));
    return boton;
  }

  function crearSeccionParte(form, parte) {
    const esGeneral = !parte.clave;
    const seccion = document.createElement("section");
    seccion.className =
      "parte-receta-card" + (esGeneral ? " parte-receta-card-general" : "");
    seccion.dataset.parteClave = parte.clave || "";

    const encabezado = document.createElement("div");
    encabezado.className = "parte-receta-card-header";

    const textos = document.createElement("div");
    textos.className = "parte-receta-card-textos";

    const titulo = document.createElement("h3");
    titulo.className = "parte-receta-card-title";
    titulo.textContent = parte.nombre;
    textos.appendChild(titulo);

    if (parte.instrucciones) {
      const instrucciones = document.createElement("p");
      instrucciones.className = "parte-receta-card-instrucciones";
      instrucciones.textContent = parte.instrucciones;
      textos.appendChild(instrucciones);
    }

    encabezado.appendChild(textos);

    const acciones = document.createElement("div");
    acciones.className = "parte-receta-card-actions";

    const agregar = crearBoton(
      "Ingrediente",
      "btn btn-sm btn-outline-primary js-agregar-ingrediente-parte",
      "fa-solid fa-plus"
    );
    agregar.dataset.parteClave = parte.clave || "";
    agregar.dataset.parteNombre = parte.nombre;
    acciones.appendChild(agregar);

    if (!esGeneral) {
      const editar = crearBoton(
        "Editar",
        "btn btn-sm btn-outline-secondary js-editar-parte-receta",
        "fa-regular fa-pen-to-square"
      );
      editar.dataset.parteClave = parte.clave;
      acciones.appendChild(editar);

      const eliminar = crearBoton(
        "Eliminar",
        "btn btn-sm btn-outline-danger js-eliminar-parte-receta",
        "fa-solid fa-trash-can"
      );
      eliminar.dataset.parteClave = parte.clave;
      eliminar.setAttribute("data-bs-toggle", "modal");
      eliminar.setAttribute("data-bs-target", "#confirmActionModal");
      eliminar.dataset.confirmTitle = "Eliminar parte de la receta";
      eliminar.dataset.confirmBtn = "Sí, eliminar";
      eliminar.dataset.confirmHint = "Los cambios se aplicarán al guardar el plato.";
      eliminar.dataset.confirmEvent = "partes-receta:eliminar";
      acciones.appendChild(eliminar);
    }

    encabezado.appendChild(acciones);
    seccion.appendChild(encabezado);

    const lista = document.createElement("ul");
    lista.className = "list-group list-group-flush parte-receta-ingredientes";
    lista.dataset.parteLista = parte.clave || "";
    seccion.appendChild(lista);

    const vacio = document.createElement("div");
    vacio.className = "parte-receta-vacia text-muted small";
    vacio.textContent = "Todavía no agregaste ingredientes en esta parte.";
    seccion.appendChild(vacio);

    return seccion;
  }

  function actualizarVacios(root) {
    root.querySelectorAll(".parte-receta-card").forEach(function (seccion) {
      const filasVisibles = Array.from(
        seccion.querySelectorAll("[data-ingrediente-row]")
      ).filter(function (fila) {
        return fila.style.display !== "none" && fila.getAttribute("aria-hidden") !== "true";
      });

      const vacio = seccion.querySelector(".parte-receta-vacia");
      if (vacio) vacio.classList.toggle("d-none", filasVisibles.length > 0);
    });
  }

  function renderizarPartes(form) {
    const root = form.querySelector("[data-partes-receta-root]");
    if (!root) return;

    const controles = form.querySelector("[data-partes-receta-controles]");

    const filas = Array.from(root.querySelectorAll("[data-ingrediente-row]"));
    filas.forEach(function (fila) {
      fila.remove();
    });
    root.replaceChildren();

    const partes = leerPartes(form);
    const todas = [
      {
        clave: "",
        nombre: "Ingredientes generales",
        instrucciones: "Ingredientes que corresponden al plato completo.",
      },
    ].concat(partes);

    const listas = new Map();

    todas.forEach(function (parte) {
      const seccion = crearSeccionParte(form, parte);
      root.appendChild(seccion);

      if (!parte.clave && controles) {
        root.appendChild(controles);
      }

      listas.set(parte.clave || "", seccion.querySelector("[data-parte-lista]"));
    });

    filas.forEach(function (fila) {
      const clave = obtenerClaveFila(fila);
      const lista = listas.get(clave) || listas.get("");

      if (!listas.has(clave)) asignarClaveFila(fila, "");
      lista.appendChild(fila);
    });

    actualizarVacios(root);
  }

  function ocultarEditor(form) {
    const editor = form.querySelector("[data-parte-receta-editor]");
    if (!editor) return;

    editor.classList.add("d-none");
    editor.querySelector("[data-parte-editor-clave]").value = "";
    editor.querySelector("[data-parte-editor-nombre]").value = "";
    editor.querySelector("[data-parte-editor-instrucciones]").value = "";
  }

  function mostrarEditor(form, parte) {
    const editor = form.querySelector("[data-parte-receta-editor]");
    if (!editor) return;

    editor.querySelector("[data-parte-editor-clave]").value = parte?.clave || "";
    editor.querySelector("[data-parte-editor-nombre]").value = parte?.nombre || "";
    editor.querySelector("[data-parte-editor-instrucciones]").value =
      parte?.instrucciones || "";
    editor.classList.remove("d-none");
    editor.querySelector("[data-parte-editor-nombre]").focus();
    editor.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  function guardarEditor(form) {
    const editor = form.querySelector("[data-parte-receta-editor]");
    if (!editor) return;

    const claveActual = editor.querySelector("[data-parte-editor-clave]").value.trim();
    const nombre = editor.querySelector("[data-parte-editor-nombre]").value.trim();
    const instrucciones = editor
      .querySelector("[data-parte-editor-instrucciones]")
      .value.trim();

    if (!nombre) {
      alert("Escribí un nombre para la parte de la receta.");
      editor.querySelector("[data-parte-editor-nombre]").focus();
      return;
    }

    const partes = leerPartes(form);
    const repetida = partes.some(function (parte) {
      return (
        parte.clave !== claveActual &&
        String(parte.nombre || "").trim().toLocaleLowerCase() ===
          nombre.toLocaleLowerCase()
      );
    });

    if (repetida) {
      alert("Ya existe una parte con ese nombre.");
      return;
    }

    if (claveActual) {
      const parte = partes.find(function (item) {
        return item.clave === claveActual;
      });
      if (!parte) return;
      parte.nombre = nombre;
      parte.instrucciones = instrucciones;
    } else {
      partes.push({
        clave: crearClaveParte(),
        nombre: nombre,
        instrucciones: instrucciones,
        orden: partes.length,
      });
    }

    guardarPartes(form, partes);
    ocultarEditor(form);
    renderizarPartes(form);
  }

  function escaparHtml(valor) {
    return String(valor || "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function filasActivasDeParte(form, clave) {
    return Array.from(
      form.querySelectorAll('[data-ingrediente-row] input[name$="-parte_clave"]')
    )
      .filter(function (campo) {
        if (campo.value !== clave) return false;
        const fila = campo.closest("[data-ingrediente-row]");
        const borrar = fila?.querySelector('input[name$="-DELETE"]');
        return fila && !borrar?.checked;
      })
      .map(function (campo) {
        return campo.closest("[data-ingrediente-row]");
      });
  }

  function prepararConfirmacionEliminarParte(form, boton) {
    const clave = boton.dataset.parteClave;
    const parte = leerPartes(form).find(function (item) {
      return item.clave === clave;
    });
    if (!parte) return;

    const cantidad = filasActivasDeParte(form, clave).length;
    const detalle = cantidad === 0
      ? "Esta parte no contiene ingredientes."
      : cantidad === 1
        ? "También se eliminará el ingrediente que contiene."
        : "También se eliminarán sus " + cantidad + " ingredientes.";

    boton.dataset.confirmBody =
      "¿Querés eliminar la parte <strong>" +
      escaparHtml(parte.nombre) +
      "</strong>? " +
      detalle;
  }

  function eliminarParteConfirmada(form, clave) {
    const partes = leerPartes(form);
    if (!partes.some(function (item) { return item.clave === clave; })) return;

    filasActivasDeParte(form, clave).forEach(function (fila) {
      const borrar = fila.querySelector('input[name$="-DELETE"]');
      if (borrar) borrar.checked = true;

      fila.style.setProperty("display", "none", "important");
      fila.setAttribute("aria-hidden", "true");
    });

    guardarPartes(
      form,
      partes.filter(function (item) {
        return item.clave !== clave;
      })
    );
    renderizarPartes(form);
  }

  function mostrarDestinoIngrediente(nombre) {
    const aviso = document.getElementById("ingredienteParteActual");
    if (!aviso) return;

    aviso.textContent = "Este ingrediente se agregará en: " + nombre;
    aviso.classList.remove("d-none");
  }

  function iniciarFormulario(form) {
    if (!form || form.dataset.partesRecetaInicializado === "1") return;
    if (!obtenerCampoPartes(form) || !form.querySelector("[data-partes-receta-root]")) return;

    form.dataset.partesRecetaInicializado = "1";
    obtenerEstado(form);
    renderizarPartes(form);

    form.addEventListener("click", function (event) {
      const agregarParte = event.target.closest(".js-agregar-parte-receta");
      if (agregarParte) {
        event.preventDefault();
        mostrarEditor(form, null);
        return;
      }

      const cancelarParte = event.target.closest(".js-cancelar-parte-receta");
      if (cancelarParte) {
        event.preventDefault();
        ocultarEditor(form);
        return;
      }

      const guardarParte = event.target.closest(".js-guardar-parte-receta");
      if (guardarParte) {
        event.preventDefault();
        guardarEditor(form);
        return;
      }

      const editarParte = event.target.closest(".js-editar-parte-receta");
      if (editarParte) {
        event.preventDefault();
        const parte = leerPartes(form).find(function (item) {
          return item.clave === editarParte.dataset.parteClave;
        });
        if (parte) mostrarEditor(form, parte);
        return;
      }

      const eliminarParteBtn = event.target.closest(".js-eliminar-parte-receta");
      if (eliminarParteBtn) {
        prepararConfirmacionEliminarParte(form, eliminarParteBtn);
        return;
      }

      const agregarEnParte = event.target.closest(".js-agregar-ingrediente-parte");
      if (agregarEnParte) {
        event.preventDefault();

        const estado = obtenerEstado(form);
        estado.parteObjetivo = agregarEnParte.dataset.parteClave || "";
        estado.activandoIngredienteDeParte = true;

        const botonGeneral = form.querySelector(".js-agregar-ingrediente");
        if (botonGeneral) botonGeneral.click();

        estado.activandoIngredienteDeParte = false;
        mostrarDestinoIngrediente(
          agregarEnParte.dataset.parteNombre || "Ingredientes generales"
        );
        return;
      }

      const botonGeneral = event.target.closest(".js-agregar-ingrediente");
      if (botonGeneral) {
        const estado = obtenerEstado(form);
        if (!estado.activandoIngredienteDeParte) {
          estado.parteObjetivo = "";
          mostrarDestinoIngrediente("Ingredientes generales");
        }
      }
    });
  }

  function iniciarTodos(root) {
    const contexto = root || document;

    if (contexto.matches?.("#platoForm")) iniciarFormulario(contexto);
    contexto.querySelectorAll?.("#platoForm").forEach(iniciarFormulario);
  }

  function procesarFilaNueva(fila) {
    const form = fila.closest("#platoForm");
    if (!form || !estados.has(form)) return;

    let campoParte = obtenerCampoParteFila(fila, false);
    if (campoParte) return;

    const estado = obtenerEstado(form);
    asignarClaveFila(fila, estado.parteObjetivo || "");
    renderizarPartes(form);
  }

  document.addEventListener("partes-receta:eliminar", function (event) {
    const boton = event.detail?.trigger;
    const form = boton?.closest("#platoForm");
    const clave = boton?.dataset.parteClave;

    if (form && clave) eliminarParteConfirmada(form, clave);
  });

  document.addEventListener("DOMContentLoaded", function () {
    iniciarTodos(document);
  });

  iniciarTodos(document);

  const observador = new MutationObserver(function (mutaciones) {
    mutaciones.forEach(function (mutacion) {
      mutacion.addedNodes.forEach(function (nodo) {
        if (!(nodo instanceof Element)) return;

        iniciarTodos(nodo);

        if (nodo.matches("[data-ingrediente-row]")) procesarFilaNueva(nodo);
        nodo.querySelectorAll?.("[data-ingrediente-row]").forEach(procesarFilaNueva);
      });
    });
  });

  observador.observe(document.documentElement, {
    childList: true,
    subtree: true,
  });
})();
