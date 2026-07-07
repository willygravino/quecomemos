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
from AdminVideos.models import ElementoCompartido, Amistad, ProfilePlatoCompra, HabitoSemanal, Ingrediente, IngredienteEnPlato, Lugar, MenuDia, MenuItem, Plato, Profile, Mensaje, ProfileIngrediente, LoQueTengoPalabra
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string   # ✅ ← ESTA ES LA CLAVE
from django.http import Http404, HttpRequest, HttpResponseNotAllowed, JsonResponse
from django.urls import reverse, reverse_lazy
from django.contrib.auth.forms import UserCreationForm
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from datetime import date, timedelta

from nuestrotubo import settings
from .forms import IngredienteEnPlatoFormSet, LugarForm, PlatoFilterForm, PlatoForm, CustomAuthenticationForm
from django.contrib.auth.models import User  # Asegúrate de importar el modelo User
from django.db.models import Q, Subquery, OuterRef, Prefetch, Min, Max, F
import random
import datetime
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.db import transaction
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.core.exceptions import PermissionDenied
from AdminVideos.services.pantry import (
    persist_profile_ingrediente_from_post,
    get_pantry_map,
    sort_items_by_name,
)
from django.utils.http import url_has_allowed_host_and_scheme
from django.db.models.expressions import OrderBy
from django.db.models import Case, When, IntegerField
from django.views.generic.edit import FormView


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

    
@login_required
def fijar_o_eliminar_habito(request, es_lugar, objeto_id, comida):
    usuario = request.user
    es_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

    dia_str = request.session.get("dia_activo")
    if not dia_str:
        message = "No hay día activo seleccionado."

        if es_ajax:
            return JsonResponse({
                "ok": False,
                "message": message,
            }, status=400)

        messages.error(request, message)
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
            fijado = False
            nombre = lugar.nombre
            message = f"Se eliminó el hábito de {nombre} para {comida}."
        else:
            HabitoSemanal.objects.create(
                perfil=perfil,
                dia_semana=dia_semana,
                momento=comida,
                lugar=lugar
            )
            fijado = True
            nombre = lugar.nombre
            message = f"Se fijó el hábito de {nombre} para {comida}."

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
            fijado = False
            message = f"Se eliminó el hábito de {nombre} para {comida}."
        else:
            HabitoSemanal.objects.create(
                perfil=perfil,
                dia_semana=dia_semana,
                momento=comida,
                plato=plato
            )
            fijado = True
            message = f"Se fijó el hábito de {nombre} para {comida}."

    if es_ajax:
        return JsonResponse({
            "ok": True,
            "fijado": fijado,
            "message": message,
        })

    messages.success(request, message)
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
    palabra_clave = (request.POST.get("palabra_clave") or "").strip()

    quecomemos = request.session.get('quecomemos', None)
    misplatos = request.session.get('misplatos', "misplatos")
    # preseleccionados = request.session.get('preseleccionados', None)

    # Obtener el valor del parámetro 'tipo' desde la URL
    tipo_parametro = (request.GET.get("tipopag") or "Principal").strip()


    # # Obtener el usuario actual
    # usuario = request.user

    # Devolver las variables por separado
    return tipo_parametro, quecomemos, misplatos, medios, categoria, dificultad, palabra_clave


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

    # # Ingredientes del plato (relación intermedia IEP)
    # ingredientes_qs = (
    #     plato.ingredientes_en_plato
    #     .select_related("ingrediente")
    #     .all()
    # )

    # Ingredientes directos del plato
    ingredientes_directos = list(
        plato.ingredientes_en_plato
        .select_related("ingrediente")
        .all()
    )

    # Platos asociados/componentes
    componentes = list(
        plato.componentes
        .prefetch_related("ingredientes_en_plato__ingrediente")
        .all()
    )

    # Ingredientes de los platos asociados
    ingredientes_componentes = []

    for componente in componentes:
        ingredientes_componentes.extend(
            componente.ingredientes_en_plato.all()
        )

    # Ingredientes usados para guardar y leer estado de despensa
    ingredientes_para_guardar = ingredientes_directos + ingredientes_componentes


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

            for iep in ingredientes_directos:
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

    ing_ids = list({
        iep.ingrediente_id
        for iep in ingredientes_para_guardar
        if iep.ingrediente_id
    })
    
    pantry_map = get_pantry_map(
    perfil=perfil,
    ing_ids=ing_ids,
    only_fields=("ingrediente_id", "tengo", "comentario", "updated_at"),
            )

    items = []
    for iep in ingredientes_directos:
        ing = iep.ingrediente
        if not ing:
            continue

        ing_id = iep.ingrediente_id
        if not ing_id:
            continue

        # Si este ingrediente también viene de un plato asociado,
        # se muestra solo dentro del bloque del plato asociado.
       
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

    componentes_items = []

    for componente in componentes:  
        subitems = []

        for iep in componente.ingredientes_en_plato.all():
            ing = iep.ingrediente
            if not ing:
                continue

            ing_id = iep.ingrediente_id
            if not ing_id:
                continue

            p = pantry_map.get(ing_id)

            tengo = p.tengo if p else False
            comentario = (p.comentario or "") if p else ""

            subitems.append({
                "ingrediente_id": ing_id,
                "nombre": ing.nombre,
                "cantidad": iep.cantidad,
                "unidad": iep.unidad,
                "a_comprar": (not tengo),
                "comentario": comentario,
            })

        sort_items_by_name(subitems)

        componentes_items.append({
            "plato": componente,
            "items": subitems,
        })

    # ======================================================
    # 4) Links / tokens (lo tuyo, sin cambiar lógica)
    # ======================================================
    if not perfil.share_token:
        perfil.ensure_share_token()

    ctx = {
        "plato": plato,
        "componentes_items": componentes_items,
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



def compartir_ing_plato(request, token, pk: int):
    share_user, perfil = _get_user_by_token_or_404(token)
    plato = get_object_or_404(Plato, pk=pk)

    # Ingredientes directos del plato
    ingredientes_directos_qs = (
        plato.ingredientes_en_plato
        .select_related("ingrediente")
        .all()
    )

    # Ingredientes de platos asociados/componentes
    ingredientes_componentes = []

    for componente in plato.componentes.prefetch_related("ingredientes_en_plato__ingrediente").all():
        ingredientes_componentes.extend(
            componente.ingredientes_en_plato.all()
        )

    # Ingredientes finales: directos + componentes
    ingredientes_qs = list(ingredientes_directos_qs) + ingredientes_componentes

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
                    .prefetch_related("plato__componentes")
                    .annotate(
                        momento_orden=Case(
                            When(momento="desayuno", then=0),
                            When(momento="almuerzo", then=1),
                            When(momento="merienda", then=2),
                            When(momento="cena", then=3),
                            default=99,
                            output_field=IntegerField(),
                        )
                    )
                    .order_by("momento_orden", "id")
                ),
                # queryset=(
                #     MenuItem.objects
                #     # .select_related("plato", "lugar")
                #     # .order_by("id")
                #     .select_related("plato", "lugar")
                #     .prefetch_related("plato__componentes")
                #     .order_by("id")
                # ),
            )
        )
    )

    # =====================================================
    # POST: guardar menú SOLO si origen == "menu"
    # =====================================================
    post_origen = request.POST.get("post_origen", "") if request.method == "POST" else ""

    
    
    # Guarda selección persistente de plato para lista de compras
    if request.method == "POST" and post_origen == "menu":
        plato_id = request.POST.get("toggle_plato_id")
        checked = request.POST.get("toggle_plato_checked") == "1"

        if plato_id and plato_id.isdigit():
            plato = get_object_or_404(
                Plato,
                id=int(plato_id),
                propietario=request.user,
            )

            ProfilePlatoCompra.objects.update_or_create(
                perfil=perfil,
                plato=plato,
                defaults={"elegido": checked},
            )

            # Mantiene sincronizados los MenuItem reales de ese plato.
            MenuItem.objects.filter(
                menu__propietario=request.user,
                menu__fecha__gte=today,
                plato_id=plato.id,
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
                    .prefetch_related("plato__componentes")
                    .annotate(
                        momento_orden=Case(
                            When(momento="desayuno", then=0),
                            When(momento="almuerzo", then=1),
                            When(momento="merienda", then=2),
                            When(momento="cena", then=3),
                            default=99,
                            output_field=IntegerField(),
                        )
                    )
                    .order_by("momento_orden", "id")
                ),
                # queryset=(
                #     MenuItem.objects
                #     .select_related("plato", "lugar")
                #     .order_by("id")
                # ),
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

    # Platos programados como items reales del menú
    plato_ids_programados = set(
        MenuItem.objects
        .filter(menu__in=menues, plato__isnull=False)
        .values_list("plato_id", flat=True)
    )

    # Componentes asociados a esos platos programados
    componente_ids_programados = set(
        Plato.objects
        .filter(forma_parte_de__id__in=plato_ids_programados)
        .values_list("id", flat=True)
    )

    # Todos los platos que pueden aportar ingredientes:
    # platos principales + componentes
    plato_ids_disponibles = plato_ids_programados | componente_ids_programados

    # Estados persistentes por usuario/perfil.
    # Si no existe registro todavía, usamos como fallback el estado de MenuItem.elegido.
    estados_compra = {
        estado.plato_id: estado.elegido
        for estado in ProfilePlatoCompra.objects.filter(
            perfil=perfil,
            plato_id__in=plato_ids_disponibles,
        )
    }

    menuitem_elegidos_ids = set(
        MenuItem.objects
        .filter(menu__in=menues, plato__isnull=False, elegido=True)
        .values_list("plato_id", flat=True)
    )

    platos_elegidos_ids = {
        plato_id
        for plato_id in plato_ids_disponibles
        if estados_compra.get(plato_id, plato_id in menuitem_elegidos_ids)
    }

    plato_ids = list(platos_elegidos_ids)
    plato_ids_con_componentes = list(platos_elegidos_ids)


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
        .filter(plato_id__in=plato_ids_con_componentes)
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

    items_por_rubro = defaultdict(list)

    for item in items:
        rubro = item.get("tipo") or "otro"
        items_por_rubro[rubro].append(item)

    token = perfil.ensure_share_token()
    share_url = request.build_absolute_uri(reverse("compartir-lista", args=[token]))

    summary = {
        "total": len(items),
        "to_buy": sum(i["estado"] == "no-tengo" for i in items),
        "fresh": sum(i["estado"] == "recien-comprado" for i in items),
        "have": sum(i["estado"] == "tengo" for i in items),
    }

    componentes_elegidos_keys = set(
    f"{menu_id}_{momento}_{plato_id}"
    for menu_id, momento, plato_id in MenuItem.objects
    .filter(
        menu__propietario=request.user,
        menu__fecha__gte=today,
        plato__isnull=False,
        elegido=True,
    )
    .values_list("menu_id", "momento", "plato_id")
    )   

    RUBROS_LABELS = {
    "verduleria": "Verdulería",
    "fiambreria": "Fiambriería",
    "carniceria": "Carnicería",
    "pescaderia": "Pescadería",
    "panaderia": "Panadería",
    "almacen": "Almacén",
    "lacteos": "Lácteos",
    "bebidas": "Bebidas",
    "otro": "Otros",
    }

    items_por_rubro = {
        RUBROS_LABELS.get(rubro, rubro): lista
        for rubro, lista in items_por_rubro.items()
    }

    context = {
        "menues": menues,
        "items_elegidos": items_elegidos,
        "share_url": share_url,
        "shopping": {"items": items, "summary": summary},
        "parametro": "lista-compras",
        "componentes_elegidos_keys": componentes_elegidos_keys,
        "shopping_por_rubro": items_por_rubro, 
        "platos_elegidos_ids": platos_elegidos_ids,
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
            "tipo": data["tipo"],
            "comentario": comentario,
            "estado": estado,
            "needed_by": data["needed_by"],
        })



    items.sort(key=lambda i: i["nombre"].casefold())

    RUBROS_LABELS = {
    "verduleria": "Verdulería",
    "fiambreria": "Fiambriería",
    "carniceria": "Carnicería",
    "pescaderia": "Pescadería",
    "panaderia": "Panadería",
    "almacen": "Almacén",
    "lacteos": "Lácteos",
    "bebidas": "Bebidas",
    "otro": "Otros",
    }

    items_por_rubro = defaultdict(list)

    for item in items:
        rubro = item.get("tipo") or "otro"
        items_por_rubro[rubro].append(item)

    items_por_rubro = {
        RUBROS_LABELS.get(rubro, rubro): lista
        for rubro, lista in items_por_rubro.items()
    }

    # Tokens
    if not perfil.share_token:
        perfil.ensure_share_token()

  
    return render(request, "AdminVideos/compartir_lista.html", {
        "items": items,
        "items_por_rubro": items_por_rubro,
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
        context["amigues"] = obtener_usernames_amigues(self.request.user)        

        return context



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

    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    return_to = request.POST.get("return_to") or request.GET.get("return_to")

    with transaction.atomic():
        perfil = get_object_or_404(Profile, user=request.user)

        if plato.id_original and plato.id_original in perfil.sugeridos_descartados:
            perfil.sugeridos_descartados.remove(plato.id_original)

        if plato.id_original and plato.id_original in perfil.sugeridos_importados:
            perfil.sugeridos_importados.remove(plato.id_original)

        perfil.save()

        Plato.objects.filter(plato_padre=plato, propietario=request.user).delete()

        plato.delete()

    if return_to:
        return redirect(return_to)

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
        return super().form_invalid(form)

    def form_valid(self, form):
        lugar = form.save(commit=False)
        lugar.propietario = self.request.user


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



TITULOS_FORMULARIO_PLATO = {
    "Principal": "Agregar un plato principal",
    "Entrada": "Agregar una entrada",
    "Guarnicion": "Agregar una guarnición",
    "Dip": "Agregar un dip",
    "Salsa": "Agregar una salsa",
    "Picada": "Agregar una picada",
    "Ingrediente de picada": "Agregar un ingrediente de picada",
    "Postre": "Agregar un postre",
    "Trago": "Agregar una bebida / trago",
}


def titulo_formulario_plato(tipopag, accion="Agregar"):
    tipo = (tipopag or "Principal").strip()
    titulo = TITULOS_FORMULARIO_PLATO.get(tipo)

    if titulo and accion == "Agregar":
        return titulo

    if accion == "Editar":
        return "Editar plato"

    if accion == "Agregar variedad":
        return "Agregar variedad"

    return f"{accion} plato"



class PlatoCreate(LoginRequiredMixin, CreateView):
    model = Plato
    form_class = PlatoForm
    # Fallback de template por si tipopag no matchea
    DEFAULT_TEMPLATE = 'AdminVideos/ppal_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

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
            'Picada': 'AdminVideos/ppal_form.html',
            'Ingrediente de picada': 'AdminVideos/ppal_form.html',
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
        "Ingrediente de picada": ["Ingrediente de picada","Guarnicion", "Entrada"],
        "Picada": ["Picada"],
        "Salsa": ["Salsa", "Dip", "Guarnicion", "Entrada"],
    }

    # 1) Alinear “tipos” con tu modelo actual (CharField CSV)
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        template_param = self.request.GET.get('tipopag')

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
        context["titulo_formulario"] = titulo_formulario_plato(template_param, accion="Agregar")

        if self.request.method == 'POST':
            context['ingrediente_formset'] = IngredienteEnPlatoFormSet(self.request.POST)
        else:
            context['ingrediente_formset'] = IngredienteEnPlatoFormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        ingrediente_formset = context['ingrediente_formset']

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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

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
        context["titulo_formulario"] = "Editar plato"

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
        return self.render_to_response(context)




class PlatoDetail(DetailView):
    model = Plato
    context_object_name = "plato"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plato = self.get_object()

        # Tipos: string "Entrada,Principal" -> lista
        if plato.tipos:
            context["tipos_lista"] = [t.strip() for t in plato.tipos.split(",") if t.strip()]
        else:
            context["tipos_lista"] = []

        # Variedades hijas
        context["variedades"] = plato.variedades_hijas.all().order_by("nombre_plato")

        # Padre, si este plato es una variedad
        context["plato_padre"] = plato.plato_padre

        return context

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data()

        html = render_to_string(
            "AdminVideos/plato_detail_content.html",
            context,
            request=request,
        )

        return JsonResponse({
            "html": html,
        })





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
        context["titulo_formulario"] = f"Agregar variedad de {self.padre.nombre_plato}"

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

    def form_valid(self, form):
        response = super().form_valid(form)

        self.request.session.set_expiry(settings.SESSION_COOKIE_AGE)
        self.request.session.modified = True

        return response

class SignUp(CreateView):
    form_class = UserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('filtro-de-platos')

@login_required
def user_logout(request):
    logout(request)
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
            "platos": Plato.objects.none()
        }

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
    if tipo_parametro == "Picada":
        platos_qs = platos_qs.filter(
            tipos__icontains="Picada"
        ).exclude(
            tipos__icontains="Ingrediente de picada"
        )
    elif tipo_parametro == "Ingrediente de picada":
        platos_qs = platos_qs.filter(tipos__icontains="Ingrediente de picada")
    elif tipo_parametro:
        platos_qs = platos_qs.filter(tipos__icontains=tipo_parametro)

    if medios and medios != "-":
        platos_qs = platos_qs.filter(medios=medios)

    if categoria and categoria != "-":
        platos_qs = platos_qs.filter(categoria=categoria)

    if dificultad and dificultad != "-":
        platos_qs = platos_qs.filter(dificultad=dificultad)

    if palabra_clave:
        platos_qs = platos_qs.filter(
            Q(nombre_plato__icontains=palabra_clave) |
            Q(ingredientes__icontains=palabra_clave) |
            Q(ingredientes_en_plato__ingrediente__nombre__icontains=palabra_clave)
        ).distinct()

    # Orden de prioridad de los platos:
    # 1) Nunca programados históricamente primero.
    # 2) Después, los que hace más tiempo que no se programan históricamente.
    # 3) Al final, los más recientemente programados históricamente.
    # 4) Los menús futuros no cuentan como histórico hasta que llegue/pase su fecha.
    # 5) Como desempate final, los más nuevos (-id).

    hoy = timezone.localdate()
    filtro_programaciones_historicas = (
        Q(en_menus__menu__propietario=usuario)
        & Q(en_menus__plato__isnull=False)
        & Q(en_menus__menu__fecha__lte=hoy)
    )

    # queryset ANOTADO para variedades (hijas) del usuario "usuario"
    variedades_qs = Plato.objects.annotate(
        programaciones_count=Count(
            "en_menus__menu__fecha",
            filter=filtro_programaciones_historicas,
            distinct=True,
        ),
        ultima_programacion=Max(
            "en_menus__menu__fecha",
            filter=filtro_programaciones_historicas,
        ),
    ).order_by(
        OrderBy(F("ultima_programacion"), descending=False, nulls_first=True),
        "-id",
    )

    platos_qs = platos_qs.annotate(
        programaciones_count=Count(
            "en_menus__menu__fecha",
            filter=filtro_programaciones_historicas,
            distinct=True,
        ),
        ultima_programacion=Max(
            "en_menus__menu__fecha",
            filter=filtro_programaciones_historicas,
        ),
        variedades_count=Count("variedades_hijas", distinct=True),
    ).order_by(
        OrderBy(F("ultima_programacion"), descending=False, nulls_first=True),
        "-id",
    ).prefetch_related(
        Prefetch("variedades_hijas", queryset=variedades_qs)
    )

    
    return {
        "platos": platos_qs,
    }


