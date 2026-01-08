from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import MenuItem

@receiver(post_delete, sender=MenuItem)
def borrar_menu_dia_si_queda_sin_items(sender, instance, **kwargs):
    menu = getattr(instance, "menu", None)
    if not menu:
        return

    # Si aún quedan items (plato o lugar), NO borrar
    if menu.items.exists():
        return

    # Si no queda ningún item, borrar el día
    menu.delete()
