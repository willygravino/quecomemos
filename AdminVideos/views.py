from itertools import groupby
import locale
from django.contrib import messages  # Para mostrar mensajes al usuario
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from AdminVideos.models import Plato, Profile, Mensaje, Preseleccionados, ElegidosXDia, Sugeridos
from django.http import Http404, HttpResponseForbidden, JsonResponse
from django.urls import reverse, reverse_lazy
from django.contrib.auth.forms import UserCreationForm
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from datetime import datetime, timedelta
from .forms import PlatoFilterForm, PlatoForm
from django.views.generic import TemplateView
from datetime import date, datetime
from django.contrib.auth.models import User  # Asegúrate de importar el modelo User
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, reverse
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
import datetime
from django.utils import timezone



def obtener_parametros_sesion(request):

    # Recupera los parámetros de sesión y los valores de los parámetros URL.

    # Recuperar parámetros de sesión
    medios = request.session.get('medios_estable', None)
    categoria = request.session.get('categoria_estable', None)
    dificultad = request.session.get('dificultad_estable', None)
    palabra_clave = request.session.get('palabra_clave', "")

    quecomemos = request.session.get('quecomemos', None)
    misplatos = request.session.get('misplatos', "misplatos")
    preseleccionados = request.session.get('preseleccionados', None)

    # Obtener el valor del parámetro 'tipo' desde la URL
    tipo_parametro = request.GET.get('tipopag', 'Dash')

    # # Obtener el usuario actual
    # usuario = request.user

    # Devolver las variables por separado
    return tipo_parametro, quecomemos, misplatos, preseleccionados, medios, categoria, dificultad, palabra_clave

class SugerenciasRandom(TemplateView):
    template_name = 'AdminVideos/random.html'

def index(request):
    #  return render(request, "AdminVideos/lista_filtrada.html")
    return redirect(reverse_lazy("filtro-de-platos"))

def about(request):
    return render(request, "AdminVideos/about.html")



def descartar_sugerido(request, nombre_plato):
    # Obtener el perfil del usuario logueado
    profile = request.user.profile

    # Verificar si el plato_id ya está en la lista para evitar duplicados
    if nombre_plato not in profile.sugeridos_descartados:
        profile.sugeridos_descartados.append(nombre_plato)  # Agregar el ID del plato a la lista
        profile.save()  # Guardar los cambios en el perfil

    return redirect('filtro-de-platos')

def plato_preseleccionado(request):
    if request.method == 'GET':
        # Obtener parámetros de la solicitud
        nombre_plato = request.GET.get('opcion1')
        plato_tipo = request.GET.get('tipoplato')
        accion = request.GET.get('accion')
        # tipo_pag = request.GET.get('tipopag')

        # # Validar parámetros necesarios
        # if not nombre_plato or not plato_tipo:
        #     return JsonResponse({"error": "Faltan parámetros necesarios"}, status=400)

        # Obtener el usuario logueado
        usuario = request.user

        # Realizar acción según el valor de 'accion'
        if accion == "borrar":
            # Eliminar el plato de la lista de platos preseleccionados
            Preseleccionados.objects.filter(usuario=usuario, nombre_plato_elegido=nombre_plato).delete()
            resultado = "borrar"
        else:
            # Agregar el plato a la lista de platos preseleccionados
            Preseleccionados.objects.get_or_create(usuario=usuario, nombre_plato_elegido=nombre_plato, tipo_plato=plato_tipo)
            resultado = "preseleccionar"

        # Actualizar la lista de preseleccionados
        preseleccionados = list(
            Preseleccionados.objects.filter(usuario=usuario).values_list('nombre_plato_elegido', flat=True)
        )

        # vista_preseleccionados = request.session.get('preseleccionados', None)
        # if vista_preseleccionados == "preseleccionados":
        #     return JsonResponse({
        #         "success": True,
        #         "accion": resultado,
        #         "preseleccionados": preseleccionados,
        #         "plato_eliminado" : nombre_plato
        #     })

        # # Verificar si es una solicitud AJAX
        # if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        #     # Responder con JSON si es una solicitud AJAX
        # else:
        return JsonResponse({
                "success": True,
                "accion": resultado,
                "preseleccionados": preseleccionados
            })
        # else:
        #     # Redirigir si no es una solicitud AJAX
        #     return redirect(f"{reverse('filtro-de-platos')}?tipopag={"verga"}")
    else:
        # Responder con error si el método no es GET
        return JsonResponse({"error": "Método no permitido"}, status=405)



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

