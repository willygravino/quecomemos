from collections import defaultdict
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
from AdminVideos.models import HistoricoDia, HistoricoItem, Ingrediente, IngredienteEnPlato, Lugar, Plato, Profile, Mensaje,  ElegidosXDia
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string   # ✅ ← ESTA ES LA CLAVE
from django.http import Http404, JsonResponse
from django.urls import reverse, reverse_lazy
from django.contrib.auth.forms import UserCreationForm
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from datetime import datetime, timedelta
from .forms import IngredienteEnPlatoFormSet, LugarForm, PlatoFilterForm, PlatoForm, CustomAuthenticationForm
from datetime import date, datetime
from django.contrib.auth.models import User  # Asegúrate de importar el modelo User
from django.db.models import Q, Subquery, OuterRef
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



# def api_ingredientes(request):
#     q = request.GET.get('q', '')
#     ingredientes = Ingrediente.objects.filter(nombre__icontains=q).order_by('nombre')[:20]  # límite de resultados
#     data = [{"id": ing.id, "nombre": ing.nombre} for ing in ingredientes]
#     return JsonResponse(data, safe=False)



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

def procesar_item(platos_dia, item_nombre, menu_del_dia, dia_en_que_comemos_str, request, lista_de_ingredientes, no_incluir):

    resultado = {}
    # Extraer el plato y los ingredientes del item
    # ej guarnicion1
    # item = platos_dia.get(item_nombre, {})
    # ej Tortilla
    item_plato = platos_dia.get(item_nombre, {}).get("plato", [])
    item_ingredientes  = platos_dia.get(item_nombre, {}).get("ingredientes", [])

    # item_plato = platos_dia..get("plato", [])
    # ej papa, huevo
    # item_ingredientes = item.get("ingredientes", [])

    # Crear la cadena `buscar_item` con el día concatenado si `plato` tiene valor
    if item_plato:
        buscar_item = item_plato + dia_en_que_comemos_str
       # Variable para indicar si el item fue elegido
        # item_elegido = False

        # Si `buscar_item` está en los datos POST de la petición
        if buscar_item in request.POST:
            item_elegido = True
            lista_de_ingredientes.update({ingrediente.strip() for ingrediente in item_ingredientes.split(',')})

            # Marcar el item como elegido si aún no está marcado
            if not menu_del_dia.platos_que_comemos[item_nombre]["elegido"]:
                menu_del_dia.platos_que_comemos[item_nombre]["elegido"] = True
                # Guardar cambios en la base de datos
                menu_del_dia.save()
                no_incluir.update({ingrediente.strip() for ingrediente in item_ingredientes.split(',')})

        else:
            item_elegido = False
            # Si el item no se seleccionó, marcarlo como no elegido
            menu_del_dia.platos_que_comemos[item_nombre]["elegido"] = False
            # Guardar cambios en la base de datos
            menu_del_dia.save()

        # Agregar el item al diccionario `items` con la estructura deseada
        resultado [item_nombre] = {"plato": item_plato,
            "ingredientes": item_ingredientes,
            "elegido": item_elegido
        }
    # else:
    #     resultado = {}



    # Retornar los valores que necesitarás fuera de la función
    return resultado,  lista_de_ingredientes, no_incluir