def obtener_dias_desde_hoy(cantidad=7):
    fecha_actual = datetime.datetime.now().date()
    dias_desde_hoy = [
        fecha_actual + timedelta(days=i)
        for i in range(0, cantidad)
    ]
    return fecha_actual, dias_desde_hoy


def obtener_perfil_usuario(usuario):
    try:
        return usuario.profile
    except Profile.DoesNotExist:
        return None


def obtener_habitos_usuario(perfil):
    habitos = HabitoSemanal.objects.filter(
        perfil=perfil
    ).select_related("plato", "lugar")

    habitos_set = set()

    for h in habitos:
        if h.plato_id:
            habitos_set.add(("plato", h.plato_id, h.dia_semana, h.momento))
        elif h.lugar_id:
            habitos_set.add(("lugar", h.lugar_id, h.dia_semana, h.momento))

    return habitos, habitos_set


def asegurar_menus_desde_habitos(request, usuario, dias_desde_hoy, habitos):
    for fecha in dias_desde_hoy:
        dia_semana = fecha.weekday()  # 0=lunes ... 6=domingo

        habitos_del_dia = [
            h for h in habitos
            if h.dia_semana == dia_semana
        ]

        if not habitos_del_dia:
            continue

        menu_dia, creado = MenuDia.objects.get_or_create(
            propietario=usuario,
            fecha=fecha
        )

        if creado:
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



