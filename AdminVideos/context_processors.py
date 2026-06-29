from django.utils import timezone

from AdminVideos.models import MenuItem


def lista_compras_global(request):
    user = getattr(request, "user", None)

    hay_lista_de_compras = False

    if user and user.is_authenticated:
        hay_lista_de_compras = (
            MenuItem.objects
            .filter(
                menu__propietario=user,
                menu__fecha__gte=timezone.localdate(),
                plato__isnull=False,
            )
            .exists()
        )

    return {
        "hay_lista_de_compras": hay_lista_de_compras,
    }