@login_required
def lista_de_compras(request):
    # locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')  # Configura la localización a español

    locale.setlocale(locale.LC_TIME, 'C')

    # Obtener la fecha actual
    today = date.today()

    lista_de_ingredientes = set()
    ingredientes_unicos = {}  # Diccionario para almacenar ingredientes a comprar, estado, comentario
    lista_de_compras = set()
    no_elegidos = set()
    ingredientes_elegidos = set()

    # Filtrar los objetos de ElegidosXDia para excluir aquellos cuya fecha sea anterior a la fecha actual
    menues_del_usuario = ElegidosXDia.objects.filter(user=request.user, el_dia_en_que_comemos__gte=today).order_by('el_dia_en_que_comemos')

    # menues_del_usuario = ComidaDelDia.objects.filter(user=request.user, fecha__gte=today).order_by('fecha', 'momento')

    # Obtener el perfil del usuario actual
    perfil = get_object_or_404(Profile, user=request.user)

    # VARIABLES PARA PRUEBAS
    # ingrediente_limpio = set()
    # ingredientes_elegidos_calculados = set()
    # no_elegidos_calculados = set()
    # clave_fecha = ""
    # variedades_seleccionadas = ""

    def norm(s: str) -> str:
        return (s or "").strip().lower()
    
    ingredientes_elegidos = set(request.POST.getlist("ingrediente_a_comprar"))

    if request.method == 'POST':
        # 1) Estructuras auxiliares
        # platos seleccionados: set de claves "platoId_fecha"
        platos_seleccionados = set(request.POST.getlist("plato_seleccionado"))  # p.ej. {"155_20250926", ...}

        # variedades seleccionadas por clave_fecha
        # Ej: variedades_sel["155_20250926"] = {"con huevo", "sin huevo"}
        variedades_sel = defaultdict(set)
        for value in request.POST.getlist("variedad_seleccionada"):
            try:
                clave_plato_fecha, nombre_var = value.split("|", 1)  # "155_20250926" | "con huevo"
            except ValueError:
                continue
            variedades_sel[clave_plato_fecha].add(norm(nombre_var))

        # 2) Recorrer menús y actualizar true / false según lo que llegó del form
        for menu in menues_del_usuario:
            platos = menu.platos_que_comemos or {}
            fecha_menu = menu.el_dia_en_que_comemos.strftime("%Y%m%d")

            for comida, lista_platos in platos.items():
                for plato in lista_platos:
                    plato_id = str(plato.get("id_plato", ""))
                    clave_fecha = f"{plato_id}_{fecha_menu}"

                    if clave_fecha in platos_seleccionados:
                        plato_estaba_elegido = plato.get("elegido", False)
                        # Si antes era False y ahora (según el form) es True
                        if (clave_fecha in platos_seleccionados) and not plato_estaba_elegido:
                                ingred_plato_agregado = {
                                    ing.strip() for ing in (plato.get("ingredientes") or "").split(",") if ing.strip()
                                }
                                if ingred_plato_agregado:
                                    ingredientes_tengo = set(perfil.ingredientes_que_tengo)
                                    # no_elegidos_calculados = ingred_variedad_agregada & ingredientes_tengo
                                    # ingredientes_elegidos_calculados |= ingred_variedad_agregada - ingredientes_tengo
                                    no_elegidos = ingred_plato_agregado & ingredientes_tengo
                                    ingredientes_elegidos |= ingred_plato_agregado - ingredientes_tengo

                        # Actualiza el estado (sin usar variable intermedia)
                        plato["elegido"] = True

                        # Variedades: comparamos por NOMBRE normalizado (lo que llega del form)
                        seleccionadas = variedades_sel.get(clave_fecha, set())
                        
                        for _, var_data in (plato.get("variedades") or {}).items():
                            nombre_var = var_data.get("nombre")
                            var_estaba_elegida = var_data.get("elegido", False)

                            # Si antes era False y ahora (según el form) es True
                            if (nombre_var in seleccionadas) and not var_estaba_elegida:
                                ingred_variedad_agregada = {
                                    ing.strip() for ing in (var_data.get("ingredientes") or "").split(",") if ing.strip()
                                }
                                if ingred_variedad_agregada:
                                    ingredientes_tengo = set(perfil.ingredientes_que_tengo)
                                    # no_elegidos_calculados = ingred_variedad_agregada & ingredientes_tengo
                                    # ingredientes_elegidos_calculados |= ingred_variedad_agregada - ingredientes_tengo
                                    no_elegidos = ingred_variedad_agregada & ingredientes_tengo
                                    ingredientes_elegidos |= ingred_variedad_agregada - ingredientes_tengo

                            # Actualiza el estado (sin usar variable intermedia)
                            var_data["elegido"] = (nombre_var in seleccionadas)
                        
                    else:
                        plato["elegido"] = False
                        for var_data in (plato.get("variedades") or {}).values():
                            var_data["elegido"] = False

            # 3) Persistir
            menu.platos_que_comemos = platos
            menu.save()

        # Suponiendo que perfil.comentarios contiene una lista de cadenas en el formato "ingrediente%comentario"
        comentarios_guardados_lista = perfil.comentarios
        comentarios_guardados = {}

        if comentarios_guardados_lista:
            # Recorrer los comentarios guardados y convertirlos en un diccionario
            for item in comentarios_guardados_lista:
                ingrediente, comentario = item.split("%", 1)  # Divide en ingrediente y comentario
                comentarios_guardados[ingrediente] = comentario  # Guarda en el diccionario

        comentarios_posteados = {}

        for key, value in request.POST.items():
            if key.endswith("_comentario"):  # Filtra solo los comentarios
                ingrediente = key.replace("_comentario", "")  # Extraer el ingrediente del nombre del campo
                comentario_posteado = value.strip()  # Eliminar espacios en blanco al inicio y al final

                # Guarda el comentario (puede ser vacío)
                comentarios_posteados[ingrediente] = comentario_posteado

        # Recorremos el diccionario de comentarios guardados
        for ingrediente_posteado, comentario_posteado in comentarios_posteados.items():
            if ingrediente_posteado in comentarios_guardados:  # Verificamos si el ingrediente está en ambos diccionarios
                # Obtenemos el comentario guardado
                comentario_guardado = comentarios_guardados[ingrediente_posteado]
                # prepara el registro nuevo por si lo usa
                registro = f"{ingrediente_posteado}%{comentario_guardado}"
                if not comentario_posteado:
                    # Eliminar el comentario del ingrediente
                    perfil.comentarios.remove(registro)
                elif comentario_posteado != comentario_guardado:
                        # Actualizar el comentario del ingrediente
                    perfil.comentarios[perfil.comentarios.index(registro)] = f"{ingrediente_posteado}%{comentario_posteado}"

            elif comentario_posteado:
                # Unir el ingrediente nuevo con el comentario, separado por '%'
                ingrediente_con_comentario = f"{ingrediente_posteado}%{comentario_posteado}"
                # Actualizar el campo ingredientes_que_tengo
                perfil.comentarios.append(ingrediente_con_comentario)

            # Guardar los cambios en el perfil
            perfil.save()
    
    # Recorrer los menús del usuario
    for menu in menues_del_usuario:
        platos = menu.platos_que_comemos or []  # Asegurar que no sea None, sino una lista vacía

        # Recorrer las comidas del usuario (desayuno, almuerzo, cena, etc.)
        for comida, lista_platos in platos.items():
            # Recorrer cada plato en la comida
            for datos in lista_platos:
                # Si el plato está marcado como elegido, añadimos sus ingredientes
                if datos.get("elegido") and datos.get("ingredientes"):
                    lista_de_ingredientes.update(map(str.strip, datos["ingredientes"].split(",")))

                # Recorrer variedades si existen y están marcadas como elegidas
                for variedad in datos.get("variedades", {}).values():
                    if variedad.get("elegido"):
                        lista_de_ingredientes.update(map(str.strip, variedad["ingredientes"].split(",")))
                     
    if ingredientes_elegidos:
        no_elegidos = lista_de_ingredientes - ingredientes_elegidos
        for ingrediente_a_comprar in lista_de_ingredientes:
            if ingrediente_a_comprar in perfil.ingredientes_que_tengo:
                # Eliminar el ingrediente de la lista
                perfil.ingredientes_que_tengo.remove(ingrediente_a_comprar)
                # Guardar el perfil actualizado
                perfil.save()
    elif request.method != "GET":
        no_elegidos = lista_de_ingredientes    
                
    if no_elegidos:
        for ingrediente in no_elegidos:
            if ingrediente not in perfil.ingredientes_que_tengo:
                # Actualizar el campo ingredientes_que_tengo
                perfil.ingredientes_que_tengo.append(ingrediente)
                # Guardar el perfil actualizado
                perfil.save()
   
    if lista_de_ingredientes:
        for ingrediente in lista_de_ingredientes:
            el_comentario = ""
            # Recorrer la lista y buscar el comentario asociado
            for item in perfil.comentarios:
                # if "%" in item:
                ingrediente_archivado, comentario = item.split("%", 1)  # Dividir en ingrediente y comentario
                if ingrediente_archivado == ingrediente:
                    el_comentario = comentario

            if ingrediente in perfil.ingredientes_que_tengo:
                ingredientes_unicos [ingrediente] = {
                    "comentario": el_comentario,
                    "estado": "tengo" }
            else:
                ingredientes_unicos [ingrediente] = {
                    "comentario": el_comentario,
                    "estado": "no-tengo" }
   
    lista_de_compras =[]
    # Recorrer el diccionario para formatear los ingredientes que no tienes
    for ingrediente, detalles in ingredientes_unicos.items():
        if detalles["estado"] == "no-tengo":
            comentario = detalles["comentario"]
            # Formatear el ingrediente con el comentario si está presente
            if comentario:
                # mensaje_whatsapp += f"• {ingrediente} ({comentario})\n"
                lista_de_compras.append(f"{ingrediente} ({comentario})")

            else:
                # mensaje_whatsapp += f"• {ingrediente}\n"
                lista_de_compras.append(f"{ingrediente}")
    
    token = perfil.ensure_share_token()  # genera uno si no existe

    share_url = request.build_absolute_uri(
        reverse("compartir-lista", args=[token]))

    context = {
        'menues_del_usuario': menues_del_usuario,
        'ingredientes_con_tengo_y_comentario': ingredientes_unicos, # DICT TODOS LOS INGREDIENTES, CON TENGO Y COMENTARIO
        "lista_de_compras": lista_de_compras, # LISTA DE COMPRAS PARA VERLO EN ENVAR A WHATS APP
        "parametro" : "lista-compras",
        'share_url': share_url,             # 👈 NUEVO
        "lista_de_ingredientes": lista_de_ingredientes,
        "no_elegidos": no_elegidos,
        "ingredientes_elegidos": ingredientes_elegidos,
        # "ingredientes_elegidos_calculados": ingredientes_elegidos_calculados,
        # "no_elegidos_calculados" : no_elegidos_calculados,
        
     }

    return render(request, 'AdminVideos/lista_de_compras.html', context)