def obtener_dia_activo(request, dias_desde_hoy):
    """
    Devuelve un día activo válido para las pestañas.

    Si la sesión no tiene día activo, o tiene un día viejo que ya no está
    dentro del rango visible, usa el primer día disponible.
    """
    dias_validos = [dia.isoformat() for dia in dias_desde_hoy]
    primer_dia = dias_validos[0]

    dia_activo = request.session.get("dia_activo")

    if dia_activo not in dias_validos:
        dia_activo = primer_dia
        request.session["dia_activo"] = dia_activo
        request.session.modified = True

    dia_activo_obj = datetime.datetime.strptime(
        dia_activo,
        "%Y-%m-%d"
    ).date()

    return dia_activo, dia_activo_obj






def obtener_fechas_existentes_menu(usuario, fecha_actual):
    return list(
        MenuDia.objects.filter(
            propietario=usuario,
            fecha__gte=fecha_actual
        ).values_list("fecha", flat=True)
    )



def obtener_amistades_usuario(usuario, estado=Amistad.ACEPTADA):
    """
    Devuelve relaciones de amistad del usuario en el estado pedido.
    """
    return (
        Amistad.objects
        .filter(
            Q(usuario_1=usuario) | Q(usuario_2=usuario),
            estado=estado,
        )
        .select_related("usuario_1", "usuario_2", "solicitada_por")
        .order_by("-actualizada_el")
    )


def obtener_usuarios_amigues(usuario):
    """
    Devuelve objetos User que son amigues aceptados del usuario.
    """
    usuarios = []

    for amistad in obtener_amistades_usuario(usuario, estado=Amistad.ACEPTADA):
        otro = amistad.otro_usuario(usuario)

        if otro:
            usuarios.append(otro)

    return usuarios


def obtener_usernames_amigues(usuario):
    """
    Devuelve usernames de amigues aceptados.

    Mantiene compatibilidad con templates que esperan una lista simple.
    """
    return [
        usuario_amigue.username
        for usuario_amigue in obtener_usuarios_amigues(usuario)
    ]



@login_required
def ajax_solicitudes_amistad(request):
    cantidad = obtener_solicitudes_amistad_pendientes(request.user).count()

    return JsonResponse({
        "cantidad": cantidad,
    })


def obtener_solicitudes_amistad_pendientes(usuario):
    """
    Devuelve solicitudes pendientes recibidas por el usuario.
    """
    return (
        obtener_amistades_usuario(usuario, estado=Amistad.PENDIENTE)
        .exclude(solicitada_por=usuario)
    )


def obtener_solicitudes_amistad_enviadas(usuario):
    """
    Devuelve usernames de usuarios a quienes se les envió solicitud pendiente.
    """
    solicitudes = (
        obtener_amistades_usuario(usuario, estado=Amistad.PENDIENTE)
        .filter(solicitada_por=usuario)
    )

    return [
        amistad.otro_usuario(usuario).username
        for amistad in solicitudes
        if amistad.otro_usuario(usuario)
    ]



def obtener_ids_usuarios_con_amistad_activa(usuario):
    """
    Devuelve IDs de usuarios que ya tienen relación pendiente o aceptada.

    Se usa para no ofrecerlos otra vez en el formulario de solicitud.
    """
    ids = []

    amistades = (
        Amistad.objects
        .filter(Q(usuario_1=usuario) | Q(usuario_2=usuario))
        .exclude(estado=Amistad.RECHAZADA)
    )

    for amistad in amistades:
        otro = amistad.otro_usuario(usuario)

        if otro:
            ids.append(otro.id)

    return ids






def obtener_mensajes_agrupados(usuario):
    """
    Devuelve el último mensaje de texto visible por usuario.
    """
    subquery_ultimo_mensaje = (
        Mensaje.objects
        .filter(
            usuario_que_envia_fk=OuterRef("usuario_que_envia_fk"),
            destinatario=usuario,
            usuario_que_envia_fk__isnull=False,
        )
        .order_by("-creado_el")
        .values("id")[:1]
    )

    mensajes_x_usuario = (
        Mensaje.objects
        .filter(
            id__in=Subquery(subquery_ultimo_mensaje),
            usuario_que_envia_fk__isnull=False,
        )
        .select_related("usuario_que_envia_fk__profile")
        .order_by("-creado_el")
    )

    mensajes_agrupados = {
        mensaje.usuario_que_envia_fk.username: {
            "avatar_url": getattr(
                mensaje.usuario_que_envia_fk.profile,
                "avatar_url",
                "/media/avatares/logo.png",
            ) if hasattr(mensaje.usuario_que_envia_fk, "profile") else "/media/avatares/logo.png",
            "mensaje": {
                "contenido": mensaje.mensaje,
                "creado_el": (timezone.now() - mensaje.creado_el).days,
                "leido": mensaje.leido,
            },
        }
        for mensaje in mensajes_x_usuario
    }

    return mensajes_agrupados