def grabar_menu_elegido(request):
    if request.method == 'POST':

        platos_del_dia = {}
        # Obtener el usuario logueado
        usuario = request.user

        # AQUÍ, PONER LAS INSTRUCCIONES ADECUADAS PARA BORRAR LOS REGISTROS DE DÍAS MÁS ALLÁ DE 45 DÍAS ATRÁS; DE ESTE MODO SE PODRÁ CALCULAR LO QUE SE COMIÓ EN LOS ÚLTIMOS 45 DÍAS "HACE 45 DÍAS QUE NO COMÉS PESCADO"

        # Obtener las fechas y platos elegidos del formulario
        fecha = limpiar_none(request.POST.get("fecha"))


        almuerzo = limpiar_none(request.POST.get("almuerzo"))
        cena = limpiar_none(request.POST.get("cena"))
        entrada1 = limpiar_none(request.POST.get("entrada1"))
        entrada2 = limpiar_none(request.POST.get("entrada2"))
        entrada3 = limpiar_none(request.POST.get("entrada3"))
        entrada4 = limpiar_none(request.POST.get("entrada4"))
        guarnicion1 = limpiar_none(request.POST.get("guarnicion1"))
        guarnicion2 = limpiar_none(request.POST.get("guarnicion2"))
        guarnicion3 = limpiar_none(request.POST.get("guarnicion3"))
        guarnicion4 = limpiar_none(request.POST.get("guarnicion4"))
        postre1 = limpiar_none(request.POST.get("postre1"))
        postre2 = limpiar_none(request.POST.get("postre2"))
        salsa1 = limpiar_none(request.POST.get("salsa1"))
        salsa2 = limpiar_none(request.POST.get("salsa2"))
        salsa3 = limpiar_none(request.POST.get("salsa3"))
        salsa4 = limpiar_none(request.POST.get("salsa4"))
        dip1 = limpiar_none(request.POST.get("dip1"))
        dip2 = limpiar_none(request.POST.get("dip2"))
        dip3 = limpiar_none(request.POST.get("dip3"))
        dip4 = limpiar_none(request.POST.get("dip4"))
        trago1 = limpiar_none(request.POST.get("trago1"))
        trago2 = limpiar_none(request.POST.get("trago2"))

        registro_existente = ElegidosXDia.objects.filter(user=usuario, el_dia_en_que_comemos=fecha).first()

        if registro_existente and all(item is None for item in [almuerzo, cena, entrada1, entrada2, entrada3, entrada4, guarnicion1, guarnicion2, guarnicion3, guarnicion4, postre1, postre2, salsa1, salsa2, salsa3, salsa4, dip1, dip2, dip3, dip4, trago1, trago2]):
                registro_existente.delete()

        # if registro_existente and almuerzo is None and cena is None:
        #     registro_existente.delete()

        # if almuerzo is not None and cena is not None:

        # Condición para verificar que alguno de los datos no sea None
        if any(item is not None for item in [
            almuerzo, cena, entrada1, entrada2, entrada3, entrada4,
            guarnicion1, guarnicion2, guarnicion3, guarnicion4,
            postre1, postre2, salsa1, salsa2, salsa3, salsa4,
            dip1, dip2, dip3, dip4, trago1, trago2]):

            # Obtener datos de almuerzo y cena
            almuerzo_result = Plato.objects.filter(nombre_plato=almuerzo).values("ingredientes", "variedades").first()
            almuerzo_variedades = almuerzo_result['variedades'] if almuerzo_result else None
            almuerzo_ingredientes = almuerzo_result['ingredientes'] if almuerzo_result else None

            variedad_almuerzo_con_elegidos = {}
            if almuerzo_variedades:
                for variedad, detalles_variedad in almuerzo_variedades.items():
                    if registro_existente and almuerzo == registro_existente.platos_que_comemos["almuerzo"]["plato"]:
                            elegido = registro_existente.platos_que_comemos["variedades_almuerzo"][variedad]["elegido"]
                    else: elegido = True
                    variedad_almuerzo_con_elegidos[variedad] = {
                        "variedad": detalles_variedad.get("variedad", ""),
                        "ingredientes_de_variedades": detalles_variedad.get("ingredientes_de_variedades", []),
                        "elegido": elegido
                    }

            cena_result  = Plato.objects.filter(nombre_plato=cena).values("ingredientes", "variedades").first()
            cena_variedades = cena_result['variedades'] if cena_result else None
            cena_ingredientes = cena_result['ingredientes'] if cena_result else None

            variedad_cena_con_elegidos = {}
            if cena_variedades:
                for variedad, detalles_variedad in cena_variedades.items():
                    if registro_existente and cena == registro_existente.platos_que_comemos["cena"]["plato"]:
                            elegido = registro_existente.platos_que_comemos["variedades_cena"][variedad]["elegido"]
                    else: elegido = True
                    variedad_cena_con_elegidos[variedad] = {
                        "variedad": detalles_variedad.get("variedad", ""),
                        "ingredientes_de_variedades": detalles_variedad.get("ingredientes_de_variedades", []),
                        "elegido": elegido
                    }

            guar1_ingredientes =  Plato.objects.filter(nombre_plato=guarnicion1).values("ingredientes").first()
            guar1_ingredientes = guar1_ingredientes['ingredientes'] if guar1_ingredientes else None

            # Agregar guarnicion1
            agregar_plato(platos_del_dia, "guarnicion1", guarnicion1, guar1_ingredientes)


            # # Si guar1_ingredientes no es None, lo agregamos al diccionario
            # if guarnicion1 is not None:
            #     platos_del_dia["guarnicion1"] = {
            #         "plato": guarnicion1,
            #         "ingredientes": guar1_ingredientes,
            #         "elegido": True
            #     }

            guar2_ingredientes =  Plato.objects.filter(nombre_plato=guarnicion2).values("ingredientes").first()
            guar2_ingredientes = guar2_ingredientes['ingredientes'] if guar2_ingredientes else None

             # Agregar
            agregar_plato(platos_del_dia, "guarnicion2", guarnicion2, guar2_ingredientes)

            guar3_ingredientes =  Plato.objects.filter(nombre_plato=guarnicion3).values("ingredientes").first()
            guar3_ingredientes = guar3_ingredientes['ingredientes'] if guar3_ingredientes else None

            # Agregar
            agregar_plato(platos_del_dia, "guarnicion3", guarnicion3, guar3_ingredientes)

            guar4_ingredientes =  Plato.objects.filter(nombre_plato=guarnicion4).values("ingredientes").first()
            guar4_ingredientes = guar4_ingredientes['ingredientes'] if guar4_ingredientes else None

            # Agregar
            agregar_plato(platos_del_dia, "guarnicion4", guarnicion4, guar4_ingredientes)

            ent1_ingredientes =  Plato.objects.filter(nombre_plato=entrada1).values("ingredientes").first()
            ent1_ingredientes = ent1_ingredientes['ingredientes'] if ent1_ingredientes else None

            # Agregar
            agregar_plato(platos_del_dia, "entrada1", entrada1, ent1_ingredientes)

            ent2_ingredientes =  Plato.objects.filter(nombre_plato=entrada2).values("ingredientes").first()
            ent2_ingredientes = ent2_ingredientes['ingredientes'] if ent2_ingredientes else None

            ent3_ingredientes =  Plato.objects.filter(nombre_plato=entrada3).values("ingredientes").first()
            ent3_ingredientes = ent3_ingredientes['ingredientes'] if ent3_ingredientes else None

            ent4_ingredientes =  Plato.objects.filter(nombre_plato=entrada4).values("ingredientes").first()
            ent4_ingredientes = ent4_ingredientes['ingredientes'] if ent4_ingredientes else None

            post1_ingredientes =  Plato.objects.filter(nombre_plato=postre1).values("ingredientes").first()
            post1_ingredientes = post1_ingredientes['ingredientes'] if post1_ingredientes else None

            post2_ingredientes =  Plato.objects.filter(nombre_plato=postre2).values("ingredientes").first()
            post2_ingredientes = post2_ingredientes['ingredientes'] if post2_ingredientes else None

            dip1_ingredientes =  Plato.objects.filter(nombre_plato=dip1).values("ingredientes").first()
            dip1_ingredientes = dip1_ingredientes['ingredientes'] if dip1_ingredientes else None

            dip2_ingredientes =  Plato.objects.filter(nombre_plato=dip2).values("ingredientes").first()
            dip2_ingredientes = dip2_ingredientes['ingredientes'] if dip2_ingredientes else None

            dip3_ingredientes =  Plato.objects.filter(nombre_plato=dip3).values("ingredientes").first()
            dip3_ingredientes = dip3_ingredientes['ingredientes'] if dip3_ingredientes else None

            dip4_ingredientes =  Plato.objects.filter(nombre_plato=dip4).values("ingredientes").first()
            dip4_ingredientes = dip4_ingredientes['ingredientes'] if dip4_ingredientes else None

            dip4_ingredientes =  Plato.objects.filter(nombre_plato=dip4).values("ingredientes").first()
            dip4_ingredientes = dip4_ingredientes['ingredientes'] if dip4_ingredientes else None

            salsa1_ingredientes =  Plato.objects.filter(nombre_plato=salsa1).values("ingredientes").first()
            salsa1_ingredientes = salsa1_ingredientes['ingredientes'] if salsa1_ingredientes else None

            salsa2_ingredientes =  Plato.objects.filter(nombre_plato=salsa2).values("ingredientes").first()
            salsa2_ingredientes = salsa2_ingredientes['ingredientes'] if salsa2_ingredientes else None

            salsa3_ingredientes =  Plato.objects.filter(nombre_plato=salsa3).values("ingredientes").first()
            salsa3_ingredientes = salsa3_ingredientes['ingredientes'] if salsa3_ingredientes else None

            salsa4_ingredientes =  Plato.objects.filter(nombre_plato=salsa4).values("ingredientes").first()
            salsa4_ingredientes = salsa4_ingredientes['ingredientes'] if salsa4_ingredientes else None

            trago1_ingredientes =  Plato.objects.filter(nombre_plato=trago1).values("ingredientes").first()
            trago1_ingredientes = trago1_ingredientes['ingredientes'] if trago1_ingredientes else None

            trago2_ingredientes =  Plato.objects.filter(nombre_plato=trago2).values("ingredientes").first()
            trago2_ingredientes = trago2_ingredientes['ingredientes'] if trago2_ingredientes else None

            agregar_plato(platos_del_dia, "entrada2", entrada2, ent2_ingredientes)
            agregar_plato(platos_del_dia, "entrada3", entrada3, ent3_ingredientes)
            agregar_plato(platos_del_dia, "entrada4", entrada4, ent4_ingredientes)

            agregar_plato(platos_del_dia, "postre1", postre1, post1_ingredientes)
            agregar_plato(platos_del_dia, "postre2", postre2, post2_ingredientes)

            agregar_plato(platos_del_dia, "dip1", dip1, dip1_ingredientes)
            agregar_plato(platos_del_dia, "dip2", dip2, dip2_ingredientes)
            agregar_plato(platos_del_dia, "dip3", dip3, dip3_ingredientes)
            agregar_plato(platos_del_dia, "dip4", dip4, dip4_ingredientes)

            agregar_plato(platos_del_dia, "salsa1", salsa1, salsa1_ingredientes)
            agregar_plato(platos_del_dia, "salsa2", salsa2, salsa2_ingredientes)
            agregar_plato(platos_del_dia, "salsa3", salsa3, salsa3_ingredientes)
            agregar_plato(platos_del_dia, "salsa4", salsa4, salsa4_ingredientes)

            agregar_plato(platos_del_dia, "trago1", trago1, trago1_ingredientes)
            agregar_plato(platos_del_dia, "trago2", trago2, trago2_ingredientes)

            # # Datos nuevos a agregar
            almuerzo_cena = {
                "almuerzo": {"plato": almuerzo, "ingredientes": almuerzo_ingredientes, "elegido": True},
                "variedades_almuerzo": variedad_almuerzo_con_elegidos,
                "cena": {"plato": cena, "ingredientes": cena_ingredientes, "elegido": True},
                "variedades_cena": variedad_cena_con_elegidos,
                # "guarnicion2": {"plato": guarnicion2, "ingredientes": guar2_ingredientes, "elegido": True},
                # "guarnicion3": {"plato": guarnicion3, "ingredientes": guar3_ingredientes, "elegido": True},
                # "guarnicion4": {"plato": guarnicion4, "ingredientes": guar4_ingredientes, "elegido": True},
                # "entrada1": {"plato": entrada1, "ingredientes": ent1_ingredientes, "elegido": True},
                # "entrada2": {"plato": entrada2, "ingredientes": ent2_ingredientes, "elegido": True},
                # "entrada3": {"plato": entrada3, "ingredientes": ent3_ingredientes, "elegido": True},
                # "entrada4": {"plato": entrada4, "ingredientes": ent4_ingredientes, "elegido": True},
                # "postre1": {"plato": postre1, "ingredientes": post1_ingredientes, "elegido": True},
                # "postre2": {"plato": postre2, "ingredientes": post2_ingredientes, "elegido": True},
                # "dip1": {"plato": dip1, "ingredientes": dip1_ingredientes, "elegido": True},
                # "dip2": {"plato": dip2, "ingredientes": dip2_ingredientes, "elegido": True},
                # "dip3": {"plato": dip3, "ingredientes": dip3_ingredientes, "elegido": True},
                # "dip4": {"plato": dip4, "ingredientes": dip4_ingredientes, "elegido": True},
                # "salsa1": {"plato": salsa1, "ingredientes": salsa1_ingredientes, "elegido": True},
                # "salsa2": {"plato": salsa2, "ingredientes": salsa2_ingredientes, "elegido": True},
                # "salsa3": {"plato": salsa3, "ingredientes": salsa3_ingredientes, "elegido": True},
                # "salsa4": {"plato": salsa4, "ingredientes": salsa4_ingredientes, "elegido": True},
                # "trago1": {"plato": trago1, "ingredientes": trago1_ingredientes, "elegido": True},
                # "trago2": {"plato": trago2, "ingredientes": trago2_ingredientes, "elegido": True},
            }

            platos_del_dia.update(almuerzo_cena)

            if registro_existente:
                    # Actualizar el registro existente
                    if "almuerzo" in registro_existente.platos_que_comemos:
                        if almuerzo == registro_existente.platos_que_comemos["almuerzo"]["plato"]:
                            platos_del_dia["almuerzo"]["elegido"] = registro_existente.platos_que_comemos["almuerzo"]["elegido"]

                    if "cena" in registro_existente.platos_que_comemos:
                        if cena == registro_existente.platos_que_comemos["cena"]["plato"]:
                            platos_del_dia["cena"]["elegido"] = registro_existente.platos_que_comemos["cena"]["elegido"]

                    if "guarnicion1" in registro_existente.platos_que_comemos:
                         if guarnicion1 == registro_existente.platos_que_comemos["guarnicion1"]["plato"]:
                            platos_del_dia["guarnicion1"]["elegido"] = registro_existente.platos_que_comemos["guarnicion1"]["elegido"]


                    registro_existente.platos_que_comemos = platos_del_dia
                    registro_existente.save()
            else:
                ElegidosXDia.objects.create(user=usuario, el_dia_en_que_comemos=fecha, platos_que_comemos=platos_del_dia)

        return redirect(reverse_lazy("filtro-de-platos"))
    else:
        return JsonResponse({'error': 'El método de solicitud debe ser POST'})



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

