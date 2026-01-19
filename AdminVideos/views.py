from collections import defaultdict
from django.db.models import Count
import json
import locale
from copy import deepcopy
from django.contrib.auth import get_user_model
import unicodedata
from django.core.signing import dumps as signed_dumps
from django.core.signing import loads as signed_loads, BadSignature
from django import forms
from django.contrib import messages  # Para mostrar mensajes al usuario
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from AdminVideos import models
from AdminVideos.models import HistoricoDia, HistoricoItem, Ingrediente, IngredienteEnPlato, IngredienteEstado, Lugar, MenuDia, MenuItem, Plato, Profile, Mensaje, ProfileIngrediente
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string   # ✅ ← ESTA ES LA CLAVE
from django.http import Http404, HttpRequest, JsonResponse
from django.urls import reverse, reverse_lazy
from django.contrib.auth.forms import UserCreationForm
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from datetime import datetime, timedelta
from .forms import IngredienteEnPlatoFormSet, LugarForm, PlatoFilterForm, PlatoForm, CustomAuthenticationForm
from datetime import date, datetime
from django.contrib.auth.models import User  # Asegúrate de importar el modelo User
from django.db.models import Q, Subquery, OuterRef, Prefetch, Min
import random
from django.shortcuts import redirect, reverse
from django.shortcuts import redirect
from django.urls import reverse
import datetime
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.db import transaction
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.core.exceptions import PermissionDenied




# def api_ingredientes(request):
#     q = request.GET.get('q', '')
#     ingredientes = Ingrediente.objects.filter(nombre__icontains=q).order_by('nombre')[:20]  # límite de resultados
#     data = [{"id": ing.id, "nombre": ing.nombre} for ing in ingredientes]
#     return JsonResponse(data, safe=False)


# def plato_ingredientes(request: HttpRequest, pk: int):
#     plato = get_object_or_404(Plato, pk=pk)

#     # Ajustá esto al related_name real:
#     # Ej: plato.ingredientes_en_plato.all()
#     ingredientes_qs = plato.ingredientes_en_plato.select_related("ingrediente").all()

#     ctx = {
#         "plato": plato,
#         "ingredientes": ingredientes_qs,
#         "share_url": request.build_absolute_uri(),
#     }

#     # detectar fetch/AJAX (compatible con tu estilo actual)
#     is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

#     if is_ajax:
#         return render(request, "AdminVideos/_modal_plato_ingredientes.html", ctx)


#     # si alguien abre el link desde WhatsApp
#     return render(request, "AdminVideos/plato_ingredientes_page.html", ctx)




@login_required
def plato_ingredientes(request: HttpRequest, pk: int):
    plato = get_object_or_404(Plato, pk=pk)
    perfil = get_object_or_404(Profile, user=request.user)

    ingredientes_qs = (
        plato.ingredientes_en_plato
        .select_related("ingrediente")
        .all()
    )

    ing_ids = list(ingredientes_qs.values_list("ingrediente_id", flat=True))

    pantry_qs = (
        ProfileIngrediente.objects
        .filter(profile=perfil, ingrediente_id__in=ing_ids)
        .only("ingrediente_id", "tengo", "comentario", "last_bought_at")
    )
    pantry_map = {pi.ingrediente_id: pi for pi in pantry_qs}

    # =========================
    # Helpers
    # =========================
    def _norm(s: str) -> str:
        return " ".join((s or "").strip().lower().split())

    # =========================
    # POST: 2 modos
    # 1) Form POST (tu modal viejo): guarda checks + comentarios en ProfileIngrediente (igual que antes)
    # 2) JSON POST (tu fetch nuevo): guarda comentario en IngredienteEstado
    # =========================
    if request.method == "POST":
        content_type = (request.headers.get("Content-Type") or "").lower()

        # ---------- (2) JSON POST (fetch): comentario ----------
        if "application/json" in content_type:
            try:
                payload = json.loads(request.body.decode("utf-8"))
            except Exception:
                return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

            nombre = (payload.get("nombre") or "").strip()
            comentario = payload.get("comentario", None)

            if not nombre:
                return JsonResponse({"ok": False, "error": "nombre requerido"}, status=400)

            # si viene comentario, lo persistimos
            if comentario is not None:
                obj, _ = IngredienteEstado.objects.update_or_create(
                    user=request.user,
                    nombre=_norm(nombre),
                    defaults={"comentario": (comentario or "").strip()},
                )
                return JsonResponse({"ok": True, "nombre": obj.nombre, "comentario": obj.comentario})

            # si no vino comentario, no hacemos nada acá (para no romper)
            return JsonResponse({"ok": True})

        # ---------- (1) Form POST (HTML): tu lógica original ----------
        now = timezone.now()

        # checked => "no-tengo" => aparece en POST como to_buy_id
        to_buy_ids = set(
            int(x) for x in request.POST.getlist("ingrediente_a_comprar_id") if x.isdigit()
        )

        # persistimos SOLO los ingredientes del plato
        for iep in ingredientes_qs:
            ing_id = iep.ingrediente_id
            want_tengo = (ing_id not in to_buy_ids)  # no marcado => lo tengo

            pi = pantry_map.get(ing_id)
            if not pi:
                pi = ProfileIngrediente(profile=perfil, ingrediente_id=ing_id)
                pi.tengo = want_tengo
            else:
                # transición no-tengo -> tengo => recién comprado
                if (pi.tengo is False) and (want_tengo is True):
                    pi.last_bought_at = now
                pi.tengo = want_tengo

            # comentario (mismo naming que en lista de compras)
            comentario_key = f"comentario_{ing_id}"
            if comentario_key in request.POST:
                pi.comentario = (request.POST.get(comentario_key) or "").strip()

            pi.save()

        return JsonResponse({"success": True})

    # =========================
    # GET: preparar items para render
    # =========================
    # Traemos comentarios “nuevos” desde IngredienteEstado (si existen) para mostrarlos.
    nombres_norm = []
    ingid_to_nombre_norm = {}

    for iep in ingredientes_qs:
        n = _norm(iep.ingrediente.nombre)
        nombres_norm.append(n)
        ingid_to_nombre_norm[iep.ingrediente_id] = n

    ie_qs = IngredienteEstado.objects.filter(user=request.user, nombre__in=nombres_norm).only("nombre", "comentario", "estado")
    ie_map = {ie.nombre: ie for ie in ie_qs}

    items = []
    for iep in ingredientes_qs:
        ing = iep.ingrediente
        pi = pantry_map.get(iep.ingrediente_id)

        # misma convención: checked = "no-tengo" (esto queda igual)
        estado = "tengo"
        comentario = ""
        if pi:
            comentario = pi.comentario or ""
            if pi.tengo is False:
                estado = "no-tengo"

        # ✅ si hay comentario en IngredienteEstado, lo priorizamos para que “se vea” lo que guardaste por fetch
        key = ingid_to_nombre_norm.get(iep.ingrediente_id)
        ie = ie_map.get(key) if key else None
        if ie and (ie.comentario is not None) and (ie.comentario.strip() != ""):
            comentario = ie.comentario

        items.append({
            "ingrediente_id": iep.ingrediente_id,
            "nombre": ing.nombre,
            "cantidad": iep.cantidad,
            "unidad": iep.unidad,
            "estado": estado,
            "comentario": comentario,
        })

    if not perfil.share_token:
        perfil.ensure_share_token()

    ctx = {
        "plato": plato,
        "items": items,
        "api_token": perfil.share_token,
        "share_url": request.build_absolute_uri(),
    }

    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    if is_ajax:
        return render(request, "AdminVideos/_modal_plato_ingredientes.html", ctx)

    return render(request, "AdminVideos/plato_ingredientes_page.html", ctx)


@require_http_methods(["GET", "POST"])
def api_ingredientes(request):
    if request.method == "GET":
        q = (request.GET.get('q') or '').strip()
        qs = Ingrediente.objects.all()
        if q:
            qs = qs.filter(nombre__icontains=q)
        ingredientes = qs.order_by('nombre')[:50]
        data = [{"id": ing.id, "nombre": ing.nombre} for ing in ingredientes]
        return JsonResponse(data, safe=False)

    # POST: crear si no existe; si existe, devolvés el existente (UX más amable)
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "JSON inválido"}, status=400)

    nombre = (payload.get("nombre") or "").strip()
    tipo = (payload.get("tipo") or "").strip()
    detalle = (payload.get("detalle") or "").strip() or ""

    # Validaciones mínimas
    if not nombre:
        return JsonResponse({"errors": {"nombre": ["Requerido"]}}, status=400)
    if not tipo:
        return JsonResponse({"errors": {"tipo": ["Requerido"]}}, status=400)

    # Si ya existe por nombre (case-insensitive), devolvés ese ID
    existente = Ingrediente.objects.filter(nombre__iexact=nombre).first()
    if existente:
        return JsonResponse({"id": existente.id, "nombre": existente.nombre, "existed": True}, status=200)

    # Crear nuevo respetando la clean() del modelo (detalle vs tipo)
    try:
        obj = Ingrediente(nombre=nombre, tipo=tipo, detalle=detalle)
        obj.full_clean()     # ejecuta clean() + field validators
        obj.save()
    except ValidationError as e:
        return JsonResponse({"errors": e.message_dict}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"id": obj.id, "nombre": obj.nombre}, status=201)



def set_dia_activo(request):
    if request.method == "POST":
        dia = request.POST.get("dia_activo")
        if dia:
            request.session["dia_activo"] = dia
            return JsonResponse({"status": "ok"})
    return JsonResponse({"status": "error"}, status=400)


def obtener_parametros_sesion(request):

    # Recupera los parámetros de sesión y los valores de los parámetros URL.

    # Recuperar parámetros de sesión
    medios = request.session.get('medios_estable', None)
    categoria = request.session.get('categoria_estable', None)
    dificultad = request.session.get('dificultad_estable', None)
    palabra_clave = request.session.get('palabra_clave', "")

    quecomemos = request.session.get('quecomemos', None)
    misplatos = request.session.get('misplatos', "misplatos")
    # preseleccionados = request.session.get('preseleccionados', None)

    # Obtener el valor del parámetro 'tipo' desde la URL
    tipo_parametro = request.GET.get('tipopag', 'Dash')

    # # Obtener el usuario actual
    # usuario = request.user

    # Devolver las variables por separado
    return tipo_parametro, quecomemos, misplatos, medios, categoria, dificultad, palabra_clave

# class SugerenciasRandom(TemplateView):
#     template_name = 'AdminVideos/random.html'

def index(request):
    return redirect(reverse_lazy("filtro-de-platos"))

def about(request):
    return render(request, "AdminVideos/about.html")



def limpiar_none(value):
    return None if value == 'None' or value == '' else value

def agregar_plato(diccionario, clave, plato, ingredientes):
    """
    Agrega un plato al diccionario si el plato no es None.

    :param diccionario: Diccionario donde se agregará el plato.
    :param clave: Clave en el diccionario (por ejemplo, "guarnicion1").
    :param plato: Nombre del plato.
    :param ingredientes: Ingredientes del plato.
    :param elegido: Indica si el plato está elegido. Por defecto, True.
    """
    if plato is not None:
        diccionario[clave] = {
            "plato": plato,
            "ingredientes": ingredientes,
            "elegido": True
        }