@login_required
def ajax_mensajes_usuario(request):
    mensajes = obtener_mensajes_agrupados(request.user)
    amigues = obtener_usernames_amigues(request.user)

    usuarios_con_conversacion = set(mensajes.keys())
    amigues_nuevo_mensaje = [
        amigue for amigue in amigues
        if amigue not in usuarios_con_conversacion
    ]

    cantidad_no_leidos = (
        Mensaje.objects
        .filter(
            destinatario=request.user,
            leido=False,
            usuario_que_envia_fk__isnull=False,
        )
        .values("usuario_que_envia_fk")
        .distinct()
        .count()
    )

    html = render_to_string(
        "AdminVideos/partials/_dropdown_mensajes.html",
        {
            "mensajes": mensajes,
            "amigues_nuevo_mensaje": amigues_nuevo_mensaje,
        },
        request=request,
    )

    return JsonResponse({
        "html": html,
        "cantidad": cantidad_no_leidos,
    })




@login_required
@require_POST
def ajax_eliminar_mensaje_chat(request, pk):
    mensaje = get_object_or_404(
        Mensaje.objects.select_related("usuario_que_envia_fk", "destinatario"),
        pk=pk,
    )

    # Seguridad: solo puede borrar quien participa en la conversación.
    if (
        mensaje.usuario_que_envia_fk_id != request.user.id
        and mensaje.destinatario_id != request.user.id
    ):
        return JsonResponse({
            "ok": False,
            "message": "No podés borrar este mensaje.",
        }, status=403)

    # Necesitamos saber con quién era el chat antes de borrar.
    destinatario = (
        mensaje.destinatario
        if mensaje.usuario_que_envia_fk_id == request.user.id
        else mensaje.usuario_que_envia_fk
    )

    mensaje.delete()

    Mensaje.objects.filter(
        usuario_que_envia_fk=destinatario,
        destinatario=request.user,
        leido=False,
    ).update(leido=True)

    mensajes = Mensaje.objects.filter(
        Q(usuario_que_envia_fk=request.user, destinatario=destinatario) |
        Q(usuario_que_envia_fk=destinatario, destinatario=request.user)
    ).order_by("-creado_el")

    MensajeForm = forms.modelform_factory(
        Mensaje,
        fields=["mensaje", "destinatario"],
    )

    form = MensajeForm(initial={"destinatario": destinatario})
    form.fields["destinatario"].queryset = User.objects.filter(pk=destinatario.pk)
    form.fields["destinatario"].widget = forms.HiddenInput()

    cantidad = (
        Mensaje.objects
        .filter(
            destinatario=request.user,
            leido=False,
            usuario_que_envia_fk__isnull=False,
        )
        .values("usuario_que_envia_fk")
        .distinct()
        .count()
    )

    html = render_to_string(
        "AdminVideos/partials/_chat_modal_content.html",
        {
            "form": form,
            "mensajes": mensajes,
            "destinatario": destinatario,
            "amigues": obtener_usernames_amigues(request.user),
        },
        request=request,
    )

    return JsonResponse({
        "ok": True,
        "html": html,
        "cantidad": cantidad,
    })



def obtener_lugares_compartidos_pendientes(usuario):
    """
    Devuelve lugares compartidos pendientes.
    """
    compartidos = (
        ElementoCompartido.objects
        .filter(
            destinatario=usuario,
            tipo=ElementoCompartido.LUGAR,
            estado=ElementoCompartido.PENDIENTE,
            lugar__isnull=False,
        )
        .select_related("usuario_que_envia", "lugar")
        .order_by("-creado_el")
    )

    return [
        {
            "compartido_id": compartido.id,
            "id_lugar": compartido.lugar.id,
            "nombre": compartido.lugar.nombre,
            "usuario_que_envia": compartido.usuario_que_envia.username,
            "mensaje": compartido.mensaje,
        }
        for compartido in compartidos
    ]



def obtener_platos_compartidos_pendientes(usuario):
    """
    Devuelve los platos compartidos pendientes para mostrar en la pantalla de platos.

    Mantiene nombres de claves compatibles con el template actual:
    - mensaje_id ahora representa el id de ElementoCompartido
    - id_plato sigue siendo el id del plato original
    """
    compartidos = (
        ElementoCompartido.objects
        .filter(
            destinatario=usuario,
            tipo=ElementoCompartido.PLATO,
            estado=ElementoCompartido.PENDIENTE,
            plato__isnull=False,
        )
        .select_related("usuario_que_envia", "plato")
        .order_by("-creado_el")
    )

    platos_compartidos = []

    for compartido in compartidos:
        plato = compartido.plato

        platos_compartidos.append({
            "mensaje_id": compartido.id,
            "id_plato": plato.id,
            "nombre_plato": plato.nombre_plato,
            "usuario_que_envia": compartido.usuario_que_envia.username,
            "mensaje": compartido.mensaje,
            "receta": plato.receta,
            "ingredientes": plato.ingredientes,
            "image_url": plato.image_url,
        })

    return platos_compartidos




def obtener_platos_dia_x_dia(usuario, fechas_existentes, habitos_set):
    dias_programados = set()

    platos_dia_x_dia = defaultdict(
        lambda: {
            "desayuno": [],
            "almuerzo": [],
            "merienda": [],
            "cena": [],
        }
    )

    items = (
        MenuItem.objects
        .filter(
            menu__propietario=usuario,
            menu__fecha__in=fechas_existentes
        )
        .select_related("menu", "plato", "lugar")
    )

    for item in items:
        fec = item.menu.fecha
        dias_programados.add(fec)

        dia_semana = fec.weekday()

        if item.plato:
            fijo = (
                "plato",
                item.plato.id,
                dia_semana,
                item.momento
            ) in habitos_set

            platos_dia_x_dia[fec][item.momento].append({
                "menuitem_id": item.id,
                "objeto_id": item.plato.id,
                "nombre": item.plato.nombre_plato,
                "fijo": fijo,
                "tipo": item.plato.tipos,
                "es_lugar": False,
            })

        elif item.lugar:
            fijo = (
                "lugar",
                item.lugar.id,
                dia_semana,
                item.momento
            ) in habitos_set

            platos_dia_x_dia[fec][item.momento].append({
                "menuitem_id": item.id,
                "objeto_id": item.lugar.id,
                "nombre": item.lugar.nombre,
                "tipo": "",
                "fijo": fijo,
                "es_lugar": True,
            })

    return dict(platos_dia_x_dia), dias_programados





def obtener_estado_filtros_platos(request, dia_activo):
    """
    Centraliza el estado de filtros de la pantalla de platos.

    Reglas:
    - En POST, el request actual manda.
      Esto es importante para AJAX: si un checkbox no viene,
      significa que está destildado.
    - En GET, se usan valores de sesión como estado inicial.
    - tipopag puede venir por POST, GET o sesión, en ese orden.
    - La sesión se actualiza solo cuando llega un POST de filtros.
    """

    (
        tipo_sesion,
        quecomemos_sesion,
        misplatos_sesion,
        medios_sesion,
        categoria_sesion,
        dificultad_sesion,
        palabra_sesion,
    ) = obtener_parametros_sesion(request)

    tipopag = (
        request.POST.get("tipopag")
        or request.GET.get("tipopag")
        or tipo_sesion
        or "Principal"
    ).strip()

    if request.method == "POST":
        form = PlatoFilterForm(request.POST)

        medios = request.POST.get("medios") or None
        categoria = request.POST.get("categoria") or None
        dificultad = request.POST.get("dificultad") or None
        palabra_clave = (request.POST.get("palabra_clave") or "").strip()

        quecomemos = request.POST.get("quecomemos")
        misplatos = request.POST.get("misplatos")
        usar_lo_que_tengo = request.POST.get("usar_lo_que_tengo")

        if tipopag == "LoQueTengo":
            usar_lo_que_tengo = "1"

            if not quecomemos and not misplatos:
                quecomemos = "quecomemos"
                misplatos = "misplatos"

        request.session["medios_estable"] = medios
        request.session["categoria_estable"] = categoria
        request.session["dificultad_estable"] = dificultad
        request.session["palabra_clave"] = palabra_clave

        if tipopag != "LoQueTengo":
            request.session["quecomemos"] = quecomemos
            request.session["misplatos"] = misplatos
            request.session["usar_lo_que_tengo"] = usar_lo_que_tengo

        request.session["dia_activo"] = dia_activo

    else:
        medios = medios_sesion
        categoria = categoria_sesion
        dificultad = dificultad_sesion
        palabra_clave = palabra_sesion

        quecomemos = quecomemos_sesion
        misplatos = misplatos_sesion
        usar_lo_que_tengo = request.session.get("usar_lo_que_tengo")

        if tipopag == "LoQueTengo":
            usar_lo_que_tengo = "1"

            if not quecomemos and not misplatos:
                quecomemos = "quecomemos"
                misplatos = "misplatos"

        form = PlatoFilterForm(initial={
            "medios": medios,
            "categoria": categoria,
            "dificultad": dificultad,
            "palabra_clave": palabra_clave,
        })

    return {
        "form": form,
        "tipo_parametro": tipopag,
        "tipopag": tipopag,
        "quecomemos": quecomemos,
        "misplatos": misplatos,
        "usar_lo_que_tengo": usar_lo_que_tengo,
        "medios": medios,
        "categoria": categoria,
        "dificultad": dificultad,
        "palabra_clave": palabra_clave,
    }