# valores que necesito
#    "guarnicion1": {"plato": guarnicion1, "ingredientes": ing_guar1, "elegido": guar1_elegido},

# lista de ingredientes

# no incluir


@login_required
def lista_de_compras(request):
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')  # Configura la localización a español
    # Obtener la fecha actual
    today = date.today()
    # Filtrar los objetos de ElegidosXDia para excluir aquellos cuya fecha sea anterior a la fecha actual
    menues_del_usuario = ElegidosXDia.objects.filter(user=request.user, el_dia_en_que_comemos__gte=today).order_by('el_dia_en_que_comemos')

    platos_por_dia = {}

    no_incluir =""

    hay_comentario = "no hay comentario"

    lista_de_ingredientes = set()

    ingredientes_unicos = {}  # Diccionario para almacenar ingredientes a comprar, estado, comentario
    
    # estas dos definiciones de variables tal vez se puedan sacar
    dia_en_que_comemos_str = ""
    buscar_cena_por_dia = ""
    # xxxxxxxx
    
    ingredientes_no_comprados = []
    lista_de_compras = []

    items_resultados = {}

    # Obtener el perfil del usuario actual
    perfil = get_object_or_404(Profile, user=request.user)

    if request.method == 'POST':

                no_incluir = set()
                # items = {} la necesito acá pero la muevo para ver contexto

                lista_de_compras = request.POST.getlist("ingrediente_a_comprar")

                for menu_del_dia in menues_del_usuario:
                    platos_dia = menu_del_dia.platos_que_comemos
                    # Convertir dia_en_que_comemos a cadena con un formato específico
                    dia_en_que_comemos_str = menu_del_dia.el_dia_en_que_comemos.strftime('%d %b %Y')

                    almuerzo_que_comemos = platos_dia.get("almuerzo", {}).get("plato", [])
                    almuerzo_info = platos_dia.get("almuerzo", {}).get("ingredientes", [])

                    # Concatenar el valor de 'dia_en_que_comemos' a 'variedad_value["variedad"]'
                    if almuerzo_que_comemos:
                        buscar_almuerzo_por_dia = almuerzo_que_comemos + dia_en_que_comemos_str
                    else:
                         buscar_almuerzo_por_dia = None

                    if buscar_almuerzo_por_dia in request.POST:
                          almuerzo_elegido = True
                          lista_de_ingredientes.update({ingrediente.strip() for ingrediente in almuerzo_info.split(',')})

                          if not menu_del_dia.platos_que_comemos["almuerzo"]["elegido"]:
                                    menu_del_dia.platos_que_comemos["almuerzo"]["elegido"] = True
                                    # Guardar el objeto en la base de datos
                                    menu_del_dia.save()
                                    no_incluir.update({ingrediente.strip() for ingrediente in almuerzo_info.split(',')})

                    else:
                        almuerzo_elegido = False
                        menu_del_dia.platos_que_comemos["almuerzo"]["elegido"] = False
                        # Guardar el objeto en la base de datos
                        menu_del_dia.save()

                    item_nombres = [
                            "entrada1", "entrada2", "entrada3", "entrada4",
                            "guarnicion1", "guarnicion2", "guarnicion3", "guarnicion4",
                            "postre1", "postre2", "salsa1", "salsa2", "salsa3", "salsa4",
                            "dip1", "dip2", "dip3", "dip4", "trago1", "trago2"
                        ]

                    platos_por_dia[menu_del_dia.el_dia_en_que_comemos] = {}

                        # Iterar sobre cada item y acumular resultados
                    for item_nombre in item_nombres:

                        # Llamada a la función y desglosar los tres resultados
                        resultado, lista_de_ingredientes, no_incluir = procesar_item(platos_dia, item_nombre, menu_del_dia, dia_en_que_comemos_str, request, lista_de_ingredientes, no_incluir)

                        # Actualizar `items` con el resultado específico del item
                        items_resultados[item_nombre] = resultado

                        # AQUI SE GENERA UNA DOBLE REFERENCIA QUE ESTARÍA BUENO CORREGIR
                        # CON ESTO items_resultados[item_nombre] = resultado ASÍ >>>>> {}, 'guarnicion1': {'guarnicion1': {'plato': 'Puré', 'ingredientes': 'papas, leche, sal, manteca', 'elegido': False}}, 'guarnicion2': {}

                        # Luego puedes llamar a `.update()` sin problemas
                        platos_por_dia[menu_del_dia.el_dia_en_que_comemos].update({
                            item_nombre: {
                                "plato": items_resultados.get(item_nombre, {}).get(item_nombre, {}).get("plato"),
                                "ingredientes": items_resultados.get(item_nombre, {}).get(item_nombre, {}).get("ingredientes"),
                                "elegido": items_resultados.get(item_nombre, {}).get(item_nombre, {}).get("elegido")
                            }
                            })

                    cena_que_comemos = platos_dia.get("cena", {}).get("plato", [])
                    cena_info = platos_dia.get("cena", {}).get("ingredientes", [])
                    # # Convertir dia_en_que_comemos a cadena con un formato específico
                    # dia_en_que_comemos_str = menu_del_dia.el_dia_en_que_comemos.strftime('%d %b. %Y')

                    # Concatenar el valor de 'dia_en_que_comemos' a 'variedad_value["variedad"]'
                    if cena_que_comemos:
                        buscar_cena_por_dia = cena_que_comemos + dia_en_que_comemos_str
                    else:
                         buscar_cena_por_dia = None

                    if buscar_cena_por_dia in request.POST:
                          cena_elegida = True
                          lista_de_ingredientes.update({ingrediente.strip() for ingrediente in cena_info.split(',')})

                          if not menu_del_dia.platos_que_comemos["cena"]["elegido"]:
                                menu_del_dia.platos_que_comemos["cena"]["elegido"] = True
                                # Guardar el objeto en la base de datos
                                menu_del_dia.save()
                                no_incluir.update({ingrediente.strip() for ingrediente in cena_info.split(',')})
                    else:
                          cena_elegida = False
                          menu_del_dia.platos_que_comemos["cena"]["elegido"] = False
                        # Guardar el objeto en la base de datos
                          menu_del_dia.save()

                    almuerzo_variedades = platos_dia.get("variedades_almuerzo", {})
                    if almuerzo_variedades:

                            for variedad_key, variedad_value in almuerzo_variedades.items():
                                  # Convertir dia_en_que_comemos a cadena con un formato específico
                                dia_en_que_comemos_str = menu_del_dia.el_dia_en_que_comemos.strftime('%d %b. %Y')
                                 # Concatenar el valor de 'dia_en_que_comemos' a 'variedad_value["variedad"]'
                                buscar_variedad_por_dia = variedad_value["variedad"] + dia_en_que_comemos_str
                                if buscar_variedad_por_dia in request.POST:

                                   ingredientes = variedad_value['ingredientes_de_variedades']
                                #    lista_de_ingredientes = [ingrediente.strip() for ingrediente in ingredientes.split(',')]
                                   lista_de_ingredientes.update({ingrediente.strip() for ingrediente in ingredientes.split(',')})

                                   if not menu_del_dia.platos_que_comemos["variedades_almuerzo"][variedad_key]["elegido"]:
                                        almuerzo_variedades[variedad_key]["elegido"] = True
                                        menu_del_dia.save()
                                        no_incluir.update(({ingrediente.strip() for ingrediente in ingredientes.split(',')}))
                                else:
                                     almuerzo_variedades[variedad_key]["elegido"] = False
                                     menu_del_dia.platos_que_comemos["variedades_almuerzo"] = almuerzo_variedades
                                     menu_del_dia.save()

                    cena_variedades = platos_dia.get("variedades_cena", {})

                    if cena_variedades:

                            for variedad_key, variedad_value in cena_variedades.items():
                                 # Convertir dia_en_que_comemos a cadena con un formato específico
                                dia_en_que_comemos_str = menu_del_dia.el_dia_en_que_comemos.strftime('%d %b. %Y')
                                 # Concatenar el valor de 'dia_en_que_comemos' a 'variedad_value["variedad"]'
                                buscar_variedad_por_dia = variedad_value["variedad"] + dia_en_que_comemos_str
                                if buscar_variedad_por_dia in request.POST:
                                   ingredientes = variedad_value['ingredientes_de_variedades']
                                   lista_de_ingredientes.update({ingrediente.strip() for ingrediente in ingredientes.split(',')})

                                   if not menu_del_dia.platos_que_comemos["variedades_cena"][variedad_key]["elegido"]:
                                        cena_variedades[variedad_key]["elegido"] = True

                                        # Asignar la variable modificada al objeto correspondiente
                                        menu_del_dia.platos_que_comemos["variedades_cena"] = cena_variedades
                                            # Guardar el objeto en la base de datos
                                        menu_del_dia.save()
                                        no_incluir.update(({ingrediente.strip() for ingrediente in ingredientes.split(',')}))

                                else:
                                     cena_variedades[variedad_key]["elegido"] = False
                                      # Asignar la variable modificada al objeto correspondiente
                                     menu_del_dia.platos_que_comemos["variedades_cena"] = cena_variedades
                                      # Guardar el objeto en la base de datos
                                     menu_del_dia.save()

                    set_compras = set(lista_de_compras)
                    # Identificar elementos que están en lista_de_ingredientes pero no en set_compras
                    ingredientes_no_comprados_1 = lista_de_ingredientes - set_compras
                    ingredientes_no_comprados = ingredientes_no_comprados_1 - no_incluir

                    if ingredientes_no_comprados:
                            for ingrediente_nuevo in ingredientes_no_comprados:
                                if ingrediente_nuevo not in perfil.ingredientes_que_tengo:
                                    # Actualizar el campo ingredientes_que_tengo
                                    perfil.ingredientes_que_tengo.append(ingrediente_nuevo)
                                    # Guardar el perfil actualizado
                                    perfil.save()

                                    # # Obtener el comentario del request.POST usando la clave construida
                                    # clave_comentario = f"{ingrediente_nuevo}_detalle"
                                    # el_comentario = request.POST.get(clave_comentario, '')

                    if lista_de_compras:
                            for ingrediente_a_comprar in lista_de_compras:
                                 if ingrediente_a_comprar in perfil.ingredientes_que_tengo:
                                    # Eliminar el ingrediente de la lista
                                    perfil.ingredientes_que_tengo.remove(ingrediente_a_comprar)
                                    # Guardar el perfil actualizado
                                    perfil.save()

                    el_comentario = ""

                    if lista_de_ingredientes:
                       for ingrediente in lista_de_ingredientes:
                            if ingrediente in no_incluir:
                                 for item in perfil.comentarios:
                                    ingrediente_archivado, comentario = item.split("%", 1)  # Dividir en ingrediente y comentario
                                    if ingrediente_archivado == ingrediente:
                                            el_comentario = comentario
                                            # ingrediente_final = ingrediente_archivado
                            else:
                                # Obtener el comentario del request.POST usando la clave construida
                                clave_comentario = f"{ingrediente}_detalle"
                                el_comentario = request.POST.get(clave_comentario, '')
                                # hay_comentario = el_coment

                                actualizado = False

                                # Recorrer la lista y buscar el comentario asociado
                                for item in perfil.comentarios:
                                    ingrediente_archivado, comentario = item.split("%", 1)  # Dividir en ingrediente y comentario
                                    if ingrediente_archivado == ingrediente:
                                        if el_comentario:
                                            # Variable de control para saber si se actualizó algún elemento
                                            actualizado = True
                                            # Actualizar el comentario del ingrediente
                                            perfil.comentarios[perfil.comentarios.index(item)] = f"{ingrediente}%{el_comentario}"
                                        else:
                                            actualizado = True
                                            # Eliminar el comentario del ingrediente
                                            perfil.comentarios.remove(item)

                                if not actualizado and el_comentario:
                                    # Unir el ingrediente nuevo con el comentario, separado por '%'
                                    ingrediente_con_comentario = f"{ingrediente}%{el_comentario}"
                                    # Actualizar el campo ingredientes_que_tengo
                                    perfil.comentarios.append(ingrediente_con_comentario)

                                # Guardar el perfil actualizado
                                perfil.save()

                            if ingrediente in perfil.ingredientes_que_tengo:
                                ingredientes_unicos [ingrediente] = {
                                "comentario": el_comentario,
                                "estado": "tengo" }

                            else:
                                ingredientes_unicos [ingrediente] = {
                                "comentario": el_comentario,
                                "estado": "no-tengo" }



                    platos_por_dia[menu_del_dia.el_dia_en_que_comemos].update({
                        "almuerzo": almuerzo_que_comemos,
                        "almuerzo_elegido": almuerzo_elegido,
                        "cena": cena_que_comemos,
                        "cena_elegida": cena_elegida,
                        "almuerzo_info": almuerzo_info,
                        "cena_info": cena_info,
                        "variedades": almuerzo_variedades,
                        "variedades_cena": cena_variedades
                    })

    else:

        for menu_del_dia in menues_del_usuario:
            platos_dia = menu_del_dia.platos_que_comemos

            # almuerzo_que_comemos = platos_dia.get("almuerzo", {}).get("plato", [])
            almuerzo_que_comemos = platos_dia.get("almuerzo", {}).get("plato", None)

            almuerzo_info = platos_dia.get("almuerzo", {}).get("ingredientes", [])
            almuerzo_elegido = platos_dia.get("almuerzo", {}).get("elegido", []) # podría precindirse de esto si hardcodeamos a True mas abajo

            cena_que_comemos = platos_dia.get("cena", {}).get("plato", [])
            cena_info = platos_dia.get("cena", {}).get("ingredientes", [])
            cena_elegida = platos_dia.get("cena", {}).get("elegido", []) # podría precindirse de esto si hardcodeamos a True mas abajo

            almuerzo_variedades = platos_dia.get("variedades_almuerzo", {})

            # Iterar a través del diccionario y extraer los ingredientes
            if almuerzo_variedades:
                for key, value in almuerzo_variedades.items():
                    if value["elegido"] == True:
                        ingredientes = value['ingredientes_de_variedades']
                        lista_de_ingredientes.update({ingrediente.strip() for ingrediente in ingredientes.split(',')})

            cena_variedades = platos_dia.get("variedades_cena", {})

            # Iterar a través del diccionario y extraer los ingredientes
            if cena_variedades:
                for key, value in cena_variedades.items():
                    if value["elegido"] == True:
                        ingredientes = value['ingredientes_de_variedades']
                        lista_de_ingredientes.update({ingrediente.strip() for ingrediente in ingredientes.split(',')})

            if almuerzo_info and almuerzo_elegido:
                     lista_de_ingredientes.update({ingrediente.strip() for ingrediente in almuerzo_info.split(',')})

            if cena_info and cena_elegida:
                    lista_de_ingredientes.update({ingrediente.strip() for ingrediente in cena_info.split(',')})

            # # ingredientes_separados_por_comas

            # if cena_variedades:
            #     for key, value in cena_variedades.items():
            #         if value["elegido"] == True:
            #             ingredientes = value['ingredientes_de_variedades']
            #             lista_de_ingredientes.update({ingrediente.strip() for ingrediente in ingredientes.split(',')})


            # Lista de claves de los distintos tipos de platos a procesar, incluyendo las guarniciones
            tipos_de_platos = ["entrada1", "entrada2", "entrada3", "entrada4",
                            "postre1", "postre2",
                            "dip1", "dip2", "dip3", "dip4",
                            "salsa1", "salsa2", "salsa3", "salsa4",
                            "trago1", "trago2",
                            "guarnicion1", "guarnicion2", "guarnicion3", "guarnicion4"]

            # Inicializa el conjunto para los ingredientes
            # lista_de_ingredientes = set()

            # Itera sobre cada clave en la lista
            for tipo in tipos_de_platos:
                # Accede al diccionario de cada plato o guarnición
                plato = platos_dia.get(tipo, {})
                # Obtén los ingredientes de cada plato o guarnición
                ingredientes = plato.get("ingredientes")
                elegido = plato.get("elegido")

                # Verifica que los ingredientes existan y no sean None
                if ingredientes and elegido:
                    # Divide los ingredientes por comas y actualiza el conjunto
                    lista_de_ingredientes.update({ingrediente.strip() for ingrediente in ingredientes.split(',')})

            # Inicializa el diccionario base con las claves fijas
            platos_por_dia[menu_del_dia.el_dia_en_que_comemos] = {
                "almuerzo": almuerzo_que_comemos,
                "almuerzo_elegido": almuerzo_elegido,  # puede harcodearse a TRUE
                "cena": cena_que_comemos,
                "cena_elegida": cena_elegida,  # puede harcodearse a TRUE
                "almuerzo_info": almuerzo_info,
                "cena_info": cena_info,
                "variedades": almuerzo_variedades,
                "variedades_cena": cena_variedades,
            }

            # Itera sobre cada tipo de plato y sus elementos para agregar al diccionario
            for tipo in tipos_de_platos:
               plato = platos_dia.get(tipo, {})
               platos_por_dia[menu_del_dia.el_dia_en_que_comemos][tipo] = {
                        "plato": plato.get("plato"),
                        "ingredientes": plato.get("ingredientes"),
                        "elegido": plato.get("elegido")
                    }

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

    # Generar el mensaje de WhatsApp
    mensaje_whatsapp = "Lista de compras:\n"

    lista_de_compras =[]
    # Recorrer el diccionario para formatear los ingredientes que no tienes
    for ingrediente, detalles in ingredientes_unicos.items():
        if detalles["estado"] == "no-tengo":
            comentario = detalles["comentario"]
            # Formatear el ingrediente con el comentario si está presente
            if comentario:
                mensaje_whatsapp += f"• {ingrediente} ({comentario})\n"
                lista_de_compras.append(f"{ingrediente} ({comentario})")

            else:
                mensaje_whatsapp += f"• {ingrediente}\n"
                lista_de_compras.append(f"{ingrediente}")


    # Reemplazar los saltos de línea para que sean compatibles con la URL de WhatsApp
    mensaje_whatsapp = mensaje_whatsapp.replace("\n", "%0A")
    # if ingredientes_unicos:
    #     mensaje_whatsapp += "\n".join(ingredientes_unicos)
    # mensaje_whatsapp = mensaje_whatsapp.replace("\n", "%0A")  # Reemplazar saltos de línea para la URL

