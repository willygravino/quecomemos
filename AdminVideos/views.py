from collections import defaultdict
from urllib.parse import parse_qs, parse_qsl, urlencode, urlparse, urlunparse
from django.db.models import Count
import json
import unicodedata
from django import forms
from django.contrib import messages  # Para mostrar mensajes al usuario
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from AdminVideos.models import Armado, HabitoSemanal, Ingrediente, IngredienteEnPlato, Lugar, MenuDia, MenuItem, Plato, Profile, Mensaje, ProfileIngrediente
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string   # ✅ ← ESTA ES LA CLAVE
from django.http import Http404, HttpRequest, HttpResponseNotAllowed, JsonResponse
from django.urls import reverse, reverse_lazy
from django.contrib.auth.forms import UserCreationForm
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from datetime import datetime, timedelta
from .forms import ArmadoForm, IngredienteEnPlatoFormSet, LugarForm, PlatoFilterForm, PlatoForm, CustomAuthenticationForm
from datetime import date, datetime
from django.contrib.auth.models import User  # Asegúrate de importar el modelo User
from django.db.models import Q, Subquery, OuterRef, Prefetch, Min, Max, F
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
from django.db.models.expressions import OrderBy
from AdminVideos.services.pantry import (
    persist_profile_ingrediente_from_post,
    get_pantry_map,
    sort_items_by_name,
)
from django.utils.http import url_has_allowed_host_and_scheme

# Paso 8.1: eliminar varios platos seleccionados con la misma lógica que eliminar_plato
@login_required
def eliminar_platos_masivo(request):
    # ✅ Solo por POST
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    ids = request.POST.getlist("ids")

    # ✅ Nos quedamos solo con IDs numéricos válidos
    ids_validos = [int(i) for i in ids if str(i).isdigit()]

    if not ids_validos:
        return redirect("filtro-de-platos")

    with transaction.atomic():
        # Perfil del usuario logueado
        perfil = get_object_or_404(Profile, user=request.user)

        # Solo platos del usuario logueado
        platos = Plato.objects.filter(id__in=ids_validos, propietario=request.user)

        for plato in platos:
            # Limpieza de listas
            if plato.id_original and plato.id_original in perfil.sugeridos_descartados:
                perfil.sugeridos_descartados.remove(plato.id_original)

            if plato.id_original and plato.id_original in perfil.sugeridos_importados:
                perfil.sugeridos_importados.remove(plato.id_original)

            # Si es plato padre: borrar variedades hijas
            Plato.objects.filter(plato_padre=plato, propietario=request.user).delete()

            # Borrar plato
            plato.delete()

        perfil.save()

    return redirect("filtro-de-platos")


class ArmadoDeleteView(LoginRequiredMixin, DeleteView):
    model = Armado

    def get_queryset(self):
        return Armado.objects.filter(propietario=self.request.user)

    def get_success_url(self):
        return self.request.GET.get("return_to") or reverse("filtro-de-platos")
    

@login_required
def fijar_o_eliminar_habito(request, es_lugar, objeto_id, comida):
    usuario = request.user

    dia_str = request.session.get("dia_activo")
    if not dia_str:
        messages.error(request, "No hay día activo seleccionado.")
        return redirect("filtro-de-platos")

    dia = datetime.datetime.strptime(dia_str, "%Y-%m-%d").date()
    dia_semana = dia.weekday()

    perfil = usuario.profile
    es_lugar = int(es_lugar)

    if es_lugar == 1:
        lugar = get_object_or_404(Lugar, id=objeto_id, propietario=usuario)

        habito = HabitoSemanal.objects.filter(
            perfil=perfil,
            dia_semana=dia_semana,
            momento=comida,
            lugar=lugar
        ).first()

        if habito:
            habito.delete()
            messages.success(request, f"Se eliminó el hábito de {lugar.nombre} para {comida}.")
        else:
            HabitoSemanal.objects.create(
                perfil=perfil,
                dia_semana=dia_semana,
                momento=comida,
                lugar=lugar
            )
            messages.success(request, f"Se fijó el hábito de {lugar.nombre} para {comida}.")

    else:
        plato = get_object_or_404(Plato, id=objeto_id, propietario=usuario)

        habito = HabitoSemanal.objects.filter(
            perfil=perfil,
            dia_semana=dia_semana,
            momento=comida,
            plato=plato
        ).first()

        nombre = getattr(plato, "nombre_plato", None) or getattr(plato, "nombre", str(plato))

        if habito:
            habito.delete()
            messages.success(request, f"Se eliminó el hábito de {nombre} para {comida}.")
        else:
            HabitoSemanal.objects.create(
                perfil=perfil,
                dia_semana=dia_semana,
                momento=comida,
                plato=plato
            )
            messages.success(request, f"Se fijó el hábito de {nombre} para {comida}.")

    return redirect("filtro-de-platos")




@require_http_methods(["GET", "POST"])
def api_ingredientes(request):

    if request.method == "GET":
        q = (request.GET.get('q') or '').strip()
        qs = Ingrediente.objects.all()
    

        if q:
            q_low = q.lower()

            # Expansiones rápidas (sin tocar modelo)
            EXPAND = {
                "carne": ["nalga", "bola de lomo", "cuadrada", "peceto", "carne picada", "asado", "vacio", "entraña", "roast beef", "ojo de bife", "bife de chorizo"],
                "vaca":  ["nalga", "bola de lomo", "cuadrada", "peceto", "carne picada", "asado", "vacio", "entraña"],
                "res":   ["nalga", "bola de lomo", "cuadrada", "peceto", "carne picada", "asado", "vacio", "entraña"],
                "pollo": ["suprema", "pechuga", "muslo", "pata", "alitas", "pollo entero", "cuarto trasero"],
                "cerdo": ["bondiola", "carré", "costilla", "pechito", "matambre", "paleta", "chuleta", "jamón de cerdo"],
                "cordero": ["pierna", "costillar", "paleta", "chuleta", "cordero trozado"],
                "queso": ["mozzarella", "cremoso", "tybo", "pategrás", "sardo", "reggianito", "azul", "port salut", "ricota"],
            }

            terms = [q]
            if q_low in EXPAND:
                terms = [q] + EXPAND[q_low]   # incluye el texto original también


            from django.db.models import Q
            cond = Q()
            for t in terms:
                cond |= Q(nombre__icontains=t)

            qs = qs.filter(cond)


        ingredientes = qs.order_by('nombre')[:50]

        return JsonResponse({
            "results": [{"id": ing.id, "text": ing.nombre} for ing in ingredientes]
        })

    # if request.method == "GET":
    #     q = (request.GET.get('q') or '').strip()
    #     qs = Ingrediente.objects.all()
    #     if q:
    #         qs = qs.filter(nombre__icontains=q)
    #     ingredientes = qs.order_by('nombre')[:50]
    #     data = [{"id": ing.id, "nombre": ing.nombre} for ing in ingredientes]
    #     return JsonResponse(data, safe=False)

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
    tipo_parametro = (request.GET.get("tipopag") or "Principal").strip()


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
def plato_ingredientes(request: HttpRequest, pk: int):
    # ======================================================
    # 1) Cargar plato + perfil del usuario
    # ======================================================
    plato = get_object_or_404(Plato, pk=pk)
    perfil = get_object_or_404(Profile, user=request.user)

    # Ingredientes del plato (relación intermedia IEP)
    ingredientes_qs = (
        plato.ingredientes_en_plato
        .select_related("ingrediente")
        .all()
    )

    # ======================================================
    # 2) POST: guardar cambios (modo nuevo AJAX o masivo form)
    # ======================================================
    if request.method == "POST":
        post_origen = request.POST.get("post_origen")

        # --------------------------------------------------
        # 2.A) POST modo "ingredientes" (toggle/comentario por ingrediente)
        #     - ahora usa helper compartido
        # --------------------------------------------------
        if post_origen == "ingredientes":
            result = persist_profile_ingrediente_from_post(perfil=perfil, post=request.POST)

            if not result.ok:
                return JsonResponse({"success": False, "error": result.error or "Error"}, status=400)

            return JsonResponse({"success": True})

        # --------------------------------------------------
        # 2.B) POST masivo del form completo
        #     - Se usa cuando guardás toda la lista de una vez
        # --------------------------------------------------
        else:
            # Los que vienen tildados son "a comprar" => tengo=False
            to_buy_ids = set(
                int(x) for x in request.POST.getlist("ingrediente_a_comprar_id") if x.isdigit()
            )

            for iep in ingredientes_qs:
                ing = iep.ingrediente
                if not ing:
                    continue

                ing_id = iep.ingrediente_id
                if not ing_id:
                    continue

                # Si está en to_buy => NO lo tengo
                tengo = (ing_id not in to_buy_ids)

                defaults = {"tengo": tengo}

                # Si lo tengo, registramos compra/actualización (opcional pero útil)
                if tengo:
                    defaults["last_bought_at"] = timezone.now()

                # Comentario del ingrediente
                comentario_key = f"comentario_{ing_id}"
                if comentario_key in request.POST:
                    defaults["comentario"] = (request.POST.get(comentario_key) or "").strip()

                # Si NO lo tengo y no hay comentario, borramos el registro para no llenar la DB
                if (not tengo) and defaults.get("comentario", "") == "":
                    ProfileIngrediente.objects.filter(profile=perfil, ingrediente_id=ing_id).delete()
                else:
                    ProfileIngrediente.objects.update_or_create(
                        profile=perfil,
                        ingrediente_id=ing_id,
                        defaults=defaults,
                    )

            return JsonResponse({"success": True})

    # ======================================================
    # 3) GET: preparar items para renderizar el modal
    #    - lee el estado por ingrediente_id desde ProfileIngrediente
    # ======================================================
    ing_ids = [iep.ingrediente_id for iep in ingredientes_qs if iep.ingrediente_id]

    pantry_map = get_pantry_map(
    perfil=perfil,
    ing_ids=ing_ids,
    only_fields=("ingrediente_id", "tengo", "comentario", "updated_at"),
            )

    items = []
    for iep in ingredientes_qs:
        ing = iep.ingrediente
        if not ing:
            continue

        ing_id = iep.ingrediente_id
        if not ing_id:
            continue

        p = pantry_map.get(ing_id)

        # Si no hay registro, asumimos que NO lo tiene (=> hay que comprar)
        tengo = p.tengo if p else False
        comentario = (p.comentario or "") if p else ""

        items.append({
            "ingrediente_id": ing_id,
            "nombre": ing.nombre,
            "cantidad": iep.cantidad,
            "unidad": iep.unidad,
            "a_comprar": (not tengo),      # True => checkbox checked
            "comentario": comentario,
        })

    # ✅ Orden igual que lista de compras
    sort_items_by_name(items)

    # ======================================================
    # 4) Links / tokens (lo tuyo, sin cambiar lógica)
    # ======================================================
    if not perfil.share_token:
        perfil.ensure_share_token()

    ctx = {
        "plato": plato,
        "items": items,
        "api_token": perfil.share_token,

        # URL de la pantalla de ingredientes del plato (tu vista normal)
        "action_url": request.build_absolute_uri(
            reverse("plato_ingredientes", args=[plato.pk])
        ),

        # URL para COMPARTIR solo este plato (usa tu ruta: s/<token>/plato/<pk>/)
        "plato_share_url": request.build_absolute_uri(
            reverse("compartir-plato", args=[perfil.share_token, plato.pk])
        ),
    }

    return render(request, "AdminVideos/_modal_plato_ingredientes.html", ctx)