@login_required
def lista_de_compras(request):
    today = date.today()
    perfil = get_object_or_404(Profile, user=request.user)

    # =====================================================
    # Menús futuros + items prefetcheados (sin adapters)
    # =====================================================
    menues = (
        MenuDia.objects
        .filter(propietario=request.user, fecha__gte=today)
        .order_by("fecha")
        .prefetch_related(
            Prefetch(
                "items",
                queryset=(
                    MenuItem.objects
                    .select_related("plato", "lugar")
                    .order_by("id")
                ),
            )
        )
    )

    # =====================================================
    # POST: guardar menú SOLO si origen == "menu"
    # =====================================================
    post_origen = request.POST.get("post_origen", "") if request.method == "POST" else ""

    # =====================================================
    # POST: guardar ingredientes SOLO si origen == "ingredientes"
    # =====================================================
    if request.method == "POST" and post_origen == "menu":
        plato_id = request.POST.get("toggle_plato_id")
        checked = request.POST.get("toggle_plato_checked") == "1"

        if plato_id and plato_id.isdigit():
            plato_id = int(plato_id)

            # aplicar a TODOS los días futuros donde aparezca ese plato
            MenuItem.objects.filter(
                menu__propietario=request.user,
                menu__fecha__gte=today,
                plato_id=plato_id,
            ).update(elegido=checked)

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True})
        
    if request.method == "POST" and post_origen == "ingredientes":
        ing_id = request.POST.get("toggle_ing_id") or request.POST.get("comment_ing_id")
        checked = request.POST.get("toggle_ing_checked")  # "1" o "0" o None

        if ing_id and ing_id.isdigit():
            ing_id = int(ing_id)

            defaults = {}

            # toggle checkbox: checked=1 => "no-tengo" => tengo=False
            if checked in ("0", "1"):
                defaults["tengo"] = (checked == "0")

            # comentario (si vino)
            comentario_key = f"comentario_{ing_id}"
            if comentario_key in request.POST:
                defaults["comentario"] = (request.POST.get(comentario_key) or "").strip()

            if defaults:
                ProfileIngrediente.objects.update_or_create(
                    profile=perfil,
                    ingrediente_id=ing_id,
                    defaults=defaults
                )

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True})



    # ⚠️ IMPORTANTE: menues estaba prefetcheado ANTES del update.
    # Rehacer el queryset para que el template vea los elegidos actualizados.
    menues = (
        MenuDia.objects
        .filter(propietario=request.user, fecha__gte=today)
        .order_by("fecha")
        .prefetch_related(
            Prefetch(
                "items",
                queryset=(
                    MenuItem.objects
                    .select_related("plato", "lugar")
                    .order_by("id")
                ),
            )
        )
    )

    # =====================================================
    # Ítems elegidos (platos) para calcular ingredientes
    # =====================================================
    items_elegidos = (
        MenuItem.objects
        .filter(menu__in=menues, plato__isnull=False, elegido=True)
        .select_related("menu", "plato")
    )

    plato_ids = list(items_elegidos.values_list("plato_id", flat=True))

    # si no hay platos elegidos
    if not plato_ids:
        token = perfil.ensure_share_token()
        share_url = request.build_absolute_uri(reverse("compartir-lista", args=[token]))
        return render(
            request,
            "AdminVideos/lista_de_compras.html",
            {
                "menues": menues,
                "items_elegidos": items_elegidos,
                "share_url": share_url,
                "shopping": {"items": [], "summary": {"total": 0, "to_buy": 0, "fresh": 0, "have": 0}},
            },
        )

    # =====================================================
    # Ingredientes relacionales usados por los platos
    # =====================================================
    ingredientes_rows = (
        IngredienteEnPlato.objects
        .filter(plato_id__in=plato_ids)
        .select_related("ingrediente", "plato")
        .only(
            "plato_id",
            "ingrediente_id",
            "cantidad",
            "unidad",
            "ingrediente__nombre",
            "ingrediente__tipo",
            "ingrediente__detalle",
        )
    )

    # fecha más cercana de uso por plato
    plato_min_fecha = {
        row["plato_id"]: row["min_fecha"]
        for row in (
            items_elegidos
            .values("plato_id")
            .annotate(min_fecha=Min("menu__fecha"))
        )
    }

    # agrupar por ingrediente
    agregados = {}
    for row in ingredientes_rows:
        if not row.ingrediente:
            continue

        ing_id = row.ingrediente.id
        needed_by = plato_min_fecha.get(row.plato_id)

        if ing_id not in agregados:
            agregados[ing_id] = {
                "ingrediente_id": ing_id,
                "nombre": row.ingrediente.nombre,
                "tipo": row.ingrediente.tipo,
                "detalle": row.ingrediente.detalle,
                "needed_by": needed_by,
                "cantidades": defaultdict(float),
                "usos": [],
            }

        if needed_by and (
            agregados[ing_id]["needed_by"] is None
            or needed_by < agregados[ing_id]["needed_by"]
        ):
            agregados[ing_id]["needed_by"] = needed_by

        if row.cantidad is not None:
            agregados[ing_id]["cantidades"][row.unidad or "-"] += float(row.cantidad)

        agregados[ing_id]["usos"].append({"plato_id": row.plato_id, "fecha": needed_by})

    # estados guardados para estos ingredientes
    pantry_qs = (
        ProfileIngrediente.objects
        .filter(profile=perfil, ingrediente_id__in=agregados.keys())
        .only("ingrediente_id", "tengo", "comentario", "last_bought_at")
    )
    pantry_map = {pi.ingrediente_id: pi for pi in pantry_qs}

   

    # =====================================================
    # reglas de estado (igual espíritu que antes + "recién comprado")
    # =====================================================
    def fresh_until(fecha_uso):
        return fecha_uso or (today + timedelta(days=7))

    def estado_final(pi, limite):
        if not pi:
            return "tengo"
        if not pi.tengo:
            return "no-tengo"
        if (
            pi.last_bought_at
            and pi.last_bought_at >= timezone.now() - timedelta(days=7)
            and today <= limite
        ):
            return "recien-comprado"
        return "tengo"

    items = []
    for ing_id, data in agregados.items():
        pi = pantry_map.get(ing_id)
        limite = fresh_until(data["needed_by"])

        items.append({
            "ingrediente_id": ing_id,
            "nombre": data["nombre"],
            "tipo": data["tipo"],
            "detalle": data["detalle"],
            "estado": estado_final(pi, limite),
            "comentario": pi.comentario if pi else "",
            "last_bought_at": pi.last_bought_at if pi else None,
            "needed_by": data["needed_by"],
            "fresh_until": limite,
            "cantidades": [{"unidad": u, "total": t} for u, t in data["cantidades"].items()],
            "usos": data["usos"],
        })

    order = {"no-tengo": 0, "recien-comprado": 1, "tengo": 2}
    items.sort(key=lambda i: (order[i["estado"]], i["nombre"].casefold()))

    token = perfil.ensure_share_token()
    share_url = request.build_absolute_uri(reverse("compartir-lista", args=[token]))

    summary = {
        "total": len(items),
        "to_buy": sum(i["estado"] == "no-tengo" for i in items),
        "fresh": sum(i["estado"] == "recien-comprado" for i in items),
        "have": sum(i["estado"] == "tengo" for i in items),
    }

    return render(
        request,
        "AdminVideos/lista_de_compras.html",
        {
            "menues": menues,                 # 👈 para render viejo sin adapters
            "items_elegidos": items_elegidos, # si lo querés para debug o lista plana
            "share_url": share_url,
            "shopping": {"items": items, "summary": summary},
        },
    )



def _get_user_by_token_or_404(token):
    perfil = get_object_or_404(Profile, share_token=str(token))
    return perfil.user, perfil



def compartir_lista(request, token):
    share_user, perfil = _get_user_by_token_or_404(token)

    today = date.today()

    # =====================================================
    # Platos elegidos (igual que tu lista nueva)
    # =====================================================
    items_elegidos = (
        MenuItem.objects
        .filter(
            menu__propietario=share_user,
            menu__fecha__gte=today,
            plato__isnull=False,
            elegido=True,
        )
        .select_related("menu", "plato")
    )

    plato_ids = list(items_elegidos.values_list("plato_id", flat=True).distinct())

    # Si no hay platos elegidos, devolvemos vacío
    if not plato_ids:
        if not perfil.share_token:
            perfil.ensure_share_token()
        return render(request, "AdminVideos/compartir_lista.html", {
            "items": [],
            "token": f"user-{perfil.pk}",
            "api_token": perfil.share_token,
        })

    # =====================================================
    # Ingredientes relacionales usados por esos platos
    # =====================================================
    ingredientes_rows = (
        IngredienteEnPlato.objects
        .filter(plato_id__in=plato_ids)
        .select_related("ingrediente")
        .only(
            "plato_id",
            "ingrediente_id",
            "cantidad",
            "unidad",
            "ingrediente__nombre",
            "ingrediente__tipo",
            "ingrediente__detalle",
        )
    )

    # fecha más cercana de uso por plato (para "needed_by")
    plato_min_fecha = {
        row["plato_id"]: row["min_fecha"]
        for row in (
            items_elegidos
            .values("plato_id")
            .annotate(min_fecha=Min("menu__fecha"))
        )
    }

    # =====================================================
    # Agregamos por ingrediente (como en lista nueva)
    # =====================================================
    agregados = {}
    for row in ingredientes_rows:
        if not row.ingrediente:
            continue

        ing_id = row.ingrediente.id
        needed_by = plato_min_fecha.get(row.plato_id)

        if ing_id not in agregados:
            agregados[ing_id] = {
                "ingrediente_id": ing_id,
                "nombre": row.ingrediente.nombre,
                "tipo": row.ingrediente.tipo,
                "detalle": row.ingrediente.detalle,
                "needed_by": needed_by,
                "cantidades": defaultdict(float),
            }

        # earliest needed_by
        if needed_by and (
            agregados[ing_id]["needed_by"] is None
            or needed_by < agregados[ing_id]["needed_by"]
        ):
            agregados[ing_id]["needed_by"] = needed_by

        if row.cantidad is not None:
            agregados[ing_id]["cantidades"][row.unidad or "-"] += float(row.cantidad)

    # =====================================================
    # Estados guardados (tengo / comentario / last_bought_at)
    # =====================================================
    pantry_qs = (
        ProfileIngrediente.objects
        .filter(profile=perfil, ingrediente_id__in=agregados.keys())
        .only("ingrediente_id", "tengo", "comentario", "last_bought_at")
    )
    pantry_map = {pi.ingrediente_id: pi for pi in pantry_qs}

    def fresh_until(fecha_uso):
        return fecha_uso or (today + timedelta(days=7))

    def estado_final(pi, limite):
        if not pi:
            return "tengo"  # o "no-tengo" si querés default comprar; pero tu lista nueva usa "tengo"
        if not pi.tengo:
            return "no-tengo"
        if (
            pi.last_bought_at
            and pi.last_bought_at >= timezone.now() - timedelta(days=7)
            and today <= limite
        ):
            return "recien-comprado"
        return "tengo"

    # =====================================================
    # Items para template compartido
    # (Yo te recomiendo mostrar TODOS, y que el template tache "fresh".
    #  Si querés, podés filtrar solo "no-tengo".)
    # =====================================================
    items = []
    for ing_id, data in agregados.items():
        pi = pantry_map.get(ing_id)
        limite = fresh_until(data["needed_by"])
        estado = estado_final(pi, limite)

        items.append({
            "ingrediente_id": ing_id,
            "nombre": data["nombre"],
            "comentario": (pi.comentario if pi else ""),
            "estado": estado,
            "last_bought_at": (pi.last_bought_at if pi else None),
            "needed_by": data["needed_by"],
        })

    # Orden como tu lista nueva
    order = {"no-tengo": 0, "recien-comprado": 1, "tengo": 2}
    items.sort(key=lambda i: (order[i["estado"]], i["nombre"].casefold()))

    # Tokens
    if not perfil.share_token:
        perfil.ensure_share_token()

    return render(request, "AdminVideos/compartir_lista.html", {
        "items": items,
        "token": f"user-{perfil.pk}",
        "api_token": perfil.share_token,
    })