def filtrar_platos_por_lo_que_tengo(platos, usuario, usar_lo_que_tengo):
    if usar_lo_que_tengo != "1":
        return platos

    palabras = [
        palabra.strip()
        for palabra in LoQueTengoPalabra.objects.filter(
            profile__user=usuario
        ).values_list("palabra", flat=True)
        if palabra and palabra.strip()
    ]

    if not palabras:
        return platos

    condicion = Q()

    for palabra in palabras:
        condicion |= Q(nombre_plato__icontains=palabra)
        condicion |= Q(ingredientes__icontains=palabra)
        condicion |= Q(ingredientes_en_plato__ingrediente__nombre__icontains=palabra)

    return platos.filter(condicion).distinct()


def obtener_resultados_principales(
    usuario,
    tipo_parametro,
    quecomemos,
    misplatos,
    medios,
    categoria,
    dificultad,
    palabra_clave,
    usar_lo_que_tengo=None
):


    if tipo_parametro == "Delivery":
        lugares = Lugar.objects.filter(
            propietario=usuario,
            delivery=True
        )

        if palabra_clave:
            lugares = lugares.filter(
                Q(nombre__icontains=palabra_clave)
            )

        platos = ""
        platos_carousel = ""
        platos_listado = ""

        return lugares, platos, platos_carousel, platos_listado


    if tipo_parametro == "Comerafuera":
        lugares = Lugar.objects.filter(
            propietario=usuario,
            delivery=False
        )

        if palabra_clave:
            lugares = lugares.filter(
                Q(nombre__icontains=palabra_clave)
            )

        platos = ""
        platos_carousel = ""
        platos_listado = ""

        return lugares, platos, platos_carousel, platos_listado

    lugares = ""

    tipo_parametro_filtro = None if tipo_parametro == "LoQueTengo" else tipo_parametro

    resultado_filtro = filtrar_platos(
        usuario=usuario,
        tipo_parametro=tipo_parametro_filtro,
        quecomemos=quecomemos,
        misplatos=misplatos,
        medios=medios,
        categoria=categoria,
        dificultad=dificultad,
        palabra_clave=palabra_clave,
    )

    platos = resultado_filtro["platos"]

    platos = filtrar_platos_por_lo_que_tengo(

        platos=platos,

        usuario=usuario,

        usar_lo_que_tengo=usar_lo_que_tengo,

    )

    platos_carousel = platos
    platos_listado = platos

    hoy = timezone.localdate()

    for p in platos:
        p.dias_desde_ultima = (
            hoy - p.ultima_programacion
        ).days if getattr(p, "ultima_programacion", None) else None

        for v in p.variedades_hijas.all():
            v.dias_desde_ultima = (
                hoy - v.ultima_programacion
            ).days if getattr(v, "ultima_programacion", None) else None

    return lugares, platos, platos_carousel, platos_listado



ORDEN_GRUPOS_LO_QUE_TENGO = [
    ("Principal", "Platos Principales", ("Principal",)),
    ("Entrada", "Entradas", ("Entrada",)),
    ("Dip", "Dips y Salsas", ("Dip", "Salsa")),
    ("Guarnicion", "Guarniciones", ("Guarnicion", "Guarnición")),
    ("Picada", "Picadas", ("Picada",)),
    ("Postre", "Postres / Reposterías", ("Postre", "Torta")),
    ("Trago", "Bebidas / Tragos", ("Trago",)),
]


def agrupar_platos_para_lo_que_tengo(platos):
    platos_lista = list(platos)
    usados = set()
    grupos = []

    for codigo, titulo, tipos_grupo in ORDEN_GRUPOS_LO_QUE_TENGO:
        platos_grupo = []

        for plato in platos_lista:
            if plato.id in usados:
                continue

            tipos_plato = plato.tipos or ""

            if any(tipo in tipos_plato for tipo in tipos_grupo):
                platos_grupo.append(plato)
                usados.add(plato.id)

        if platos_grupo:
            grupos.append({
                "codigo": codigo,
                "titulo": titulo,
                "platos": platos_grupo,
            })

    return grupos


def obtener_extras_platos(usuario):
    guarniciones = (
        Plato.objects
        .filter(propietario=usuario)
        .filter(
            Q(tipos__icontains="Guarnicion") |
            Q(tipos__icontains="Guarnición")
        )
        .order_by("nombre_plato")
    )

    salsas = (
        Plato.objects
        .filter(
            propietario=usuario,
            tipos__icontains="Salsa"
        )
        .order_by("nombre_plato")
    )

    return guarniciones, salsas


def obtener_habitos_lookup(habitos):
    return {
        (h.dia_semana, h.momento, h.plato_id): h.id
        for h in habitos
    }


def obtener_contexto_compartidos(usuario):
    """
    Devuelve datos laterales de la pantalla de platos.

    No participa del filtrado principal de platos:
    - mensajes agrupados
    - platos compartidos pendientes de importar
    """
    return {
        "platos_compartidos": obtener_platos_compartidos_pendientes(usuario),
        "lugares_compartidos": obtener_lugares_compartidos_pendientes(usuario),

    }


@login_required(login_url=reverse_lazy('login'), redirect_field_name=None)
def FiltroDePlatos(request):

    fecha_actual, dias_desde_hoy = obtener_dias_desde_hoy()

    # Obtener el usuario actual
    usuario = request.user

    perfil = obtener_perfil_usuario(usuario)
    if perfil is None:
        return redirect("profile-create")

    habitos, habitos_set = obtener_habitos_usuario(perfil)
    
    asegurar_menus_desde_habitos(request, usuario, dias_desde_hoy, habitos)

    dia_activo, dia_activo_obj = obtener_dia_activo(request, dias_desde_hoy)

    estado_filtros = obtener_estado_filtros_platos(request, dia_activo)
    form = estado_filtros["form"]
    tipo_parametro = estado_filtros["tipo_parametro"]
    tipopag = estado_filtros["tipopag"]
    quecomemos = estado_filtros["quecomemos"]
    misplatos = estado_filtros["misplatos"]
    medios = estado_filtros["medios"]
    categoria = estado_filtros["categoria"]
    dificultad = estado_filtros["dificultad"]
    palabra_clave = estado_filtros["palabra_clave"]
    usar_lo_que_tengo = estado_filtros["usar_lo_que_tengo"]

    lugares, platos, platos_carousel, platos_listado = obtener_resultados_principales(
        usuario=usuario,
        tipo_parametro=tipo_parametro,
        quecomemos=quecomemos,
        misplatos=misplatos,
        medios=medios,
        categoria=categoria,
        dificultad=dificultad,
        palabra_clave=palabra_clave,
        usar_lo_que_tengo=usar_lo_que_tengo,
    )



    fechas_existentes = obtener_fechas_existentes_menu(usuario, fecha_actual)

    # Accede al atributo `amigues` desde la instancia
    amigues = obtener_usernames_amigues(request.user)

    # el avatar
    avatar = perfil.avatar_url

    contexto_compartidos = obtener_contexto_compartidos(usuario)
    

    platos_dia_x_dia, dias_programados = obtener_platos_dia_x_dia(
        usuario,
        fechas_existentes,
        habitos_set
    )



    habitos_lookup = obtener_habitos_lookup(habitos)


    guarniciones, salsas = obtener_extras_platos(usuario)

    platos_agrupados_lo_que_tengo = (
        agrupar_platos_para_lo_que_tengo(platos_listado)
        if tipopag == "LoQueTengo"
        else None
    )

    return_to_url = request.get_full_path()

    contexto = {
                'formulario': form,
                'platos': platos_listado,
                "return_to_url": return_to_url,
                "platos_agrupados_lo_que_tengo": platos_agrupados_lo_que_tengo,
                "carousel_items": platos_carousel,
                "dias_desde_hoy": dias_desde_hoy,
                "dias_programados": dias_programados,
                "quecomemos_ck": quecomemos,
                "misplatos_ck": misplatos,
                "usar_lo_que_tengo_ck": usar_lo_que_tengo,
                "amigues": amigues,
                "parametro_activo": tipo_parametro,
                **contexto_compartidos,
                'dia_activo': dia_activo,
                'dia_activo_obj': dia_activo_obj,
                "guarniciones": guarniciones,
                "salsas": salsas,
                "platos_dia_x_dia": platos_dia_x_dia,
                "lugares": lugares,
                "habitos_lookup": habitos_lookup,
            }

    
    # tipopag = (request.GET.get("tipopag") or "Principal").strip()
    contexto["tipopag"] = tipopag

    return render(request, 'AdminVideos/lista_filtrada.html', contexto)

