from __future__ import annotations

from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme


def get_safe_return_to(
    request,
    *,
    fallback_url_name: str | None = None,
    include_referer: bool = True,
) -> str:
    """Devuelve un destino interno seguro para volver después de una acción.

    Prioridad: POST return_to -> GET return_to -> Referer opcional -> fallback.
    Nunca devuelve una URL de otro host.
    """
    candidates = [
        request.POST.get("return_to"),
        request.GET.get("return_to"),
    ]

    if include_referer:
        candidates.append(request.META.get("HTTP_REFERER"))

    for candidate in candidates:
        candidate = (candidate or "").strip()
        if not candidate:
            continue

        if url_has_allowed_host_and_scheme(
            candidate,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return candidate

    if fallback_url_name:
        return reverse(fallback_url_name)

    return ""