# @csrf_exempt
# @require_POST
# def api_toggle_item(request, token):
#     user, perfil = _get_user_by_token_or_404(token)

#     try:
#         payload = json.loads(request.body.decode("utf-8"))
#     except Exception:
#         return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

#     checked = bool(payload.get("checked"))
#     nombre = (payload.get("nombre") or "").strip()

#     if not nombre:
#         return JsonResponse({"ok": False, "error": "nombre requerido"}, status=400)

#     # Buscamos el ingrediente por nombre (case-insensitive)
#     ingrediente = Ingrediente.objects.filter(nombre__iexact=nombre).first()
#     if not ingrediente:
#         return JsonResponse({"ok": False, "error": f"No existe Ingrediente con nombre='{nombre}'"}, status=404)

#     pi, _ = ProfileIngrediente.objects.get_or_create(
#         profile=perfil,
#         ingrediente=ingrediente,
#         defaults={"tengo": False},
#     )

#     # Convención pedida:
#     # checked => tengo (y marco last_bought_at)
#     # unchecked => no-tengo (y limpio last_bought_at)
#     if checked:
#         pi.tengo = True
#         pi.last_bought_at = timezone.now()
#     else:
#         pi.tengo = False
#         pi.last_bought_at = None

#     pi.save(update_fields=["tengo", "last_bought_at"])

#     return JsonResponse({
#         "ok": True,
#         "ingrediente_id": ingrediente.id,
#         "nombre": ingrediente.nombre,
#         "tengo": pi.tengo,
#         "last_bought_at": pi.last_bought_at.isoformat() if pi.last_bought_at else None,
#         "checked": checked,
#     })

@csrf_exempt
@require_POST
def api_toggle_item(request, token):
    user, perfil = _get_user_by_token_or_404(token)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

    def _norm(s):
        return " ".join((s or "").strip().lower().split())

    nombre = _norm(payload.get("nombre"))
    if not nombre:
        return JsonResponse({"ok": False, "error": "nombre requerido"}, status=400)

    comentario = (payload.get("comentario") or "").strip()

    defaults = {"comentario": comentario}

    # Si viene checked, actualizamos estado. Si no viene, solo comentario.
    if "checked" in payload:
        checked = bool(payload.get("checked"))

        if checked:
            defaults["estado"] = IngredienteEstado.Estado.RECIEN_COMPRADO
            defaults["estado_hasta"] = (timezone.localdate() + timedelta(days=3))
        else:
            defaults["estado"] = IngredienteEstado.Estado.NO_TENGO
            defaults["estado_hasta"] = None

    obj, _created = IngredienteEstado.objects.update_or_create(
        user=user,
        nombre=nombre,
        defaults=defaults,
    )

    return JsonResponse({
        "ok": True,
        "nombre": obj.nombre,
        "estado": obj.estado,
        "comentario": obj.comentario,
        "estado_hasta": obj.estado_hasta.isoformat() if obj.estado_hasta else None,
    })


class LugarDetail(DetailView):
    model = Lugar
    template_name = 'AdminVideos/lugar_detail.html'
    context_object_name = "lugar"

    def get_context_data(self, **kwargs):
        # Llamar al método original para obtener el contexto base
        context = super().get_context_data(**kwargs)

        # Obtener el perfil del usuario actual
        perfil = get_object_or_404(Profile, user=self.request.user)

        # Pasar la lista de amigues al contexto
        context["amigues"] = perfil.amigues  # Lista JSONField desde Profile

        return context



# @login_required
# def eliminar_lugar(request, lugar_id):
#     lugar = get_object_or_404(Lugar, id=lugar_id)

#     # Verificar si el usuario es el propietario del lugar
#     if lugar.propietario != request.user:
#         raise Http404("No tenés permiso para eliminar este lugar.")

#     # Obtener el perfil del usuario actual
#     perfil = get_object_or_404(Profile, user=request.user)

#     # Eliminar el lugar si aparece en listas personalizadas (si aplica)
#     if lugar.id in perfil.sugeridos_descartados:
#         perfil.sugeridos_descartados.remove(lugar.id)
#         perfil.save()

#     if lugar.id in perfil.sugeridos_importados:
#         perfil.sugeridos_importados.remove(lugar.id)
#         perfil.save()

#     # Eliminar el lugar de la base de datos
#     lugar.delete()

#     # Redirigir a la página que quieras (modificá este nombre si tenés otra vista)
#     return redirect('filtro-de-platos')


@login_required
def eliminar_lugar(request, lugar_id):
    lugar = get_object_or_404(Lugar, id=lugar_id)

    # 🔒 Seguridad: solo el propietario puede borrar
    if lugar.propietario != request.user:
        raise Http404("No tenés permiso para eliminar este lugar.")

    # 🔧 Desasignar de menús (MUY IMPORTANTE)
    MenuItem.objects.filter(
        lugar=lugar,
        menu__propietario=request.user
    ).delete()

    # 🗑️ Eliminar lugar
    lugar.delete()

    # 🔁 Volver al filtro respetando tipopag
    tipopag = request.GET.get("tipopag")
    url = reverse("filtro-de-platos")
    if tipopag:
        url += f"?tipopag={tipopag}"

    return redirect(url)

@login_required
def eliminar_plato(request, plato_id):
    plato = get_object_or_404(Plato, id=plato_id, propietario=request.user)

    if request.method == 'POST':
        perfil = get_object_or_404(Profile, user=request.user)

        if plato.id_original in perfil.sugeridos_descartados:
            perfil.sugeridos_descartados.remove(plato.id_original)

        if plato.id_original in perfil.sugeridos_importados:
            perfil.sugeridos_importados.remove(plato.id_original)

        perfil.save()
        plato.delete()
        return redirect('filtro-de-platos')

    # Si viene por GET, no borrar:
    from django.http import HttpResponseNotAllowed
    return HttpResponseNotAllowed(['POST'])



class LugarUpdate(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Lugar
    form_class = LugarForm
    template_name = 'AdminVideos/lugar_update.html'
    success_url = reverse_lazy("filtro-de-platos")  # O ponés donde quieras redirigir después

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Podrías agregar aquí cosas extra si quieres mostrar otros datos en el template
        return context

    def form_valid(self, form):
        # Este método se ejecuta cuando el formulario es válido
        lugar = form.save(commit=False)
        lugar.propietario = self.request.user  # Forzar que el propietario siempre sea el usuario logueado
        lugar.save()
        return redirect(self.success_url)

    def test_func(self):
        # Esto verifica que solo el propietario pueda editar su lugar
        lugar = self.get_object()
        return lugar.propietario == self.request.user






class CrearLugar(LoginRequiredMixin, CreateView):
    model = Lugar
    form_class = LugarForm
    template_name = 'AdminVideos/crearlugar_form.html'
    success_url = reverse_lazy("crear-lugar")


    def form_invalid(self, form):
        print("Errores en el formulario:", form.errors)
        return super().form_invalid(form)

    def form_valid(self, form):
        lugar = form.save(commit=False)
        lugar.propietario = self.request.user

        print("GET tipopag:", self.request.GET.get("tipopag"))
        print("POST tipopag:", self.request.POST.get("tipopag"))
        print("PATH:", self.request.get_full_path())

        # Obtener el valor del parámetro 'template' desde la URL
        template_param = self.request.GET.get('tipopag')

        if template_param == 'Delivery':
            lugar.delivery = True
        elif template_param == 'Comerafuera':
            lugar.delivery = False

        lugar.save()

        # Obtener el parámetro 'tipopag' y pasarlo en la redirección
        template_param = self.request.GET.get('tipopag')
        return redirect(reverse("crear-lugar") + f"?tipopag={template_param}")



class PlatoCreate(LoginRequiredMixin, CreateView):
    model = Plato
    form_class = PlatoForm
    # Fallback de template por si tipopag no matchea
    DEFAULT_TEMPLATE = 'AdminVideos/ppal_form.html'

    def get(self, request, *args, **kwargs):
        self.object = None  # ← necesario para evitar AttributeError
        context = self.get_context_data()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            html = render_to_string('AdminVideos/plato_form_inner.html', context, request=request)
            return JsonResponse({'html': html})

        return super().get(request, *args, **kwargs)



    def get_template_names(self):
        template_param = self.request.GET.get('tipopag')
        templates = {
            'Entrada': 'AdminVideos/entrada_form.html',
            'Dip': 'AdminVideos/dip_form.html',
            'Principal': 'AdminVideos/ppal_form.html',
            'Dash': 'AdminVideos/ppal_form.html',
            'Trago': 'AdminVideos/trago_form.html',
            'Salsa': 'AdminVideos/salsa_form.html',
            'Guarnicion': 'AdminVideos/guarnicion_form.html',
            'Postre': 'AdminVideos/postre_form.html',
            'Delivery': 'AdminVideos/delivery.html',
            'Comerafuera': 'AdminVideos/comerafuera.html',
        }
        return [templates.get(template_param, self.DEFAULT_TEMPLATE)]

    TIPOS_POR_TEMPLATE = {
        "Entrada": ["Guarnicion","Picada","Principal", "Entrada"],
        "Guarnicion": ["Guarnicion", "Principal", "Entrada", "Picada"],
        "Trago": ["Trago"],
        "Dip": ["Dip", "Guarnicion"],
        "Torta": ["Torta", "Postre"],
        "Postre": ["Postre"],
        "Principal": ["Principal", "Guarnicion", "Entrada", "Picada"],
        "Dash": ["Principal", "Guarnicion", "Entrada", "Picada"],
        "Picada": ["Picada","Guarnicion", "Entrada"],
        "Salsa": ["Salsa", "Dip", "Guarnicion", "Entrada"],
    }

    # 1) Alinear “tipos” con tu modelo actual (CharField CSV)
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        template_param = self.request.GET.get('tipopag')
        if template_param == "Dash":
            template_param = "Principal"

        opciones = self.TIPOS_POR_TEMPLATE.get(template_param, [])
        if opciones:
            form.fields['tipos'].choices = [
                (k, v) for (k, v) in Plato.TIPOS_CHOICES if k in opciones
            ]
            if template_param in opciones:
                form.fields['tipos'].initial = [template_param]
            elif form.fields['tipos'].choices:
                form.fields['tipos'].initial = [form.fields['tipos'].choices[0][0]]

            if len(form.fields['tipos'].choices) == 1:
                form.fields['tipos'].widget = forms.MultipleHiddenInput()
        else:
            form.fields['tipos'].choices = []
            form.fields['tipos'].initial = []

        # Imagen no requerida (por si el widget envia archivo sin nombre)
        if 'image' in form.fields:
            form.fields['image'].required = False

        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        template_param = self.request.GET.get('tipopag')
        context['items'] = self.TIPOS_POR_TEMPLATE.get(template_param, [])
        context['tipopag'] = template_param

        if self.request.method == 'POST':
            context['ingrediente_formset'] = IngredienteEnPlatoFormSet(self.request.POST)
        else:
            context['ingrediente_formset'] = IngredienteEnPlatoFormSet()
        return context

    def form_valid(self, form):
        
        context = self.get_context_data()
        ingrediente_formset = context['ingrediente_formset']

        print("🔹 Headers:", dict(self.request.headers))
        print("🔹 User:", self.request.user)

        print("== POST RECEIVED ==")
        for key in self.request.POST:
            print(key, "=>", self.request.POST.get(key))
    
        # --- Validación del formset ---
        if not ingrediente_formset.is_valid():
            # Si vino por AJAX (modal)
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                html = render_to_string('AdminVideos/plato_form_inner.html', context, request=self.request)
                return JsonResponse({'success': False, 'html': html})
            # Si es página normal
            return self.render_to_response(self.get_context_data(form=form))


        # --- Manejo de imagen ---
        uploaded = self.request.FILES.get('image')
        if not uploaded:
            form.instance.image = None
        else:
            if not getattr(uploaded, 'name', None):
                uploaded.name = 'upload.jpg'

        # --- Guardado atómico ---
        with transaction.atomic():
            plato = form.save(commit=False)
            plato.propietario = self.request.user

            # --- Concatenar ingredientes del formset ---
            lista_ingredientes = []
            for ing_form in ingrediente_formset:
                if ing_form.cleaned_data and not ing_form.cleaned_data.get("DELETE", False):
                    nombre = ing_form.cleaned_data.get("nombre_ingrediente")
                    texto = (nombre or '').strip()
                    if texto:
                        lista_ingredientes.append(texto)

            plato.ingredientes = ", ".join(lista_ingredientes)

            # --- Guardar variedades ---
            variedades = {}
            for i in range(1, 7):
                variedad = form.cleaned_data.get(f'variedad{i}')
                ingredientes_variedad_str = form.cleaned_data.get(f'ingredientes_de_variedad{i}')
                if variedad:
                    variedades[f"variedad{i}"] = {
                        "nombre": variedad,
                        "ingredientes": ingredientes_variedad_str,
                        "elegido": True
                    }

            plato.variedades = variedades
            plato.save()
            form.save_m2m()

            ingrediente_formset.instance = plato
            ingrediente_formset.save()

        
        # --- Si es un request AJAX (modal) ---
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'nombre': plato.nombre_plato})

        # # --- Si hay return_to (volver a formulario anterior) ---
        # return_to = self.request.POST.get("return_to") or self.request.GET.get("return_to")
        # if return_to:
        #     return redirect(return_to)

        # 🔹 Si viene desde modal (AJAX), responder JSON
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "success": True,
                "nombre": plato.nombre_plato,
                "id": plato.id,
            })


        # --- Comportamiento normal (página completa) ---
        template_param = self.request.GET.get('tipopag')
        tail = f"?tipopag={template_param}&guardado=ok" if template_param else "?guardado=ok"
        return redirect(f"{reverse('videos-create')}{tail}")


    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        print("❌ Errores del formulario principal:")
        print(form.errors)

        ingrediente_formset = context.get('ingrediente_formset')
        if ingrediente_formset:
            print("❌ Errores del formset de ingredientes:")
            for i, f in enumerate(ingrediente_formset.forms):
                if f.errors:
                    print(f"Errores en el formulario #{i}: {f.errors}")

        # 🔹 Si la petición viene del modal (AJAX)
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            html = render_to_string('AdminVideos/plato_form_inner.html', context, request=self.request)
            return JsonResponse({'success': False, 'html': html})

        # 🔹 Si es una página completa
        return self.render_to_response(context)





