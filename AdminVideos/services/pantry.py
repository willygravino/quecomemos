from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple

from django.db import transaction
from django.utils import timezone

from AdminVideos.models import Ingrediente, Profile, ProfileIngrediente  # ajustá si tu app se llama distinto


@dataclass(frozen=True)
class PantrySaveResult:
    ok: bool
    error: Optional[str] = None
    ing_id: Optional[int] = None


@transaction.atomic
def persist_profile_ingrediente_from_post(*, perfil: Profile, post) -> PantrySaveResult:
    """
    Unifica lógica de POST 'ingredientes':
    - toggle (checked "1" => necesito comprar => tengo=False)
    - comentario
    - limpieza: si finalmente queda tengo=False y comentario vacío => borrar
    - tengo=True => guardar siempre (aunque comentario vacío)
    """
    ing_id = post.get("toggle_ing_id") or post.get("comment_ing_id")
    checked = post.get("toggle_ing_checked")  # "1" / "0" / None

    if not (ing_id and str(ing_id).isdigit()):
        return PantrySaveResult(ok=False, error="ing_id inválido")

    ing_id_int = int(ing_id)

    if not Ingrediente.objects.filter(pk=ing_id_int).exists():
        return PantrySaveResult(ok=False, error="Ingrediente no existe", ing_id=ing_id_int)

    comentario_key = f"comentario_{ing_id_int}"
    comentario = (post.get(comentario_key) or "").strip()

    # 👇 IMPORTANTe: estado actual si el POST viene solo con comentario
    existing = (
        ProfileIngrediente.objects
        .filter(profile=perfil, ingrediente_id=ing_id_int)
        .only("tengo")
        .first()
    )
    existing_tengo = existing.tengo if existing else None

    defaults = {}

    if checked in ("0", "1"):
        if checked == "1":
            defaults["tengo"] = False
        else:
            defaults["tengo"] = True
            defaults["last_bought_at"] = timezone.now()

        defaults["comentario"] = comentario
    else:
        # solo comentario
        defaults["comentario"] = comentario

    # ✅ Limpieza correcta:
    # - Si el POST define tengo=False, usamos eso
    # - Si no lo define (solo comentario), usamos el estado existente
    final_tengo = defaults.get("tengo", existing_tengo)

    if final_tengo is False and defaults.get("comentario", "") == "":
        ProfileIngrediente.objects.filter(profile=perfil, ingrediente_id=ing_id_int).delete()
        return PantrySaveResult(ok=True, ing_id=ing_id_int)

    ProfileIngrediente.objects.update_or_create(
        profile=perfil,
        ingrediente_id=ing_id_int,
        defaults=defaults,
    )

    return PantrySaveResult(ok=True, ing_id=ing_id_int)


def get_pantry_map(
    *,
    perfil: Profile,
    ing_ids: List[int],
    only_fields: Tuple[str, ...] = (),
) -> Dict[int, ProfileIngrediente]:
    """
    Devuelve {ingrediente_id: ProfileIngrediente} para un perfil.
    """
    qs = ProfileIngrediente.objects.filter(profile=perfil, ingrediente_id__in=ing_ids)
    if only_fields:
        qs = qs.only(*only_fields)
    return {p.ingrediente_id: p for p in qs}


def sort_items_by_name(items: List[dict]) -> None:
    """
    Orden in-place por 'nombre' (case-insensitive).
    """
    items.sort(key=lambda i: (i.get("nombre") or "").casefold())