def _get_user_by_token_or_404(token):
    perfil = get_object_or_404(Profile, share_token=str(token))
    return perfil.user, perfil

def compartir_lista(request, token):
    share_user, perfil = _get_user_by_token_or_404(token)

    today = date.today()
    ingredientes = set()

    for menu in ElegidosXDia.objects.filter(user=share_user, el_dia_en_que_comemos__gte=today):
        platos = menu.platos_que_comemos or {}
        for _, lista_platos in platos.items():
            for p in lista_platos:
                if p.get("elegido") and p.get("ingredientes"):
                    ingredientes.update(map(str.strip, p["ingredientes"].split(",")))
                for v in (p.get("variedades") or {}).values():
                    if v.get("elegido") and v.get("ingredientes"):
                        ingredientes.update(map(str.strip, v["ingredientes"].split(",")))

    comentarios = {}
    for item in (perfil.comentarios or []):
        try:
            ingr, coment = item.split("%", 1)
            comentarios[ingr] = coment
        except ValueError:
            pass

    tengo = set(perfil.ingredientes_que_tengo or [])
    items = []
    for ing in sorted(ingredientes):
        if ing not in tengo:
            items.append({"nombre": ing, "comentario": comentarios.get(ing, "")})

    # token_for_local = f"user-{perfil.pk}"
      # Garantizar UUID
    if not perfil.share_token:
        perfil.ensure_share_token()          # genera y guarda un UUID
    api_token = perfil.share_token           # UUID para la URL del API
    local_token = f"user-{perfil.pk}"        # solo para localStorage

    api_token   = perfil.share_token          # UUID válido para el path del API

    return render(request, "AdminVideos/compartir_lista.html", {
        "items": items,
        "token": local_token,                 # ← se usa para localStorage
        "api_token": api_token,               # ← se usa para la URL del API
    })

    # return render(request, "AdminVideos/compartir_lista.html", {
    #     "items": items,
    #     "token": token_for_local,  # solo para localStorage del visitante
    # })


# def compartir_lista(request, user_id):
#     User = get_user_model()
#     share_user = get_object_or_404(User, pk=user_id)

#     today = date.today()
#     ingredientes = set()

#     for menu in ElegidosXDia.objects.filter(user=share_user, el_dia_en_que_comemos__gte=today):
#         platos = menu.platos_que_comemos or {}
#         for _, lista_platos in platos.items():
#             for p in lista_platos:
#                 if p.get("elegido") and p.get("ingredientes"):
#                     ingredientes.update(map(str.strip, p["ingredientes"].split(",")))
#                 for v in (p.get("variedades") or {}).values():
#                     if v.get("elegido") and v.get("ingredientes"):
#                         ingredientes.update(map(str.strip, v["ingredientes"].split(",")))

#     perfil = get_object_or_404(Profile, user=share_user)
#     comentarios = {}
#     for item in (perfil.comentarios or []):
#         try:
#             ingr, coment = item.split("%", 1)
#             comentarios[ingr] = coment
#         except ValueError:
#             pass