@login_required(login_url=reverse_lazy('login'), redirect_field_name=None)
def ajax_listado_platos(request):
    usuario = request.user

    perfil = obtener_perfil_usuario(usuario)
    if perfil is None:
        return redirect("profile-create")

    fecha_actual, dias_desde_hoy = obtener_dias_desde_hoy()
    dia_activo, dia_activo_obj = obtener_dia_activo(request, dias_desde_hoy)

    estado_filtros = obtener_estado_filtros_platos(request, dia_activo)

    tipo_parametro = estado_filtros["tipo_parametro"]
    tipopag = estado_filtros["tipopag"]
    quecomemos = estado_filtros["quecomemos"]
    misplatos = estado_filtros["misplatos"]
    medios = estado_filtros["medios"]
    categoria = estado_filtros["categoria"]
    dificultad = estado_filtros["dificultad"]
    palabra_clave = estado_filtros["palabra_clave"]
    usar_lo_que_tengo = estado_filtros["usar_lo_que_tengo"]

    lugares, platos, platos_carousel, platos_listado = obtener_resultados_principales(
        usuario=usuario,
        tipo_parametro=tipo_parametro,
        quecomemos=quecomemos,
        misplatos=misplatos,
        medios=medios,
        categoria=categoria,
        dificultad=dificultad,
        palabra_clave=palabra_clave,
        usar_lo_que_tengo=usar_lo_que_tengo,
    )

    platos_agrupados_lo_que_tengo = (
        agrupar_platos_para_lo_que_tengo(platos_listado)
        if tipopag == "LoQueTengo"
        else None
    )

    return_to_url = request.POST.get("return_to") or reverse("filtro-de-platos")

    contexto = {
        "platos": platos_listado,
        "return_to_url": return_to_url,
        "platos_agrupados_lo_que_tengo": platos_agrupados_lo_que_tengo,
        "carousel_items": platos_carousel,
        "lugares": lugares,
        "amigues": obtener_usernames_amigues(request.user),
        "tipopag": tipopag,
    }

    html_listado = render_to_string(
        "AdminVideos/partials/_listado_platos.html",
        contexto,
        request=request
    )

    html_carousel = render_to_string(
        "AdminVideos/partials/_carousel_platos.html",
        contexto,
        request=request
    )

    html_lugares = render_to_string(
        "AdminVideos/partials/_listado_lugares.html",
        contexto,
        request=request
    )

    return JsonResponse({
        "html_listado": html_listado,
        "html_carousel": html_carousel,
        "html_lugares": html_lugares,
    })



def _profile_usuario(usuario):
    profile, _ = Profile.objects.get_or_create(user=usuario)
    return profile


def _serializar_palabras_lo_que_tengo(profile):
    palabras = (
        LoQueTengoPalabra.objects
        .filter(profile=profile)
        .order_by("palabra")
    )

    return [
        {
            "id": palabra.id,
            "palabra": palabra.palabra,
        }
        for palabra in palabras
    ]


@login_required
def ajax_lo_que_tengo_palabras(request):
    profile = _profile_usuario(request.user)

    return JsonResponse({
        "ok": True,
        "palabras": _serializar_palabras_lo_que_tengo(profile),
    })


@login_required
@require_POST
def ajax_lo_que_tengo_agregar(request):
    profile = _profile_usuario(request.user)

    palabra = (request.POST.get("palabra") or "").strip()

    if not palabra:
        return JsonResponse({
            "ok": False,
            "error": "Ingresá una palabra.",
        }, status=400)

    if len(palabra) > 60:
        return JsonResponse({
            "ok": False,
            "error": "La palabra no puede superar los 60 caracteres.",
        }, status=400)

    existente = LoQueTengoPalabra.objects.filter(
        profile=profile,
        palabra__iexact=palabra,
    ).first()

    if not existente:
        LoQueTengoPalabra.objects.create(
            profile=profile,
            palabra=palabra,
        )

    return JsonResponse({
        "ok": True,
        "palabras": _serializar_palabras_lo_que_tengo(profile),
    })


@login_required
@require_POST
def ajax_lo_que_tengo_eliminar(request, pk):
    profile = _profile_usuario(request.user)

    palabra = get_object_or_404(
        LoQueTengoPalabra,
        pk=pk,
        profile=profile,
    )
    palabra.delete()

    return JsonResponse({
        "ok": True,
        "palabras": _serializar_palabras_lo_que_tengo(profile),
    })



class SolicitarAmistadForm(forms.Form):
    destinatario = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label="Usuario",
    )


class SolicitarAmistad(LoginRequiredMixin, FormView):
    form_class = SolicitarAmistadForm

    def es_ajax(self):
        return self.request.headers.get("x-requested-with") == "XMLHttpRequest"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        usuarios_excluidos = obtener_ids_usuarios_con_amistad_activa(self.request.user)
        usuarios_excluidos.append(self.request.user.id)

        form.fields["destinatario"].queryset = (
            User.objects
            .exclude(id__in=usuarios_excluidos)
            .order_by("username")
        )

        return form

    def render_form_ajax(self, form, status=200):
        html = render_to_string(
            "AdminVideos/partials/_form_solicitar_amistad.html",
            {"form": form},
            request=self.request,
        )

        return JsonResponse({
            "ok": False,
            "html": html,
        }, status=status)

    def render_panel_amigues_ajax(self, mensaje, nivel="success"):
        context = obtener_contexto_amigues(self.request.user)

        html = render_to_string(
            "AdminVideos/partials/_panel_amigues.html",
            context,
            request=self.request,
        )

        return JsonResponse({
            "ok": True,
            "message": mensaje,
            "level": nivel,
            "html": html,
            "cantidad": context["solicitudes_pendientes"].count(),
        })

    def get(self, request, *args, **kwargs):
        form = self.get_form()

        html = render_to_string(
            "AdminVideos/partials/_form_solicitar_amistad.html",
            {"form": form},
            request=request,
        )

        return JsonResponse({
            "ok": True,
            "html": html,
        })

    def form_invalid(self, form):
        return self.render_form_ajax(form, status=400)

    def form_valid(self, form):
        solicitante = self.request.user
        destinatario = form.cleaned_data["destinatario"]

        usuario_1, usuario_2 = Amistad.normalizar_usuarios(solicitante, destinatario)

        amistad, creada = Amistad.objects.get_or_create(
            usuario_1=usuario_1,
            usuario_2=usuario_2,
            defaults={
                "solicitada_por": solicitante,
                "estado": Amistad.PENDIENTE,
            },
        )

        if not creada:
            if amistad.estado == Amistad.ACEPTADA:
                return self.render_panel_amigues_ajax(
                    "Ya son amigues.",
                    "info",
                )

            if amistad.estado == Amistad.PENDIENTE:
                return self.render_panel_amigues_ajax(
                    "Ya hay una solicitud de amistad pendiente.",
                    "info",
                )

            amistad.estado = Amistad.PENDIENTE
            amistad.solicitada_por = solicitante
            amistad.save(update_fields=["estado", "solicitada_por", "actualizada_el"])

        return self.render_panel_amigues_ajax(
            "Solicitud de amistad enviada.",
            "success",
        )




