"""
§31-reformulado: servicios de slots semanales.

- PRESETS: catálogo fijo de filtros pre-armados (D2=A, no editables por usuario).
- filtrar_platos_por_criterio: aplica un criterio JSON a un QuerySet de Plato.
"""
from __future__ import annotations

from typing import Optional

from django.db.models import Q, QuerySet

from AdminVideos.models import Plato, SUBTIPO_CARTA_CHOICES


PRESETS = {
    "carne_roja":   {"label": "Carne roja",     "criterio": {"subtipo_carta": ["carnes_rojas"]}},
    "aves":         {"label": "Aves",           "criterio": {"subtipo_carta": ["aves"]}},
    "cerdo":        {"label": "Cerdo",          "criterio": {"subtipo_carta": ["cerdo"]}},
    "pescado":      {"label": "Pescado",        "criterio": {"subtipo_carta": ["pescados"]}},
    "pasta":        {"label": "Pasta",          "criterio": {"subtipo_carta": ["pastas"]}},
    "vegetariano":  {"label": "Vegetariano",    "criterio": {"subtipo_carta": ["vegetarianos"]}},
    "rapido":       {"label": "Rápido",         "criterio": {"elaboracion_max": 30, "coccion_max": 30}},
    "guarnicion":   {"label": "Guarnición",     "criterio": {"tipos": ["Guarnicion"]}},
    "postre":       {"label": "Postre",         "criterio": {"tipos": ["Postre"]}},
}

# §41: tipos filtrables en el modal de slot
TIPOS_SLOT_CHOICES = [
    ("Principal", "Principal"),
    ("Guarnicion", "Guarnición"),
    ("Entrada", "Entrada"),
    ("Picada", "Picada"),
    ("Ingrediente de picada", "Ingrediente de picada"),
    ("Dip", "Dip"),
    ("Salsa", "Salsa"),
    ("Postre", "Postre"),
    ("Torta", "Torta"),
    ("Trago", "Trago"),
]

# Subtipos de carta sin el vacío inicial
SUBTIPO_SLOT_CHOICES = [(k, v) for k, v in SUBTIPO_CARTA_CHOICES if k]

# §42: opciones de ligereza para el modal (sin la opción vacía)
# §44: en el filtro de slot solo se ofrece "Liviano" (nadie busca "pesado"
# para programar). El form de plato sigue con 3 valores (para clasificar).
LIGEREZA_SLOT_CHOICES = [
    ("liviano", "Liviano"),
]

# Labels completos para renderizar slots legacy con "medio"/"pesado"
LIGEREZA_LABELS = {
    "liviano": "Liviano",
    "medio": "Mediano",
    "pesado": "Pesado",
}

# §44: categorías filtrables en el slot (sin "Ambos": es "aplica a las dos",
# no una categoría a buscar)
SLOT_CATEGORIA_CHOICES = [
    ("Cotidiano", "Cotidiano"),
    ("Especial", "Especial"),
]



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
        # NULL se trata como 0 (un plato sin dato de elaboración se considera rápido)
        qs = qs.filter(Q(elaboracion__isnull=True) | Q(elaboracion__lte=elab_max))

    cocc_max = criterio.get("coccion_max")
    if cocc_max is not None:
        # NULL se trata como 0 (un plato sin dato de cocción se considera rápido)
        qs = qs.filter(Q(coccion__isnull=True) | Q(coccion__lte=cocc_max))

    ligereza = criterio.get("ligereza") or []
    if ligereza:
        qs = qs.filter(ligereza__in=ligereza)

    return qs


def label_preset(preset: str) -> str:
    """Devuelve el label visible del preset. 'Personalizado' si preset vacío."""
    if not preset:
        return "Personalizado"
    entry = PRESETS.get(preset)
    return entry["label"] if entry else preset


def label_criterio(criterio: dict) -> str:
    '''Genera label dinámico desde un criterio JSON.
    Orden: tipos · subtipo · ligereza · medios · Rápido
    Ej: {'tipos': ['Principal'], 'medios': ['Sin coccion']}
        -> 'Principal · Sin cocción'
    '''
    if not criterio:
        return "Personalizado"

    parts = []
    tipo_labels = dict(TIPOS_SLOT_CHOICES)
    subtipo_labels = dict(SUBTIPO_CARTA_CHOICES)
    medios_labels = dict(Plato.MEDIOS_CHOICES)

    for t in criterio.get("tipos") or []:
        parts.append(tipo_labels.get(t, t))

    for s_ in criterio.get("subtipo_carta") or []:
        parts.append(subtipo_labels.get(s_, s_))

    categoria_labels = dict(Plato.CATEGORIA_CHOICES)
    for cat in criterio.get("categoria") or []:
        parts.append(categoria_labels.get(cat, cat))

    for lig in criterio.get("ligereza") or []:
        parts.append(LIGEREZA_LABELS.get(lig, lig))

    for med in criterio.get("medios") or []:
        parts.append(medios_labels.get(med, med))

    if criterio.get("elaboracion_max") or criterio.get("coccion_max"):
        parts.append("Rápido")

    return " · ".join(parts) if parts else "Personalizado"
