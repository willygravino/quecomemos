// Sync Offline - Lista Súper
// Cola tipada: ingrediente:ID / insumo:ID.

import {
  colaGuardarEstadoFinal,
  colaLeerTodo,
  colaLimpiarTodo,
} from "./idb_cola_offline.js";

async function enviarToggle(
  API,
  itemType,
  itemId,
  checked
) {
  const response = await fetch(API, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      item_type: itemType,
      item_id: itemId,
      checked,
    }),
  });

  if (!response.ok) {
    throw new Error("POST no ok");
  }
}

function normalizarArgs(
  itemTypeOrId,
  itemIdOrChecked,
  maybeChecked
) {
  // Firma histórica:
  // postToggleOfflineFirst(API, ingrediente_id, checked)
  if (maybeChecked === undefined) {
    return {
      item_type: "ingrediente",
      item_id: itemTypeOrId,
      checked: itemIdOrChecked,
    };
  }

  return {
    item_type: itemTypeOrId,
    item_id: itemIdOrChecked,
    checked: maybeChecked,
  };
}

export async function postToggleOfflineFirst(
  API,
  itemTypeOrId,
  itemIdOrChecked,
  maybeChecked
) {
  const operation = normalizarArgs(
    itemTypeOrId,
    itemIdOrChecked,
    maybeChecked
  );

  try {
    await enviarToggle(
      API,
      operation.item_type,
      operation.item_id,
      operation.checked
    );

    return {
      ok: true,
      queued: false,
    };
  } catch (error) {
    await colaGuardarEstadoFinal({
      ...operation,
      client_ts: new Date().toISOString(),
    });

    if (!navigator.onLine) {
      console.log(
        "📌 Sin internet: guardado para sincronizar luego."
      );
    }

    return {
      ok: false,
      queued: true,
    };
  }
}

let syncEnCurso = false;

export async function syncPendientes(API) {
  if (syncEnCurso) return;
  if (!navigator.onLine) return;

  syncEnCurso = true;

  try {
    const operations = await colaLeerTodo();

    if (!operations.length) return;

    for (const operation of operations) {
      const itemType =
        operation.item_type || "ingrediente";

      const itemId =
        operation.item_id ??
        operation.ingrediente_id;

      await enviarToggle(
        API,
        itemType,
        itemId,
        operation.checked
      );
    }

    await colaLimpiarTodo();
  } finally {
    syncEnCurso = false;
  }
}