#     tengo = set(perfil.ingredientes_que_tengo or [])
#     items = []
#     for ing in sorted(ingredientes):
#         if ing not in tengo:
#             items.append({"nombre": ing, "comentario": comentarios.get(ing, "")})

#     token = f"user-{share_user.pk}"  # solo para localStorage

#     return render(request, "AdminVideos/compartir_lista.html", {"items": items, "token": token})


@csrf_exempt
@require_POST
def api_toggle_item(request, token):
    _, perfil = _get_user_by_token_or_404(token)
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

    nombre = (payload.get("nombre") or "").strip()
    checked = bool(payload.get("checked"))

    if not nombre:
        return JsonResponse({"ok": False, "error": "nombre requerido"}, status=400)

    # Normalizamos la lista
    lista = list(perfil.ingredientes_que_tengo or [])

    if checked and nombre not in lista:
        lista.append(nombre)
    if not checked and nombre in lista:
        lista.remove(nombre)

    perfil.ingredientes_que_tengo = lista
    perfil.save(update_fields=["ingredientes_que_tengo"])

    return JsonResponse({"ok": True, "nombre": nombre, "checked": checked})








class PlatoDetail(DetailView):
    model = Plato
    template_name = 'AdminVideos/plato_detail.html'
    context_object_name = "plato"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Perfil y amigues (como ya tenés)
        perfil = get_object_or_404(Profile, user=self.request.user)
        context["amigues"] = perfil.amigues

        # Obtener el plato actual
        plato = self.get_object()

        # Convertir el campo 'tipos' (string separado por comas) a lista
        if plato.tipos:
            context['tipos_lista'] = [t.strip() for t in plato.tipos.split(',')]
        else:
            context['tipos_lista'] = []

        return context


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



@login_required
def eliminar_lugar(request, lugar_id):
    lugar = get_object_or_404(Lugar, id=lugar_id)

    # Verificar si el usuario es el propietario del lugar
    if lugar.propietario != request.user:
        raise Http404("No tenés permiso para eliminar este lugar.")

    # Obtener el perfil del usuario actual
    perfil = get_object_or_404(Profile, user=request.user)

    # Eliminar el lugar si aparece en listas personalizadas (si aplica)
    if lugar.id in perfil.sugeridos_descartados:
        perfil.sugeridos_descartados.remove(lugar.id)
        perfil.save()

    if lugar.id in perfil.sugeridos_importados:
        perfil.sugeridos_importados.remove(lugar.id)
        perfil.save()

    # Eliminar el lugar de la base de datos
    lugar.delete()

    # Redirigir a la página que quieras (modificá este nombre si tenés otra vista)
    return redirect('filtro-de-platos')

# @login_required
# def eliminar_plato(request, plato_id):
#     # Verificar que el usuario es el propietario del plato
#     plato = get_object_or_404(Plato, id=plato_id)

#     # Comprobar si el usuario actual es el propietario del plato
#     if plato.propietario != request.user:
#         raise Http404("No tienes permiso para eliminar este plato.")

#     # Actualizar la lista sugeridos_descartados del perfil del usuario
#     # profile = request.user.profile

#     # Obtener el perfil del usuario actual
#     perfil = get_object_or_404(Profile, user=request.user)

#     # Eliminar el plato de la lista de sugeridos_descartados si está allí
#     if plato.id_original in perfil.sugeridos_descartados:
#         perfil.sugeridos_descartados.remove(plato.id_original)
#         perfil.save()

#   # Eliminar el plato de la lista de sugeridos_importados si está allí
#     if plato.id_original in perfil.sugeridos_importados:
#         perfil.sugeridos_importados.remove(plato.id_original)
#         perfil.save()

#     # Eliminar el plato de la base de datos
#     plato.delete()

#     # # Eliminar el plato de la base de datos
#     # plato.delete()