class PlatoUpdate(LoginRequiredMixin, UpdateView):
    model = Plato
    form_class = PlatoForm
    template_name = "AdminVideos/plato_update.html"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data()

        # ✅ Si es AJAX: devolver fragmento HTML como JSON
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            html = render_to_string("AdminVideos/plato_form_inner.html", context, request=request)
            return JsonResponse({"html": html})

        return self.render_to_response(context)

    # 👉 TIPOS: ofrecer TODOS y marcar los que tenga el plato
    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # Mostrar todas las opciones
        form.fields["tipos"].choices = Plato.TIPOS_CHOICES

        # Sugerir tipopag si no hay initial
        if not form.initial.get("tipos"):
            tipopag = self.request.GET.get("tipopag")
            valid_keys = {k for k, _ in Plato.TIPOS_CHOICES}
            if tipopag in valid_keys:
                form.fields["tipos"].initial = [tipopag]

        # Imagen no requerida
        if "image" in form.fields:
            form.fields["image"].required = False

        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # --- Formset ingredientes (POST/GET) ---
        if self.request.method == "POST":
            formset = IngredienteEnPlatoFormSet(self.request.POST, instance=self.object)
        else:
            formset = IngredienteEnPlatoFormSet(instance=self.object)

        # ✅ PARCHE: asegurar nombre_ingrediente en initial (evita VariableDoesNotExist)
        for f in formset.forms:
            if "nombre_ingrediente" not in f.initial:
                ing = getattr(f.instance, "ingrediente", None)
                f.initial["nombre_ingrediente"] = getattr(ing, "nombre", "") if ing else ""

        context["ingrediente_formset"] = formset

        # 👉 TIPOS: enviar TODOS al template
        context["items"] = [k for (k, _) in Plato.TIPOS_CHOICES]
        context["tipopag"] = self.request.GET.get("tipopag", "Dash")

        # ❌ Variedades legacy: removido (ya no se usa)
        # context["variedades_en_base"] = ...
        # context["ingredientes_variedad"] = ...
        # ✅ Variedades (hijos) en orden fijo (creación)
        context["variedades"] = (
            Plato.objects
            .filter(plato_padre=self.object)
            .order_by("id")
        )

        return context

    def form_valid(self, form):
        context = self.get_context_data()
        ingrediente_formset = context["ingrediente_formset"]

        if not ingrediente_formset.is_valid():
            return self.render_to_response(self.get_context_data(form=form))

        # 🔒 Imagen: normalizar (si no viene nueva, no tocar la actual)
        uploaded = self.request.FILES.get("image")
        if uploaded and not getattr(uploaded, "name", None):
            uploaded.name = "upload.jpg"

        with transaction.atomic():
            plato = form.save(commit=False)
            plato.propietario = self.request.user

            # reconstruir string "ingredientes" desde el formset
            lista_ingredientes = []
            for ing_form in ingrediente_formset:
                if ing_form.cleaned_data and not ing_form.cleaned_data.get("DELETE", False):
                    nombre = ing_form.cleaned_data.get("nombre_ingrediente")
                    texto = (nombre or "").strip()
                    if texto:
                        lista_ingredientes.append(texto)

            plato.ingredientes = ", ".join(lista_ingredientes)

            # ❌ Variedades legacy: removido (ya no se guarda plato.variedades)
            # plato.variedades = ...

            plato.save()
            form.save_m2m()

            ingrediente_formset.instance = plato
            ingrediente_formset.save()

        # 1️⃣ Si fue llamado desde un modal (AJAX), responder con JSON
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "success": True,
                "nombre": plato.nombre_plato,
                "id": plato.id,
            })

        # 2️⃣ Si hay return_to (volver a donde fue llamado)
        return_to = self.request.POST.get("return_to") or self.request.GET.get("return_to")
        if return_to:
            return redirect(return_to)

        # 3️⃣ Fallback: redirigir normalmente
        template_param = self.request.GET.get("tipopag")
        tail = f"?tipopag={template_param}&modificado=ok" if template_param else "?modificado=ok"
        return redirect(f"{reverse('videos-create')}{tail}")

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        print("Errores al editar plato:", form.errors)
        ingrediente_formset = context.get("ingrediente_formset")
        if ingrediente_formset:
            for i, f in enumerate(ingrediente_formset.forms):
                if f.errors:
                    print(f"Errores en ingrediente #{i}: {f.errors}")
        return self.render_to_response(context)


class PlatoVariedadCreate(PlatoCreate):
    
