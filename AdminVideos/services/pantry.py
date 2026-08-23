from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Dict, Iterable, List, Optional, Tuple

from django.db import transaction
from django.utils import timezone

from AdminVideos.models import (
    Ingrediente,
    Insumo,
    Plato,
    Profile,
    ProfileIngrediente,
    ProfileInsumo,
)


PANTRY_INGREDIENTE = "ingrediente"
PANTRY_INSUMO = "insumo"
PANTRY_TIPOS = {PANTRY_INGREDIENTE, PANTRY_INSUMO}


@dataclass(frozen=True)
class PantrySaveResult:
    ok: bool
    error: Optional[str] = None
    ing_id: Optional[int] = None
    item_type: Optional[str] = None
    item_id: Optional[int] = None


def normalize_pantry_type(value: Optional[str]) -> Optional[str]:
    value = (value or "").strip().lower()
    return value if value in PANTRY_TIPOS else None


def pantry_key(item_type: str, item_id: int) -> str:
    return f"{item_type}-{int(item_id)}"


def decorate_pantry_item(item: dict, item_type: str, item_id: int) -> dict:
    item["pantry_type"] = item_type
    item["pantry_id"] = int(item_id)
    item["pantry_key"] = pantry_key(item_type, item_id)
    return item


def _pantry_config(item_type: str):
    if item_type == PANTRY_INGREDIENTE:
        return Ingrediente, ProfileIngrediente, "ingrediente_id"
    if item_type == PANTRY_INSUMO:
        return Insumo, ProfileInsumo, "insumo_id"
    raise ValueError("Tipo de pantry inválido")


def pantry_estado(record) -> str:
    if record is None or record.tengo is False:
        return "no-tengo"

    if (
        record.last_bought_at
        and record.last_bought_at >= timezone.now() - timedelta(hours=3)
    ):
        return "recien-comprado"

    return "tengo"


@transaction.atomic
def persist_profile_pantry_from_post(
    *,
    perfil: Profile,
    post,
) -> PantrySaveResult:
    item_type = normalize_pantry_type(post.get("pantry_item_type"))
    item_id = post.get("pantry_item_id")
    checked = post.get("pantry_item_checked")

    comentario_present = "pantry_comment" in post
    comentario = (post.get("pantry_comment") or "").strip()

    # Compatibilidad con el protocolo histórico de Ingredientes.
    if item_type is None:
        item_type = PANTRY_INGREDIENTE

    if not item_id:
        item_id = post.get("toggle_ing_id") or post.get("comment_ing_id")

    if checked is None:
        checked = post.get("toggle_ing_checked")

    if not (item_id and str(item_id).isdigit()):
        return PantrySaveResult(
            ok=False,
            error="item_id inválido",
            item_type=item_type,
        )

    item_id_int = int(item_id)
    catalog_model, state_model, fk_name = _pantry_config(item_type)

    if not catalog_model.objects.filter(pk=item_id_int).exists():
        return PantrySaveResult(
            ok=False,
            error=f"{item_type.capitalize()} no existe",
            ing_id=(
                item_id_int
                if item_type == PANTRY_INGREDIENTE
                else None
            ),
            item_type=item_type,
            item_id=item_id_int,
        )

    if not comentario_present and item_type == PANTRY_INGREDIENTE:
        legacy_key = f"comentario_{item_id_int}"
        comentario_present = legacy_key in post
        if comentario_present:
            comentario = (post.get(legacy_key) or "").strip()

    existing = (
        state_model.objects
        .filter(profile=perfil, **{fk_name: item_id_int})
        .only("tengo", "comentario")
        .first()
    )

    existing_tengo = existing.tengo if existing else None
    existing_comentario = (
        (existing.comentario or "").strip()
        if existing
        else ""
    )

    defaults = {}

    # Pantalla normal:
    # checked=1 => necesito comprar => tengo=False
    # checked=0 => lo tengo => tengo=True
    if checked in ("0", "1"):
        tengo = checked == "0"
        defaults["tengo"] = tengo
        if tengo:
            defaults["last_bought_at"] = timezone.now()

    if comentario_present:
        defaults["comentario"] = comentario

    final_tengo = defaults.get("tengo", existing_tengo)
    final_comentario = defaults.get(
        "comentario",
        existing_comentario,
    )

    # Default de negocio = no tengo y sin comentario.
    # No necesitamos guardar una fila para ese estado.
    if final_tengo in (False, None) and final_comentario == "":
        state_model.objects.filter(
            profile=perfil,
            **{fk_name: item_id_int},
        ).delete()

        return PantrySaveResult(
            ok=True,
            ing_id=(
                item_id_int
                if item_type == PANTRY_INGREDIENTE
                else None
            ),
            item_type=item_type,
            item_id=item_id_int,
        )

    state_model.objects.update_or_create(
        profile=perfil,
        **{fk_name: item_id_int},
        defaults=defaults,
    )

    return PantrySaveResult(
        ok=True,
        ing_id=(
            item_id_int
            if item_type == PANTRY_INGREDIENTE
            else None
        ),
        item_type=item_type,
        item_id=item_id_int,
    )


def persist_profile_ingrediente_from_post(
    *,
    perfil: Profile,
    post,
) -> PantrySaveResult:
    # Wrapper para llamadas históricas.
    return persist_profile_pantry_from_post(
        perfil=perfil,
        post=post,
    )