#     return redirect('filtro-de-platos')  # Redirigir a la página de filtro de platos

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
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string("AdminVideos/plato_form_inner.html", context, request=request)
            return JsonResponse({'html': html})
        
        return self.render_to_response(context)

    # 👉 TIPOS: ofrecer TODOS y marcar los que tenga el plato
    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # Mostrar todas las opciones
        form.fields['tipos'].choices = Plato.TIPOS_CHOICES

        # Sugerir tipopag si no hay initial
        if not form.initial.get('tipos'):
            tipopag = self.request.GET.get('tipopag')
            valid_keys = {k for k, _ in Plato.TIPOS_CHOICES}
            if tipopag in valid_keys:
                form.fields['tipos'].initial = [tipopag]

        # Imagen no requerida
        if 'image' in form.fields:
            form.fields['image'].required = False

        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.method == "POST":
            context["ingrediente_formset"] = IngredienteEnPlatoFormSet(
                self.request.POST, instance=self.object
            )
        else:
            context["ingrediente_formset"] = IngredienteEnPlatoFormSet(
                instance=self.object
            )

        # 👉 TIPOS: enviar TODOS al template
        context['items'] = [k for (k, _) in Plato.TIPOS_CHOICES]
        context['tipopag'] = self.request.GET.get('tipopag', 'Dash')

        # 👉 Variedades: exponer maps como espera el template
        data = self.object.variedades or {}
        context['variedades_en_base'] = {
            f"variedad{i}": (data.get(f"variedad{i}", {}) or {}).get("nombre", "")
            for i in range(1, 7)
        }
        context['ingredientes_variedad'] = {
            f"variedad{i}": (data.get(f"variedad{i}", {}) or {}).get("ingredientes", "")
            for i in range(1, 7)
        }

        return context

    def form_valid(self, form):

        context = self.get_context_data()
        ingrediente_formset = context["ingrediente_formset"]

        if not ingrediente_formset.is_valid():
            return self.render_to_response(self.get_context_data(form=form))

        # 🔒 Imagen: normalizar
        uploaded = self.request.FILES.get('image')
        # Eso te borra la imagen en cada edición si no subís otra.

        # if not uploaded:
        #     form.instance.image = None  # si no se manda nueva, mantener actual; si querés mantenerla, comenta esta línea
        # else:
        #     if not getattr(uploaded, 'name', None):
        #         uploaded.name = 'upload.jpg'

        # Cambialo por:
       
        if uploaded:
            if not getattr(uploaded, 'name', None):
                uploaded.name = 'upload.jpg'
        # si no viene uploaded, no toques image (queda la actual)

        with transaction.atomic():
            plato = form.save(commit=False)
            plato.propietario = self.request.user

            # reconstruir string "ingredientes"
            lista_ingredientes = []
            for ing_form in ingrediente_formset:
                if ing_form.cleaned_data and not ing_form.cleaned_data.get("DELETE", False):
                    nombre = ing_form.cleaned_data.get("nombre_ingrediente")
                    # cantidad = ing_form.cleaned_data.get("cantidad")
                    # unidad = ing_form.cleaned_data.get("unidad")

                    texto = (nombre or '').strip()
                    # if cantidad not in [None, '']:
                    #     texto += f" {cantidad}".rstrip()
                    # if unidad:
                    #     texto += f" {unidad}".rstrip()
                    if texto:
                        lista_ingredientes.append(texto)

            plato.ingredientes = ", ".join(lista_ingredientes)

            # variedades
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
            

        template_param = self.request.GET.get("tipopag")
        tail = f"?tipopag={template_param}&modificado=ok" if template_param else "?modificado=ok"


        # 🔁 Si el plato editado está en algún menú del día (ElegidosXDia), actualizamos su info
        registros = ElegidosXDia.objects.filter(
            Q(platos_que_comemos__icontains=f'"id_plato": "{plato.id}"')
        )

        for registro in registros:
            actualizado = False
            data = registro.platos_que_comemos or {}

            if not isinstance(data, dict):
                continue  # Seguridad ante datos corruptos

            for comida, platos in data.items():
                for i, p in enumerate(platos):
                    if str(p.get("id_plato")) == str(plato.id):
                        # Actualizar datos del plato
                        p["plato"] = plato.nombre_plato
                        p["tipo"] = plato.tipos
                        p["ingredientes"] = plato.ingredientes
                        p["variedades"] = {
                            vid: {
                                "nombre": info.get("nombre", ""),
                                "ingredientes": info.get("ingredientes", ""),
                                "elegido": True
                            }
                            for vid, info in (plato.variedades or {}).items()
                        }
                        actualizado = True

            if actualizado:
                registro.platos_que_comemos = data
                registro.save()

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
        if self.padre.tipos:
            initial["tipos"] = [t.strip() for t in self.padre.tipos.split(",") if t.strip()]
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # útil para mostrar "creando variedad de X"
        context["plato_padre_obj"] = self.padre

        # ✅ CLAVE: tu template usa `items` para pintar los checkboxes
        context["items"] = [k for (k, _) in Plato.TIPOS_CHOICES]

        # ✅ `tipopag` lo usa tu template para marcar alguno por defecto
        # tomamos el primero del padre o fallback
        raw = (self.padre.tipos or "").split(",")[0].strip()
        context["tipopag"] = raw or self.request.GET.get("tipopag") or "Principal"

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
            variedades = {}
            for i in range(1, 7):
                variedad = form.cleaned_data.get(f"variedad{i}")
                ingredientes_variedad_str = form.cleaned_data.get(f"ingredientes_de_variedad{i}")
                if variedad:
                    variedades[f"variedad{i}"] = {
                        "nombre": variedad,
                        "ingredientes": ingredientes_variedad_str,
                        "elegido": True,
                    }
            plato.variedades = variedades

            plato.save()
            form.save_m2m()

            ingrediente_formset.instance = plato
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
        return Plato.objects.none()  # Retorna un queryset vacío
    else:
        # Construir la consulta con Q
        query = Q()

        if quecomemos == "quecomemos":
            usuario_quecomemos = User.objects.filter(username="quecomemos").first()
            if usuario_quecomemos:
                query |= Q(propietario=usuario_quecomemos)

            # Excluir platos descartados
            platos_descartados = usuario.profile.sugeridos_descartados
            if platos_descartados:
                # query &= ~Q(nombre_plato__in=platos_descartados)
                query &= ~Q(id__in=platos_descartados)  # Usamos el id del plato para excluirlo


        if misplatos == "misplatos":
            query |= Q(propietario=usuario)

        # if tipo_parametro and tipo_parametro != "Dash":
        #     query &= Q(tipo=tipo_parametro)

        # if tipo_parametro and tipo_parametro != "Dash":
        #     query &= Q(tipos__nombre=tipo_parametro)

        if tipo_parametro and tipo_parametro != "Dash":
            query &= Q(tipos__icontains=tipo_parametro)  # ✅

        if medios and medios != '-':
            query &= Q(medios=medios)

        if categoria and categoria != '-':
            query &= Q(categoria=categoria)

        if dificultad and dificultad != '-':
            query &= Q(dificultad=dificultad)

        if palabra_clave:
            query &= Q(ingredientes__icontains=palabra_clave) | Q(nombre_plato__icontains=palabra_clave)

        # Aplicar la consulta
        return Plato.objects.filter(query)