#     Crea un Plato hijo asociado a un Plato padre.
#     Reusa template, form, formset y AJAX de PlatoCreate.
#   else:
#     form.fields['tipos'].choices = []
#     form.fields['tipos'].initial = [] 
# 

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # ✅ Para variedades, no queremos invalidar los checkboxes por falta de tipopag
        form.fields["tipos"].choices = Plato.TIPOS_CHOICES
        return form 

    def get_initial(self):
        initial = super().get_initial()

        p = self.padre

        # Sugerencia de nombre
        initial["nombre_plato"] = f"{p.nombre_plato} (variedad)"

        # Copiar campos “normales”
        initial["receta"] = p.receta
        initial["porciones"] = p.porciones
        initial["medios"] = p.medios
        initial["elaboracion"] = p.elaboracion
        initial["coccion"] = p.coccion
        initial["categoria"] = p.categoria
        initial["estacionalidad"] = p.estacionalidad
        initial["enlace"] = p.enlace

        # Tipos: tu form usa MultipleChoiceField; el padre guarda CSV
        initial["tipos"] = [t.strip() for t in (p.tipos or "").split(",") if t.strip()]

        return initial

    def dispatch(self, request, *args, **kwargs):
        self.padre = get_object_or_404(Plato, pk=kwargs["padre_id"])

        # regla: NO variedades de variedades
        if self.padre.plato_padre_id is not None:
            raise PermissionDenied("No se pueden crear variedades de una variedad.")

        # seguridad: mismo propietario
        if self.padre.propietario_id != request.user.id:
            raise PermissionDenied()

        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self):
        """
        Mantener el mismo look & feel que el padre.
        Si viene tipopag por GET lo respeta; si no, intenta inferir desde el padre.
        """
        tipopag = self.request.GET.get("tipopag")

        if not tipopag:
            # tu campo 'tipos' es CSV; tomamos el primero como "tipopag" razonable
            raw = (self.padre.tipos or "").split(",")[0].strip()
            tipopag = raw or "Dash"

        # hack simple: reutiliza tu mapping interno de PlatoCreate.get_template_names
        self.request.GET._mutable = True
        self.request.GET["tipopag"] = tipopag
        self.request.GET._mutable = False

        return super().get_template_names()

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)

    #     if self.request.method == "POST":
    #         # POST: que valide lo que vino del modal
    #         context["ingrediente_formset"] = IngredienteEnPlatoFormSet(self.request.POST)
    #         return context

    #     # GET: clonar ingredientes del padre como initial
    #     inicial = []
    #     # 👇 ajustá el related_name si el tuyo es distinto
    #     for rel in self.padre.ingredienteenplato_set.all():
    #         inicial.append({
    #             "ingrediente": rel.ingrediente_id,
    #             "nombre_ingrediente": rel.ingrediente.nombre if rel.ingrediente else "",
    #             "cantidad": rel.cantidad,
    #             "unidad": rel.unidad,
    #         })

    #     context["ingrediente_formset"] = IngredienteEnPlatoFormSet(initial=inicial)
    #     return context
    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)

    #     # ✅ SIEMPRE: en variedades queremos mostrar tipos disponibles
    #     context["items"] = [k for (k, _) in Plato.TIPOS_CHOICES]

    #     # ✅ tipopag: si no vino en la URL del modal, inferir desde el padre
    #     tipopag = self.request.GET.get("tipopag")
    #     if not tipopag:
    #         raw = (self.padre.tipos or "").split(",")[0].strip()
    #         tipopag = raw or "Dash"
    #     context["tipopag"] = tipopag

    #     context["plato_padre_obj"] = self.padre

    #     # POST: que valide lo que vino del modal
    #     if self.request.method == "POST":
    #         context["ingrediente_formset"] = IngredienteEnPlatoFormSet(self.request.POST)
    #         return context

    #     # GET: clonar ingredientes del padre como initial
    #     inicial = []
    #     for rel in self.padre.ingredientes_en_plato.select_related("ingrediente").all():
    #         inicial.append({
    #             "ingrediente": rel.ingrediente_id,
    #             "nombre_ingrediente": rel.ingrediente.nombre if rel.ingrediente else "",
    #             "cantidad": rel.cantidad,
    #             "unidad": rel.unidad,
    #         })

    #     context["ingrediente_formset"] = IngredienteEnPlatoFormSet(initial=inicial)
    #     return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["items"] = [k for (k, _) in Plato.TIPOS_CHOICES]

        tipopag = self.request.GET.get("tipopag")
        if not tipopag:
            raw = (self.padre.tipos or "").split(",")[0].strip()
            tipopag = raw or "Dash"
        context["tipopag"] = tipopag

        context["plato_padre_obj"] = self.padre

        if self.request.method == "POST":
            context["ingrediente_formset"] = IngredienteEnPlatoFormSet(self.request.POST)
            return context

        # GET: clonar ingredientes del padre
        inicial = []
        for rel in self.padre.ingredientes_en_plato.select_related("ingrediente").all():
            inicial.append({
                "ingrediente": rel.ingrediente_id,
                "nombre_ingrediente": rel.ingrediente.nombre if rel.ingrediente else "",
                "cantidad": rel.cantidad,
                "unidad": rel.unidad,
            })

        # 👇 CLAVE: si tu formset es inlineformset, necesita extra >= len(inicial)
        context["ingrediente_formset"] = IngredienteEnPlatoFormSet(
            initial=inicial,
            queryset=self.padre.ingredientes_en_plato.none(),  # opcional, evita traer del padre
        )
        context["ingrediente_formset"].extra = len(inicial)

        return context




    def form_valid(self, form):
        context = self.get_context_data()
        ingrediente_formset = context["ingrediente_formset"]

        print("=== VARIEDAD CREATE POST CHECK ===")
        print("keys TOTAL_FORMS:", [k for k in self.request.POST.keys() if "TOTAL_FORMS" in k])
        print("keys INITIAL_FORMS:", [k for k in self.request.POST.keys() if "INITIAL_FORMS" in k])


        # --- Validación del formset ---
        if not ingrediente_formset.is_valid():
            if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
                html = render_to_string("AdminVideos/plato_form_inner.html", context, request=self.request)
                return JsonResponse({"success": False, "html": html})
            return self.render_to_response(self.get_context_data(form=form))

        # --- Manejo de imagen (idéntico a tu create) ---
        uploaded = self.request.FILES.get("image")
        if not uploaded:
            form.instance.image = None
        else:
            if not getattr(uploaded, "name", None):
                uploaded.name = "upload.jpg"

        with transaction.atomic():
            plato = form.save(commit=False)
            plato.propietario = self.request.user

            # ✅ CLAVE: asociar variedad al padre
            plato.plato_padre = self.padre

            # --- Concatenar ingredientes del formset (igual) ---
            lista_ingredientes = []
            for ing_form in ingrediente_formset:
                if ing_form.cleaned_data and not ing_form.cleaned_data.get("DELETE", False):
                    nombre = ing_form.cleaned_data.get("nombre_ingrediente")
                    texto = (nombre or "").strip()
                    if texto:
                        lista_ingredientes.append(texto)

            plato.ingredientes = ", ".join(lista_ingredientes)

            # legacy variedades (si ya lo estás vaciando en template, quedará {})
            # variedades = {}
            # for i in range(1, 7):
            #     variedad = form.cleaned_data.get(f"variedad{i}")
            #     ingredientes_variedad_str = form.cleaned_data.get(f"ingredientes_de_variedad{i}")
            #     if variedad:
            #         variedades[f"variedad{i}"] = {
            #             "nombre": variedad,
            #             "ingredientes": ingredientes_variedad_str,
            #             "elegido": True,
            #         }
            # plato.variedades = variedades

            plato.save()
            form.save_m2m()

            ingrediente_formset.instance = plato

            # Si no vinieron ingredientes en el POST, clonarlos del padre
            hay_al_menos_uno = False
            for f in ingrediente_formset.forms:
                if f.cleaned_data and not f.cleaned_data.get("DELETE", False):
                    nombre = (f.cleaned_data.get("nombre_ingrediente") or "").strip()
                    if nombre:
                        hay_al_menos_uno = True
                        break

            if not hay_al_menos_uno:
                # 1) borrar cualquier cosa que haya quedado (por seguridad)
                # (en create normalmente no hay, pero no molesta)
                # plato.ingredientes_en_plato.all().delete()  # si ya existen

                # 2) clonar relaciones desde el padre
                from .models import IngredienteEnPlato  # ajustá si tu import es distinto

                IngredienteEnPlato.objects.bulk_create([
                    IngredienteEnPlato(
                        plato=plato,
                        ingrediente=rel.ingrediente,
                        cantidad=rel.cantidad,
                        unidad=rel.unidad,
                    )
                    for rel in self.padre.ingredientes_en_plato.select_related("ingrediente").all()
                    if rel.ingrediente_id
                ])

                # 3) y reconstruir el string "ingredientes"
                nombres = [
                    rel.ingrediente.nombre
                    for rel in self.padre.ingredientes_en_plato.select_related("ingrediente").all()
                    if rel.ingrediente_id and rel.ingrediente and rel.ingrediente.nombre
                ]
                plato.ingredientes = ", ".join(nombres)
                plato.save(update_fields=["ingredientes"])
            else:
                ingrediente_formset.instance = plato
                ingrediente_formset.save()

            ingrediente_formset.save()

        # AJAX (modal) — lo dejamos compatible para el paso 4
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True, "nombre": plato.nombre_plato, "id": plato.id})

        # ✅ Redirect seguro: volver al padre (edit) con flag opcional
        # 🔹 SI ES PANTALLA COMPLETA → VOLVER AL PADRE
        return redirect(
            reverse("videos-update", kwargs={"pk": self.padre.id})
        )

class PlatoVariedadUpdate(PlatoUpdate):
    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.plato_padre_id is None:
            raise PermissionDenied("Este plato no es una variedad.")

        if self.object.propietario_id != request.user.id:
            raise PermissionDenied()

        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        # usa la lógica de guardado del update normal
        resp = super().form_valid(form)

        # ✅ si es AJAX (modal), respetar JSON (tu JS ya cierra y recarga)
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            return resp

        # ✅ pantalla completa: volver al padre
        return redirect(reverse("videos-update", kwargs={"pk": self.padre.id}))



class PlatoVariedadDelete(LoginRequiredMixin, DeleteView):
    model = Plato

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.plato_padre_id is None:
            raise PermissionDenied("Este plato no es una variedad.")
        if self.object.propietario_id != request.user.id:
            raise PermissionDenied()

        self.padre = self.object.plato_padre
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.padre = self.object.plato_padre
        self.object.delete()

        # si lo llamás por AJAX
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True})

        # pantalla completa: volver al padre
        return redirect(reverse("videos-update", kwargs={"pk": self.padre.id}))


class Login(LoginView):
    authentication_form = CustomAuthenticationForm
    next_page = reverse_lazy("filtro-de-platos")


class SignUp(CreateView):
    form_class = UserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('filtro-de-platos')

@login_required
def user_logout(request):
    logout(request)
    # return render(request, 'registration/logout.html', {})
    return redirect(reverse_lazy("login"))


class ProfileCreate(LoginRequiredMixin, CreateView):
    model = Profile
    success_url = reverse_lazy("filtro-de-platos")
    fields = ["nombre", "apellido", "telefono","avatar"]

    def form_valid(self, form):
        el_user = form.save(commit=False)
        el_user.user = self.request.user
        el_user.save()
        return redirect(self.success_url)

class ProfileUpdate(LoginRequiredMixin, UserPassesTestMixin,  UpdateView):
    model = Profile
    success_url = reverse_lazy("filtro-de-platos")
    fields = ["nombre", "apellido", "telefono","avatar"]

    def test_func(self):
        return Profile.objects.filter(user=self.request.user).exists()




def filtrar_platos(
    usuario,
    tipo_parametro,
    quecomemos,
    misplatos,
    medios,
    categoria,
    dificultad,
    palabra_clave
):

    # Si no se selecciona 'quecomemos' ni 'misplatos', no mostrar platos
    if quecomemos != "quecomemos" and misplatos != "misplatos":
        return Plato.objects.none()

    # 🔒 BASE: SOLO PLATOS PADRE (excluye variedades)
    query = Q(plato_padre__isnull=True)

    if quecomemos == "quecomemos":
        usuario_quecomemos = User.objects.filter(username="quecomemos").first()
        if usuario_quecomemos:
            query |= Q(propietario=usuario_quecomemos, plato_padre__isnull=True)

        platos_descartados = usuario.profile.sugeridos_descartados
        if platos_descartados:
            query &= ~Q(id__in=platos_descartados)

    if misplatos == "misplatos":
        query |= Q(propietario=usuario, plato_padre__isnull=True)

    if tipo_parametro and tipo_parametro != "Dash":
        query &= Q(tipos__icontains=tipo_parametro)

    if medios and medios != '-':
        query &= Q(medios=medios)

    if categoria and categoria != '-':
        query &= Q(categoria=categoria)

    if dificultad and dificultad != '-':
        query &= Q(dificultad=dificultad)

    if palabra_clave:
        query &= (
            Q(ingredientes__icontains=palabra_clave) |
            Q(nombre_plato__icontains=palabra_clave)
        )

    # ✅ ACÁ está el paso clave
    return (
        Plato.objects
        .filter(query)
        .annotate(variedades_count=Count("variedades_hijas"))
    )





