// IndexedDB - Cola Offline (Lista Súper)
// Guarda SOLO el último estado por ingrediente_id (evita duplicados).

const DB_NAME = "lista_super_offline";
const STORE = "cola_por_ingrediente";
const DB_VER = 2; // subimos versión porque cambia el schema

function openDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VER);

    req.onupgradeneeded = () => {
      const db = req.result;

      // Si cambia el schema, lo más simple es recrear el store
      if (db.objectStoreNames.contains(STORE)) {
        db.deleteObjectStore(STORE);
      }

      // keyPath = ingrediente_id => 1 registro por ingrediente
      db.createObjectStore(STORE, { keyPath: "ingrediente_id" });
    };

    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

// Guarda/actualiza (pisando) el estado final del ingrediente
export async function colaGuardarEstadoFinal(op) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readwrite");
    tx.objectStore(STORE).put(op); // put = insert o update
    tx.oncomplete = () => resolve(true);
    tx.onerror = () => reject(tx.error);
  });
}

// Lee todo lo pendiente
export async function colaLeerTodo() {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readonly");
    const req = tx.objectStore(STORE).getAll();
    req.onsuccess = () => resolve(req.result || []);
    req.onerror = () => reject(req.error);
  });
}

// Limpia la cola completa (ya que son "estados finales")
export async function colaLimpiarTodo() {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readwrite");
    tx.objectStore(STORE).clear();
    tx.oncomplete = () => resolve(true);
    tx.onerror = () => reject(tx.error);
  });
}