from datetime import timedelta
from django.utils import timezone
from django.shortcuts import get_object_or_404, render

def compartir_ing_plato(request, token, pk: int):
    share_user, perfil = _get_user_by_token_or_404(token)
    plato = get_object_or_404(Plato, pk=pk)

    # Ingredientes del plato
    ingredientes_qs = (
        plato.ingredientes_en_plato
        .select_related("ingrediente")
        .all()
    )

    # IDs de ingredientes del plato
    ing_ids = [
        iep.ingrediente_id
        for iep in ingredientes_qs
        if iep.ingrediente_id and iep.ingrediente
    ]

    # Si no hay ingredientes, render vacío
    if not ing_ids:
        if not perfil.share_token:
            perfil.ensure_share_token()
        return render(request, "AdminVideos/compartir_lista.html", {
            "items": [],
            "api_token": perfil.share_token,
            "token": f"user-{perfil.pk}",
        })

    # Estados guardados por ingrediente_id (nuevo modelo)
    pantry_qs = (
        ProfileIngrediente.objects
        .filter(profile=perfil, ingrediente_id__in=ing_ids)
        .only("ingrediente_id", "tengo", "comentario", "last_bought_at")
    )
    pantry_map = {pi.ingrediente_id: pi for pi in pantry_qs}

    now = timezone.now()

    items = []
    for iep in ingredientes_qs:
        ing = iep.ingrediente
        if not ing:
            continue

        pi = pantry_map.get(iep.ingrediente_id)
        comentario = (pi.comentario or "") if pi else ""

        if pi and pi.tengo:
            # Solo mostrar si es "recién comprado" (mismo criterio que compartir_lista)
            if pi.last_bought_at and pi.last_bought_at >= now - timedelta(hours=3):
                estado = "recien-comprado"
            else:
                continue  # tengo normal -> no mostrar
        else:
            estado = "no-tengo"

        items.append({
            "ingrediente_id": iep.ingrediente_id,
            "nombre": ing.nombre,
            "comentario": comentario,
            "estado": estado,
        })

    items.sort(key=lambda i: i["nombre"].casefold())

    if not perfil.share_token:
        perfil.ensure_share_token()

    return render(request, "AdminVideos/compartir_lista.html", {
        "items": items,
        "api_token": perfil.share_token,
        "token": f"user-{perfil.pk}",
    })



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

    # ✅ REFACTORIZADO: POST ingredientes usa helper (sin tocar el resto)
    if request.method == "POST" and post_origen == "ingredientes":
        result = persist_profile_ingrediente_from_post(perfil=perfil, post=request.POST)

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            if not result.ok:
                return JsonResponse({"success": False, "error": result.error or "Error"}, status=400)
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

    # =====================================================
    # Traer estados por ingrediente_id (ProfileIngrediente)
    # =====================================================
    ing_ids = list(agregados.keys())

    pantry_map = get_pantry_map(
        perfil=perfil,
        ing_ids=ing_ids,
        only_fields=("ingrediente_id", "tengo", "comentario", "last_bought_at", "updated_at"),
    )


    now = timezone.now()

    items = []
    for ing_id, data in agregados.items():
        p = pantry_map.get(ing_id)

        # Default igual que hoy: si no hay registro => "no-tengo"
        if not p:
            estado = "no-tengo"
        else:
            if p.tengo is False:
                estado = "no-tengo"
            elif p.last_bought_at and p.last_bought_at >= now - timedelta(hours=3):
                estado = "recien-comprado"
            else:
                estado = "tengo"

        comentario = (p.comentario or "") if p else ""

        items.append({
            "ingrediente_id": ing_id,
            "nombre": data["nombre"],
            "tipo": data["tipo"],
            "detalle": data["detalle"],
            "estado": estado,
            "comentario": comentario,   # 👈 IMPORTANTÍSIMO para el template
            "needed_by": data["needed_by"],
            "cantidades": [{"unidad": u, "total": t} for u, t in data["cantidades"].items()],
            "usos": data["usos"],
        })

    sort_items_by_name(items)

    token = perfil.ensure_share_token()
    share_url = request.build_absolute_uri(reverse("compartir-lista", args=[token]))

    summary = {
        "total": len(items),
        "to_buy": sum(i["estado"] == "no-tengo" for i in items),
        "fresh": sum(i["estado"] == "recien-comprado" for i in items),
        "have": sum(i["estado"] == "tengo" for i in items),
    }

    context = {
        "menues": menues,
        "items_elegidos": items_elegidos,
        "share_url": share_url,
        "shopping": {"items": items, "summary": summary},
        "parametro": "lista-compras",
    }

    return render(request, "AdminVideos/lista_de_compras.html", context)




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
    # AHORA por ProfileIngrediente (NO por nombre)
    # =====================================================
    pantry_qs = (
        ProfileIngrediente.objects
        .filter(profile=perfil, ingrediente_id__in=agregados.keys())
        .only("ingrediente_id", "tengo", "comentario", "last_bought_at")
    )
    pantry_map = {pi.ingrediente_id: pi for pi in pantry_qs}

    now = timezone.now()

    items = []
    for ing_id, data in agregados.items():
        pi = pantry_map.get(ing_id)

        comentario = (pi.comentario or "") if pi else ""

        if pi and pi.tengo:
            # Solo mostrar si es reciente
            if pi.last_bought_at and pi.last_bought_at >= now - timedelta(hours=3):
                estado = "recien-comprado"
            else:
                continue
        else:
            # NO hay registro, o tengo=False => por defecto: falta comprar
            estado = "no-tengo"

        items.append({
            "ingrediente_id": ing_id,
            "nombre": data["nombre"],
            "comentario": comentario,
            "estado": estado,
            "needed_by": data["needed_by"],
        })



    items.sort(key=lambda i: i["nombre"].casefold())

    # Tokens
    if not perfil.share_token:
        perfil.ensure_share_token()

    return render(request, "AdminVideos/compartir_lista.html", {
        "items": items,
        "token": f"user-{perfil.pk}",
        "api_token": perfil.share_token,
        "DEBUG_VISTA": f"compartir_lista items={len(items)}",
    })