@login_required(login_url=reverse_lazy('login'), redirect_field_name=None)
def FiltroDePlatos(request):

    # Obtener la fecha actual
    fecha_actual = datetime.datetime.now().date()

    DIAS_ES = ['LU','MA','MI','JU','VI','SA','DO']  # tu mapeo

    # if False:  # 🔴 BLOQUE DESACTIVADO (refactor nuevo menú)

    #     registros_antiguos = ElegidosXDia.objects.filter(
    #         el_dia_en_que_comemos__lt=fecha_actual, user=request.user
    #     )

    #     with transaction.atomic():
    #         for registro in registros_antiguos:
    #             fecha = registro.el_dia_en_que_comemos
    #             datos = registro.platos_que_comemos or {}

    #             historico, _ = HistoricoDia.objects.get_or_create(
    #                 fecha=fecha,
    #                 propietario=request.user,
    #                 defaults={'dia_semana': DIAS_ES[fecha.weekday()]}
    #             )
    #             if not historico.dia_semana:
    #                 historico.dia_semana = DIAS_ES[fecha.weekday()]
    #                 historico.save(update_fields=['dia_semana'])

    #             for momento in ["desayuno", "almuerzo", "merienda", "cena"]:
    #                 for plato_data in datos.get(momento, []):
    #                     pid = plato_data.get("id_plato")
    #                     if not pid:
    #                         continue

    #                     # Intentamos resolver el Plato SOLO para capturar snapshot de nombre (si aún existe)
    #                     plato_obj = Plato.objects.filter(id=pid, propietario=request.user).only('id','nombre_plato').first()
    #                     nombre_snap = plato_obj.nombre_plato if plato_obj else (plato_data.get("nombre_plato") or "Plato eliminado")

    #                     HistoricoItem.objects.get_or_create(
    #                         historico=historico,
    #                         plato_id_ref=pid,
    #                         momento=momento
    #                         # defaults={'plato_nombre_snapshot': nombre_snap}
    #                     )

    #             registro.delete()







    # # Calcular y agregar las fechas y nombres de los días para los próximos 6 días
    dias_desde_hoy = [(fecha_actual + timedelta(days=i)) for i in range(0, 7)]

    primer_dia = dias_desde_hoy[0].isoformat()

    # Obtener el día activo de la sesión o asignar el primer día si no está definido
    dia_activo = request.session.get('dia_activo', primer_dia)

    # Si 'dia_activo' es menor que el primer día, reasignarlo
    if dia_activo < primer_dia:
        request.session['dia_activo'] = primer_dia

    pla = ""

    dias_programados = set()  # Usamos set para evitar fechas repetidas

    # Recuperar los parámetros desde la sesión y la URL
    tipo_parametro, quecomemos, misplatos, medios, categoria, dificultad, palabra_clave = obtener_parametros_sesion(request)

    # Obtener el usuario actual
    usuario = request.user

    # Formularios y datos iniciales
    if request.method == "POST":

            form = PlatoFilterForm(request.POST)

            if form.is_valid():

                medios = form.cleaned_data.get('medios')
                categoria = form.cleaned_data.get('categoria')
                dificultad = form.cleaned_data.get('dificultad')
                palabra_clave =  form.cleaned_data.get('palabra_clave')

                request.session['medios_estable'] = medios
                request.session['categoria_estable'] = categoria
                request.session['dificultad_estable'] = dificultad
                request.session['palabra_clave'] = palabra_clave

                quecomemos = request.POST.get('quecomemos')
                misplatos = request.POST.get('misplatos')

                request.session['quecomemos'] = quecomemos
                request.session['misplatos'] = misplatos

                request.session['dia_activo'] = dia_activo


    else:
        items_iniciales = {

                        'medios': medios,
                        'categoria': categoria,
                        'dificultad': dificultad,
                        'palabra_clave': palabra_clave

                    }

        form = PlatoFilterForm(initial=items_iniciales)

    if tipo_parametro == "Delivery":
        lugares = Lugar.objects.filter(propietario=request.user, delivery=True)
        platos = ""


    elif tipo_parametro == "Comerafuera":
        lugares = Lugar.objects.filter(propietario=request.user, delivery=False)
        platos = ""


    else:
        lugares = ""
        # Llamar a la función filtrar_platos pasando las variables recuperadas
        platos = filtrar_platos(
            usuario=usuario,
            tipo_parametro=tipo_parametro,
            quecomemos=quecomemos,
            misplatos=misplatos,
            medios=medios,
            categoria=categoria,
            dificultad=dificultad,
            palabra_clave=palabra_clave
        )

    # Filtra las fechas únicas en `el_dia_en_que_comemos` para los objetos del usuario actual
    # fechas_existentes = ElegidosXDia.objects.filter(user=usuario,el_dia_en_que_comemos__gte=fecha_actual).values_list('el_dia_en_que_comemos', flat=True).distinct()

    # REFACTORIZACIÓN
    fechas_existentes = list(
        MenuDia.objects.filter(
            propietario=usuario,
            fecha__gte=fecha_actual
        ).values_list('fecha', flat=True)
    )



    # Obtén el perfil del usuario autenticado
    # perfil = get_object_or_404(Profile, user=usuario)

    try:
        perfil = Profile.objects.get(user=usuario)
    except Profile.DoesNotExist:
        return redirect('profile-create')  # Asegúrate de tener una vista para que el usuario cree su perfil

    # Accede al atributo `amigues` desde la instancia
    amigues = perfil.amigues  # Esto cargará la lista almacenada en JSONField

    # el avatar
    avatar = perfil.avatar_url

    # -------------------   LISTA DE PRIMEROS MENSAJES
    # Subquery para obtener el último mensaje de cada usuario
    subquery_ultimo_mensaje = (
        Mensaje.objects.filter(usuario_que_envia=OuterRef('usuario_que_envia'), destinatario=usuario)
        .order_by('-creado_el')
        .values('id')[:1]  # Tomamos solo el ID del mensaje más reciente
    )

    # Filtramos solo los últimos mensajes de cada usuario
    mensajes_x_usuario = Mensaje.objects.filter(id__in=Subquery(subquery_ultimo_mensaje))

    # Construimos el diccionario
    mensajes_agrupados = {
        mensaje.usuario_que_envia if isinstance(mensaje.usuario_que_envia, str) else mensaje.usuario_que_envia.username: {
            "avatar_url": getattr(
                mensaje.usuario_que_envia.profile, 'avatar_url', '/media/avatares/logo.png'
            ) if hasattr(mensaje.usuario_que_envia, 'profile') else '/media/avatares/logo.png',
            "mensaje": {
                "contenido": mensaje.mensaje,
                "creado_el": (timezone.now() - mensaje.creado_el).days,
                "leido": mensaje.leido
            }
        }
        for mensaje in mensajes_x_usuario
    }

# ------------------- LISTA DE PLATOS COMPARTIDOS

    # MENSAJES CON PLATOS COMPARTIDOS QUE AÚN NO FUERON IMPORTADOS
    mensajes_platos_compartidos = Mensaje.objects.filter(destinatario=usuario, importado=False).exclude(tipo_mensaje__in=["mensaje", "solicitar"])

    # Obtener los IDs de los platos compartidos junto con el ID del mensaje
    ids_platos_compartidos = {msg.id_elemento: msg.id for msg in mensajes_platos_compartidos if msg.id_elemento}

    # Buscar los platos correspondientes en la base de datos
    # los_platos_compartidos = {
    #     str(plato.id): plato for plato in Plato.objects.filter(id__in=ids_platos_compartidos)
    # }

    los_platos_compartidos = {
        plato.id: plato for plato in Plato.objects.filter(id__in=ids_platos_compartidos)
    }

    # Extraer los platos compartidos de los mensajes
    platos_compartidos = [
        {
            "id_plato": msg.id_elemento,
            "mensaje_id": msg.id, # Agregar el ID del mensaje del cual proviene
            "mensaje": msg.mensaje,
            "nombre_plato": msg.nombre_elemento_compartido,
            "quien_comparte": msg.usuario_que_envia,
            "receta": los_platos_compartidos[msg.id_elemento].receta if msg.id_elemento in los_platos_compartidos else "",
            # "descripcion": los_platos_compartidos[msg.id_elemento].descripcion_plato if msg.id_elemento in los_platos_compartidos else "",
            "ingredientes": los_platos_compartidos[msg.id_elemento].ingredientes if msg.id_elemento in los_platos_compartidos else "",
            # "tipo": los_platos_compartidos[msg.id_elemento].tipo if msg.id_elemento in los_platos_compartidos else "",
            "image_url": los_platos_compartidos[msg.id_elemento].image_url if msg.id_elemento in los_platos_compartidos else ""
        }
        for msg in mensajes_platos_compartidos if msg.nombre_elemento_compartido
    ]

# ---------------------


    dia_activo = request.session.get('dia_activo', None)  # 🟢 Recuperamos la fecha activa

    # Inicializar un diccionario donde cada fecha tendrá listas separadas para cada tipo de comida
    platos_dia_x_dia = defaultdict(lambda: {"desayuno": [], "almuerzo": [], "merienda": [], "cena": []})


    items = (
        MenuItem.objects
        .filter(
            menu__propietario=request.user,
            menu__fecha__in=fechas_existentes
        )
        .select_related("menu", "plato", "lugar")
    )

    for item in items:
        fec = item.menu.fecha
        dias_programados.add(fec)

        if item.plato:
            platos_dia_x_dia[fec][item.momento].append({
                "id": item.plato.id,
                "nombre": item.plato.nombre_plato
            })
        elif item.lugar:
            platos_dia_x_dia[fec][item.momento].append({
                "id": item.lugar.id,
                "nombre": item.lugar.nombre
            })


    # Convertir defaultdict a dict antes de pasarlo a la plantilla
    platos_dia_x_dia = dict(platos_dia_x_dia)



    contexto = {
                'formulario': form,
                'platos': platos,
                "dias_desde_hoy": dias_desde_hoy,
                "dias_programados": dias_programados,
                "quecomemos_ck": quecomemos,
                "misplatos_ck": misplatos,
                "amigues" : amigues,
                "parametro": tipo_parametro,
                "mensajes": mensajes_agrupados,
                'dia_activo': dia_activo,
                "platos_dia_x_dia": platos_dia_x_dia,
                # "idesplatos": ids_platos_importados,
                # "ides_descartable": ids_platos_compartidos,
                "platos_compartidos": platos_compartidos,
                "lugares": lugares,
                # "sumados": sumar_historico

               }

    return render(request, 'AdminVideos/lista_filtrada.html', contexto)





class SolicitarAmistad(CreateView):
   model = Mensaje
   success_url = reverse_lazy('filtro-de-platos')
   fields = '__all__'
   template_name = 'AdminVideos/solicitar_amistad.html'

   def form_valid(self, form):
        # Asigna el valor predeterminado al campo 'amistad'
        form.instance.tipo_mensaje = "amistad"
        return super().form_valid(form)


   def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # Obtener el perfil del usuario autenticado
        perfil_usuario = self.request.user.profile

        # Obtener la lista de amigos (amigues) del usuario actual (en base al nombre de usuario)
        amigos = perfil_usuario.amigues

        # Obtener los usuarios que no son amigos, excluyendo al usuario actual
        usuarios_no_amigos = User.objects.exclude(id=self.request.user.id)  # Excluir al usuario actual

        # Filtrar usuarios que no estén en la lista de amigos (compara nombre de usuario)
        usuarios_no_amigos = usuarios_no_amigos.exclude(username__in=amigos)

        form.fields['destinatario'].queryset = usuarios_no_amigos
        return form

class EnviarMensaje(LoginRequiredMixin, CreateView):
    model = Mensaje
    # success_url = reverse_lazy('enviar-mensaje')
    template_name = 'AdminVideos/enviar_mensaje.html'
    fields = ['mensaje', 'destinatario']

    def get_destinatario(self):
        return get_object_or_404(User, username=self.kwargs.get("usuario"))

    def form_valid(self, form):
        form.instance.usuario_que_envia = self.request.user.username
        form.instance.tipo_mensaje = "texto"
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('enviar-mensaje', kwargs={'usuario': self.kwargs['usuario']})

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        destinatario = self.get_destinatario()
        form.fields['destinatario'].queryset = User.objects.filter(username=destinatario.username)
        form.initial['destinatario'] = destinatario
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        destinatario = self.get_destinatario()

        mensajes = Mensaje.objects.filter(
            Q(usuario_que_envia=self.request.user.username, destinatario__username=destinatario.username) |
            Q(usuario_que_envia=destinatario.username, destinatario=self.request.user)
        ).order_by('creado_el')

        context["mensajes"] = mensajes

        # Obtener el perfil del usuario actual
        perfil = get_object_or_404(Profile, user=self.request.user)

        # Pasar la lista de amigues al contexto
        context["amigues"] = perfil.amigues  # Lista JSONField desde Profile

        return context

# from .models import IngredienteEnPlato, Plato, Lugar, Mensaje, TipoPlato  # Asegúrate de importar los modelos necesarios


