from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import MenuDia, MenuItem

@receiver(post_delete, sender=MenuItem)
def borrar_menu_dia_si_queda_sin_items(sender, instance, **kwargs):
    menu_id = instance.menu_id
    if not menu_id:
        return

    # Si todavía quedan items para ese menú, NO borrar el día
    if MenuItem.objects.filter(menu_id=menu_id).exists():
        return

    # Si no queda ningún item, borrar el día (por id, sin usar related manager)
    MenuDia.objects.filter(id=menu_id).delete()