(function () {
  "use strict";

  function getForm(el) {
    return el && el.closest ? el.closest("form#frm-menu") : null;
  }

  function csrfFrom(form) {
    return form.querySelector('input[name="csrfmiddlewaretoken"]')?.value || "";
  }

  function setOrigen(form, value) {
    const input = form.querySelector('input[name="post_origen"]');
    if (input) input.value = value;
  }

  async function autosave(form) {
    const response = await fetch(form.action, {
      method: "POST",
      headers: {
        "X-CSRFToken": csrfFrom(form),
        "X-Requested-With": "XMLHttpRequest",
      },
      body: new FormData(form),
      credentials: "same-origin",
    });

    if (!response.ok) {
      throw new Error("No se pudo guardar la selección de compra.");
    }
  }

  function refreshAfterMenuChange(form) {
    if (form.closest("#shoppingPanel")) {
      document.dispatchEvent(new CustomEvent("shopping-panel:refresh"));
      return;
    }
    window.location.reload();
  }

  document.addEventListener("change", async function (event) {
    const el = event.target;
    const form = getForm(el);
    if (!form) return;

    if (el.matches('input[name="plato_seleccionado"]')) {
      try {
        setOrigen(form, "menu");

        const platoId = (el.value || "").split("_", 1)[0];
        const toggleId = form.querySelector('input[name="toggle_plato_id"]');
        const toggleChecked = form.querySelector('input[name="toggle_plato_checked"]');

        if (toggleId) toggleId.value = platoId;
        if (toggleChecked) toggleChecked.value = el.checked ? "1" : "0";

        await autosave(form);
        refreshAfterMenuChange(form);
      } catch (error) {
        console.error("No se pudo guardar y refrescar la lista", error);
      }
      return;
    }

    if (el.matches('input[name="componente_seleccionado"]')) {
      try {
        setOrigen(form, "menu");

        const parts = (el.value || "").split("_");
        const componentePlatoId = parts[1] || "";
        const toggleId = form.querySelector('input[name="toggle_plato_id"]');
        const toggleChecked = form.querySelector('input[name="toggle_plato_checked"]');

        if (toggleId) toggleId.value = componentePlatoId;
        if (toggleChecked) toggleChecked.value = el.checked ? "1" : "0";

        await autosave(form);
        refreshAfterMenuChange(form);
      } catch (error) {
        console.error("No se pudo guardar el componente", error);
      }
    }
  });

  document.addEventListener("submit", function (event) {
    if (event.target && event.target.matches("form#frm-menu")) {
      event.preventDefault();
    }
  });
})();