class EnviarMensaje(LoginRequiredMixin, CreateView):
    model = Mensaje
    fields = ["mensaje", "destinatario"]

    def es_ajax(self):
        return self.request.headers.get("X-Requested-With") == "XMLHttpRequest"

    def get_destinatario(self):
        return get_object_or_404(User, username=self.kwargs.get("usuario"))

    def configurar_form_destinatario(self, form):
        destinatario = self.get_destinatario()
        form.fields["destinatario"].queryset = User.objects.filter(pk=destinatario.pk)
        form.initial["destinatario"] = destinatario
        return form

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        return self.configurar_form_destinatario(form)

    def get_empty_form(self):
        form_class = self.get_form_class()
        form = form_class()
        return self.configurar_form_destinatario(form)

    def get_success_url(self):
        return reverse_lazy("enviar-mensaje", kwargs={"usuario": self.kwargs["usuario"]})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        destinatario = self.get_destinatario()

        Mensaje.objects.filter(
            usuario_que_envia_fk=destinatario,
            destinatario=self.request.user,
            leido=False,
        ).update(leido=True)

        mensajes = Mensaje.objects.filter(
            Q(usuario_que_envia_fk=self.request.user, destinatario=destinatario) |
            Q(usuario_que_envia_fk=destinatario, destinatario=self.request.user)
        ).order_by("-creado_el")

        context["destinatario"] = destinatario
        context["mensajes"] = mensajes
        context["amigues"] = obtener_usernames_amigues(self.request.user)

        return context

    def cantidad_no_leidos(self):
        return (
            Mensaje.objects
            .filter(
                destinatario=self.request.user,
                leido=False,
                usuario_que_envia_fk__isnull=False,
            )
            .values("usuario_que_envia_fk")
            .distinct()
            .count()
        )


    def render_chat_ajax(self, form=None, status=200):
        if form is None:
            form = self.get_empty_form()

        context = self.get_context_data(form=form)

        html = render_to_string(
            "AdminVideos/partials/_chat_modal_content.html",
            context,
            request=self.request,
        )

        return JsonResponse({
            "ok": status < 400,
            "html": html,
            "cantidad": self.cantidad_no_leidos(),
        }, status=status)

    def get(self, request, *args, **kwargs):
        self.object = None

        if self.es_ajax():
            return self.render_chat_ajax()

        return redirect("filtro-de-platos")

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.usuario_que_envia_fk = self.request.user
        self.object.destinatario = self.get_destinatario()
        self.object.save()

        if self.es_ajax():
            return self.render_chat_ajax(form=self.get_empty_form())

        return redirect(self.get_success_url())

    def form_invalid(self, form):
        self.object = None

        if self.es_ajax():
            return self.render_chat_ajax(form=form, status=400)

        return redirect("filtro-de-platos")



class compartir_elemento(CreateView):
    model = ElementoCompartido
    template_name = 'AdminVideos/compartir_elemento.html'
    success_url = reverse_lazy('filtro-de-platos')

    # Solo incluimos el campo del mensaje.
    # El elemento compartido, destinatario y tipo se asignan manualmente.
    fields = ['mensaje']

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["mensaje"].required = True
        return form

    def get_context_data(self, **kwargs):
        # =====================================================
        # Contexto para confirmar el elemento que se va a compartir
        # =====================================================
        context = super().get_context_data(**kwargs)

        elemento_id = self.request.POST.get('elemento_id', '').strip()
        amigue = self.request.POST.get('amigue', '').strip()
        tipo_elemento = self.request.POST.get('tipo_elemento', '').strip()

        context['elemento_id'] = elemento_id
        context['amigue'] = amigue
        context['tipo_elemento'] = tipo_elemento

        return context

    def form_valid(self, form):
        # =====================================================
        # Datos enviados desde el formulario de compartir
        # =====================================================
        elemento_id = self.request.POST.get('elemento_id', '').strip()
        amigue_username = self.request.POST.get('amigue', '').strip()
        tipo_elemento = self.request.POST.get('tipo_elemento', '').strip()

        # =====================================================
        # Validaciones mínimas
        # =====================================================
        if not elemento_id or not elemento_id.isdigit():
            messages.error(self.request, "No se pudo compartir: falta el elemento.")
            return redirect(self.success_url)

        if not amigue_username:
            messages.error(self.request, "No se pudo compartir: falta seleccionar un amigue.")
            return redirect(self.success_url)

        if tipo_elemento not in (ElementoCompartido.PLATO, ElementoCompartido.LUGAR):
            messages.error(self.request, "No se pudo compartir: tipo de elemento inválido.")
            return redirect(self.success_url)

        elemento_id = int(elemento_id)
        destinatario = get_object_or_404(User, username=amigue_username)

        # =====================================================
        # Datos comunes del compartido
        # =====================================================
        form.instance.usuario_que_envia = self.request.user
        form.instance.destinatario = destinatario
        form.instance.tipo = tipo_elemento
        form.instance.estado = ElementoCompartido.PENDIENTE

        # =====================================================
        # Elemento compartido
        # =====================================================
        if tipo_elemento == ElementoCompartido.PLATO:
            form.instance.plato = get_object_or_404(Plato, id=elemento_id)

        elif tipo_elemento == ElementoCompartido.LUGAR:
            form.instance.lugar = get_object_or_404(Lugar, id=elemento_id)

        messages.success(self.request, "Elemento compartido correctamente.")
        return super().form_valid(form)








def obtener_contexto_amigues(usuario):
    """
    Devuelve el contexto necesario para mostrar el panel de amigues.
    """
    return {
        "amigues": obtener_usernames_amigues(usuario),
        "solicitudes_pendientes": obtener_solicitudes_amistad_pendientes(usuario),
        "solicitudes_enviadas": obtener_solicitudes_amistad_enviadas(usuario),
        "parametro": "amigues",
    }

@login_required
def ajax_panel_amigues(request):
    context = obtener_contexto_amigues(request.user)

    html = render_to_string(
        "AdminVideos/partials/_panel_amigues.html",
        context,
        request=request,
    )

    return JsonResponse({
        "html": html,
        "cantidad": context["solicitudes_pendientes"].count(),
    })