@csrf_exempt
@require_POST
def api_toggle_item(request, token):
    user, perfil = _get_user_by_token_or_404(token)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

    ing_id = payload.get("ingrediente_id", None)
    checked = payload.get("checked", None)

    if ing_id is None or checked is None:
        return JsonResponse({"ok": False, "error": "ingrediente_id y checked requeridos"}, status=400)

    try:
        ing_id = int(ing_id)
    except Exception:
        return JsonResponse({"ok": False, "error": "ingrediente_id inválido"}, status=400)

    if not Ingrediente.objects.filter(pk=ing_id).exists():
        return JsonResponse({"ok": False, "error": "Ingrediente no existe"}, status=404)

    checked = bool(checked)

    pi = (
        ProfileIngrediente.objects
        .filter(profile=perfil, ingrediente_id=ing_id)
        .only("id", "comentario")
        .first()
    )
    comentario = (pi.comentario or "").strip() if pi else ""

    if checked:
        obj, _ = ProfileIngrediente.objects.update_or_create(
            profile=perfil,
            ingrediente_id=ing_id,
            defaults={"tengo": True, "last_bought_at": timezone.now()},
        )
        return JsonResponse({
            "ok": True,
            "ingrediente_id": ing_id,
            "tengo": True,
            "last_bought_at": obj.last_bought_at.isoformat() if obj.last_bought_at else None,
        })

    # checked=False => "no tengo"
    # Si no hay comentario, volvemos al default (sin registro)
    if comentario == "":
        ProfileIngrediente.objects.filter(profile=perfil, ingrediente_id=ing_id).delete()
        return JsonResponse({"ok": True, "ingrediente_id": ing_id, "tengo": False, "last_bought_at": None})

    # Si hay comentario, lo conservamos, pero marcamos tengo=False
    obj, _ = ProfileIngrediente.objects.update_or_create(
        profile=perfil,
        ingrediente_id=ing_id,
        defaults={"tengo": False},
    )
    return JsonResponse({
        "ok": True,
        "ingrediente_id": ing_id,
        "tengo": False,
        "last_bought_at": obj.last_bought_at.isoformat() if obj.last_bought_at else None,
    })


# @csrf_exempt
# @require_POST
# def api_toggle_item(request, token):
#     user, perfil = _get_user_by_token_or_404(token)

#     try:
#         payload = json.loads(request.body.decode("utf-8"))
#     except Exception:
#         return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

#     ing_id = payload.get("ingrediente_id", None)
#     checked = payload.get("checked", None)

#     if ing_id is None or checked is None:
#         return JsonResponse({"ok": False, "error": "ingrediente_id y checked requeridos"}, status=400)

#     try:
#         ing_id = int(ing_id)
#     except Exception:
#         return JsonResponse({"ok": False, "error": "ingrediente_id inválido"}, status=400)

#     ing = Ingrediente.objects.filter(pk=ing_id).only("nombre").first()
#     if not ing:
#         return JsonResponse({"ok": False, "error": "Ingrediente no existe"}, status=404)

#     nombre_norm = ing.nombre.casefold()
#     checked = bool(checked)

#     # En LISTA COMPARTIDA: checked=True => TENGO (comprado)
#     if checked:
#         obj, _created = IngredienteEstado.objects.update_or_create(
#             user=user,
#             nombre=nombre_norm,
#             defaults={
#                 "estado": IngredienteEstado.Estado.TENGO,
#                 "last_bought_at": timezone.now(),
#             },
#         )
#         return JsonResponse({
#             "ok": True,
#             "ingrediente_id": ing_id,
#             "estado": obj.estado,
#             "last_bought_at": obj.last_bought_at.isoformat() if obj.last_bought_at else None,
#         })

#     # checked=False => NO_TENGO
#     existing = (
#         IngredienteEstado.objects
#         .filter(user=user, nombre=nombre_norm)
#         .only("comentario")
#         .first()
#     )

#     # Modelo A: NO_TENGO sin comentario => borrar registro
#     if existing and (existing.comentario or "").strip():
#         IngredienteEstado.objects.filter(user=user, nombre=nombre_norm).update(
#             estado=IngredienteEstado.Estado.NO_TENGO
#         )
#     else:
#         IngredienteEstado.objects.filter(user=user, nombre=nombre_norm).delete()

#     return JsonResponse({
#         "ok": True,
#         "ingrediente_id": ing_id,
#         "estado": IngredienteEstado.Estado.NO_TENGO,
#         "last_bought_at": None,
#     })



# @csrf_exempt
# @require_POST
# def api_toggle_item(request, token):
#     user, perfil = _get_user_by_token_or_404(token)

#     try:
#         payload = json.loads(request.body.decode("utf-8"))
#     except Exception:
#         return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

#     ing_id = payload.get("ingrediente_id", None)
#     checked = payload.get("checked", None)

#     if ing_id is None or checked is None:
#         return JsonResponse({"ok": False, "error": "ingrediente_id y checked requeridos"}, status=400)

#     try:
#         ing_id = int(ing_id)
#     except Exception:
#         return JsonResponse({"ok": False, "error": "ingrediente_id inválido"}, status=400)

#     # Validar que existe el ingrediente
#     ing = Ingrediente.objects.filter(pk=ing_id).only("id").first()
#     if not ing:
#         return JsonResponse({"ok": False, "error": "Ingrediente no existe"}, status=404)

#     checked = bool(checked)

#     # checked=True => tengo (comprado)
#     if checked:
#         obj, _created = ProfileIngrediente.objects.update_or_create(
#             profile=perfil,
#             ingrediente_id=ing_id,
#             defaults={
#                 "tengo": True,
#                 "last_bought_at": timezone.now(),
#             },
#         )
#         return JsonResponse({
#             "ok": True,
#             "ingrediente_id": ing_id,
#             "tengo": True,
#             "last_bought_at": obj.last_bought_at.isoformat() if obj.last_bought_at else None,
#         })

#     # checked=False => no tengo (pero NO borramos el registro)
#     obj, _created = ProfileIngrediente.objects.update_or_create(
#         profile=perfil,
#         ingrediente_id=ing_id,
#         defaults={
#             "tengo": False,
#         },
#     )
#     return JsonResponse({
#         "ok": True,
#         "ingrediente_id": ing_id,
#         "tengo": False,
#         "last_bought_at": obj.last_bought_at.isoformat() if obj.last_bought_at else None,
#     })






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

# @login_required
# def eliminar_plato(request, plato_id):
#     plato = get_object_or_404(Plato, id=plato_id, propietario=request.user)

#     if request.method == 'POST':
#         perfil = get_object_or_404(Profile, user=request.user)

#         if plato.id_original in perfil.sugeridos_descartados:
#             perfil.sugeridos_descartados.remove(plato.id_original)

#         if plato.id_original in perfil.sugeridos_importados:
#             perfil.sugeridos_importados.remove(plato.id_original)

#         perfil.save()
#         plato.delete()
#         return redirect('filtro-de-platos')

#     # Si viene por GET, no borrar:
#     from django.http import HttpResponseNotAllowed
#     return HttpResponseNotAllowed(['POST'])


