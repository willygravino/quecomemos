"""
§31-reformulado: servicios de slots semanales.

- PRESETS: catálogo fijo de filtros pre-armados (D2=A, no editables por usuario).
- filtrar_platos_por_criterio: aplica un criterio JSON a un QuerySet de Plato.
"""
from __future__ import annotations

from typing import Optional

from django.db.models import Q, QuerySet

from AdminVideos.models import Plato


PRESETS = {
    "carne_roja":   {"label": "Carne roja",     "criterio": {"subtipo_carta": ["carnes_rojas"]}},
    "aves":         {"label": "Aves",           "criterio": {"subtipo_carta": ["aves"]}},
    "cerdo":        {"label": "Cerdo",          "criterio": {"subtipo_carta": ["cerdo"]}},
    "pescado":      {"label": "Pescado",        "criterio": {"subtipo_carta": ["pescados"]}},
    "pasta":        {"label": "Pasta",          "criterio": {"subtipo_carta": ["pastas"]}},
    "vegetariano":  {"label": "Vegetariano",    "criterio": {"subtipo_carta": ["vegetarianos"]}},
    "rapido":       {"label": "Rápido",         "criterio": {"elaboracion_max": 30, "coccion_max": 20}},
    "guarnicion":   {"label": "Guarnición",     "criterio": {"tipos": ["Guarnicion"]}},
    "postre":       {"label": "Postre",         "criterio": {"tipos": ["Postre"]}},
}


def criterio_desde_preset(preset: str) -> dict:
    entry = PRESETS.get(preset)
    return dict(entry["criterio"]) if entry else {}


def filtrar_platos_por_criterio(criterio, platos_qs=None):
    if platos_qs is None:
        platos_qs = Plato.objects.all()
    if not criterio:
        return platos_qs

    qs = platos_qs

    tipos = criterio.get("tipos") or []
    if tipos:
        q_tipos = Q()
        for t in tipos:
            q_tipos |= Q(tipos__icontains=t)
        qs = qs.filter(q_tipos)

    subtipos = criterio.get("subtipo_carta") or []
    if subtipos:
        qs = qs.filter(subtipo_carta__in=subtipos)

    categorias = criterio.get("categoria") or []
    if categorias:
        qs = qs.filter(categoria__in=categorias)

    medios = criterio.get("medios") or []
    if medios:
        qs = qs.filter(medios__in=medios)

    estacionalidades = criterio.get("estacionalidad") or []
    if estacionalidades:
        qs = qs.filter(estacionalidad__in=estacionalidades)

    elab_max = criterio.get("elaboracion_max")
    if elab_max is not None:
        qs = qs.filter(elaboracion__isnull=False, elaboracion__lte=elab_max)

    cocc_max = criterio.get("coccion_max")
    if cocc_max is not None:
        qs = qs.filter(coccion__isnull=False, coccion__lte=cocc_max)

    return qs