class compartir_elemento(CreateView):
    model = Mensaje
    template_name = 'AdminVideos/compartir_elemento.html'
    success_url = reverse_lazy('filtro-de-platos')

    fields = ['mensaje']  # Solo incluimos el campo del mensaje, ya que otros se asignarán automáticamente

    def get_context_data(self, **kwargs):
        # Obtén el contexto base de la vista
        context = super().get_context_data(**kwargs)

        # Recupera el elemento_id y el amigue del request POST
        id_elemento = self.request.POST.get('id_elemento')
        amigue = self.request.POST.get('amigue')
        tipo_elemento = self.request.POST.get('tipo_elemento')

        # Agrega plato y amigue al contexto
        context['id_elemento'] = id_elemento
        context['amigue'] = amigue
        context['tipo_elemento'] = tipo_elemento

        return context

    def form_valid(self, form):
        # Obtén los datos necesarios del request
        id_elemento = self.request.POST.get('id_elemento')
        amigue_username = self.request.POST.get('amigue')  # Supone que el valor es el nombre de usuario

        # Obtén el mensaje que el usuario escribió en el formulario
        mensaje_usuario = form.cleaned_data.get('mensaje')
        tipo_mensaje = self.request.POST.get('tipo_mensaje')

        if tipo_mensaje == "plato":
            # Busca el plato y el destinatario
            plato = get_object_or_404(Plato, id=id_elemento)
            # plato = Plato.objects.get(id=id_elemento)
            form.instance.nombre_elemento_compartido = plato.nombre_plato
            form.instance.tipo_mensaje = "plato"
        elif tipo_mensaje == "lugar":
            lugar = Lugar.objects.get(id=id_elemento)
            form.instance.nombre_elemento_compartido = lugar.nombre

            if lugar.delivery:
                form.instance.tipo_mensaje = "delivery"
            else:
                form.instance.tipo_mensaje = "comerafuera"

        destinatario = get_object_or_404(User, username=amigue_username)

        # Completa los datos automáticos del mensaje
        form.instance.usuario_que_envia = self.request.user.username
        form.instance.destinatario = destinatario
        form.instance.id_elemento = id_elemento  # aqui mando el ID DEL ELEMENTO que se comparte
        form.instance.mensaje = mensaje_usuario

        return super().form_valid(form)