@login_required
def eliminar_plato(request, plato_id):
    # ✅ Seguridad: solo permite borrar platos del usuario logueado
    plato = get_object_or_404(Plato, id=plato_id, propietario=request.user)

    # ✅ Solo por POST
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    with transaction.atomic():
        # Perfil (siempre del usuario logueado)
        perfil = get_object_or_404(Profile, user=request.user)

        # Limpieza de listas (si id_original es None, no hacemos nada)
        if plato.id_original and plato.id_original in perfil.sugeridos_descartados:
            perfil.sugeridos_descartados.remove(plato.id_original)

        if plato.id_original and plato.id_original in perfil.sugeridos_importados:
            perfil.sugeridos_importados.remove(plato.id_original)

        perfil.save()

        # ✅ Si es PLATO PADRE: borrar TODAS sus variedades hijas
        # (extra seguro: también filtramos por propietario=request.user)
        Plato.objects.filter(plato_padre=plato, propietario=request.user).delete()

        # ✅ Borrar el plato (padre o variedad)
        plato.delete()

    return redirect("filtro-de-platos")



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


# ==========================================
# Helper: agregar params a una URL (sin romper querystring)
# ==========================================
def _add_qs(url, **params):
    parts = urlparse(url)
    q = dict(parse_qsl(parts.query))
    q.update({k: v for k, v in params.items() if v is not None})
    return urlunparse(parts._replace(query=urlencode(q)))


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
            # 'Dash': 'AdminVideos/ppal_form.html',
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
        # "Dash": ["Principal", "Guarnicion", "Entrada", "Picada"],
        "Picada": ["Picada","Guarnicion", "Entrada"],
        "Salsa": ["Salsa", "Dip", "Guarnicion", "Entrada"],
    }

    # 1) Alinear “tipos” con tu modelo actual (CharField CSV)
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        template_param = self.request.GET.get('tipopag')
        # if template_param == "Dash":
        #     template_param = "Principal"

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
            form.fields['tipos'].choices = Plato.TIPOS_CHOICES
            form.fields['tipos'].initial = []

        # Imagen no requerida (por si el widget envia archivo sin nombre)
        if 'image' in form.fields:
            form.fields['image'].required = False

        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        template_param = self.request.GET.get('tipopag')
        context['items'] = [k for (k, _) in Plato.TIPOS_CHOICES]
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

       
        # ✅ Unificamos detección AJAX (así no te quedan 2 returns distintos)
        is_ajax = self.request.headers.get("X-Requested-With") == "XMLHttpRequest"

        # --- Validación del formset ---
        if not ingrediente_formset.is_valid():
            # Si vino por AJAX (modal)
            if is_ajax:
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

        # --- Guardado atómico (no tocamos tu lógica) ---
        with transaction.atomic():
            plato = form.save(commit=False)
            plato.propietario = self.request.user

            # # # --- Guardar variedades ---
            # # variedades = {}
            # # for i in range(1, 7):
            # #     variedad = form.cleaned_data.get(f'variedad{i}')
            # #     ingredientes_variedad_str = form.cleaned_data.get(f'ingredientes_de_variedad{i}')
            # #     if variedad:
            # #         variedades[f"variedad{i}"] = {
            # #             "nombre": variedad,
            # #             "ingredientes": ingredientes_variedad_str,
            # #             "elegido": True
            # #         }

            # plato.variedades = variedades
            plato.save()
            form.save_m2m()

            ingrediente_formset.instance = plato
            ingrediente_formset.save()

        # ==========================================
        # ✅ NUEVO: resolver "return_to" (volver a la página origen)
        # y agregar guardado=ok para que aparezca el toast
        # ==========================================
        return_to = (
            self.request.POST.get("return_to")
            or self.request.GET.get("return_to")
            or self.request.META.get("HTTP_REFERER")
            or ""
        )

        if return_to and not url_has_allowed_host_and_scheme(return_to, allowed_hosts={self.request.get_host()}):
            return_to = ""

        # --- Si es un request AJAX (modal): devolvemos redirect_url ---
        if is_ajax:
            redirect_url = _add_qs(return_to or "/", msg="Guardado OK.", level="success")
            return JsonResponse({
                "success": True,
                "redirect_url": redirect_url,   # 👈 clave para que el JS navegue
                "nombre": plato.nombre_plato,
                "id": plato.id,
            })

        # --- Si NO es AJAX: si hay return_to, volvemos ahí ---
        if return_to:
            return redirect(_add_qs(return_to, msg="Guardado OK.", level="success"))

        # --- Comportamiento normal (tu lógica original) ---
        template_param = self.request.GET.get('tipopag')
        if template_param:
            tail = _add_qs(f"?tipopag={template_param}", msg="Guardado OK.", level="success")
        else:
            tail = _add_qs("", msg="Guardado OK.", level="success")
        return redirect(f"{reverse('videos-create')}{tail}")


class PlatoUpdate(LoginRequiredMixin, UpdateView):
    model = Plato
    form_class = PlatoForm
    template_name = "AdminVideos/plato_update.html"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.propietario != self.request.user:
            raise PermissionDenied("No tienes permiso para editar este plato.")
        return obj

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
        # if not form.initial.get("tipos"):
        #     tipopag = self.request.GET.get("tipopag")
        #     valid_keys = {k for k, _ in Plato.TIPOS_CHOICES}
        #     if tipopag in valid_keys:
        #         form.fields["tipos"].initial = [tipopag]

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

        # 👉 TIPOS: enviar TODOS al template (para render del menú lateral)
        context["items"] = [k for (k, _) in Plato.TIPOS_CHOICES]

        # ✅ tipopag SOLO para "menú activo" (contexto de navegación)
        # 1) si viene en la URL del update, usarlo
        tipopag = (self.request.GET.get("tipopag") or "").strip()

        # 2) si no viene, sacarlo del return_to (?tipopag=...)
        if not tipopag:
            return_to = (
                self.request.GET.get("return_to")
                or self.request.POST.get("return_to")
                or ""
            ).strip()

            if return_to:
                qs = parse_qs(urlparse(return_to).query)
                tipopag = (qs.get("tipopag") or [""])[0].strip()

        # 3) si no hay origen, NO inventamos nada
        context["tipopag"] = tipopag  # puede ser ""

        # ✅ Variedades (hijos) en orden fijo
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

        # Helper: agregar querystring sin romper el existente
        def _add_qs(url, **params):
            parts = urlparse(url)
            q = dict(parse_qsl(parts.query))
            q.update({k: v for k, v in params.items() if v is not None})
            return urlunparse(parts._replace(query=urlencode(q)))

        with transaction.atomic():
            plato = form.save(commit=False)
            plato.propietario = self.request.user

            # reconstruir string "ingredientes" desde el formset
            # lista_ingredientes = []
            # for ing_form in ingrediente_formset:
            #     if ing_form.cleaned_data and not ing_form.cleaned_data.get("DELETE", False):
            #         nombre = ing_form.cleaned_data.get("nombre_ingrediente")
            #         texto = (nombre or "").strip()
            #         if texto:
            #             lista_ingredientes.append(texto)

            # plato.ingredientes = ", ".join(lista_ingredientes)

            plato.save()
            form.save_m2m()

            ingrediente_formset.instance = plato
            ingrediente_formset.save()

        # Resolver return_to (para volver a donde fue llamado)
        return_to = (
            self.request.POST.get("return_to")
            or self.request.GET.get("return_to")
            or self.request.META.get("HTTP_REFERER")
            or "/"
        )

        # Seguridad: evitar redirecciones a otro dominio
        if return_to and not url_has_allowed_host_and_scheme(return_to, allowed_hosts={self.request.get_host()}):
            return_to = "/"

        redirect_url = _add_qs(return_to, msg="Modificado OK.", level="success")

        # 1️⃣ Si fue llamado desde un modal (AJAX), responder con JSON + redirect_url
        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({
                "success": True,
                "redirect_url": redirect_url,
                "nombre": plato.nombre_plato,
                "id": plato.id,
            })

        # 2️⃣ No-AJAX: volver a donde fue llamado con toast
        return redirect(redirect_url)
 


    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        print("Errores al editar plato:", form.errors)
        ingrediente_formset = context.get("ingrediente_formset")
        if ingrediente_formset:
            for i, f in enumerate(ingrediente_formset.forms):
                if f.errors:
                    print(f"Errores en ingrediente #{i}: {f.errors}")
        return self.render_to_response(context)





