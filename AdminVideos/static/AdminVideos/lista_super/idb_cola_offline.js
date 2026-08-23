// IndexedDB - Cola Offline (Lista Súper)
// Guarda el último estado por item de pantry (tipo + id).

const DB_NAME = "lista_super_offline";
const STORE = "cola_por_item";
const LEGACY_STORE = "cola_por_ingrediente";
const DB_VER = 3;

function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(
      DB_NAME,
      DB_VER
    );

    request.onupgradeneeded = () => {
      const db = request.result;

      let newStore;

      if (!db.objectStoreNames.contains(STORE)) {
        newStore = db.createObjectStore(
          STORE,
          { keyPath: "item_key" }
        );
      } else {
        newStore =
          request.transaction.objectStore(STORE);
      }

      // Migramos cualquier toggle pendiente de la cola vieja.
      if (
        db.objectStoreNames.contains(LEGACY_STORE)
      ) {
        const legacyStore =
          request.transaction.objectStore(
            LEGACY_STORE
          );

        const cursorRequest =
          legacyStore.openCursor();

        cursorRequest.onsuccess = () => {
          const cursor = cursorRequest.result;

          if (!cursor) return;

          const old = cursor.value || {};
          const itemId =
            old.item_id ?? old.ingrediente_id;

          if (itemId !== undefined && itemId !== null) {
            newStore.put({
              ...old,
              item_type:
                old.item_type || "ingrediente",
              item_id: itemId,
              item_key:
                (old.item_type || "ingrediente") +
                ":" +
                itemId,
            });
          }

          cursor.continue();
        };
      }
    };

    request.onsuccess = () =>
      resolve(request.result);

    request.onerror = () =>
      reject(request.error);
  });
}

export async function colaGuardarEstadoFinal(op) {
  const db = await openDB();

  const itemType =
    op.item_type || "ingrediente";

  const itemId =
    op.item_id ?? op.ingrediente_id;

  const normalized = {
    ...op,
    item_type: itemType,
    item_id: itemId,
    item_key: itemType + ":" + itemId,
  };

  return new Promise((resolve, reject) => {
    const tx = db.transaction(
      STORE,
      "readwrite"
    );

    tx.objectStore(STORE).put(normalized);

    tx.oncomplete = () => resolve(true);
    tx.onerror = () => reject(tx.error);
  });
}

export async function colaLeerTodo() {
  const db = await openDB();

  return new Promise((resolve, reject) => {
    const tx = db.transaction(
      STORE,
      "readonly"
    );

    const request =
      tx.objectStore(STORE).getAll();

    request.onsuccess = () =>
      resolve(request.result || []);

    request.onerror = () =>
      reject(request.error);
  });
}

export async function colaLimpiarTodo() {
  const db = await openDB();

  return new Promise((resolve, reject) => {
    const tx = db.transaction(
      STORE,
      "readwrite"
    );

    tx.objectStore(STORE).clear();

    tx.oncomplete = () => resolve(true);
    tx.onerror = () => reject(tx.error);
  });
}
