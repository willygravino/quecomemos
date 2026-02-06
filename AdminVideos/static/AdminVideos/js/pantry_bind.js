// static/js/pantry_bind.js
// ==========================================================
// PANTRY BIND (reutilizable)
// Unifica la persistencia de "ingredientes del pantry" en:
// - Lista de compras
// - Modal de ingredientes del plato
//
// Convención de inputs:
// - Checkbox:  name="ingrediente_a_comprar_id"  value="<ingrediente_id>"
//   * checked   => "necesito comprar" => tengo=False
//   * unchecked => "lo tengo"         => tengo=True
//
// - Comentario: name="comentario_<ingrediente_id>"
//
// Backend esperado (POST):
// - post_origen=ingredientes
// - toggle_ing_id / toggle_ing_checked / comentario_<id>  (para checkbox)
// - comment_ing_id / comentario_<id>                      (para comentario)
//
// Requisito:
// - El <form> contenedor debe tener action correcto (form.action)
// - Debe existir csrfmiddlewaretoken dentro del form
// ==========================================================

(function () {
  "use strict";

  // Evita doble carga del binder si el JS se incluye más de una vez
  if (document.__pantryBindLoaded) return;
  document.__pantryBindLoaded = true;

  console.log("🧺 pantry_bind.js cargado");

  // ----------------------------------------------------------
  // Helper: contexto del form (action + csrf)
  // ----------------------------------------------------------
  function getFormContext(el) {
    const form = el.closest("form");
    if (!form) return null;

    const csrf = form.querySelector("input[name='csrfmiddlewaretoken']")?.value || "";
    const url = form.action;
    if (!url) return null;

    return { form, csrf, url };
  }

  // ----------------------------------------------------------
  // Helper: POST con FormData y validación de respuesta JSON
  // ----------------------------------------------------------
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

    const ct = res.headers.get("content-type") || "";
    if (!ct.includes("application/json")) {
      const text = await res.text();
      console.error("❌ Respuesta no JSON:", res.status, text.slice(0, 300));
      return;
    }

    const data = await res.json().catch(() => ({}));
    if (!res.ok || data.success === false) {
      console.error("❌ POST error:", res.status, data);
    }
  }

  // ==========================================================
  // 1) Checkbox: "necesito comprar" (toggle tengo/no-tengo)
  // ==========================================================
  document.addEventListener("change", async (ev) => {
    const chk = ev.target.closest("input[type='checkbox'][name='ingrediente_a_comprar_id']");
    if (!chk) return;

    const ctx = getFormContext(chk);
    if (!ctx) return;

    const ingId = chk.value;
    if (!ingId) return;

    // checked => "1" = necesito comprar (tengo=False)
    const toggleChecked = chk.checked ? "1" : "0";

    // comentario actual (si existe)
    const commentInput = ctx.form.querySelector(`input[name="comentario_${ingId}"]`);
    const comentario = commentInput ? (commentInput.value || "") : "";

    const fd = new FormData();
    fd.append("post_origen", "ingredientes");
    fd.append("toggle_ing_id", ingId);
    fd.append("toggle_ing_checked", toggleChecked);
    fd.append(`comentario_${ingId}`, comentario);

    try {
      await postFormData({ url: ctx.url, csrf: ctx.csrf, fd });
    } catch (e) {
      console.error("No se pudo persistir el toggle", e);
    }
  });

  // ==========================================================
  // 2) Comentario: debounce mientras escribe
  // ==========================================================
  let t = null;

  document.addEventListener("input", (ev) => {
    const inp = ev.target.closest("input[name^='comentario_']");
    if (!inp) return;

    const ctx = getFormContext(inp);
    if (!ctx) return;

    const m = inp.name.match(/^comentario_(\d+)$/);
    if (!m) return;

    const ingId = m[1];
    const comentario = inp.value || "";

    clearTimeout(t);
    t = setTimeout(async () => {
      const fd = new FormData();
      fd.append("post_origen", "ingredientes");
      fd.append("comment_ing_id", ingId);
      fd.append(`comentario_${ingId}`, comentario);

      try {
        await postFormData({ url: ctx.url, csrf: ctx.csrf, fd });
      } catch (e) {
        console.error("No se pudo persistir el comentario", e);
      }
    }, 450);
  });
})();