class PlatoDetail(DetailView):
    model = Plato
    template_name = "AdminVideos/plato_detail.html"  # fallback normal
    context_object_name = "plato"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plato = self.get_object()

        # Tipos: string "Entrada,Principal" -> lista
        if plato.tipos:
            context["tipos_lista"] = [t.strip() for t in plato.tipos.split(",") if t.strip()]
        else:
            context["tipos_lista"] = []

        # ✅ Variedades hijas (usa related_name="variedades_hijas")
        context["variedades"] = plato.variedades_hijas.all().order_by("nombre_plato")

        # ✅ Padre (si este plato es una variedad)
        context["plato_padre"] = plato.plato_padre  # puede ser None

        return context

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data()

        # AJAX: devolver parcial como JSON
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            html = render_to_string(
                "AdminVideos/plato_detail_content.html",
                context,
                request=request
            )
            return JsonResponse({"html": html})

        return super().get(request, *args, **kwargs)
    

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

        print("VARIEDAD DISPATCH view=", self.__class__.__name__)
        print("VARIEDAD DISPATCH path=", request.path)
        print("VARIEDAD DISPATCH kwargs=", kwargs)
        print(">>> HIT PlatoVariedadCreate", request.method, request.path, kwargs)


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
            tipopag = raw or "Principal"

        # hack simple: reutiliza tu mapping interno de PlatoCreate.get_template_names
        self.request.GET._mutable = True
        self.request.GET["tipopag"] = tipopag
        self.request.GET._mutable = False

        return super().get_template_names()


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["items"] = [k for (k, _) in Plato.TIPOS_CHOICES]

        tipopag = self.request.GET.get("tipopag")
        if not tipopag:
            raw = (self.padre.tipos or "").split(",")[0].strip()
            tipopag = raw or "Principal"
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

            # ✅ (1) RESTAURAR: reconstruir string "ingredientes" ANTES del save
            lista_ingredientes = []
            for ing_form in ingrediente_formset:
                if ing_form.cleaned_data and not ing_form.cleaned_data.get("DELETE", False):
                    nombre = ing_form.cleaned_data.get("nombre_ingrediente")
                    texto = (nombre or "").strip()
                    if texto:
                        lista_ingredientes.append(texto)
            plato.ingredientes = ", ".join(lista_ingredientes)

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

                nombres = [
                    rel.ingrediente.nombre
                    for rel in self.padre.ingredientes_en_plato.select_related("ingrediente").all()
                    if rel.ingrediente_id and rel.ingrediente and rel.ingrediente.nombre
                ]
                plato.ingredientes = ", ".join(nombres)
                plato.save(update_fields=["ingredientes"])
            else:
                ingrediente_formset.save()

            # ✅ (2) NO volver a guardar si ya se guardó en el else
            # (si no hay_al_menos_uno == False, usamos bulk_create arriba; si True, ya hicimos save)
            # ingrediente_formset.save()  <- eliminado

        # --- destino: volver al padre, preservando return_to + toast ---
        return_to = (
            self.request.POST.get("return_to")
            or self.request.GET.get("return_to")
            or ""
        )

        tipopag = (self.request.GET.get("tipopag") or self.request.POST.get("tipopag") or "").strip()

        parent_url = reverse("videos-update", kwargs={"pk": self.padre.id})

        if return_to:
            parent_url = _add_qs(parent_url, return_to=return_to)

        if tipopag:
            parent_url = _add_qs(parent_url, tipopag=tipopag)

        parent_url = _add_qs(parent_url, msg="Variedad OK.", level="success")

        # AJAX (modal)
        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({
                "success": True,
                "redirect_url": parent_url,
                "nombre": plato.nombre_plato,
                "id": plato.id,
            })

        # pantalla completa
        return redirect(parent_url)


    def form_invalid(self, form):
        # Si es AJAX, devolvemos JSON con el HTML del form + errores
        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            context = self.get_context_data(form=form)

            # IMPORTANTE: si el POST venía con formset también, pásalo para que se renderice
            if "ingrediente_formset" not in context:
                context["ingrediente_formset"] = IngredienteEnPlatoFormSet(self.request.POST)

            html = render_to_string(
                "AdminVideos/plato_form_inner.html",
                context,
                request=self.request
            )
            return JsonResponse({"success": False, "html": html}, status=400)

        # No-AJAX: comportamiento normal
        return super().form_invalid(form)



# class PlatoVariedadUpdate(PlatoUpdate):
#     def dispatch(self, request, *args, **kwargs):
#         self.object = self.get_object()

#         if self.object.plato_padre_id is None:
#             raise PermissionDenied("Este plato no es una variedad.")

#         if self.object.propietario_id != request.user.id:
#             raise PermissionDenied()
        
#         self.padre = self.object.plato_padre

#         return super().dispatch(request, *args, **kwargs)
    
#     def get_success_url(self):
#         # cuando se guarda una VARIEDAD, el "éxito" debe volver al PADRE
#         url = reverse("videos-update", kwargs={"pk": self.padre.id})

#         rt = self.request.GET.get("return_to")
#         if rt:
#             url += "?" + urlencode({"return_to": rt})

#         return url
    
#     def form_valid(self, form):
#         # usa la lógica de guardado del update normal
#         resp = super().form_valid(form)

#         # ✅ si es AJAX (modal), respetar JSON (tu JS ya cierra y recarga)
#         if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
#             return resp

#         # ✅ pantalla completa: volver al padre
#         return redirect(reverse("videos-update", kwargs={"pk": self.padre.id}))