@login_required
def historial(request):
    # Obtener el perfil del usuario autenticado
    profile = request.user.profile

    # Obtener todos los mensajes donde el usuario es el destinatario, ordenados por fecha de creación
    # mensajes = Mensaje.objects.filter(destinatario=request.user).order_by("-creado_el")

    # Obtener todos los mensajes donde el usuario es el destinatario o el que los envió, ordenados por fecha de creación
    mensajes = Mensaje.objects.filter(
        Q(destinatario=request.user) | Q(usuario_que_envia_fk=request.user)
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
    def respuesta_ajax(mensaje, nivel="success", ok=True, status=200):
        context = obtener_contexto_amigues(request.user)

        html = render_to_string(
            "AdminVideos/partials/_panel_amigues.html",
            context,
            request=request,
        )

        return JsonResponse({
            "ok": ok,
            "message": mensaje,
            "level": nivel,
            "html": html,
            "cantidad": context["solicitudes_pendientes"].count(),
        }, status=status)

    if request.method != "POST":
        return respuesta_ajax(
            "Método no permitido.",
            nivel="warning",
            ok=False,
            status=405,
        )

    amistad_id = request.POST.get("amistad_id")

    amistad = get_object_or_404(
        Amistad,
        id=amistad_id,
        estado=Amistad.PENDIENTE,
    )

    if not amistad.involucra_a(request.user):
        return respuesta_ajax(
            "No podés aceptar esta solicitud.",
            nivel="danger",
            ok=False,
            status=403,
        )

    if amistad.solicitada_por_id == request.user.id:
        return respuesta_ajax(
            "No podés aceptar una solicitud enviada por vos.",
            nivel="warning",
            ok=False,
            status=400,
        )

    amistad.estado = Amistad.ACEPTADA
    amistad.save(update_fields=["estado", "actualizada_el"])

    return respuesta_ajax(
        "Solicitud de amistad aceptada.",
        nivel="success",
    )



@login_required
@require_POST
def amigue_borrar(request, pk):

    amigue = get_object_or_404(User, username=pk)

    usuario_1, usuario_2 = Amistad.normalizar_usuarios(request.user, amigue)

    borradas, _ = Amistad.objects.filter(
        usuario_1=usuario_1,
        usuario_2=usuario_2,
    ).delete()

    if borradas:
        mensaje = "Amigue eliminado."
        nivel = "success"
    else:
        mensaje = "No se encontró esa amistad para borrar."
        nivel = "warning"

    context = obtener_contexto_amigues(request.user)

    html = render_to_string(
        "AdminVideos/partials/_panel_amigues.html",
        context,
        request=request,
    )

    return JsonResponse({
        "ok": bool(borradas),
        "message": mensaje,
        "level": nivel,
        "html": html,
        "cantidad": context["solicitudes_pendientes"].count(),
    })



def copiar_lugar_para_usuario(lugar_original, usuario):
    """
    Crea una copia simple de un lugar para otro usuario.
    """
    return Lugar.objects.create(
        nombre=lugar_original.nombre,
        direccion=lugar_original.direccion,
        telefono=lugar_original.telefono,
        enlace=lugar_original.enlace,
        dias_horarios=lugar_original.dias_horarios,
        image=lugar_original.image,
        delivery=lugar_original.delivery,
        propietario=usuario,
    )


def copiar_plato_para_usuario(plato_original, usuario):
    """
    Crea una copia de un plato para otro usuario.

    Copia:
    - campos principales del plato
    - componentes
    - ingredientes detallados
    """
    nuevo_plato = Plato.objects.create(
        nombre_plato=plato_original.nombre_plato,
        nombre_grupo=plato_original.nombre_grupo,
        receta=plato_original.receta,
        ingredientes=plato_original.ingredientes,
        medios=plato_original.medios,
        categoria=plato_original.categoria,
        elaboracion=plato_original.elaboracion,
        coccion=plato_original.coccion,
        tipos=plato_original.tipos,
        estacionalidad=plato_original.estacionalidad,
        porciones=plato_original.porciones,
        enlace=plato_original.enlace,
        propietario=usuario,
        image=plato_original.image,
        proviene_de=plato_original.propietario.username,
        id_original=plato_original.id,
    )

    # Copiar componentes
    nuevo_plato.componentes.set(plato_original.componentes.all())

    # Copiar ingredientes detallados sin depender de una lista fija de campos
    for ingrediente_en_plato in plato_original.ingredientes_en_plato.all():
        datos_ingrediente = {
            field.name: getattr(ingrediente_en_plato, field.name)
            for field in IngredienteEnPlato._meta.fields
            if field.name not in ("id", "plato")
        }

        IngredienteEnPlato.objects.create(
            plato=nuevo_plato,
            **datos_ingrediente,
        )

    return nuevo_plato


@login_required
def agregar_lugar_compartido(request, pk, compartido_id):
    """
    Importa un lugar compartido al usuario logueado.
    """
    with transaction.atomic():
        compartido = get_object_or_404(
            ElementoCompartido,
            pk=compartido_id,
            destinatario=request.user,
            tipo=ElementoCompartido.LUGAR,
            estado=ElementoCompartido.PENDIENTE,
            lugar_id=pk,
        )

        copiar_lugar_para_usuario(compartido.lugar, request.user)

        compartido.estado = ElementoCompartido.IMPORTADO
        compartido.save(update_fields=["estado", "actualizado_el"])

    messages.success(request, "El lugar se agregó exitosamente.")
    return redirect("filtro-de-platos")


@login_required
def agregar_plato_compartido(request, pk, mensaje_id):
    """
    Importa un plato compartido al usuario logueado.

    Nota:
    - mensaje_id queda como nombre de parámetro por compatibilidad con la URL actual.
    - Internamente ahora representa el id de ElementoCompartido.
    """
    with transaction.atomic():
        compartido = get_object_or_404(
            ElementoCompartido,
            pk=mensaje_id,
            destinatario=request.user,
            tipo=ElementoCompartido.PLATO,
            estado=ElementoCompartido.PENDIENTE,
            plato_id=pk,
        )

        plato_original = compartido.plato
        nuevo_plato = copiar_plato_para_usuario(plato_original, request.user)

        compartido.estado = ElementoCompartido.IMPORTADO
        compartido.plato_importado = nuevo_plato
        compartido.save(update_fields=["estado", "plato_importado", "actualizado_el"])

    messages.success(request, "El plato se agregó exitosamente.")
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
        es_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

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

                # Asegúrate de que el objeto lugar se está pasando correctamente
                menu_item = MenuItem.objects.create(
                    menu=menu_dia,
                    momento=momento,
                    lugar=lugar,  # Asignamos el lugar al MenuItem
                )
                
                messages.success(request, f"Lugar {lugar.nombre} (ID: {lugar.id}) asignado correctamente a {momento}.")


        except Exception as e:
            messages.warning(request, "Ese elemento ya estaba asignado a esa comida en ese día.")

            if es_ajax:
                return JsonResponse({
                    "ok": False,
                    "message": "Ese elemento ya estaba asignado o no se pudo asignar.",
                    "error": str(e),
                }, status=400)

        if es_ajax:
            return JsonResponse({
                "ok": True,
                "message": "Elemento asignado correctamente.",
            })

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


def eliminar_item_programado(usuario, es_lugar, objeto_id, comida, fecha):
    """
    Elimina un plato o lugar programado de un menú diario.

    También elimina el hábito semanal asociado a ese mismo:
    - perfil
    - día de semana
    - momento/comida
    - plato o lugar

    Devuelve un dict con:
    - ok: bool
    - level: success | warning | error
    - message: texto para mostrar
    """

    if isinstance(fecha, str):
        try:
            fecha = datetime.datetime.strptime(fecha, "%Y-%m-%d").date()
        except ValueError:
            return {
                "ok": False,
                "level": "error",
                "message": "Fecha inválida.",
            }

    menu = MenuDia.objects.filter(
        propietario=usuario,
        fecha=fecha
    ).first()

    if not menu:
        return {
            "ok": False,
            "level": "error",
            "message": "No se encontró el menú del día.",
        }

    try:
        es_lugar = bool(int(es_lugar))
    except (TypeError, ValueError):
        return {
            "ok": False,
            "level": "error",
            "message": "Tipo inválido.",
        }

    qs = menu.items.filter(momento=comida)
    dia_semana = fecha.weekday()
    perfil = usuario.profile

    if es_lugar:
        lugar_qs = Lugar.objects.all()

        if hasattr(Lugar, "propietario"):
            lugar_qs = lugar_qs.filter(propietario=usuario)

        lugar = lugar_qs.filter(id=objeto_id).first()

        if not lugar:
            return {
                "ok": False,
                "level": "error",
                "message": f"Lugar con ID '{objeto_id}' no encontrado.",
            }

        borrados, _ = qs.filter(lugar_id=lugar.id).delete()

        if borrados:
            HabitoSemanal.objects.filter(
                perfil=perfil,
                dia_semana=dia_semana,
                momento=comida,
                lugar_id=lugar.id
            ).delete()

            return {
                "ok": True,
                "level": "success",
                "message": f"Lugar '{lugar.nombre}' eliminado correctamente.",
            }

        return {
            "ok": False,
            "level": "warning",
            "message": f"No se encontró el lugar '{lugar.nombre}' para {comida}.",
        }

    plato = Plato.objects.filter(
        id=objeto_id,
        propietario=usuario
    ).first()

    if not plato:
        return {
            "ok": False,
            "level": "error",
            "message": f"Plato con ID '{objeto_id}' no encontrado.",
        }

    borrados, _ = qs.filter(plato_id=plato.id).delete()

    nombre = (
        getattr(plato, "nombre_plato", None)
        or getattr(plato, "nombre", str(plato))
    )

    if borrados:
        HabitoSemanal.objects.filter(
            perfil=perfil,
            dia_semana=dia_semana,
            momento=comida,
            plato_id=plato.id
        ).delete()

        return {
            "ok": True,
            "level": "success",
            "message": f"Plato '{nombre}' eliminado correctamente.",
        }

    return {
        "ok": False,
        "level": "warning",
        "message": f"No se encontró el plato '{nombre}' para {comida}.",
    }

@login_required
def eliminar_programado(request, es_lugar, objeto_id, comida, fecha):
    resultado = eliminar_item_programado(
        usuario=request.user,
        es_lugar=es_lugar,
        objeto_id=objeto_id,
        comida=comida,
        fecha=fecha,
    )

    if resultado["level"] == "success":
        messages.success(request, resultado["message"])
    elif resultado["level"] == "warning":
        messages.warning(request, resultado["message"])
    else:
        messages.error(request, resultado["message"])

    return redirect("filtro-de-platos")



@login_required
@require_POST
def ajax_eliminar_programado(request):
    es_lugar = request.POST.get("es_lugar")
    objeto_id = request.POST.get("objeto_id")
    comida = request.POST.get("comida")
    fecha = request.POST.get("fecha")

    resultado = eliminar_item_programado(
        usuario=request.user,
        es_lugar=es_lugar,
        objeto_id=objeto_id,
        comida=comida,
        fecha=fecha,
    )

    status = 200 if resultado.get("ok") else 400
    return JsonResponse(resultado, status=status)





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