# ESTO SE REPITE EN FILTRO DE PLATOS, PODRÍA OPTIMIZARSE?????
   # Obtener la fecha y hora actuales
    fecha_actual = datetime.datetime.now().date()

         # Filtra las fechas únicas en `el_dia_en_que_comemos` para los objetos del usuario actual
    fechas_existentes = ElegidosXDia.objects.filter(user=request.user,el_dia_en_que_comemos__gte=fecha_actual).values_list('el_dia_en_que_comemos', flat=True).distinct()

    # Lista para almacenar los días y sus nombres
    dias_desde_hoy = []

     # Obtener el nombre del día de la semana para la fecha actual
    nombre_dia_semana = fecha_actual.strftime('%A')

    # Calcular y agregar las fechas y nombres de los días para los próximos 6 días
    for i in range(0, 6):
        fecha = fecha_actual + timedelta(days=i)
        nombre_dia = fecha.strftime('%A')
        dias_desde_hoy.append((fecha))


# ***********

    context = {
        'platos_por_dia': platos_por_dia,
        'ingredientes_separados_por_comas': ingredientes_unicos,
        'el_request': request.POST,
        "los_items": items_resultados,
        "lista_de_compras": lista_de_compras,
        "no_incluir": no_incluir,
        "dias_programados": fechas_existentes,
        "dias_desde_hoy": dias_desde_hoy,
        "dia_en_que_comemos_str": dia_en_que_comemos_str,
        "buscar_cena_por_dia" : buscar_cena_por_dia,
        "claves_en_el_request" : request.POST.keys(),





        # "hay_comentario": hay_comentario,

        "ingredientes_no_comprados": ingredientes_no_comprados,
        "mensaje_whatsapp": mensaje_whatsapp,
        "parametro" : "lista-compras"
    }

    return render(request, 'AdminVideos/lista_de_compras.html', context)














