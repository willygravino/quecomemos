"""§31-reformulado: filtros para acceder a slots_por_comida desde templates."""
from django import template

register = template.Library()


@register.filter
def get_dia(slots_por_comida, fecha):
    """slots_por_comida[fecha] o {} si no existe."""
    if not isinstance(slots_por_comida, dict):
        return {}
    return slots_por_comida.get(fecha) or {}


@register.filter
def get_momento(slots_dia, momento):
    """slots_dia[momento] o [] si no existe o no es lista."""
    if not isinstance(slots_dia, dict):
        return []
    val = slots_dia.get(momento)
    return val if isinstance(val, list) else []

@register.filter
def get_nota_programada(notas_dia, momento):
    """Indica si hay una nota que cuenta como plato programado en la comida."""
    if not isinstance(notas_dia, dict):
        return False
    return bool(notas_dia.get(momento, False))