class PlatoVariedadUpdate(PlatoUpdate):
    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.plato_padre_id is None:
            raise PermissionDenied("Este plato no es una variedad.")

        if self.object.propietario_id != request.user.id:
            raise PermissionDenied()

        self.padre = self.object.plato_padre

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        # cuando se guarda una VARIEDAD, el "éxito" debe volver al PADRE
        url = reverse("videos-update", kwargs={"pk": self.padre.id})

        rt = self.request.GET.get("return_to")
        if rt:
            url += "?" + urlencode({"return_to": rt})

        return url

    def _parent_url(self):
        """
        URL final al padre, preservando return_to y tipopag
        (mismo espíritu que tu create).
        """
        url = reverse("videos-update", kwargs={"pk": self.padre.id})

        rt = (self.request.POST.get("return_to") or self.request.GET.get("return_to") or "").strip()
        tp = (self.request.POST.get("tipopag") or self.request.GET.get("tipopag") or "").strip()

        params = {}
        if rt:
            params["return_to"] = rt
        if tp:
            params["tipopag"] = tp

        if params:
            url += "?" + urlencode(params)

        return url

    def form_valid(self, form):
        # usa la lógica de guardado del update normal
        super().form_valid(form)

        parent_url = self._parent_url()

        # ✅ si es AJAX (modal), devolver JSON con redirect_url al PADRE
        # (NO devolvemos el resp del super(), porque ese suele apuntar a la principal)
        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True, "redirect_url": parent_url})

        # ✅ pantalla completa: volver al padre
        return redirect(parent_url)



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
    # Si no se selecciona ninguna de las dos opciones, no mostrar nada
    if quecomemos != "quecomemos" and misplatos != "misplatos":
        return {
                    "armados": [],
                    "platos": Plato.objects.none()}
                
    armados_virtuales = []
    
    # Caso especial: las Picadas se construyen desde Armado
    if tipo_parametro == "Picada":
        armados_qs = Armado.objects.none()

        if misplatos == "misplatos":
            qs_mis_armados = Armado.objects.filter(
                propietario=usuario,
                tipo_armado="Picada",
            )
            armados_qs = armados_qs | qs_mis_armados

        if quecomemos == "quecomemos":
            usuario_quecomemos = User.objects.filter(username="quecomemos").first()
            if usuario_quecomemos:
                qs_quecomemos_armados = Armado.objects.filter(
                    propietario=usuario_quecomemos,
                    tipo_armado="Picada",
                )
                armados_qs = armados_qs | qs_quecomemos_armados

        if palabra_clave:
            armados_qs = armados_qs.filter(
                Q(nombre__icontains=palabra_clave) |
                Q(items__nombre_plato__icontains=palabra_clave) |
                Q(items__ingredientes__icontains=palabra_clave)
            ).distinct()

        armados_qs = armados_qs.prefetch_related("items").order_by("-id")

        platos_virtuales = []
        for armado in armados_qs:
            plato_virtual = Plato(
                id=-armado.id,  # negativo para evitar choque con ids reales
                nombre_plato=armado.nombre,
                tipos="Picada",
                propietario=armado.propietario,
                ingredientes=", ".join(
                    armado.items.values_list("nombre_plato", flat=True)
                ),
            )

            # atributos extra que el template espera
            plato_virtual.es_armado = True
            plato_virtual.armado_obj = armado
            plato_virtual.programaciones_count = 0
            plato_virtual.ultima_programacion = None
            plato_virtual.dias_desde_ultima = None
            plato_virtual.variedades_count = 0
            plato_virtual.proviene_de = ""
            # plato_virtual.image_url = "/media/avatares/tabla_picada.png"
            # plato_virtual.variedades_hijas = []

            platos_virtuales.append(plato_virtual)

        armados_virtuales = platos_virtuales    

        # return platos_virtuales
                

    # Comenzamos con un queryset vacío
    platos_qs = Plato.objects.none()

    # 🔹 Platos del usuario logueado
    if misplatos == "misplatos":
        qs_misplatos = Plato.objects.filter(
            propietario=usuario,
            plato_padre__isnull=True
        )
        platos_qs = platos_qs | qs_misplatos

    # 🔹 Platos de "quecomemos" (filtrando descartados)
    if quecomemos == "quecomemos":
        usuario_quecomemos = User.objects.filter(username="quecomemos").first()
        if usuario_quecomemos:
            platos_descartados = usuario.profile.sugeridos_descartados or []
            qs_quecomemos = Plato.objects.filter(
                propietario=usuario_quecomemos,
                plato_padre__isnull=True
            ).exclude(id__in=platos_descartados)
            platos_qs = platos_qs | qs_quecomemos

    # 🔹 Aplicar filtros adicionales
    if tipo_parametro:
        platos_qs = platos_qs.filter(tipos__icontains=tipo_parametro)

    if medios and medios != "-":
        platos_qs = platos_qs.filter(medios=medios)

    if categoria and categoria != "-":
        platos_qs = platos_qs.filter(categoria=categoria)

    if dificultad and dificultad != "-":
        platos_qs = platos_qs.filter(dificultad=dificultad)

    if palabra_clave:
        platos_qs = platos_qs.filter(
            Q(ingredientes__icontains=palabra_clave) |
            Q(nombre_plato__icontains=palabra_clave)
        )

    # Orden de prioridad de los platos:
    # 1) Menos días programados primero (0 = nunca usado → arriba del todo)
    # 2) A igualdad de días, los que hace más tiempo que no aparecen
    #    (NULL = nunca programado → primero; fechas viejas → antes que recientes)
    # 3) Como desempate final, los más nuevos (-id)

    # queryset ANOTADO para variedades (hijas) del usuario "usuario"
    variedades_qs = Plato.objects.annotate(
        programaciones_count=Count(
            "en_menus__menu__fecha",
            filter=Q(en_menus__menu__propietario=usuario) & Q(en_menus__plato__isnull=False),
            distinct=True,
        ),
        ultima_programacion=Max(
            "en_menus__menu__fecha",
            filter=Q(en_menus__menu__propietario=usuario) & Q(en_menus__plato__isnull=False),
        ),
    ).order_by(
        "programaciones_count",
        OrderBy(F("ultima_programacion"), descending=False, nulls_first=True),
        "-id",
    )

    platos_qs = platos_qs.annotate(
        programaciones_count=Count(
            "en_menus__menu__fecha",
            filter=Q(en_menus__menu__propietario=usuario) & Q(en_menus__plato__isnull=False),
            distinct=True,
        ),
        ultima_programacion=Max(
            "en_menus__menu__fecha",
            filter=Q(en_menus__menu__propietario=usuario) & Q(en_menus__plato__isnull=False),
        ),
        variedades_count=Count("variedades_hijas", distinct=True),
    ).order_by(
        "programaciones_count",
        OrderBy(F("ultima_programacion"), descending=False, nulls_first=True),
        "-id",
    ).prefetch_related(
        Prefetch("variedades_hijas", queryset=variedades_qs)
    )

    # # Si hay armados (caso Picada), agregarlos antes del queryset
    # if armados_virtuales:
    #     return list(armados_virtuales) + list(platos_qs)
    
    return {
    "armados": armados_virtuales,
    "platos": platos_qs,
            }   



@login_required(login_url=reverse_lazy('login'), redirect_field_name=None)
def FiltroDePlatos(request):

    # Obtener la fecha actual
    fecha_actual = datetime.datetime.now().date()

    # Obtener el usuario actual
    usuario = request.user
    try:
        perfil = usuario.profile
    except Profile.DoesNotExist:
        return redirect("profile-create")

    # DIAS_ES = ['LU', 'MA', 'MI', 'JU', 'VI', 'SA', 'DO']  # tu mapeo

    # Recuperamos los hábitos semanales del usuario
    habitos = HabitoSemanal.objects.filter(perfil=perfil).select_related("plato", "lugar")

    habitos_set = set()
    for h in habitos:
        if h.plato_id:
            habitos_set.add(("plato", h.plato_id, h.dia_semana, h.momento))
        elif h.lugar_id:
            habitos_set.add(("lugar", h.lugar_id, h.dia_semana, h.momento))


    # Calcular y agregar las fechas y nombres de los días para los próximos 6 días
    dias_desde_hoy = [(fecha_actual + timedelta(days=i)) for i in range(0, 7)]

    for fecha in dias_desde_hoy:
        dia_semana = fecha.weekday()  # 0=lunes ... 6=domingo

        # Filtrar hábitos para el día actual
        habitos_del_dia = [h for h in habitos if h.dia_semana == dia_semana]

        if not habitos_del_dia:
            continue  # Si no hay hábitos para ese día, pasamos al siguiente

        # Verificar si ya existe un menú para este día
        menu_dia, creado = MenuDia.objects.get_or_create(
            propietario=usuario,
            fecha=fecha
        )

        # Solo asignar los hábitos si el menú se acaba de crear (es decir, no existía previamente)
        if creado:
            # Asignar los platos y lugares fijados a ese día y momento
            for habito in habitos_del_dia:
                momento = habito.momento

                if habito.plato_id:
                    plato = habito.plato

                    platos_a_asignar = [plato] + list(plato.variedades_hijas.all())

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
                        f"Se asignaron {creados}/{len(platos_a_asignar)} platos al menú de {fecha} en {momento}."
                    )

                elif habito.lugar_id:
                    lugar = habito.lugar

                    _, created = MenuItem.objects.get_or_create(
                        menu=menu_dia,
                        momento=momento,
                        lugar=lugar,
                        defaults={"elegido": True},
                    )

                    if created:
                        messages.success(
                            request,
                            f"Se asignó el lugar {lugar.nombre} al menú de {fecha} en {momento}."
                        )

           

    primer_dia = dias_desde_hoy[0].isoformat()

    # ✅ Asegurar dia_activo siempre (string "YYYY-MM-DD")
    dia_activo = request.session.get("dia_activo") or primer_dia
    request.session["dia_activo"] = dia_activo  # deja persistido para próximos requests

    # ✅ Convertir a date para poder usar |date en template
    dia_activo_obj = datetime.datetime.strptime(dia_activo, "%Y-%m-%d").date()

    dias_programados = set()  # Usamos set para evitar fechas repetidas

    # Recuperar los parámetros desde la sesión y la URL
    tipo_parametro, quecomemos, misplatos, medios, categoria, dificultad, palabra_clave = obtener_parametros_sesion(request)
    tipopag = (request.GET.get("tipopag") or tipo_parametro or "Principal").strip()
    tipo_parametro = tipopag

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

        resultado_filtro = filtrar_platos(
            usuario=usuario,
            tipo_parametro=tipo_parametro,
            quecomemos=quecomemos,
            misplatos=misplatos,
            medios=medios,
            categoria=categoria,
            dificultad=dificultad,
            palabra_clave=palabra_clave
        )

        armados = resultado_filtro["armados"]
        platos = resultado_filtro["platos"]

        hoy = timezone.localdate()

        for p in armados:
            p.dias_desde_ultima = (hoy - p.ultima_programacion).days if getattr(p, "ultima_programacion", None) else None

        for p in platos:
            p.dias_desde_ultima = (hoy - p.ultima_programacion).days if getattr(p, "ultima_programacion", None) else None

            for v in p.variedades_hijas.all():
                v.dias_desde_ultima = (hoy - v.ultima_programacion).days if getattr(v, "ultima_programacion", None) else None
       

    # REFACTORIZACIÓN
    fechas_existentes = list(
        MenuDia.objects.filter(
            propietario=usuario,
            fecha__gte=fecha_actual
        ).values_list('fecha', flat=True)
    )

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


    # dia_activo = request.session.get('dia_activo', None)  # 🟢 Recuperamos la fecha activa

    dia_activo = request.session.get('dia_activo', None)  # sigue siendo string "YYYY-MM-DD"
    dia_activo_obj = None
    if dia_activo:
        dia_activo_obj = datetime.datetime.strptime(dia_activo, "%Y-%m-%d").date()

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

        dia_semana = fec.weekday()

        # Verificación para agregar solo platos válidos
        if item.plato:
            # si item.plato
            fijo = ("plato", item.plato.id, dia_semana, item.momento) in habitos_set

            platos_dia_x_dia[fec][item.momento].append({
                "menuitem_id": item.id,                 # ✅ este es el que necesitamos para extras
                "objeto_id": item.plato.id,              # ✅ para seguir yendo a videos-update
                "nombre": item.plato.nombre_plato,
                "fijo": fijo,
                "tipo": item.plato.tipos,
                "es_lugar": False
                # "dia_semana": dia_semana,
            })

        # Verificación para agregar solo lugares válidos
        elif item.lugar:
            fijo = ("lugar", item.lugar.id, dia_semana, item.momento) in habitos_set

            platos_dia_x_dia[fec][item.momento].append({
                "menuitem_id": item.id,   # ✅ también existe el MenuItem aunque sea lugar
                "objeto_id": item.lugar.id, # NO DEBE SER BUENA PRACTICA PONER AL LUGAR EL ID PLATO_ID, GPT SE CONFUNDIO Y YO TAMBIÉN, DOS D
                "nombre": item.lugar.nombre,
                "tipo": "",
                "fijo": fijo,
                "es_lugar": True
            })

    # Convertir defaultdict a dict antes de pasarlo a la plantilla
    platos_dia_x_dia = dict(platos_dia_x_dia)

    carousel_items = armados if armados else platos

    habitos_lookup = {
    (h.dia_semana, h.momento, h.plato_id): h.id
    for h in habitos}

    contexto = {
                'formulario': form,
                'platos': platos,
                'armados': armados,
                "carousel_items": carousel_items,
                "dias_desde_hoy": dias_desde_hoy,
                "dias_programados": dias_programados,
                "quecomemos_ck": quecomemos,
                "misplatos_ck": misplatos,
                "amigues" : amigues,
                "parametro_activo": tipo_parametro,
                "mensajes": mensajes_agrupados,
                'dia_activo': dia_activo,
                'dia_activo_obj': dia_activo_obj, # solo para filtros |date en el template/modal

                "platos_dia_x_dia": platos_dia_x_dia,
                # "idesplatos": ids_platos_importados,
                # "ides_descartable": ids_platos_compartidos,
                "platos_compartidos": platos_compartidos,
                "lugares": lugares,
                "habitos_lookup": habitos_lookup,


               }
    
    # tipopag = (request.GET.get("tipopag") or "Principal").strip()
    contexto["tipopag"] = tipopag

    
    contexto["guarniciones"] = Plato.objects.filter(
                propietario=request.user
            ).filter(
                Q(tipos__icontains="Guarnicion") | Q(tipos__icontains="Guarnición")
            ).order_by("nombre_plato")

    contexto["salsas"] = Plato.objects.filter(
                propietario=request.user,
                tipos__icontains="Salsa"
            ).order_by("nombre_plato")

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