class PlatoDetail(DetailView):
    model = Plato
    # template_name = 'AdminVideos/plato_detail.html'
    context_object_name = "plato"

    def get_context_data(self, **kwargs):
        # Llamar al método original para obtener el contexto base
        context = super().get_context_data(**kwargs)

        # Obtener el perfil del usuario actual
        perfil = get_object_or_404(Profile, user=self.request.user)

        # Pasar la lista de amigues al contexto
        context["amigues"] = perfil.amigues  # Lista JSONField desde Profile

        return context


# class PlatoDelete(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
#     model = Plato
#     context_object_name = "plato"
#     success_url = reverse_lazy("filtro-de-platos")

#     def test_func(self):
#         user_id = self.request.user.id
#         plato_id =  self.kwargs.get("pk")
#         return Plato.objects.filter(propietario=user_id, id=plato_id).exists()


@login_required
def eliminar_plato(request, plato_id):
    # Verificar que el usuario es el propietario del plato
    plato = get_object_or_404(Plato, id=plato_id)

    # Comprobar si el usuario actual es el propietario del plato
    if plato.propietario != request.user:
        raise Http404("No tienes permiso para eliminar este plato.")

    # Actualizar la lista sugeridos_descartados del perfil del usuario
    # profile = request.user.profile

    # Obtener el perfil del usuario actual
    perfil = get_object_or_404(Profile, user=request.user)

    # Eliminar el plato de la lista de sugeridos_descartados si está allí
    if plato.nombre_plato in perfil.sugeridos_descartados:
        perfil.sugeridos_descartados.remove(plato.nombre_plato)
        perfil.save()

  # Eliminar el plato de la lista de sugeridos_importados si está allí
    if plato.nombre_plato in perfil.sugeridos_importados:
        perfil.sugeridos_importados.remove(plato.nombre_plato)
        perfil.save()

    # Eliminar el plato de la base de datos
    plato.delete()

    # # Eliminar el plato de la base de datos
    # plato.delete()

    return redirect('filtro-de-platos')  # Redirigir a la página de filtro de platos