class MensajeDelete(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
   model = Mensaje
   context_object_name = "mensaje"
   success_url = reverse_lazy("filtro-de-platos")

   def test_func(self):
       return Mensaje.objects.filter(destinatario=self.request.user).exists()




@login_required
def amigues(request):
    # Obtén el perfil del usuario autenticado
    profile = request.user.profile

    # Obtén la lista de "amigues" desde el perfil
    lista_amigues = profile.amigues  # Esto será una lista (por el default=list en JSONField)

    # Pasa la lista como contexto a la plantilla
    context = {
        "amigues": lista_amigues,
        "parametro" : "amigues"
    }
    return render(request, "AdminVideos/amigues.html", context)




@login_required
def historial(request):
    # Obtener el perfil del usuario autenticado
    profile = request.user.profile

    # Obtener todos los mensajes donde el usuario es el destinatario, ordenados por fecha de creación
    # mensajes = Mensaje.objects.filter(destinatario=request.user).order_by("-creado_el")

    # Obtener todos los mensajes donde el usuario es el destinatario o el que los envió, ordenados por fecha de creación
    mensajes = Mensaje.objects.filter(
        Q(destinatario=request.user) | Q(usuario_que_envia=request.user.username)
    ).order_by("-creado_el")

    # Formatear los platos descartados e importados
    platos_descartados = [f"Descartado {plato}" for plato in profile.sugeridos_descartados]
    platos_importados = [f"Agregado {plato}" for plato in profile.sugeridos_importados]

    # Pasar todos los datos al contexto
    context = {
        "mensajes": mensajes,
        "platos_descartados": platos_descartados,
        "platos_importados": platos_importados,
    }

    return render(request, "AdminVideos/historial.html", context)


@login_required
def sumar_amigue(request):
    if request.method == "POST":
        # Obtén el ID del "amigue" enviado desde el formulario
        amigue_usuario = request.POST.get("amigue_usuario")
        mensaje_id = request.POST.get("mensaje_id")


        # Verifica que se haya enviado un ID válido
        # if not amigue_usuario:
        #     return HttpResponseForbidden("Solicitud inválida.")

        # Obtén el perfil del usuario autenticado
        # user_profile = request.user.profile

        # Obtener el perfil del usuario actual
        perfil = get_object_or_404(Profile, user=request.user)

        # Asegúrate de que no se repita en la lista
        if amigue_usuario not in perfil.amigues:
            # Agrega el nombre del "amigue" a la lista
            perfil.amigues.append(amigue_usuario)
            perfil.save()

        # Busca el usuario asociado al ID recibido
        aceptado = get_object_or_404(Profile, user__username=amigue_usuario)

        # Asegúrate de que el username no se repita en la lista
        if perfil.user.username not in aceptado.amigues:
            # Agrega el nombre del usuario a la lista
            aceptado.amigues.append(perfil.user.username)
            aceptado.save()

        # Marcar el mensaje como "importado" si el mensaje ID es válido
        if mensaje_id:
            mensaje = get_object_or_404(Mensaje, id=mensaje_id)
            mensaje.importado = True
            mensaje.save()

         # Construye un diccionario con las variables de contexto
    contexto = {
        "amigues": perfil.amigues,  # Lista de amigues actualizada
        "aceptado": aceptado,  # Lista de amigues actualizada

    }

    # Redirige a una página de confirmación o muestra la lista actualizada
    return render(request, "AdminVideos/amigues.html", contexto)


@login_required
def amigue_borrar(request, pk):
    # Obtener el perfil del usuario autenticado
    perfil = request.user.profile

    # Verificar si el ID del amigue existe en la lista de amigues
    if pk in perfil.amigues:
        perfil.amigues.remove(pk)
        perfil.save()  # Guardar los cambios en el perfil


    # Borrar en el registro del amigo también (no será más mi amigo)
    eliminame = get_object_or_404(Profile, user__username=pk)

    # Asegúrate de que el username tuyo este en la lista de tu amigo
    if perfil.user.username in eliminame.amigues:
        # Agrega el nombre del usuario a la lista
        eliminame.amigues.remove(perfil.user.username)
        eliminame.save()

    contexto = {
        "amigues": perfil.amigues,  # Lista de amigues actualizada
    }
    return render(request, "AdminVideos/amigues.html", contexto)

@login_required
def agregar_plato_compartido(request, pk, mensaje_id):
    # Recuperar el plato original
    plato_original = get_object_or_404(Plato, pk=pk)

    # Crear un nuevo plato para el usuario logueado
    nuevo_plato = Plato.objects.create(
        nombre_plato=plato_original.nombre_plato,
        receta=plato_original.receta,
        # descripcion_plato=plato_original.descripcion_plato,
        ingredientes=plato_original.ingredientes,
        medios=plato_original.medios,
        categoria=plato_original.categoria,
        dificultad=plato_original.dificultad,
        tipo=plato_original.tipo,
        calorias=plato_original.calorias,
        propietario=request.user,
        image=plato_original.image,
        variedades=plato_original.variedades,
        proviene_de=plato_original.propietario,
        id_original=plato_original.id
    )

    # Recuperar el mensaje por su ID
    mensaje = get_object_or_404(Mensaje, pk=mensaje_id)

    # Marcar el mensaje como importado
    mensaje.importado = True
    mensaje.save()

    # Mostrar un mensaje de éxito
    messages.success(request, "El plato se agregó exitosamente y el mensaje ha sido actualizado.")

    # Redirigir a la página de filtro de platos
    return redirect('filtro-de-platos')


def descartar_sugerido(request, plato_id):
    # Obtener el perfil del usuario logueado
    profile = request.user.profile

    # Verificar si el plato_id ya está en la lista para evitar duplicados
    if plato_id not in profile.sugeridos_descartados:
        profile.sugeridos_descartados.append(plato_id)  # Agregar el ID del plato a la lista
        profile.save()  # Guardar los cambios en el perfil

    return redirect('filtro-de-platos')




# @login_required
# def agregar_a_mi_lista(request, plato_id):
#     # 1) Plato original
#     plato_original = get_object_or_404(Plato, id=plato_id)

#     # 2) Perfil del usuario (asegura que exista)
#     profile = get_object_or_404(Profile, user=request.user)

#     # 3) Leer flag GET
#     duplicar = request.GET.get('duplicar') == 'true'

#     # 4) Nombre copia
#     nombre_copia = (
#         f"Copia de {plato_original.nombre_plato}"
#         if duplicar else
#         plato_original.nombre_plato
#     )

#     # 5) proviene_de ES CharField en tu modelo → guardar texto (p. ej. username)
#     proviene_de_str = (
#         plato_original.propietario.username
#         if plato_original.propietario != request.user else
#         ""
#     )

#     # 6) Copiar variedades sin compartir referencia (por si luego lo mutás)
#     variedades_copia = deepcopy(plato_original.variedades)

#     # 7) Crear el nuevo plato AJUSTADO al modelo
#     nuevo_plato = Plato.objects.create(
#         nombre_plato=nombre_copia,
#         receta=plato_original.receta,
#         # descripcion_plato=plato_original.descripcion_plato,
#         ingredientes=plato_original.ingredientes,
#         medios=plato_original.medios,
#         categoria=plato_original.categoria,
#         elaboracion=plato_original.elaboracion,
#         coccion=plato_original.coccion,
#         tipos=plato_original.tipos,                  # 👈 existe en el modelo (no 'tipo')
#         estacionalidad=plato_original.estacionalidad,
#         propietario=request.user,
#         image=plato_original.image,                  # referencia al mismo archivo (ok)
#         variedades=variedades_copia,
#         proviene_de=proviene_de_str,                 # 👈 string, no User
#         id_original=plato_original.id
#     )

#     # 8) Evitar duplicados en sugeridos_importados → por ID, no por nombre
#     if plato_original.id not in profile.sugeridos_importados:
#         profile.sugeridos_importados.append(plato_original.id)
#         profile.save(update_fields=["sugeridos_importados"])

#     # 9) Redirigir (tu lógica actual)
#     return redirect('descartar-sugerido', plato_id=plato_id)


# def agregar_a_mi_lista(request, plato_id):
#     # Obtener el plato a copiar
#     plato_original = get_object_or_404(Plato, id=plato_id)

#     # Obtener el perfil del usuario logueado
#     profile = request.user.profile

#     # Lee el parámetro GET
#     duplicar = request.GET.get('duplicar') == 'true'

#     # Determina el nombre del nuevo plato
#     nombre_copia = f"Copia de {plato_original.nombre_plato}" if duplicar else plato_original.nombre_plato


#     # Verificar si el plato original pertenece a otro usuario
#     proviene_de = plato_original.propietario if plato_original.propietario != request.user else None


#     # Crear una copia del plato, asignando el nuevo propietario
#     nuevo_plato = Plato.objects.create(
#         nombre_plato=nombre_copia,
#         receta=plato_original.receta,
#         descripcion_plato=plato_original.descripcion_plato,
#         ingredientes=plato_original.ingredientes,
#         medios=plato_original.medios,
#         categoria=plato_original.categoria,
#         dificultad=plato_original.dificultad,
#         tipo=plato_original.tipo,
#         calorias=plato_original.calorias,
#         propietario=request.user,  # Asignar al usuario logueado
#         image=plato_original.image,  # Copiar la imagen si aplica
#         variedades=plato_original.variedades,
#         proviene_de= proviene_de,
#         id_original=plato_original.id
#     )

#   # Verificar si el plato_id ya está en la lista para evitar duplicados
#     if plato_original.nombre_plato not in profile.sugeridos_importados:
#         profile.sugeridos_importados.append(plato_id)  # Agregar el ID del plato a la lista
#         profile.save()  # Guardar los cambios en el perfil

#     # Redirigir a la vista para descartar el plato después de agregarlo
#     return redirect('descartar-sugerido', plato_id=plato_id)


@login_required
def agregar_a_mi_lista(request, plato_id):
    # 1) Plato original
    plato_original = get_object_or_404(Plato, id=plato_id)

    # 2) Perfil del usuario
    profile = get_object_or_404(Profile, user=request.user)

    # 3) Flag GET
    duplicar = request.GET.get('duplicar') == 'true'

    # 4) Nombre
    nombre_copia = (
        f"Copia de {plato_original.nombre_plato}"
        if duplicar else
        plato_original.nombre_plato
    )

    # 5) proviene_de (string)
    proviene_de_str = (
        plato_original.propietario.username
        if plato_original.propietario != request.user else
        ""
    )

    # 6) Copiar variedades
    variedades_copia = deepcopy(plato_original.variedades)

    # 7) Crear nuevo plato (SIN ingredientes todavía)
    nuevo_plato = Plato.objects.create(
        nombre_plato=nombre_copia,
        receta=plato_original.receta,
        ingredientes="",  # 👈 se reconstruye luego
        medios=plato_original.medios,
        categoria=plato_original.categoria,
        elaboracion=plato_original.elaboracion,
        coccion=plato_original.coccion,
        tipos=plato_original.tipos,
        estacionalidad=plato_original.estacionalidad,
        propietario=request.user,
        image=plato_original.image,
        variedades=variedades_copia,
        proviene_de=proviene_de_str,
        id_original=plato_original.id
    )

    # 8) Copiar ingredientes estructurados + reconstruir texto
    ingredientes_texto = []

    for ing in plato_original.ingredientes_en_plato.all():
        IngredienteEnPlato.objects.create(
            plato=nuevo_plato,
            ingrediente=ing.ingrediente,
            cantidad=ing.cantidad,
            unidad=ing.unidad,
        )

        if ing.ingrediente:
            ingredientes_texto.append(ing.ingrediente.nombre)

    # Guardar el campo CharField como en CreateView
    nuevo_plato.ingredientes = ", ".join(ingredientes_texto)
    nuevo_plato.save(update_fields=["ingredientes"])

    # 9) Evitar duplicados en sugeridos_importados
    if plato_original.id not in profile.sugeridos_importados:
        profile.sugeridos_importados.append(plato_original.id)
        profile.save(update_fields=["sugeridos_importados"])

    # 10) Redirigir
    return redirect('descartar-sugerido', plato_id=plato_id)

class AsignarPlato(View):

    def post(self, request):
        tipo = request.POST.get("tipo_elemento")   # "plato" | "lugar"
        objeto_id = request.POST.get("plato_id")
        dia = request.POST.get("dia") or request.session.get("dia_activo")
        momento = request.POST.get("comida")

        if not dia:
            messages.error(request, "No hay día activo seleccionado.")
            return redirect("filtro-de-platos")

        try:
            fecha = datetime.datetime.strptime(dia, "%Y-%m-%d").date()
        except Exception:
            messages.error(request, "Fecha inválida.")
            return redirect("filtro-de-platos")

        request.session["dia_activo"] = dia

        menu_dia, _ = MenuDia.objects.get_or_create(
            propietario=request.user,
            fecha=fecha,
        )

        try:
            if tipo == "plato":
                # plato “en juego”
                plato_base = Plato.objects.get(id=objeto_id, propietario=request.user)

                # ✅ NUEVO: si el form manda platos_ids, asignamos solo esos
                ids_post = [x for x in request.POST.getlist("platos_ids") if x.isdigit()]

                if ids_post:
                    # solo permitimos asignar el plato base o sus hijas
                    allowed_ids = set([plato_base.id] + list(plato_base.variedades_hijas.values_list("id", flat=True)))
                    selected_ids = [int(x) for x in ids_post if int(x) in allowed_ids]

                    platos_a_asignar = list(
                        Plato.objects.filter(id__in=selected_ids, propietario=request.user)
                    )
                else:
                    # comportamiento actual (por ahora)
                    platos_a_asignar = [plato_base] + list(plato_base.variedades_hijas.all())

                creados = 0
                for p in platos_a_asignar:
                    _, created = MenuItem.objects.get_or_create(
                        menu=menu_dia,
                        momento=momento,
                        plato=p,
                        defaults={"elegido": True},
                    )
                    if created:
                        creados += 1

                messages.success(
                    request,
                    f"Asignados {creados}/{len(platos_a_asignar)} platos a {momento}."
                )

            elif tipo == "lugar":
                lugar = Lugar.objects.get(id=objeto_id)
                MenuItem.objects.create(
                    menu=menu_dia,
                    momento=momento,
                    lugar=lugar,
                )
                messages.success(request, f"Lugar {lugar.nombre} asignado correctamente a {momento}.")
            else:
                messages.error(request, "Tipo de elemento inválido.")

        except Exception:
            messages.warning(request, "Ese elemento ya estaba asignado a esa comida en ese día.")

        return redirect("filtro-de-platos")



@login_required
def plato_opciones_asignar(request, pk):
    # Plato base
    plato = get_object_or_404(Plato, pk=pk, propietario=request.user)

    # Padre + hijas
    opciones = [{
        "id": plato.id,
        "nombre": plato.nombre_plato,
    }]

    for v in plato.variedades_hijas.all():
        opciones.append({
            "id": v.id,
            "nombre": v.nombre_plato,
        })

    return JsonResponse({"opciones": opciones})



@login_required
def eliminar_plato_programado(request, nombre_plato, comida, fecha):
    usuario = request.user

    # 1) Normalizar fecha: si viene "YYYY-MM-DD" en string, pasar a date
    if isinstance(fecha, str):
        fecha = datetime.datetime.strptime(fecha, "%Y-%m-%d").date()

    # 2) Traer el menú del día (modelo nuevo)
    menu = get_object_or_404(MenuDia, propietario=usuario, fecha=fecha)

    # 3) Borrar SOLO el item del momento que coincida por nombre (plato o lugar)
    menu.items.filter(momento=comida).filter(
        plato__nombre_plato=nombre_plato
    ).delete()

    # (opcional) si también querés borrar "lugares" por nombre:
    menu.items.filter(momento=comida).filter(
        lugar__nombre=nombre_plato
    ).delete()

    # 4) Si el día quedó sin items, borrar el día completo
    if not menu.items.exists():
        menu.delete()

    return redirect("filtro-de-platos")




MOMENTOS = ["desayuno", "almuerzo", "merienda", "cena"]

def normalizar_dia(dia):
    # Quitar tildes y pasar a mayúsculas
    return ''.join(
        c for c in unicodedata.normalize('NFD', dia.upper())
        if unicodedata.category(c) != 'Mn'
    )


# def generar_elegido_desde_historico(historico, fecha_activa):
#     """Crea un ElegidosXDia para la fecha activa a partir de un HistoricoDia con HistoricoItem."""

#     # 1) limpiar el ElegidosXDia existente
#     ElegidosXDia.objects.filter(
#         user=historico.propietario,
#         el_dia_en_que_comemos=fecha_activa
#     ).delete()

#     # 2) crear nuevo contenedor vacío
#     menu_dia = ElegidosXDia.objects.create(
#         user=historico.propietario,
#         el_dia_en_que_comemos=fecha_activa,
#         platos_que_comemos={}
#     )
#     data = {m: [] for m in MOMENTOS}

#     # 3) agrupar ids por momento
#     ids_por_momento = {m: [] for m in MOMENTOS}
#     for it in historico.items.all():
#         if it.momento in ids_por_momento:
#             ids_por_momento[it.momento].append(it.plato_id_ref)

#     # 4) búsqueda y serialización
#     for momento in MOMENTOS:
#         ids = ids_por_momento[momento]
#         if not ids:
#             continue

#         platos_qs = Plato.objects.filter(id__in=ids)
#         mapa = {p.id: p for p in platos_qs}

#         for pid in ids:
#             p = mapa.get(pid)
#             if not p:
#                 continue  # plato eliminado

#             # evitar duplicados
#             if any(item.get("id_plato") == str(p.id) for item in data[momento]):
#                 continue

#             plato_json = {
#                 "id_plato": str(p.id),
#                 "plato": p.nombre_plato,
#                 "tipo": p.tipos,
#                 "ingredientes": p.ingredientes,
#                 "variedades": {
#                     vid: {
#                         "nombre": info.get("nombre"),
#                         "ingredientes": info.get("ingredientes"),
#                         "elegido": True,
#                     } for vid, info in (p.variedades or {}).items()
#                 },
#                 "elegido": True,
#             }
#             data[momento].append(plato_json)

#     # 5) guardar y devolver
#     menu_dia.platos_que_comemos = data
#     menu_dia.save()
#     return menu_dia


def _validar_y_purgar(historico: HistoricoDia) -> bool:
    """True si TODOS los platos existen. Si falta alguno, borra items + histórico y devuelve False."""
    ids = list(historico.items.values_list("plato_id_ref", flat=True))
    if not ids:
        with transaction.atomic():
            historico.items.all().delete()
            historico.delete()
        return False

    existentes = set(Plato.objects.filter(id__in=ids).values_list("id", flat=True))
    if len(existentes) != len(ids):
        with transaction.atomic():
            historico.items.all().delete()
            historico.delete()
        return False
    return True


@login_required
def random_dia(request, dia_nombre):
    usuario = request.user

    if not dia_nombre:
        return JsonResponse({"error": "Día inválido"}, status=400)

    dia_nombre = normalizar_dia(dia_nombre).upper()[:2]
    if dia_nombre not in ['LU', 'MA', 'MI', 'JU', 'VI', 'SA', 'DO']:
        return JsonResponse({"error": "Día inválido"}, status=400)

    # 1️⃣ Día activo (donde se va a asignar)
    dia_activo = request.session.get('dia_activo')
    if not dia_activo:
        messages.error(request, "No hay un día activo definido.")
        return redirect("filtro-de-platos")

    fecha_activa = datetime.datetime.strptime(dia_activo, "%Y-%m-%d").date()

    # 2️⃣ Obtener platos usados ese día de la semana (histórico REAL)
    items = (
        MenuItem.objects
        .filter(
            menu__propietario=usuario,
            menu__fecha__week_day=(
                ["DO","LU","MA","MI","JU","VI","SA"].index(dia_nombre) + 1
            ),
            plato__isnull=False
        )
        .select_related("plato")
    )

    if not items.exists():
        messages.warning(request, "No hay platos históricos para ese día.")
        return redirect("filtro-de-platos")

    # 3️⃣ Elegir un plato al azar
    plato_random = random.choice([i.plato for i in items])

    # 4️⃣ Crear (o traer) el menú del día activo
    menu_dia, _ = MenuDia.objects.get_or_create(
        propietario=usuario,
        fecha=fecha_activa
    )

    # 5️⃣ Asignar como plato principal (simple)
    try:
        MenuItem.objects.create(
            menu=menu_dia,
            momento="almuerzo",  # o el que vos definas
            plato=plato_random
        )
        messages.success(
            request,
            f"Se asignó aleatoriamente: {plato_random.nombre_plato}"
        )
    except Exception:
        messages.warning(
            request,
            "Ese plato ya estaba asignado en ese día."
        )

    return redirect("filtro-de-platos")

# def eliminar_menu_programado(request):
#     # Recuperar la fecha activa desde la sesión
#     dia_activo = request.session.get("dia_activo", None)

#     if not dia_activo:
#         messages.error(request, "No hay un día activo en la sesión.")
#         return redirect("filtro-de-platos")

#     # Buscar y eliminar el registro
#     elegido = ElegidosXDia.objects.filter(
#         user=request.user,
#         el_dia_en_que_comemos=dia_activo
#     ).first()

#     if elegido:
#         elegido.delete()
#         messages.success(request, f"Se eliminó el menú del {dia_activo}")
#     else:
#         messages.warning(request, f"No había un menú guardado para {dia_activo}")

#     return redirect("filtro-de-platos")