// PANTRY BIND
// Persistencia reutilizable para Ingredientes e Insumos.
// checked => necesito comprar => tengo=False
// unchecked => lo tengo => tengo=True

(function () {
  "use strict";

  if (document.__pantryBindLoaded) return;
  document.__pantryBindLoaded = true;

  function getFormContext(el) {
    const form = el.closest("form");
    if (!form) return null;

    const csrf =
      form.querySelector(
        "input[name='csrfmiddlewaretoken']"
      )?.value || "";

    const url = form.action;
    if (!url) return null;

    return { form, csrf, url };
  }

  async function postFormData({ url, csrf, fd }) {
    const res = await fetch(url, {
      method: "POST",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": csrf,
      },
      body: fd,
      credentials: "same-origin",
    });

    const contentType =
      res.headers.get("content-type") || "";

    if (!contentType.includes("application/json")) {
      const text = await res.text();
      throw new Error(
        "Respuesta no JSON (" +
          res.status +
          "): " +
          text.slice(0, 200)
      );
    }

    const data = await res.json().catch(() => ({}));

    if (
      !res.ok ||
      data.success === false ||
      data.ok === false
    ) {
      throw new Error(
        data.error || "No se pudo guardar el estado."
      );
    }

    return data;
  }

  function pantryIdentity(el) {
    const type = (el.dataset.pantryType || "").trim();
    const id = (el.dataset.pantryId || "").trim();

    if (
      (type === "ingrediente" || type === "insumo") &&
      /^\d+$/.test(id)
    ) {
      return {
        type,
        id,
        key:
          el.dataset.pantryKey ||
          type + "-" + id,
      };
    }

    // Compatibilidad con markup viejo.
    if (
      el.matches?.(
        "input[type='checkbox']" +
          "[name='ingrediente_a_comprar_id']"
      )
    ) {
      const legacyId = String(el.value || "").trim();

      if (/^\d+$/.test(legacyId)) {
        return {
          type: "ingrediente",
          id: legacyId,
          key: "ingrediente-" + legacyId,
        };
      }
    }

    return null;
  }

  function findComment(form, identity) {
    const generic = form.querySelector(
      'input[data-pantry-comment="1"]' +
        '[data-pantry-key="' +
        identity.key +
        '"]'
    );

    if (generic) return generic;

    return form.querySelector(
      'input[name="comentario_' +
        identity.id +
        '"]'
    );
  }

  document.addEventListener(
    "change",
    async (event) => {
      const checkbox = event.target.closest(
        "input[type='checkbox']" +
          "[data-pantry-type][data-pantry-id], " +
          "input[type='checkbox']" +
          "[name='ingrediente_a_comprar_id']"
      );

      if (!checkbox) return;

      const identity = pantryIdentity(checkbox);
      if (!identity) return;

      const context = getFormContext(checkbox);
      if (!context) return;

      const commentInput = findComment(
        context.form,
        identity
      );

      const fd = new FormData();
      fd.append("post_origen", "pantry");
      fd.append("pantry_item_type", identity.type);
      fd.append("pantry_item_id", identity.id);
      fd.append(
        "pantry_item_checked",
        checkbox.checked ? "1" : "0"
      );
      fd.append(
        "pantry_comment",
        commentInput ? commentInput.value || "" : ""
      );

      try {
        await postFormData({
          url: context.url,
          csrf: context.csrf,
          fd,
        });
      } catch (error) {
        console.error(
          "No se pudo persistir el estado del pantry",
          error
        );
      }
    }
  );

  const timers = new Map();

  document.addEventListener(
    "input",
    (event) => {
      const input = event.target.closest(
        'input[data-pantry-comment="1"], ' +
          'input[name^="comentario_"]'
      );

      if (!input) return;

      let identity = pantryIdentity(input);

      if (!identity) {
        const legacy = input.name.match(
          /^comentario_(\d+)$/
        );

        if (legacy) {
          identity = {
            type: "ingrediente",
            id: legacy[1],
            key: "ingrediente-" + legacy[1],
          };
        }
      }

      if (!identity) return;

      const context = getFormContext(input);
      if (!context) return;

      const timerKey =
        context.url + "|" + identity.key;

      if (timers.has(timerKey)) {
        clearTimeout(timers.get(timerKey));
      }

      const timer = setTimeout(
        async () => {
          const fd = new FormData();
          fd.append("post_origen", "pantry");
          fd.append(
            "pantry_item_type",
            identity.type
          );
          fd.append(
            "pantry_item_id",
            identity.id
          );
          fd.append(
            "pantry_comment",
            input.value || ""
          );

          try {
            await postFormData({
              url: context.url,
              csrf: context.csrf,
              fd,
            });
          } catch (error) {
            console.error(
              "No se pudo persistir el comentario",
              error
            );
          } finally {
            timers.delete(timerKey);
          }
        },
        450
      );

      timers.set(timerKey, timer);
    }
  );
})();