class PlatoUpdate(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Plato
    form_class = PlatoForm
    template_name = 'AdminVideos/plato_ppal_update.html'
    success_url = reverse_lazy("filtro-de-platos")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        variedades_en_base = self.object.variedades or {}

        # Crear diccionario para las variedades
        variedades = {}
       # Crear diccionario para los ingredientes
        ingredientes_por_variedad = {}
        # ingredientes_separados_por_comas = []

        for key, value in variedades_en_base.items():
            variedad = value.get('variedad', '')
            ingredientes_variedad = value.get('ingredientes_de_variedades',"")

            # Agregar la variedad al diccionario de variedades
            variedades[key] = variedad

            # Convertir la lista de ingredientes en una cadena separada por comas
            # ingredientes_separados_por_comas = ', '.join(ingredientes_variedad)
            ingredientes_separados_por_comas = ingredientes_variedad


            # Agregar los ingredientes de esta variedad al diccionario de ingredientes
            ingredientes_por_variedad[key] = ingredientes_separados_por_comas

        context['variedades_en_base'] = variedades
        context['ingredientes_variedad'] = ingredientes_por_variedad

        return context

    def test_func(self):
        user_id = self.request.user.id
        plato_id = self.kwargs.get("pk")
        return Plato.objects.filter(propietario=user_id, id=plato_id).exists()


    def form_valid(self, form):
        # Guardar el formulario y obtener la instancia del plato
        plato = form.save(commit=False)
        plato.propietario = self.request.user

        # Procesar las variedades ingresadas en el formulario
        variedades = {}
        for key, value in self.request.POST.items():
            if key.startswith('variedad'):
                numero_variedad = key.replace('variedad', '')
                ingredientes_key = 'ingredientes_de_variedad' + numero_variedad
                # if value:
                #    ingredientes_variedades = self.request.POST.get(ingredientes_key)

                if value:
                  variedades['variedad' + numero_variedad] = {
                    'variedad': value,
                    'ingredientes_de_variedades': self.request.POST.get(ingredientes_key)
                   }

        plato.variedades = variedades

        plato.save()

        #  # Actualizar Preseleccionados y Seleccionados
        # self.actualizar_preseleccionados(plato)

        return redirect(self.success_url)

# def actualizar_preseleccionados(self, plato):
#         # Aquí puedes agregar el código para actualizar otros modelos que referencian el plato
#         # Ejemplo:
#         otros_registros = OtroModelo.objects.filter(plato=plato)
#         for registro in otros_registros:
#             registro.nombre_plato = plato.nombre  # o el campo que sea adecuado
#             registro.save()

class PlatoCreate(LoginRequiredMixin, CreateView):
    model = Plato
    form_class = PlatoForm
    template_name = 'AdminVideos/platos_update.html'
    success_url = reverse_lazy("videos-create")
    # fields = ["nombre_plato","receta","descripcion_plato","ingredientes","medios","categoria","dificultad", "tipo","calorias", "image"]
#    fields = '__all__'

    # PARA CORREGIR EN ALGÚN MOMENTO
    # def dispatch(self, request, *args, **kwargs):
    #     # Almacena el valor de 'tipopag' en una variable de instancia
    #     self.template_param = request.GET.get('tipopag')
    #     return super().dispatch(request, *args, **kwargs)

    # def get_template_names(self):
    #     # Usa la variable de instancia en lugar de obtener el parámetro de nuevo
    #     if self.template_param == 'Entrada':

    def get_template_names(self):
        # Obtener el valor del parámetro 'template' desde la URL
        template_param = self.request.GET.get('tipopag')

        # Dependiendo del valor de 'template', asignar una plantilla diferente
        if template_param == 'Entrada':
            return ['AdminVideos/entrada_update.html']
        elif template_param == 'Dip':
            return ['AdminVideos/dip_update.html']
        elif template_param == 'Principal' or template_param == 'Dash':
            return ['AdminVideos/plato_ppal_update.html']
        elif template_param == 'Trago':
            return ['AdminVideos/trago_update.html']
        elif template_param == 'Salsa':
            return ['AdminVideos/salsa_update.html']
        elif template_param == 'Guarnicion':
            return ['AdminVideos/guarnicion_update.html']
        elif template_param == 'Postre':
            return ['AdminVideos/postre_update.html']
        else:
            # Plantilla por defecto
            return [self.template_name]

    def get_initial(self):
        # Llama al método original para obtener el diccionario de inicialización
        initial = super().get_initial()
         # Obtener el valor del parámetro 'template' desde la URL
        template_param = self.request.GET.get('tipopag')

        # Asigna valores predeterminados al campo 'tipo' según el valor de 'template_param'
        if template_param == 'Entrada':
            initial['tipo'] = 'Entrada'
        elif template_param == 'Salsa':
            initial['tipo'] = 'Salsa'
        elif template_param == 'Picada':
            initial['tipo'] = 'Picada'
        elif template_param == 'Principal' or template_param == 'Dash':
            initial['tipo'] = 'Principal'
        elif template_param == 'Postre':
            initial['tipo'] = 'Postre'
        elif template_param == 'Torta':
            initial['tipo'] = 'Torta'
        elif template_param == 'Dip':
            initial['tipo'] = 'Dip'
        elif template_param == 'Trago':
            initial['tipo'] = 'Trago'
        elif template_param == 'Guarnicion':
            initial['tipo'] = 'Guarnicion'
        else:
            # Valor por defecto si 'template_param' no coincide con ninguna condición
            initial['tipo'] = '-'

        return initial

    def form_valid(self, form):
        plato = form.save(commit=False)
        plato.propietario = self.request.user

        # Procesar los datos adicionales de variedad e ingredientes
        variedades = {}
        for i in range(1, 7):  # Iterar desde 1 hasta 6
            variedad = form.cleaned_data.get(f'variedad{i}')
            ingredientes_variedad_str = form.cleaned_data.get(f'ingredientes_de_variedad{i}')

            # Convertir la cadena de ingredientes en una lista
            # ingredientes_variedad = [ingrediente.strip() for ingrediente in ingredientes_variedad_str.split(',')] if ingredientes_variedad_str else []

            if variedad:  # Verificar si la variedad no está vacía
                variedades[f"variedad{i}"] = {"variedad": variedad, "ingredientes_de_variedades": ingredientes_variedad_str}

        plato.variedades = variedades
        plato.save()


        # Obtener el parámetro 'tipopag' y pasarlo en la redirección
        template_param = self.request.GET.get('tipopag')
        return redirect(reverse("videos-create") + f"?tipopag={template_param}")

        # return redirect(self.success_url)










class Login(LoginView):
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
    preseleccionados,
    medios,
    categoria,
    dificultad,
    # PREPARACIÓN = DIFICULTAD
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
                query &= ~Q(nombre_plato__in=platos_descartados)

        if misplatos == "misplatos":
            query |= Q(propietario=usuario)

        if tipo_parametro and tipo_parametro != "Dash":
            query &= Q(tipo=tipo_parametro)

        if preseleccionados == "preseleccionados":
            nombres_platos_elegidos = list(Preseleccionados.objects.filter(usuario=usuario).values_list('nombre_plato_elegido', flat=True))
            if nombres_platos_elegidos:
                query &= Q(nombre_plato__in=nombres_platos_elegidos)

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
def FiltroDePlatos (request):
    # Configuración regional y fechas
    # Establecer la configuración regional a español
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')

    # Obtener la fecha y hora actuales
    fecha_actual = datetime.datetime.now().date()

    # # Calcular y agregar las fechas y nombres de los días para los próximos 6 días
    dias_desde_hoy = [(fecha_actual + timedelta(days=i)) for i in range(0, 6)]


    # Recuperar los parámetros desde la sesión y la URL
    tipo_parametro, quecomemos, misplatos, preseleccionados, medios, categoria, dificultad, palabra_clave = obtener_parametros_sesion(request)

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
                preseleccionados = request.POST.get('preseleccionados')

                request.session['quecomemos'] = quecomemos
                request.session['misplatos'] = misplatos
                request.session['preseleccionados'] = preseleccionados

    else:
        items_iniciales = {

                        'medios': medios,
                        'categoria': categoria,
                        'dificultad': dificultad,
                        'palabra_clave': palabra_clave

                    }

        form = PlatoFilterForm(initial=items_iniciales)

    # Llamar a la función filtrar_platos pasando las variables recuperadas
    platos = filtrar_platos(
        usuario=usuario,
        tipo_parametro=tipo_parametro,
        quecomemos=quecomemos,
        misplatos=misplatos,
        preseleccionados=preseleccionados,
        medios=medios,
        categoria=categoria,
        dificultad=dificultad,
        palabra_clave=palabra_clave
    )

    if usuario:
        platos_preseleccionados = Preseleccionados.objects.filter(usuario=usuario).values_list('nombre_plato_elegido', flat=True)

    # Filtra las fechas únicas en `el_dia_en_que_comemos` para los objetos del usuario actual
    fechas_existentes = ElegidosXDia.objects.filter(user=request.user,el_dia_en_que_comemos__gte=fecha_actual).values_list('el_dia_en_que_comemos', flat=True).distinct()

    # Obtén el perfil del usuario autenticado
    perfil = get_object_or_404(Profile, user=request.user)

    # Accede al atributo `amigues` desde la instancia
    amigues = perfil.amigues  # Esto cargará la lista almacenada en JSONField

    # el avatar
    avatar = perfil.avatar_url

    mensajes_x_usuario = Mensaje.objects.filter(destinatario=request.user).all()

    mensajes_x_usuario = Mensaje.objects.filter(destinatario=request.user).order_by('-creado_el')


    # Calcular los días transcurridos
    for mensaje in mensajes_x_usuario:
        # Calcular los días transcurridos desde la fecha de creación hasta el día de hoy
        diferencia = timezone.now() - mensaje.creado_el
        mensaje.creado_el = diferencia.days  # Añadir un nuevo atributo calculado

    # Agrupar los mensajes por usuario
    mensajes_agrupados = {
        usuario: {
            "avatar_url":  getattr(User.objects.get(username=usuario).profile, 'avatar_url', '/media/avatares/logo.png'),
            "mensajes": list(mensajes)
        }
        for usuario, mensajes in groupby(mensajes_x_usuario, key=lambda x: x.usuario_que_envia)
    }

    # Agrupar mensajes por usuario
    # mensajes_agrupados = {
    #     usuario: list(mensajes) 
    #     for usuario, mensajes in groupby(mensajes_x_usuario, key=lambda x: x.usuario_que_envia)
    # }

# mensajes_agrupados ahora es un diccionario donde cada clave es un usuario,
# y cada valor es la lista de mensajes de ese usuario.

    dia_activo = request.session.get('dia_activo', None)  # 🟢 Recuperamos la fecha activa

    contexto = {
                'formulario': form,
                'platos': platos,
                'preseleccionados': platos_preseleccionados,
                "dias_desde_hoy": dias_desde_hoy,
                "dias_programados": fechas_existentes,
                "quecomemos_ck": quecomemos,
                "misplatos_ck": misplatos,
                "preseleccionados_ck": preseleccionados,
                "amigues" : amigues,
                "parametro": tipo_parametro,
                "mensajes": mensajes_agrupados,
                'dia_activo': dia_activo  # 🟢 Pasamos la variable a la plantilla

               }

    return render(request, 'AdminVideos/lista_filtrada.html', contexto)


@login_required
def desmarcar_todo(request):
    # Filtra los registros por usuario logueado y tipo de plato
    Preseleccionados.objects.filter(usuario=request.user).delete()

    # Redirige a la página anterior o a otra URL
    return redirect(reverse_lazy('filtro-de-platos'))


@login_required
def reiniciar_sugeridos(request):
    # Obtener el usuario logueado
    usuario = request.user

    # Filtrar los objetos Sugeridos asociados al usuario logueado
    platos_sugeridos_usuario = Sugeridos.objects.filter(usuario_de_sugeridos=usuario)

    # Eliminar los objetos seleccionados
    Sugeridos.objects.filter(usuario_de_sugeridos=usuario).delete()

    # Redireccionar a una página de confirmación o a donde sea necesario
    return redirect(reverse_lazy('filtro-de-platos'))


def formulario_dia (request, dia):
    # Busca los datos del día seleccionado
    plato_dia = ElegidosXDia.objects.filter(user=request.user, el_dia_en_que_comemos=dia ).first()

    # if plato_dia and plato_dia.platos_que_comemos:
    #     almuerzo_sel = plato_dia.platos_que_comemos.get("almuerzo", {}).get("plato")
    #     cena_sel = plato_dia.platos_que_comemos.get("cena", {}).get("plato")
    #     guar1_sel = plato_dia.platos_que_comemos.get("guarnicion1", {}).get("plato")
    #     guar2_sel = plato_dia.platos_que_comemos.get("guarnicion2", {}).get("plato")
    #     guar3_sel = plato_dia.platos_que_comemos.get("guarnicion3", {}).get("plato")
    #     guar4_sel = plato_dia.platos_que_comemos.get("guarnicion4", {}).get("plato")
    #     ent1_sel = plato_dia.platos_que_comemos.get("entrada1", {}).get("plato")
    #     ent2_sel = plato_dia.platos_que_comemos.get("entrada2", {}).get("plato")
    #     ent3_sel = plato_dia.platos_que_comemos.get("entrada3", {}).get("plato")
    #     ent4_sel = plato_dia.platos_que_comemos.get("entrada4", {}).get("plato")
    #     salsa1_sel = plato_dia.platos_que_comemos.get("salsa1", {}).get("plato")
    #     salsa2_sel = plato_dia.platos_que_comemos.get("salsa2", {}).get("plato")
    #     salsa3_sel = plato_dia.platos_que_comemos.get("salsa3", {}).get("plato")
    #     salsa4_sel = plato_dia.platos_que_comemos.get("salsa4", {}).get("plato")
    #     trago1_sel = plato_dia.platos_que_comemos.get("trago1", {}).get("plato")
    #     trago2_sel = plato_dia.platos_que_comemos.get("trago2", {}).get("plato")
    #     dip1_sel = plato_dia.platos_que_comemos.get("dip1", {}).get("plato")
    #     dip2_sel = plato_dia.platos_que_comemos.get("dip2", {}).get("plato")
    #     dip3_sel = plato_dia.platos_que_comemos.get("dip3", {}).get("plato")
    #     dip4_sel = plato_dia.platos_que_comemos.get("dip4", {}).get("plato")
    #     post1_sel = plato_dia.platos_que_comemos.get("postre1", {}).get("plato")
    #     post2_sel = plato_dia.platos_que_comemos.get("postre2", {}).get("plato")

    # else:
    #      almuerzo_sel = None
    #      cena_sel = None
    #      guar1_sel = None
    #      guar2_sel = None
    #      guar3_sel = None
    #      guar4_sel = None
    #      ent1_sel = None
    #      ent2_sel = None
    #      ent3_sel = None
    #      ent4_sel = None
    #      salsa1_sel= None
    #      salsa2_sel= None
    #      salsa3_sel= None
    #      salsa4_sel= None
    #      trago1_sel = None
    #      trago2_sel = None
    #      dip1_sel = None
    #      dip2_sel = None
    #      dip3_sel = None
    #      dip4_sel = None
    #      post1_sel = None
    #      post2_sel = None

    # # Primero obtén el queryset y conviértelo en un set
    # guarniciones_presel = set(Preseleccionados.objects.filter(usuario=request.user, tipo_plato="Guarnicion").values_list('nombre_plato_elegido', flat=True))

    # principales_presel = set(Preseleccionados.objects.filter(usuario=request.user, tipo_plato="Principal").values_list('nombre_plato_elegido', flat=True))
    # principales_presel.update([almuerzo_sel, cena_sel])
    # # Opcional: si almuerzo_sel o cena_sel pueden ser None, eliminarlos también NO SÉ POR QUÉ AGREGA UN NONE CADENA
    # principales_presel.discard(None)

    # salsas_presel = set(Preseleccionados.objects.filter(usuario=request.user,
    # tipo_plato="Salsa").values_list('nombre_plato_elegido', flat=True))

    # tragos_presel = set(Preseleccionados.objects.filter(usuario=request.user, tipo_plato="Trago").values_list('nombre_plato_elegido', flat=True))

    # dips_presel = set(Preseleccionados.objects.filter(usuario=request.user, tipo_plato="Dip").values_list('nombre_plato_elegido', flat=True))

    # postres_presel = set(Preseleccionados.objects.filter(usuario=request.user, tipo_plato="Postre").values_list('nombre_plato_elegido', flat=True))

    entradas_presel = set(Preseleccionados.objects.filter(usuario=request.user, tipo_plato="Entrada").values_list('nombre_plato_elegido', flat=True))

    # # Agrega las variables adicionales al set (esto evitará duplicados automáticamente)
    # guarniciones_presel.update([guar1_sel, guar2_sel, guar3_sel, guar4_sel])
    # salsas_presel.update([salsa1_sel, salsa2_sel, salsa3_sel, salsa4_sel])
    # tragos_presel.update([trago1_sel, trago2_sel])
    # dips_presel.update([dip1_sel, dip2_sel, dip3_sel, dip4_sel])
    # postres_presel.update([post1_sel, post2_sel])
    # entradas_presel.update([ent1_sel, ent2_sel, ent3_sel, ent4_sel])

    # # Convertir cada set en lista después de agregar los valores adicionales Y SACAR NONE!!!! ESTO HAY QUE REVISARLO, POR QUÉ CARGABA UN NONE??????
    # guarniciones_presel = [item for item in guarniciones_presel if item is not  None]
    # salsas_presel = [item for item in salsas_presel if item is not None]
    # tragos_presel = [item for item in tragos_presel if item is not None]
    # dips_presel = [item for item in dips_presel if item is not None]
    # postres_presel = [item for item in postres_presel if item is not None]
    # entradas_presel = [item for item in entradas_presel if item is not None]

    # context = {
    #     'menu_dia': plato_dia,
    #     'dia_del_menu': dia,
    #     "almuerzo_sel": almuerzo_sel,
    #     "cena_sel": cena_sel,
    #     "guar1_sel": guar1_sel,
    #     "guar2_sel": guar2_sel,
    #     "guar3_sel": guar3_sel,
    #     "guar4_sel": guar4_sel,
    #     "ent1_sel": ent1_sel,
    #     "ent2_sel": ent2_sel,
    #     "ent3_sel": ent3_sel,
    #     "ent4_sel": ent4_sel,
    #     "salsa1_sel": salsa1_sel,
    #     "salsa2_sel": salsa2_sel,
    #     "salsa3_sel": salsa3_sel,
    #     "salsa4_sel": salsa4_sel,
    #     "trago1_sel": trago1_sel,
    #     "trago2_sel": trago2_sel,
    #     "dip1_sel": dip1_sel,
    #     "dip2_sel": dip2_sel,
    #     "dip3_sel": dip3_sel,
    #     "dip4_sel": dip4_sel,
    #     "post1_sel": post1_sel,
    #     "post2_sel": post2_sel,

    #     "guarniciones_presel": guarniciones_presel,
    #     "entradas_presel": entradas_presel,
    #     "principales_presel": principales_presel,
    #     "tragos_presel": tragos_presel,
    #     "postres_presel": postres_presel,
    #     "salsas_presel": salsas_presel,
    #     "dips_presel": dips_presel,

    # }

    # Pasar los datos al contexto de la plantilla
    context = {
        'menu_dia': plato_dia,
        'TIPO_CHOICES': Plato.TIPO_CHOICES,  # Pasa los TIPO_CHOICES al contexto
        "entradas_presel": entradas_presel
    }

    return render(request, 'AdminVideos/formulario_dia.html', context)

class SolicitarAmistad(CreateView):
   model = Mensaje
   success_url = reverse_lazy('filtro-de-platos')
   fields = '__all__'
   template_name = 'AdminVideos/solicitar_amistad.html'


   def form_valid(self, form):
        # Asigna el valor predeterminado al campo 'amistad'
        form.instance.amistad = "solicitar"
        return super().form_valid(form)

   def get_form(self, form_class=None):
    form = super().get_form(form_class)
    form.fields['destinatario'].queryset = User.objects.exclude(id=self.request.user.id)
    return form
   
class EnviarMensaje(LoginRequiredMixin, CreateView):
    model = Mensaje
    success_url = reverse_lazy('filtro-de-platos')
    template_name = 'AdminVideos/enviar_mensaje.html'
    fields = ['mensaje', 'destinatario']

    def get_destinatario(self):
        return get_object_or_404(User, username=self.kwargs.get("usuario"))

    def form_valid(self, form):
        form.instance.usuario_que_envia = self.request.user.username
        form.instance.amistad = "mensaje"
        return super().form_valid(form)

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


    
# class EnviarMensaje(LoginRequiredMixin, CreateView):
#     model = Mensaje
#     success_url = reverse_lazy('filtro-de-platos')
#     template_name = 'AdminVideos/enviar_mensaje.html'

#     fields = ['mensaje', 'destinatario']

#     def form_valid(self, form):
#         # Asigna valores predeterminados a campos específicos
#         form.instance.usuario_que_envia = self.request.user.username
#         form.instance.amistad = "mensaje"
#         return super().form_valid(form)

#     def get_form(self, form_class=None):
#         form = super().get_form(form_class)

#         # Obtiene los amigos del usuario actual
#         amigues_names = (
#             Profile.objects.filter(user=self.request.user)
#             .values_list('amigues', flat=True)
#             .first()
#         )

#         # Filtra solo los destinatarios en la lista de amigos si existe
#         if amigues_names:
#             form.fields['destinatario'].queryset = User.objects.filter(username__in=amigues_names)
#         else:
#             form.fields['destinatario'].queryset = User.objects.none()

#         return form

class compartir_plato(CreateView):
    model = Mensaje
    template_name = 'AdminVideos/compartir_plato.html'
    success_url = reverse_lazy('filtro-de-platos')


    fields = ['mensaje']  # Solo incluimos el campo del mensaje, ya que otros se asignarán automáticamente

    def get_context_data(self, **kwargs):
        # Obtén el contexto base de la vista
        context = super().get_context_data(**kwargs)

        # Recupera el plato_id y el amigue del request GET o POST
        plato_id = self.request.POST.get('plato_id')
        amigue = self.request.POST.get('amigue')

        # Agrega plato y amigue al contexto
        context['plato_id'] = plato_id
        context['amigue'] = amigue

        return context

    def form_valid(self, form):
        # Obtén los datos necesarios del request
        plato_id = self.request.POST.get('plato_id')
        amigue_username = self.request.POST.get('amigue')  # Supone que el valor es el nombre de usuario

        # Busca el plato y el destinatario
        plato = get_object_or_404(Plato, id=plato_id)
        destinatario = get_object_or_404(User, username=amigue_username)

        # Obtén el mensaje que el usuario escribió en el formulario
        mensaje_usuario = form.cleaned_data.get('mensaje')

        # Completa los datos automáticos del mensaje
        form.instance.usuario_que_envia = self.request.user.username
        form.instance.destinatario = destinatario
        form.instance.amistad = plato_id  # aqui mando el plato que se comparte
        form.instance.nombre_plato_compartido = {plato.nombre_plato}
        form.instance.mensaje = {mensaje_usuario}

        return super().form_valid(form)


class MensajeDelete(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
   model = Mensaje
   context_object_name = "mensaje"
   success_url = reverse_lazy("mensaje-list")

   def test_func(self):
       return Mensaje.objects.filter(destinatario=self.request.user).exists()


# class Chat(LoginRequiredMixin, ListView):
#    model = Mensaje
#    context_object_name = "mensajes"
#    template_name = 'AdminVideos/chat.html'

#    def get_queryset(self):
#         destinatario_username = self.kwargs["usuario"]

#         # Filtrar mensajes enviados o recibidos entre el usuario actual y el destinatario
#         return Mensaje.objects.filter(
#             Q(usuario_que_envia=self.request.user.username, destinatario__username=destinatario_username) |
#             Q(usuario_que_envia=destinatario_username, destinatario=self.request.user)
#         ).order_by('creado_el')

#    def get_context_data(self, **kwargs):
#         # Llamar al método original para obtener el contexto base
#         context = super().get_context_data(**kwargs)

#         # Extraer el campo "amistad" de todos los mensajes del queryset
#         mensajes = self.get_queryset()  # Obtén todos los mensajes del usuario
#         platos_ids = []

#         # Iterar sobre los mensajes para extraer IDs de platos
#         for mensaje in mensajes:
#             if mensaje.amistad != "solicitar" and mensaje.amistad != "mensaje" :
#                platos_ids.append(mensaje.amistad)

#         # Eliminar duplicados en caso de que un plato esté repetido
#         platos_ids = list(set(platos_ids))

#         # Obtener el perfil del usuario actual
#         perfil = get_object_or_404(Profile, user=self.request.user)

#         # Pasar la lista de amigues al contexto
#         context["amigues"] = perfil.amigues  # Lista JSONField desde Profile

#         # Consultar los objetos Plato correspondientes
#         platos_compartidos = Plato.objects.filter(id__in=platos_ids)

#         # Crear un diccionario con los platos para acceso rápido en la plantilla
#         context["platos_dict"] = {plato.id: plato for plato in platos_compartidos}

#         return context

# class Chat(LoginRequiredMixin, ListView):
#    model = Mensaje
#    context_object_name = "mensajes"
#    template_name = 'AdminVideos/chat.html'

#    def get_queryset(self):
#         destinatario_username = self.kwargs["usuario"]

#         # Filtrar mensajes enviados o recibidos entre el usuario actual y el destinatario
#         return Mensaje.objects.filter(
#             Q(usuario_que_envia=self.request.user.username, destinatario__username=destinatario_username) |
#             Q(usuario_que_envia=destinatario_username, destinatario=self.request.user)
#         ).order_by('creado_el')

#    def get_context_data(self, **kwargs):
#         # Llamar al método original para obtener el contexto base
#         context = super().get_context_data(**kwargs)

#         # Extraer el campo "amistad" de todos los mensajes del queryset
#         mensajes = self.get_queryset()  # Obtén todos los mensajes del usuario
#         platos_ids = []

#         # Iterar sobre los mensajes para extraer IDs de platos
#         for mensaje in mensajes:
#             if mensaje.amistad != "solicitar" and mensaje.amistad != "mensaje" :
#                platos_ids.append(mensaje.amistad)

#         # Eliminar duplicados en caso de que un plato esté repetido
#         platos_ids = list(set(platos_ids))

#         # Obtener el perfil del usuario actual
#         perfil = get_object_or_404(Profile, user=self.request.user)

#         # Pasar la lista de amigues al contexto
#         context["amigues"] = perfil.amigues  # Lista JSONField desde Profile

#         # Consultar los objetos Plato correspondientes
#         platos_compartidos = Plato.objects.filter(id__in=platos_ids)

#         # Crear un diccionario con los platos para acceso rápido en la plantilla
#         context["platos_dict"] = {plato.id: plato for plato in platos_compartidos}

#         return context
   
class Chat(View):

    def get(self, request, nombre_usuario):
        usuario = get_object_or_404(User, username=nombre_usuario)
        mensajes = Mensaje.objects.filter(destinatario=request.user, usuario_que_envia=usuario.username)
        return render(request, 'chat.html', {'usuario': usuario, 'mensajes': mensajes})


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
def sumar_amigue(request):
    if request.method == "POST":
        # Obtén el ID del "amigue" enviado desde el formulario
        amigue_usuario = request.POST.get("amigue_usuario")

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

         # Construye un diccionario con las variables de contexto
    contexto = {
        "amigues": perfil.amigues,  # Lista de amigues actualizada
        "aceptado": aceptado,  # Lista de amigues actualizada

    }


    # Redirige a una página de confirmación o muestra la lista actualizada
    return render(request, "AdminVideos/amigues.html", contexto)
        # return render(request, "AdminVideos/lista_filtrada.html", {"amigues": user_profile.amigues})


    # Si no es un método POST, devuelve un error
    return HttpResponseForbidden("Método no permitido.")

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

        # Redirigir o retornar un JSON según sea necesario
        # if request.is_ajax():
        #     return JsonResponse({'success': True, 'message': 'Amigue eliminado.'})
        # return redirect('ruta_deseada')  # Reemplazar con el nombre de la vista donde redirigir

    # Si el amigue no existe, retornar un mensaje de error
    # if request.is_ajax():
        # return JsonResponse({'success': False, 'message': 'Amigue no encontrado.'})
              # Construye un diccionario con las variables de contexto
    contexto = {
        "amigues": perfil.amigues,  # Lista de amigues actualizada
    }
    return render(request, "AdminVideos/amigues.html", contexto)

@login_required
def agregar_plato_compartido(request, pk):
    # Recuperar el plato original
    plato_original = get_object_or_404(Plato, pk=pk)

    # Verificar si ya existe un plato con el mismo nombre para el usuario logueado
    if Plato.objects.filter(nombre_plato=plato_original.nombre_plato, propietario=request.user).exists():
        # Mostrar un mensaje de error
        messages.error(request, "Ya tienes un plato con este nombre.")
        return redirect('mensaje-list')  # Redirigir a una página (puedes ajustar según sea necesario)

    # Crear un nuevo plato para el usuario logueado
    nuevo_plato = Plato(
        nombre_plato=plato_original.nombre_plato,
        receta=plato_original.receta,
        descripcion_plato=plato_original.descripcion_plato,
        ingredientes=plato_original.ingredientes,
        medios=plato_original.medios,
        categoria=plato_original.categoria,
        dificultad=plato_original.dificultad,
        tipo=plato_original.tipo,
        calorias=plato_original.calorias,
        propietario=request.user,  # Asignar al usuario logueado
        image=plato_original.image,
        variedades=plato_original.variedades,
        proviene_de= plato_original.propietario
    )

    # Guardar el nuevo plato en la base de datos
    nuevo_plato.save()


    # Mostrar un mensaje de éxito
    messages.success(request, "El plato se agregó exitosamente.")


    # Redirigir a una página (puedes cambiar la redirección según sea necesario)
    return redirect('mensaje-list')



def agregar_a_mi_lista(request, plato_id):
    # Obtener el plato a copiar
    plato_original = get_object_or_404(Plato, id=plato_id)

    # Obtener el perfil del usuario logueado
    profile = request.user.profile

    # # Verificar si ya existe un plato con el mismo nombre para el usuario logueado
    # if Plato.objects.filter(nombre_plato=plato_original.nombre_plato, propietario=request.user).exists():
    #     # Mostrar un mensaje de error
    #     messages.error(request, "Ya tienes un plato con este nombre.")
    #     return redirect('filtro-de-platos')  # Redirigir a una página (puedes ajustar según sea necesario)
    
    # Crear una copia del plato, asignando el nuevo propietario
    nuevo_plato = Plato.objects.create(
        nombre_plato=plato_original.nombre_plato,
        # nombre_plato=f"{plato_original.id} - {plato_original.nombre_plato}",  # Agregar el ID al nombre del plato
        receta=plato_original.receta,
        descripcion_plato=plato_original.descripcion_plato,
        ingredientes=plato_original.ingredientes,
        medios=plato_original.medios,
        categoria=plato_original.categoria,
        dificultad=plato_original.dificultad,
        tipo=plato_original.tipo,
        calorias=plato_original.calorias,
        propietario=request.user,  # Asignar al usuario logueado
        image=plato_original.image,  # Copiar la imagen si aplica
        variedades=plato_original.variedades,
        proviene_de= plato_original.propietario
    )

  # Verificar si el plato_id ya está en la lista para evitar duplicados
    if plato_original.nombre_plato not in profile.sugeridos_importados:
        profile.sugeridos_importados.append(plato_original.nombre_plato)  # Agregar el ID del plato a la lista
        profile.save()  # Guardar los cambios en el perfil

    # Redirigir a la vista para descartar el plato después de agregarlo
    return redirect('descartar-sugerido', nombre_plato=plato_original.nombre_plato)



class AsignarPlato(View):
    def post(self, request):
        plato_id = request.POST.get('plato_id')
        dia = request.POST.get('dia')
        comida = request.POST.get('comida')
        
        # Buscar el plato
        plato = Plato.objects.get(id=plato_id)
        
        # Convertir string a fecha usando el módulo completo
        fecha_comida = datetime.datetime.strptime(dia, "%Y-%m-%d").date()

        # Guardar la fecha en la sesión para recordar la pestaña activa
        request.session['dia_activo'] = dia  # 🟢 Guardamos el día en la sesión
        
        # Buscar o crear la instancia del día
        menu_dia, created = ElegidosXDia.objects.get_or_create(
            user=request.user,
            el_dia_en_que_comemos=fecha_comida,
            defaults={"platos_que_comemos": {}}
        )
# Contar las instancias del plato con el mismo tipo (ej. "Salsa")
        count = sum(1 for key in menu_dia.platos_que_comemos if key.startswith(plato.tipo))

        # Crear la clave dinámica para platos del mismo tipo
        if count > 0:
            key = f"{plato.tipo}{count + 1}"
        else:
            key = plato.tipo  # Si no hay otros de ese tipo, usamos la clave original

        # Asignar el plato con la clave dinámica
        ingredientes = plato.ingredientes  # Ajusta esto según tu lógica de negocio
        menu_dia.platos_que_comemos[key] = {
            "plato": plato.nombre_plato,
            "ingredientes": ingredientes,
            "elegido": True
        }

        # Guardar la instancia actualizada
        menu_dia.save()
        messages.success(request, "Plato asignado correctamente.")
        
        return redirect('filtro-de-platos')