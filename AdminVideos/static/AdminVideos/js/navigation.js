/* Navegación efímera entre pantallas.

   data-nav-store-current="clave" guarda la URL actual antes de navegar.
   data-nav-return="clave" vuelve a esa URL.
   El href del enlace de retorno queda siempre como fallback.
*/
(function () {
  "use strict";

  const PREFIX = "qc_nav_origin:";

  function storageKey(name) {
    return PREFIX + name;
  }

  function setOrigin(name) {
    try {
      sessionStorage.setItem(storageKey(name), window.location.href);
    } catch (error) {
      // Sin storage, el enlace sigue funcionando normalmente.
    }
  }

  function consumeOrigin(name) {
    try {
      const key = storageKey(name);
      const value = sessionStorage.getItem(key) || "";
      sessionStorage.removeItem(key);
      return value;
    } catch (error) {
      return "";
    }
  }

  document.addEventListener("click", function (event) {
    const storeLink = event.target.closest("[data-nav-store-current]");
    if (storeLink) {
      // Si otra mejora progresiva ya interceptó el enlace (por ejemplo,
      // Lista de compras como panel), no guardar un origen que no se usó.
      if (event.defaultPrevented) return;

      const name = (storeLink.dataset.navStoreCurrent || "").trim();
      if (name) setOrigin(name);
      return;
    }

    const returnLink = event.target.closest("[data-nav-return]");
    if (!returnLink) return;

    const name = (returnLink.dataset.navReturn || "").trim();
    if (!name) return;

    const rawOrigin = consumeOrigin(name);
    if (!rawOrigin) return;

    try {
      const destination = new URL(rawOrigin, window.location.origin);
      if (destination.origin !== window.location.origin) return;
      if (destination.href === window.location.href) return;

      event.preventDefault();
      window.location.assign(destination.href);
    } catch (error) {
      // href del enlace = fallback seguro.
    }
  });
})();