def get_pantry_map(
    *,
    perfil: Profile,
    ing_ids: List[int],
    only_fields: Tuple[str, ...] = (),
) -> Dict[int, ProfileIngrediente]:
    qs = ProfileIngrediente.objects.filter(
        profile=perfil,
        ingrediente_id__in=ing_ids,
    )
    if only_fields:
        qs = qs.only(*only_fields)
    return {p.ingrediente_id: p for p in qs}


def get_insumo_pantry_map(
    *,
    perfil: Profile,
    insumo_ids: Iterable[int],
    only_fields: Tuple[str, ...] = (),
) -> Dict[int, ProfileInsumo]:
    ids = list(
        {
            int(item_id)
            for item_id in insumo_ids
            if item_id is not None
        }
    )

    qs = ProfileInsumo.objects.filter(
        profile=perfil,
        insumo_id__in=ids,
    )
    if only_fields:
        qs = qs.only(*only_fields)

    return {p.insumo_id: p for p in qs}


def build_insumo_pantry_items(
    *,
    perfil: Profile,
    plato_ids: Iterable[int],
    needed_by_map: Optional[dict] = None,
    hide_have: bool = False,
) -> List[dict]:
    ids_platos = list(
        {
            int(plato_id)
            for plato_id in plato_ids
            if plato_id is not None
        }
    )

    if not ids_platos:
        return []

    needed_by_map = needed_by_map or {}

    platos = (
        Plato.objects
        .filter(pk__in=ids_platos)
        .only("id")
        .prefetch_related("insumos")
    )

    agregados = {}

    for plato in platos:
        needed_by = needed_by_map.get(plato.pk)

        for insumo in plato.insumos.all():
            data = agregados.get(insumo.pk)

            if data is None:
                data = {
                    "insumo": insumo,
                    "needed_by": needed_by,
                    "usos": [],
                }
                agregados[insumo.pk] = data

            if (
                needed_by
                and (
                    data["needed_by"] is None
                    or needed_by < data["needed_by"]
                )
            ):
                data["needed_by"] = needed_by

            data["usos"].append(
                {
                    "plato_id": plato.pk,
                    "fecha": needed_by,
                }
            )

    pantry_map = get_insumo_pantry_map(
        perfil=perfil,
        insumo_ids=agregados.keys(),
        only_fields=(
            "insumo_id",
            "tengo",
            "comentario",
            "last_bought_at",
            "updated_at",
        ),
    )

    items = []

    for insumo_id, data in agregados.items():
        state = pantry_map.get(insumo_id)
        estado = pantry_estado(state)

        if hide_have and estado == "tengo":
            continue

        item = {
            # Compatibilidad estructural con templates existentes.
            "ingrediente_id": None,
            "insumo_id": insumo_id,
            "nombre": data["insumo"].nombre,
            "rubro": "Insumos",
            "tipo": "insumos",
            "detalle": "",
            "estado": estado,
            "a_comprar": estado == "no-tengo",
            "comentario": (
                (state.comentario or "")
                if state
                else ""
            ),
            "needed_by": data["needed_by"],
            "cantidades": [],
            "usos": data["usos"],
        }

        decorate_pantry_item(
            item,
            PANTRY_INSUMO,
            insumo_id,
        )
        items.append(item)

    sort_items_by_name(items)
    return items


@transaction.atomic
def set_pantry_have_state(
    *,
    perfil: Profile,
    item_type: str,
    item_id: int,
    tengo: bool,
) -> PantrySaveResult:
    item_type = normalize_pantry_type(item_type)

    if item_type is None:
        return PantrySaveResult(
            ok=False,
            error="Tipo de pantry inválido",
        )

    try:
        item_id = int(item_id)
    except (TypeError, ValueError):
        return PantrySaveResult(
            ok=False,
            error="item_id inválido",
            item_type=item_type,
        )

    catalog_model, state_model, fk_name = _pantry_config(item_type)

    if not catalog_model.objects.filter(pk=item_id).exists():
        return PantrySaveResult(
            ok=False,
            error=f"{item_type.capitalize()} no existe",
            item_type=item_type,
            item_id=item_id,
        )

    existing = (
        state_model.objects
        .filter(profile=perfil, **{fk_name: item_id})
        .only("comentario")
        .first()
    )
    comentario = (
        (existing.comentario or "").strip()
        if existing
        else ""
    )

    if tengo:
        state_model.objects.update_or_create(
            profile=perfil,
            **{fk_name: item_id},
            defaults={
                "tengo": True,
                "last_bought_at": timezone.now(),
            },
        )

        return PantrySaveResult(
            ok=True,
            ing_id=(
                item_id
                if item_type == PANTRY_INGREDIENTE
                else None
            ),
            item_type=item_type,
            item_id=item_id,
        )

    if comentario == "":
        state_model.objects.filter(
            profile=perfil,
            **{fk_name: item_id},
        ).delete()
    else:
        state_model.objects.update_or_create(
            profile=perfil,
            **{fk_name: item_id},
            defaults={"tengo": False},
        )

    return PantrySaveResult(
        ok=True,
        ing_id=(
            item_id
            if item_type == PANTRY_INGREDIENTE
            else None
        ),
        item_type=item_type,
        item_id=item_id,
    )


def sort_items_by_name(items: List[dict]) -> None:
    items.sort(
        key=lambda item: (item.get("nombre") or "").casefold()
    )