@login_required
def agregar_a_mi_lista(request, plato_id):
    plato_original = get_object_or_404(Plato, id=plato_id)
    profile = get_object_or_404(Profile, user=request.user)

    duplicar = request.GET.get("duplicar") == "true"

    # Nombre de la copia
    nombre_base = plato_original.nombre_plato
    nombre_copia = f"Copia de {nombre_base}" if duplicar else nombre_base

    # proviene_de (string)
    proviene_de_str = (
        plato_original.propietario.username
        if plato_original.propietario != request.user
        else ""
    )

    # ✅ Clonar SOLO el plato clickeado y dejarlo independiente
    nuevo_plato = Plato.objects.create(
        nombre_plato=nombre_copia,
        nombre_grupo="",          # 👈 evita "grupo" suelto
        receta=plato_original.receta,
        ingredientes="",          # se reconstruye luego
        medios=plato_original.medios,
        categoria=plato_original.categoria,
        elaboracion=plato_original.elaboracion,
        coccion=plato_original.coccion,
        tipos=plato_original.tipos,
        estacionalidad=plato_original.estacionalidad,
        propietario=request.user,
        image=plato_original.image,
        proviene_de=proviene_de_str,
        id_original=plato_original.id,
        plato_padre=None,         # 👈 clave: si era variedad, ahora queda como “padre”
    )

    # Clonar ingredientes estructurados + reconstruir texto
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

    nuevo_plato.ingredientes = ", ".join(ingredientes_texto)
    nuevo_plato.save(update_fields=["ingredientes"])

    # Marcar como importado (sin duplicados)
    if plato_original.id not in profile.sugeridos_importados:
        profile.sugeridos_importados.append(plato_original.id)
        profile.save(update_fields=["sugeridos_importados"])

    return redirect("descartar-sugerido", plato_id=plato_id)



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
                plato_base = Plato.objects.get(id=objeto_id)

                # ✅ Si el form manda platos_ids, asignamos solo esos (padre y/o hijas)
                ids_post = [x for x in request.POST.getlist("platos_ids") if x.isdigit()]

                if ids_post:
                    allowed_ids = set(
                        [plato_base.id] +
                        list(plato_base.variedades_hijas.values_list("id", flat=True))
                    )
                    selected_ids = [int(x) for x in ids_post if int(x) in allowed_ids]
                    platos_a_asignar = list(Plato.objects.filter(id__in=selected_ids))
                else:
                    # fallback: padre + todas sus hijas
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

                # ===== Extras (0..N) validados por tipo =====
                def _tiene_tipo(plato: Plato, tipo_txt: str) -> bool:
                    # tu campo es un string tipo "Entrada,Principal,Postre"
                    # match simple por substring (soporta tilde en Guarnición)
                    t = (plato.tipos or "")
                    if tipo_txt == "Guarnicion":
                        return ("Guarnicion" in t) or ("Guarnición" in t)
                    return (tipo_txt in t)

                def _asignar_extra(extra_id_str: str, tipo_requerido: str) -> int:
                    if not extra_id_str or not extra_id_str.isdigit():
                        return 0

                    extra = Plato.objects.filter(
                        id=int(extra_id_str),
                        propietario=request.user,
                    ).first()

                    if not extra:
                        return 0

                    if not _tiene_tipo(extra, tipo_requerido):
                        return 0

                    _, created = MenuItem.objects.get_or_create(
                        menu=menu_dia,
                        momento=momento,
                        plato=extra,
                        defaults={"elegido": True},
                    )
                    return 1 if created else 0

                # 👇 NUEVO: leer extras múltiples del modal
                extra_tipos = request.POST.getlist("extra_tipo")
                extra_ids = request.POST.getlist("extra_id")

                creados_extras = 0
                for tipo_req, extra_id_str in zip(extra_tipos, extra_ids):
                    # ignorar filas incompletas
                    if not extra_id_str or not extra_id_str.isdigit():
                        continue

                    # solo tipos permitidos
                    if tipo_req not in ("Guarnicion", "Salsa", "Postre"):
                        continue

                    creados_extras += _asignar_extra(extra_id_str, tipo_req)

                total = len(platos_a_asignar)
                messages.success(
                    request,
                    f"Asignados {creados}/{total} platos a {momento}."
                    + (f" Extras agregados: {creados_extras}." if creados_extras else "")
                )

            elif tipo == "lugar":
                lugar_id = request.POST.get("plato_id")  # Usamos plato_id para obtener el ID del lugar

                if not lugar_id or not lugar_id.isdigit():
                    messages.error(request, "ID de lugar no válido.")
                    return redirect("filtro-de-platos")
                
                lugar = Lugar.objects.get(id=lugar_id)  # Buscar el lugar por el ID recibido

                # Verifica que el objeto lugar está correcto
                print(f"Lugar encontrado: {lugar.nombre} (ID: {lugar.id})")

                # Asegúrate de que el objeto lugar se está pasando correctamente
                menu_item = MenuItem.objects.create(
                    menu=menu_dia,
                    momento=momento,
                    lugar=lugar,  # Asignamos el lugar al MenuItem
                )
                
                messages.success(request, f"Lugar {lugar.nombre} (ID: {lugar.id}) asignado correctamente a {momento}.")

           

        except Exception:
            messages.warning(request, "Ese elemento ya estaba asignado a esa comida en ese día.")

        return redirect("filtro-de-platos")








