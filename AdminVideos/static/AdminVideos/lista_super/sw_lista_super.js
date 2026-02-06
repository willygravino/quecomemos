// Service Worker - Lista Súper
// Objetivo: que la página cargue incluso sin internet usando caché.

const CACHE = "lista-super-v2";

// Archivos estáticos propios (mismo origen) que queremos guardar en caché.
const ASSETS = [
  // Archivos PWA básicos
  "/static/AdminVideos/lista_super/manifest_lista_super.json",

  // JS offline: necesarios para que funcione sin internet
  "/static/AdminVideos/lista_super/idb_cola_offline.js",
  "/static/AdminVideos/lista_super/sync_offline_lista_super.js",
];


// Instalación: crea el caché y guarda assets básicos.
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(ASSETS))
  );
  self.skipWaiting();
});

// Activación: toma control y limpia cachés viejos (si existieran).
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.map((k) => (k !== CACHE ? caches.delete(k) : null)))
    )
  );
  self.clients.claim();
});

// Fetch: intercepta requests para poder responder desde caché cuando no hay red.
self.addEventListener("fetch", (event) => {
  const req = event.request;
  const url = new URL(req.url);

  // Solo manejamos mismo origen (tu dominio). CDNs como jsdelivr quedan afuera.
  if (url.origin !== self.location.origin) return;

  // 1) Para navegación HTML (abrir la lista): network-first con fallback a caché
  if (req.mode === "navigate") {
    event.respondWith(
      fetch(req)
        .then((res) => {
          // Guardamos una copia de esta página (con su token incluido) en caché
          const copy = res.clone();
          caches.open(CACHE).then((cache) => cache.put(req, copy));
          return res;
        })
        .catch(() => caches.match(req))
    );
    return;
  }

  // 2) Para estáticos propios: cache-first
  if (url.pathname.startsWith("/static/")) {
    event.respondWith(
      caches.match(req).then((hit) => {
        if (hit) return hit;

        return fetch(req).then((res) => {
          const copy = res.clone();
          caches.open(CACHE).then((cache) => cache.put(req, copy));
          return res;
        });
      })
    );
  }
});