@login_required(login_url=reverse_lazy('login'), redirect_field_name=None)
def FiltroDePlatos(request):

    # Obtener la fecha actual
    fecha_actual = datetime.datetime.now().date()

    DIAS_ES = ['LU','MA','MI','JU','VI','SA','DO']  # tu mapeo

    registros_antiguos = ElegidosXDia.objects.filter(
        el_dia_en_que_comemos__lt=fecha_actual, user=request.user
    )

    with transaction.atomic():
        for registro in registros_antiguos:
            fecha = registro.el_dia_en_que_comemos
            datos = registro.platos_que_comemos or {}

            historico, _ = HistoricoDia.objects.get_or_create(
                fecha=fecha,
                propietario=request.user,
                defaults={'dia_semana': DIAS_ES[fecha.weekday()]}
            )
            if not historico.dia_semana:
                historico.dia_semana = DIAS_ES[fecha.weekday()]
                historico.save(update_fields=['dia_semana'])

            for momento in ["desayuno", "almuerzo", "merienda", "cena"]:
                for plato_data in datos.get(momento, []):
                    pid = plato_data.get("id_plato")
                    if not pid:
                        continue

                    # Intentamos resolver el Plato SOLO para capturar snapshot de nombre (si aún existe)
                    plato_obj = Plato.objects.filter(id=pid, propietario=request.user).only('id','nombre_plato').first()
                    nombre_snap = plato_obj.nombre_plato if plato_obj else (plato_data.get("nombre_plato") or "Plato eliminado")

                    HistoricoItem.objects.get_or_create(
                        historico=historico,
                        plato_id_ref=pid,
                        momento=momento
                        # defaults={'plato_nombre_snapshot': nombre_snap}
                    )

            registro.delete()







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
    fechas_existentes = ElegidosXDia.objects.filter(user=usuario,el_dia_en_que_comemos__gte=fecha_actual).values_list('el_dia_en_que_comemos', flat=True).distinct()

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

    # Obtener los registros completos para cada fecha y extraer los platos
    registros = ElegidosXDia.objects.filter(
        user=request.user,
        el_dia_en_que_comemos__in=fechas_existentes
    ).values('el_dia_en_que_comemos', 'platos_que_comemos')

    for registro in registros:
        fec = registro['el_dia_en_que_comemos']  # Fecha del registro
        dias_programados.add(fec)  # <--- Aquí sumás la fecha
        pla = registro['platos_que_comemos'] or {}  # Asegurar que es un diccionario
        # id_plato = registro['id_plato']

        for comida, lista_platos in pla.items():  # Iterar comidas (desayuno, almuerzo, etc.)
            for plato in lista_platos:  # Iterar cada plato dentro de la lista
                plato_nombre = plato.get('plato', 'Desconocido')
                id_plato = plato.get('id_plato')  # <-- ¡Lo obtenés de aquí!

                # Añadir a la lista de la comida correspondiente
                if comida in platos_dia_x_dia[fec]:
                    # platos_dia_x_dia[fec][comida].append(plato_nombre)
                    platos_dia_x_dia[fec][comida].append({
                            'id': id_plato,
                            'nombre': plato_nombre
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
        tipo = request.POST.get('tipo_elemento')
        objeto_id = request.POST.get('plato_id')  # Puede ser plato o lugar, el nombre del campo puede generalizarse si quieres
        dia = request.POST.get('dia')
        comida = request.POST.get('comida')

        fecha_comida = datetime.datetime.strptime(dia, "%Y-%m-%d").date()
        request.session['dia_activo'] = dia

        menu_dia, _ = ElegidosXDia.objects.get_or_create(
            user=request.user,
            el_dia_en_que_comemos=fecha_comida,
            defaults={"platos_que_comemos": {}}  # Si usas otro campo para lugares
        )

        if tipo == "plato":
            try:
                plato = Plato.objects.get(id=objeto_id)
            except Plato.DoesNotExist:
                messages.error(request, "El plato no existe.")
                return redirect('filtro-de-platos')

            data = menu_dia.platos_que_comemos
            if not isinstance(data.get(comida), list):
                data[comida] = []

            if any(p["id_plato"] == objeto_id for p in data[comida]):
                messages.warning(request, f"El plato {plato.nombre_plato} ya está asignado a {comida}.")
            else:
                data[comida].append({
                    "id_plato": objeto_id,
                    "plato": plato.nombre_plato,
                    "tipo": plato.tipos,
                    "ingredientes": plato.ingredientes,
                    "variedades": {
                        vid: {
                            "nombre": info["nombre"],
                            "ingredientes": info["ingredientes"],
                            "elegido": True
                        } for vid, info in plato.variedades.items()
                    },
                    "elegido": True
                })
                messages.success(request, f"Plato {plato.nombre_plato} asignado correctamente a {comida}.")

            menu_dia.platos_que_comemos = data

       
        elif tipo == "lugar":
                    try:
                        lugar = Lugar.objects.get(id=objeto_id)
                    except Lugar.DoesNotExist:
                        messages.error(request, "El lugar no existe.")
                        return redirect('filtro-de-platos')

                    data = menu_dia.platos_que_comemos
                    if not isinstance(data.get(comida), list):
                       data[comida] = []

                    if any(p["id_plato"] == objeto_id for p in data[comida]):
                        messages.warning(request, f"El lugar {lugar.nombre_lugar} ya está asignado a {comida}.")
                    else:
                        data[comida].append({
                            "id_plato": objeto_id,
                            "plato": lugar.nombre,  # Para mantener la clave "plato"
                            "tipo": "lugar",
                            "direccion": lugar.direccion,
                            "telefono": lugar.telefono,
                            # "elegido": True,
                            # "tipo_elemento": "lugar"
                        })

                        messages.success(request, f"Lugar {lugar.nombre} asignado correctamente a {comida}.")

        menu_dia.platos_que_comemos = data
        menu_dia.save()

        return redirect('filtro-de-platos')





def eliminar_plato_programado(request, nombre_plato, comida, fecha):
    usuario = request.user

    # Obtener el menú del usuario para la fecha especificada
    menu = get_object_or_404(ElegidosXDia, user=usuario, el_dia_en_que_comemos=fecha)

    # Obtener los platos del menú
    platos = menu.platos_que_comemos or {}

    if comida in platos:
        # Filtrar los platos que no coincidan con el nombre a eliminar
        platos[comida] = [plato for plato in platos[comida] if plato["plato"] != nombre_plato]

        # Si la categoría de comida queda vacía, eliminarla del diccionario
        if not platos[comida]:
            del platos[comida]

        # Si todas las categorías están vacías, eliminar el registro de la base de datos
        if not any(platos.values()):
            menu.delete()
        else:
            # Guardar los cambios en la base de datos
            menu.platos_que_comemos = platos
            menu.save()

    # LO NUEVO DE ComidaDelDia

    # comida_asignada = ComidaDelDia.objects.filter(
    #     user=usuario,
    #     fecha=fecha,
    #     momento=comida,
    #     plato=plato_id
    # ).first()

    # if comida_asignada:
    #     comida_asignada.delete()
    #     messages.success(request, f"El plato '{nombre_plato}' fue eliminado de {comida}.")
    # else:
    #     messages.warning(request, f"No se encontró el plato '{nombre_plato}' en {comida} para esa fecha.")

    return redirect('filtro-de-platos')






# def normalizar_dia(dia):
#     # Quitar tildes y pasar a mayúsculas
#     return ''.join(
#         c for c in unicodedata.normalize('NFD', dia.upper())
#         if unicodedata.category(c) != 'Mn'
#     )

# MOMENTOS = ["desayuno", "almuerzo", "merienda", "cena"]

# def generar_elegido_desde_historico(historico, fecha_activa):
#     """Crea un ElegidosXDia para la fecha activa a partir de un HistoricoDia con HistoricoItem."""

#     # 1) limpiar el ElegidosXDia existente (misma lógica que tenías)
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

#     # 3) agrupar ids por momento desde HistoricoItem
#     ids_por_momento = {m: [] for m in MOMENTOS}
#     for it in historico.items.all():
#         if it.momento in ids_por_momento:
#             ids_por_momento[it.momento].append(it.plato_id_ref)

#     # 4) búsqueda y serialización (manteniendo tu formato)
#     #    armamos un mapa id->Plato para mantener el orden de ids
#     for momento in MOMENTOS:
#         ids = ids_por_momento[momento]
#         if not ids:
#             continue

#         platos_qs = Plato.objects.filter(id__in=ids)
#         mapa = {p.id: p for p in platos_qs}

#         # Recorremos en el mismo orden que en el histórico
#         for pid in ids:
#             p = mapa.get(pid)
#             if not p:
#                 continue  # plato borrado -> se omite

#             # evitar duplicados en la lista del momento
#             if any(item.get("id_plato") == str(p.id) for item in data[momento]):
#                 continue

#             plato_json = {
#                 "id_plato": str(p.id),
#                 "plato": p.nombre_plato,
#                 "tipo": p.tipos,                # tu CharField CSV
#                 "ingredientes": p.ingredientes, # string ya preparado
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



# def _validar_y_purgar(historico: HistoricoDia) -> bool:
#     """True si TODOS los platos existen. Si falta alguno, borra items + histórico y devuelve False."""
#     ids = list(historico.items.values_list("plato_id_ref", flat=True))
#     if not ids:
#         with transaction.atomic():
#             historico.items.all().delete()
#             historico.delete()
#         return False

#     existentes = set(Plato.objects.filter(id__in=ids).values_list("id", flat=True))
#     if len(existentes) != len(ids):
#         with transaction.atomic():
#             historico.items.all().delete()
#             historico.delete()
#         return False
#     return True

# @login_required
# def random_dia(request, dia_nombre):
#     usuario = request.user
#     if not dia_nombre:
#         return JsonResponse({"error": "Día inválido"}, status=400)

#     # dia_nombre = normalizar_dia(dia_nombre)[:2]  # "LU", "MA", ...
#     dia_nombre = normalizar_dia(dia_nombre).upper()[:2]
#     if dia_nombre not in ['LU', 'MA', 'MI', 'JU', 'VI', 'SA', 'DO']:
#         return JsonResponse({"error": "Día inválido"}, status=400)


#     # solo no sugeridos
#     qs = HistoricoDia.objects.filter(propietario=usuario, dia_semana=dia_nombre, ya_sugerido=False)

#     # si no hay, reiniciar flags
#     if not qs.exists():
#         HistoricoDia.objects.filter(propietario=usuario, dia_semana=dia_nombre).update(ya_sugerido=False)
#         qs = HistoricoDia.objects.filter(propietario=usuario, dia_semana=dia_nombre, ya_sugerido=False)
#         if not qs.exists():
#             return JsonResponse({"error": "No hay registros para ese día"}, status=404)
#         messages.info(request, "Se reinició la lista de registros sugeridos")

#     # intentar hasta encontrar uno válido o agotar
#     MAX_INTENTOS = 100
#     intentos = 0
#     registro_valido = None

#     while qs.exists() and intentos < MAX_INTENTOS:
#         intentos += 1
#         # registro = qs.all()[random.randint(0, qs.count() - 1)]

#         ids = list(qs.values_list("id", flat=True))
#         if not ids:
#             return JsonResponse({"error": "No hay registros para ese día"}, status=404)

#         # registro_id = random.choice(ids)
#         # registro = HistoricoDia.objects.get(id=registro_id)
#         qs_map = {h.id: h for h in qs.select_related().all()}
#         ids = list(qs_map.keys())

#         registro_id = random.choice(ids)
#         registro = qs_map[registro_id]

#         if _validar_y_purgar(registro):
#             registro_valido = registro
#             break
#         # si se purgó dentro de _validar_y_purgar, refrescamos el queryset
#         qs = HistoricoDia.objects.filter(propietario=usuario, dia_semana=dia_nombre, ya_sugerido=False)

#     if not registro_valido:
#         return JsonResponse({"error": "No hay registros válidos para ese día"}, status=404)

#     # marcar como sugerido
#     registro_valido.ya_sugerido = True
#     registro_valido.save()

#     # crear ElegidosXDia con tu función existente
#     dia_activo = request.session.get('dia_activo', None)
#     generar_elegido_desde_historico(registro_valido, dia_activo)

#     messages.success(request, f"Se generó un menú para el día {dia_activo}")
#     return redirect("filtro-de-platos")


MOMENTOS = ["desayuno", "almuerzo", "merienda", "cena"]

def normalizar_dia(dia):
    # Quitar tildes y pasar a mayúsculas
    return ''.join(
        c for c in unicodedata.normalize('NFD', dia.upper())
        if unicodedata.category(c) != 'Mn'
    )


def generar_elegido_desde_historico(historico, fecha_activa):
    """Crea un ElegidosXDia para la fecha activa a partir de un HistoricoDia con HistoricoItem."""

    # 1) limpiar el ElegidosXDia existente
    ElegidosXDia.objects.filter(
        user=historico.propietario,
        el_dia_en_que_comemos=fecha_activa
    ).delete()

    # 2) crear nuevo contenedor vacío
    menu_dia = ElegidosXDia.objects.create(
        user=historico.propietario,
        el_dia_en_que_comemos=fecha_activa,
        platos_que_comemos={}
    )
    data = {m: [] for m in MOMENTOS}

    # 3) agrupar ids por momento
    ids_por_momento = {m: [] for m in MOMENTOS}
    for it in historico.items.all():
        if it.momento in ids_por_momento:
            ids_por_momento[it.momento].append(it.plato_id_ref)

    # 4) búsqueda y serialización
    for momento in MOMENTOS:
        ids = ids_por_momento[momento]
        if not ids:
            continue

        platos_qs = Plato.objects.filter(id__in=ids)
        mapa = {p.id: p for p in platos_qs}

        for pid in ids:
            p = mapa.get(pid)
            if not p:
                continue  # plato eliminado

            # evitar duplicados
            if any(item.get("id_plato") == str(p.id) for item in data[momento]):
                continue

            plato_json = {
                "id_plato": str(p.id),
                "plato": p.nombre_plato,
                "tipo": p.tipos,
                "ingredientes": p.ingredientes,
                "variedades": {
                    vid: {
                        "nombre": info.get("nombre"),
                        "ingredientes": info.get("ingredientes"),
                        "elegido": True,
                    } for vid, info in (p.variedades or {}).items()
                },
                "elegido": True,
            }
            data[momento].append(plato_json)

    # 5) guardar y devolver
    menu_dia.platos_que_comemos = data
    menu_dia.save()
    return menu_dia


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

    # 1. Obtener históricos no sugeridos
    qs = HistoricoDia.objects.filter(
        propietario=usuario,
        dia_semana=dia_nombre,
        ya_sugerido=False
    )

    # 2. Si no hay, reiniciar flags y volver a intentar
    if not qs.exists():
        HistoricoDia.objects.filter(propietario=usuario, dia_semana=dia_nombre).update(ya_sugerido=False)
        qs = HistoricoDia.objects.filter(propietario=usuario, dia_semana=dia_nombre, ya_sugerido=False)
        if not qs.exists():
            return JsonResponse({"error": "No hay registros para ese día"}, status=404)
        messages.info(request, "Se reinició la lista de registros sugeridos")

    # 3. Crear mapa {id: objeto} para evitar múltiples consultas
    qs_map = {h.id: h for h in qs.select_related()}
    ids = list(qs_map.keys())
    if not ids:
        return JsonResponse({"error": "No hay registros para ese día"}, status=404)

    MAX_INTENTOS = 100
    intentos = 0
    registro_valido = None

    while ids and intentos < MAX_INTENTOS:
        intentos += 1
        registro_id = random.choice(ids)
        registro = qs_map[registro_id]

        if _validar_y_purgar(registro):
            registro_valido = registro
            break

        # si fue eliminado, refrescar el queryset y mapa
        qs = HistoricoDia.objects.filter(propietario=usuario, dia_semana=dia_nombre, ya_sugerido=False)
        qs_map = {h.id: h for h in qs.select_related()}
        ids = list(qs_map.keys())

    if not registro_valido:
        return JsonResponse({"error": "No hay registros válidos para ese día"}, status=404)

    # 4. Marcar como sugerido
    registro_valido.ya_sugerido = True
    registro_valido.save()

    # 5. Validar sesión
    dia_activo = request.session.get('dia_activo')
    if not dia_activo:
        messages.error(request, "No hay un día activo definido.")
        return redirect("filtro-de-platos")

    # 6. Generar menú
    generar_elegido_desde_historico(registro_valido, dia_activo)
    messages.success(request, f"Se generó un menú para el día {dia_activo}")
    return redirect("filtro-de-platos")


def eliminar_menu_programado(request):
    # Recuperar la fecha activa desde la sesión
    dia_activo = request.session.get("dia_activo", None)

    if not dia_activo:
        messages.error(request, "No hay un día activo en la sesión.")
        return redirect("filtro-de-platos")

    # Buscar y eliminar el registro
    elegido = ElegidosXDia.objects.filter(
        user=request.user,
        el_dia_en_que_comemos=dia_activo
    ).first()

    if elegido:
        elegido.delete()
        messages.success(request, f"Se eliminó el menú del {dia_activo}")
    else:
        messages.warning(request, f"No había un menú guardado para {dia_activo}")

    return redirect("filtro-de-platos")