// Sync Offline - Lista Súper
// Cola por ingrediente: manda SOLO el estado final de cada uno.

import { colaGuardarEstadoFinal, colaLeerTodo, colaLimpiarTodo } from "./idb_cola_offline.js";

async function enviarToggle(API, ingrediente_id, checked) {
  const res = await fetch(API, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ingrediente_id, checked }),
  });
  if (!res.ok) throw new Error("POST no ok");
}

// Offline-first: si falla => guarda estado final por ingrediente
export async function postToggleOfflineFirst(API, ingrediente_id, checked) {
  try {
    await enviarToggle(API, ingrediente_id, checked);
    return { ok: true, queued: false };
  } catch (e) {
    await colaGuardarEstadoFinal({
      ingrediente_id,
      checked,
      client_ts: new Date().toISOString(),
    });
    return { ok: false, queued: true };
  }
}

let syncEnCurso = false;

export async function syncPendientes(API) {
  if (syncEnCurso) return;
  if (!navigator.onLine) return;

  syncEnCurso = true;
  try {
    const ops = await colaLeerTodo();
    if (!ops.length) return;

    // Manda solo el último estado de cada ingrediente
    for (const op of ops) {
      await enviarToggle(API, op.ingrediente_id, op.checked);
    }

    // Si todo salió bien, limpiamos todo
    await colaLimpiarTodo();
  } finally {
    syncEnCurso = false;
  }
}