@login_required
def plato_opciones_asignar(request, pk):
    # Plato base
    plato = get_object_or_404(Plato, pk=pk)

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

    return JsonResponse({
        "opciones": opciones,          # lo que ya devolvías
        "tipos_base": plato.tipos or ""  # 👈 nuevo
    })




@login_required
def eliminar_programado(request, es_lugar, objeto_id, comida, fecha):
    usuario = request.user

    # 1) Normalizar fecha
    if isinstance(fecha, str):
        try:
            fecha = datetime.datetime.strptime(fecha, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Fecha inválida.")
            return redirect("filtro-de-platos")

    # 2) Traer el menú del día
    menu = get_object_or_404(MenuDia, propietario=usuario, fecha=fecha)

    # 3) Query base: items del momento
    qs = menu.items.filter(momento=comida)

    # 4) es_lugar
    try:
        es_lugar = bool(int(es_lugar))
    except (TypeError, ValueError):
        messages.error(request, "Tipo inválido (es_lugar).")
        return redirect("filtro-de-platos")

    dia_semana = fecha.weekday()
    perfil = usuario.profile

    if es_lugar:
        lugar_qs = Lugar.objects.all()
        if hasattr(Lugar, "propietario"):
            lugar_qs = lugar_qs.filter(propietario=usuario)

        lugar = lugar_qs.filter(id=objeto_id).first()
        if not lugar:
            messages.error(request, f"Lugar con ID '{objeto_id}' no encontrado.")
            return redirect("filtro-de-platos")

        borrados, _ = qs.filter(lugar_id=lugar.id).delete()

        if borrados:
            messages.success(request, f"Lugar '{lugar.nombre}' eliminado correctamente.")

            # ✅ solo si realmente borré el item, borro el hábito de ESA comida y ESE día de semana
            HabitoSemanal.objects.filter(
                perfil=perfil,
                dia_semana=dia_semana,
                momento=comida,
                lugar_id=lugar.id
            ).delete()
        else:
            messages.warning(request, f"No se encontró el lugar '{lugar.nombre}' para {comida}.")

    else:
        plato = Plato.objects.filter(id=objeto_id, propietario=usuario).first()
        if not plato:
            messages.error(request, f"Plato con ID '{objeto_id}' no encontrado.")
            return redirect("filtro-de-platos")

        borrados, _ = qs.filter(plato_id=plato.id).delete()

        nombre = getattr(plato, "nombre_plato", None) or getattr(plato, "nombre", str(plato))

        if borrados:
            messages.success(request, f"Plato '{nombre}' eliminado correctamente.")

            # ✅ solo si realmente borré el item
            HabitoSemanal.objects.filter(
                perfil=perfil,
                dia_semana=dia_semana,
                momento=comida,
                plato_id=plato.id
            ).delete()
        else:
            messages.warning(request, f"No se encontró el plato '{nombre}' para {comida}.")

    return redirect("filtro-de-platos")

    

MOMENTOS = ["desayuno", "almuerzo", "merienda", "cena"]

def normalizar_dia(dia):
    # Quitar tildes y pasar a mayúsculas
    return ''.join(
        c for c in unicodedata.normalize('NFD', dia.upper())
        if unicodedata.category(c) != 'Mn'
    )


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

# from .models import MenuDia  # ajustá el import




@require_POST
def eliminar_menu_programado(request):
    dia_activo = request.session.get("dia_activo")
    if not dia_activo:
        messages.error(request, "No hay un día activo en la sesión.")
        return redirect("filtro-de-platos")

    try:
        fecha = datetime.datetime.strptime(dia_activo, "%Y-%m-%d").date()
    except ValueError:
        messages.error(request, "Fecha inválida.")
        return redirect("filtro-de-platos")

    menu_id = MenuDia.objects.filter(
        propietario=request.user,
        fecha=fecha
    ).values_list("id", flat=True).first()

    if not menu_id:
        messages.warning(request, f"No había un menú programado para {dia_activo}.")
        return redirect("filtro-de-platos")

    perfil = request.user.profile
    dia_semana = fecha.weekday()

    # Habitos del día de semana (NO hay herencia a variedades: solo ids exactos)
    habitos = HabitoSemanal.objects.filter(
        perfil=perfil,
        dia_semana=dia_semana,
    ).only("momento", "plato_id", "lugar_id")

    keep_q = Q()
    for h in habitos:
        if h.plato_id:
            keep_q |= Q(momento=h.momento, plato_id=h.plato_id)
        if getattr(h, "lugar_id", None):
            keep_q |= Q(momento=h.momento, lugar_id=h.lugar_id)

    with transaction.atomic():
        items_qs = MenuItem.objects.filter(menu_id=menu_id)

        # Borramos TODO excepto lo que coincide EXACTO con un hábito
        if keep_q:
            qs_borrar = items_qs.exclude(keep_q)
        else:
            qs_borrar = items_qs

        borrados = qs_borrar.count()
        qs_borrar.delete()
        # ✅ Tu signal (menu_id-based) borrará MenuDia si quedó sin items

    messages.success(
        request,
        f"Se eliminó el menú programado del {dia_activo} (items borrados: {borrados})."
    )
    return redirect("filtro-de-platos")


# class ArmadoCreateView(LoginRequiredMixin, CreateView):
#     model = Armado
#     form_class = ArmadoForm
#     template_name = "AdminVideos/armado_form.html"

#     def dispatch(self, request, *args, **kwargs):
#         # tipo viene por URL: /armados/nuevo/Picada/
#         self.tipo_armado = self.kwargs["tipo_armado"]
#         return super().dispatch(request, *args, **kwargs)

#     def get_form_kwargs(self):
#         kwargs = super().get_form_kwargs()
#         kwargs["propietario"] = self.request.user
#         kwargs["tipo_armado"] = self.tipo_armado
#         return kwargs

#     def form_valid(self, form):
#         obj = form.save(commit=False)
#         obj.propietario = self.request.user
#         obj.tipo_armado = self.tipo_armado
#         obj.save()
#         form.save_m2m()
#         return super().form_valid(form)

#     def get_success_url(self):
#         return reverse("armado-detail", kwargs={"pk": self.object.pk})
    
class ArmadoCreateView(LoginRequiredMixin, CreateView):
    model = Armado
    form_class = ArmadoForm
    template_name = "AdminVideos/partials/armado_form_modal.html"

    def dispatch(self, request, *args, **kwargs):
        self.tipo_armado = self.kwargs["tipo_armado"]
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["propietario"] = self.request.user
        kwargs["tipo_armado"] = self.tipo_armado
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tipo_armado"] = self.tipo_armado
        return context

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.propietario = self.request.user
        obj.tipo_armado = self.tipo_armado
        obj.save()
        form.save_m2m()
        self.object = obj
        return super().form_valid(form)

    def get_success_url(self):
        tipopag = self.request.GET.get("tipopag", self.tipo_armado)
        dia_activo = self.request.GET.get("dia_activo")

        url = reverse("filtro-de-platos")

        if dia_activo:
            return f"{url}?tipopag={tipopag}&dia_activo={dia_activo}"

        return f"{url}?tipopag={tipopag}"
        


class ArmadoDetailView(LoginRequiredMixin, DetailView):
    model = Armado
    template_name = "AdminVideos/armado_detail.html"

    def get_queryset(self):
        # Seguridad: solo ver tus armados
        return Armado.objects.filter(propietario=self.request.user)