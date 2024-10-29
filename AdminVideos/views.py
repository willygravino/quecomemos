import ast
from contextvars import Context
import copy
import json
import locale
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from AdminVideos.models import Plato, Profile, Mensaje, Elegidos, ElegidosXDia, Sugeridos
from django.http import HttpRequest, JsonResponse
from django.urls import reverse, reverse_lazy
from django.contrib.auth.forms import UserCreationForm
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from datetime import datetime, timedelta
from .forms import PlatoFilterForm, PlatoForm
from django.views.generic import TemplateView
from datetime import date, datetime
import datetime




class SugerenciasRandom(TemplateView):
    template_name = 'AdminVideos/random.html'


def index(request):
    #  return render(request, "AdminVideos/lista_filtrada.html")
    return redirect(reverse_lazy("filtro-de-platos"))


def about(request):
    return render(request, "AdminVideos/about.html")

# LA SIGUIENTE FUNCIÓN TIENE QUE VER CON LOS PLATOS PRESELECCIONADOS PARA LOS MENÚES
def plato_elegido(request):
    if request.method == 'GET':
        nombre_plato = request.GET.get('opcion1')
        plato_tipo = request.GET.get('tipo-plato')

        borrar = request.GET.get('borrar')
        tipo_pag = request.GET.get('tipopag')  # Obtener el parámetro 'tipo-pag' de la URL


        usuario = request.user  # Obtener el usuario logueado

        if borrar == "borrar":
            # Eliminar el plato de la lista de platos elegidos
            Elegidos.objects.filter(usuario=usuario, nombre_plato_elegido=nombre_plato).delete()
        else:
            # Agregar el plato a la lista de platos elegidos
            Elegidos.objects.get_or_create(usuario=usuario, nombre_plato_elegido=nombre_plato, tipo_plato=plato_tipo)

        # Redirigir manteniendo el parámetro 'tipo-pag'
        return redirect(f"{reverse('filtro-de-platos')}?tipopag={tipo_pag}")
    
    else:
        # Manejar solicitudes POST u otras solicitudes que no sean GET
        return JsonResponse({"error": "Método no permitido"}, status=405)


def grabar_menu_elegido(request):
    if request.method == 'POST':
        # Obtener el usuario logueado
        usuario = request.user

        # AQUÍ, PONER LAS INSTRUCCIONES ADECUADAS PARA BORRAR LOS REGISTROS DE DÍAS MÁS ALLÁ DE 45 DÍAS ATRÁS; DE ESTE MODO SE PODRÁ CALCULAR LO QUE SE COMIÓ EN LOS ÚLTIMOS 45 DÍAS "HACE 45 DÍAS QUE NO COMÉS PESCADO"

        # Obtener las fechas y platos elegidos del formulario
        # for i in range(1, 8):
        fecha = request.POST.get("fecha")
        almuerzo = request.POST.get("a")
        cena = request.POST.get("c")
        entrada1 = request.POST.get("entrada1")
        entrada2 = request.POST.get("entrada2")
        entrada3 = request.POST.get("entrada3")
        entrada4 = request.POST.get("entrada4")
        guarnicion1 = request.POST.get("guarnicion1")
        guarnicion2 = request.POST.get("guarnicion2")
        guarnicion3 = request.POST.get("guarnicion3")
        guarnicion4 = request.POST.get("guarnicion4")
        postre1 = request.POST.get("postre1")
        postre2 = request.POST.get("postre2")
        
        registro_existente = ElegidosXDia.objects.filter(user=usuario, el_dia_en_que_comemos=fecha).first()

        if registro_existente and (almuerzo == '-----' and cena == '-----'):
            registro_existente.delete()

        if almuerzo != '-----' or cena != '-----':

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

            guar2_ingredientes =  Plato.objects.filter(nombre_plato=guarnicion2).values("ingredientes").first()       
            guar2_ingredientes = guar2_ingredientes['ingredientes'] if guar2_ingredientes else None

            guar3_ingredientes =  Plato.objects.filter(nombre_plato=guarnicion3).values("ingredientes").first()       
            guar3_ingredientes = guar3_ingredientes['ingredientes'] if guar3_ingredientes else None

            guar4_ingredientes =  Plato.objects.filter(nombre_plato=guarnicion4).values("ingredientes").first()       
            guar4_ingredientes = guar4_ingredientes['ingredientes'] if guar4_ingredientes else None

            ent1_ingredientes =  Plato.objects.filter(nombre_plato=entrada1).values("ingredientes").first()       
            ent1_ingredientes = ent1_ingredientes['ingredientes'] if ent1_ingredientes else None

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

            # Crear el diccionario de platos para este día
            platos_del_dia = {
                "almuerzo": {"plato": almuerzo, "ingredientes": almuerzo_ingredientes, "elegido": True},
                "variedades_almuerzo": variedad_almuerzo_con_elegidos,
                "cena": {"plato": cena, "ingredientes": cena_ingredientes, "elegido": True},
                "variedades_cena": variedad_cena_con_elegidos,
                "guarnicion1": {"plato": guarnicion1, "ingredientes": guar1_ingredientes, "elegido": True}, 
                "guarnicion2": {"plato": guarnicion2, "ingredientes": guar2_ingredientes, "elegido": True}, 
                "guarnicion3": {"plato": guarnicion3, "ingredientes": guar3_ingredientes, "elegido": True}, 
                "guarnicion4": {"plato": guarnicion4, "ingredientes": guar4_ingredientes, "elegido": True}, 
                "entrada1": {"plato": entrada1, "ingredientes": ent1_ingredientes, "elegido": True}, 
                "entrada2": {"plato": entrada2, "ingredientes": ent2_ingredientes, "elegido": True}, 
                "entrada3": {"plato": entrada3, "ingredientes": ent3_ingredientes, "elegido": True}, 
                "entrada4": {"plato": entrada4, "ingredientes": ent4_ingredientes, "elegido": True}, 
                "postre1": {"plato": postre1, "ingredientes": post1_ingredientes, "elegido": True}, 
                "postre2": {"plato": postre2, "ingredientes": post2_ingredientes, "elegido": True},                                
            }

            if registro_existente:
                    # Actualizar el registro existente

                    if almuerzo == registro_existente.platos_que_comemos["almuerzo"]["plato"]:
                        platos_del_dia["almuerzo"]["elegido"] = registro_existente.platos_que_comemos["almuerzo"]["elegido"]
                    if cena == registro_existente.platos_que_comemos["cena"]["plato"]:
                        platos_del_dia["cena"]["elegido"] = registro_existente.platos_que_comemos["cena"]["elegido"]

                #  registro_existente_platos = registro_existente.platos_que_comemos
                #  actualizar_datos(registro_existente_platos, platos_del_dia)
                    registro_existente.platos_que_comemos = platos_del_dia
                    registro_existente.save()
            else:
                ElegidosXDia.objects.create(user=usuario, el_dia_en_que_comemos=fecha, platos_que_comemos=platos_del_dia)

        return redirect(reverse_lazy("filtro-de-platos"))
    else:
        return JsonResponse({'error': 'El método de solicitud debe ser POST'})


def lista_y_plan(request):
    lista_de_compras = []

    lista_de_compras = request.POST.getlist("ingrediente_a_comprar")

    lista_de_ingredientes = set()

    no_incluir = set()

    # Obtener el perfil del usuario actual
    perfil = get_object_or_404(Profile, user=request.user)

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

    if lista_de_compras:
            for ingrediente_a_comprar in lista_de_compras:
                    if ingrediente_a_comprar in perfil.ingredientes_que_tengo:
                        # Eliminar el ingrediente de la lista
                        perfil.ingredientes_que_tengo.remove(ingrediente_a_comprar)
                        # Guardar el perfil actualizado
                        perfil.save()

      # Generar el mensaje de WhatsApp
    mensaje_whatsapp = "Lista de compras:\n"
    if lista_de_compras:
        mensaje_whatsapp += "\n".join(lista_de_compras)
    mensaje_whatsapp = mensaje_whatsapp.replace("\n", "%0A")  # Reemplazar saltos de línea para la URL        

    context = {
        "lista_de_compras": "hola",
        "mensaje_whatsapp": mensaje_whatsapp
    }

    return render(request, 'AdminVideos/lista_y_plan.html', context)               


     

@login_required
def menu_elegido(request):
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')  # Configura la localización a español
    # Obtener la fecha actual
    today = date.today()
    # Filtrar los objetos de ElegidosXDia para excluir aquellos cuya fecha sea anterior a la fecha actual
    objetos_del_usuario = ElegidosXDia.objects.filter(user=request.user, el_dia_en_que_comemos__gte=today).order_by('el_dia_en_que_comemos')

    platos_por_dia = {}

    lista_de_ingredientes = set()

    ingredientes_unicos = {}  # Diccionario para almacenar ingredientes a comprar, estado, comentario
    # dia_en_que_comemos_str = ""
    ingredientes_no_comprados = []
    lista_de_compras = []

    # Obtener el perfil del usuario actual
    perfil = get_object_or_404(Profile, user=request.user)

    if request.method == 'POST':

                no_incluir = set()

                lista_de_compras = request.POST.getlist("ingrediente_a_comprar")
                # detalle_ingrediente = 

                for objeto in objetos_del_usuario:
                    platos_dia = objeto.platos_que_comemos

                    almuerzo_que_comemos = platos_dia.get("almuerzo", {}).get("plato", [])
                    almuerzo_info = platos_dia.get("almuerzo", {}).get("ingredientes", [])
                    # Convertir dia_en_que_comemos a cadena con un formato específico
                    dia_en_que_comemos_str = objeto.el_dia_en_que_comemos.strftime('%d %b. %Y')


                    # Concatenar el valor de 'dia_en_que_comemos' a 'variedad_value["variedad"]'
                    buscar_almuerzo_por_dia = almuerzo_que_comemos + dia_en_que_comemos_str
                    if buscar_almuerzo_por_dia in request.POST:
                          almuerzo_elegido = True
                          lista_de_ingredientes.update({ingrediente.strip() for ingrediente in almuerzo_info.split(',')})

                          if not objeto.platos_que_comemos["almuerzo"]["elegido"]:
                                    objeto.platos_que_comemos["almuerzo"]["elegido"] = True
                                    # Guardar el objeto en la base de datos
                                    objeto.save()
                                    no_incluir.update({ingrediente.strip() for ingrediente in almuerzo_info.split(',')})

                    else:
                        almuerzo_elegido = False
                        objeto.platos_que_comemos["almuerzo"]["elegido"] = False
                        # Guardar el objeto en la base de datos
                        objeto.save()

                    cena_que_comemos = platos_dia.get("cena", {}).get("plato", [])
                    cena_info = platos_dia.get("cena", {}).get("ingredientes", [])
                    # Convertir dia_en_que_comemos a cadena con un formato específico
                    dia_en_que_comemos_str = objeto.el_dia_en_que_comemos.strftime('%d %b. %Y')
                    # Concatenar el valor de 'dia_en_que_comemos' a 'variedad_value["variedad"]'
                    buscar_cena_por_dia = cena_que_comemos + dia_en_que_comemos_str
                    if buscar_cena_por_dia in request.POST:
                          cena_elegida = True
                          lista_de_ingredientes.update({ingrediente.strip() for ingrediente in cena_info.split(',')})

                          if not objeto.platos_que_comemos["cena"]["elegido"]:
                                objeto.platos_que_comemos["cena"]["elegido"] = True
                                # Guardar el objeto en la base de datos
                                objeto.save()
                                no_incluir.update({ingrediente.strip() for ingrediente in cena_info.split(',')})
                    else:
                          cena_elegida = False
                          objeto.platos_que_comemos["cena"]["elegido"] = False
                        # Guardar el objeto en la base de datos
                          objeto.save()

                    almuerzo_variedades = platos_dia.get("variedades_almuerzo", {})
                    if almuerzo_variedades:

                            for variedad_key, variedad_value in almuerzo_variedades.items():
                                  # Convertir dia_en_que_comemos a cadena con un formato específico
                                dia_en_que_comemos_str = objeto.el_dia_en_que_comemos.strftime('%d %b. %Y')
                                 # Concatenar el valor de 'dia_en_que_comemos' a 'variedad_value["variedad"]'
                                buscar_variedad_por_dia = variedad_value["variedad"] + dia_en_que_comemos_str
                                if buscar_variedad_por_dia in request.POST:

                                   ingredientes = variedad_value['ingredientes_de_variedades']
                                #    lista_de_ingredientes = [ingrediente.strip() for ingrediente in ingredientes.split(',')]
                                   lista_de_ingredientes.update({ingrediente.strip() for ingrediente in ingredientes.split(',')})

                                   if not objeto.platos_que_comemos["variedades_almuerzo"][variedad_key]["elegido"]:
                                        almuerzo_variedades[variedad_key]["elegido"] = True
                                        objeto.save()
                                        no_incluir.update(({ingrediente.strip() for ingrediente in ingredientes.split(',')}))
                                else:
                                     almuerzo_variedades[variedad_key]["elegido"] = False
                                     objeto.platos_que_comemos["variedades_almuerzo"] = almuerzo_variedades
                                     objeto.save()

                    cena_variedades = platos_dia.get("variedades_cena", {})

                    if cena_variedades:

                            for variedad_key, variedad_value in cena_variedades.items():
                                 # Convertir dia_en_que_comemos a cadena con un formato específico
                                dia_en_que_comemos_str = objeto.el_dia_en_que_comemos.strftime('%d %b. %Y')
                                 # Concatenar el valor de 'dia_en_que_comemos' a 'variedad_value["variedad"]'
                                buscar_variedad_por_dia = variedad_value["variedad"] + dia_en_que_comemos_str
                                if buscar_variedad_por_dia in request.POST:
                                   ingredientes = variedad_value['ingredientes_de_variedades']
                                   lista_de_ingredientes.update({ingrediente.strip() for ingrediente in ingredientes.split(',')})

                                   if not objeto.platos_que_comemos["variedades_cena"][variedad_key]["elegido"]:
                                        cena_variedades[variedad_key]["elegido"] = True

                                        # Asignar la variable modificada al objeto correspondiente
                                        objeto.platos_que_comemos["variedades_cena"] = cena_variedades
                                            # Guardar el objeto en la base de datos
                                        objeto.save()
                                        no_incluir.update(({ingrediente.strip() for ingrediente in ingredientes.split(',')}))

                                else:
                                     cena_variedades[variedad_key]["elegido"] = False
                                      # Asignar la variable modificada al objeto correspondiente
                                     objeto.platos_que_comemos["variedades_cena"] = cena_variedades
                                      # Guardar el objeto en la base de datos
                                     objeto.save()

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

                    if lista_de_compras:
                            for ingrediente_a_comprar in lista_de_compras:
                                 if ingrediente_a_comprar in perfil.ingredientes_que_tengo:
                                    # Eliminar el ingrediente de la lista
                                    perfil.ingredientes_que_tengo.remove(ingrediente_a_comprar)
                                    # Guardar el perfil actualizado
                                    perfil.save()

                    if lista_de_ingredientes:
                       for ingrediente in lista_de_ingredientes:
                                       if ingrediente in perfil.ingredientes_que_tengo:
                                         ingredientes_unicos [ingrediente] = {
                                            "comentario": "<comentario>",
                                            "estado": "tengo" }

                                       else:
                                            ingredientes_unicos [ingrediente] = {
                                            "comentario": "<comentario>",
                                            "estado": "no-tengo" }

                    platos_por_dia[objeto.el_dia_en_que_comemos] = {
                        "almuerzo": almuerzo_que_comemos,
                        "almuerzo_elegido": almuerzo_elegido,
                        "cena": cena_que_comemos,
                        "cena_elegida": cena_elegida,
                        "almuerzo_info": almuerzo_info,
                        "cena_info": cena_info,
                        "variedades": almuerzo_variedades,
                        "variedades_cena": cena_variedades
                    }

    else:
        for objeto in objetos_del_usuario:
            platos_dia = objeto.platos_que_comemos

            almuerzo_que_comemos = platos_dia.get("almuerzo", {}).get("plato", [])
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

            if lista_de_ingredientes:
                for ingrediente in lista_de_ingredientes:
                    if ingrediente in perfil.ingredientes_que_tengo:
                        ingredientes_unicos [ingrediente] = {
                            "comentario": "<comentario>",
                            "estado": "tengo" }
                    else:
                        ingredientes_unicos [ingrediente] = {
                            "comentario": "<comentario>",
                            "estado": "no-tengo" }

            if not cena_info:
                cena_info = ""
            if not almuerzo_info:
                almuerzo_info = ""

            platos_por_dia[objeto.el_dia_en_que_comemos] = {
                "almuerzo": almuerzo_que_comemos,
                "almuerzo_elegido": almuerzo_elegido,  # puede hargodearse a TRUE
                "cena": cena_que_comemos,
                "cena_elegida": cena_elegida, # puede hargodearse a TRUE
                "almuerzo_info": almuerzo_info,
                "cena_info": cena_info,
                "variedades": almuerzo_variedades,
                "variedades_cena": cena_variedades
            }
    
    # Generar el mensaje de WhatsApp
    mensaje_whatsapp = "Lista de compras:\n"
    if lista_de_compras:
        mensaje_whatsapp += "\n".join(lista_de_compras)
    mensaje_whatsapp = mensaje_whatsapp.replace("\n", "%0A")  # Reemplazar saltos de línea para la URL        

    context = {
        'platos_por_dia': platos_por_dia,
        'ingredientes_separados_por_comas': ingredientes_unicos,
        'post_data': request.POST,
        "lista_de_compras": lista_de_compras,
        "ingredientes_no_comprados": ingredientes_no_comprados,
        "mensaje_whatsapp": mensaje_whatsapp
    }

    return render(request, 'AdminVideos/menu_elegido.html', context)














class PlatoDetail(DetailView):
    model = Plato
    context_object_name = "plato"


class PlatoDelete(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Plato
    context_object_name = "plato"
    success_url = reverse_lazy("filtro-de-platos")

    def test_func(self):
        user_id = self.request.user.id
        plato_id =  self.kwargs.get("pk")
        return Plato.objects.filter(propietario=user_id, id=plato_id).exists()












class PlatoUpdate(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Plato
    form_class = PlatoForm
    template_name = 'AdminVideos/plato_update.html'
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

        return redirect(self.success_url)


class PlatoCreate(LoginRequiredMixin, CreateView):
    model = Plato
    form_class = PlatoForm

    
    template_name = 'AdminVideos/plato_update.html'

    def get_template_names(self):
        # Obtener el valor del parámetro 'template' desde la URL
        template_param = self.request.GET.get('template', '')

        # Dependiendo del valor de 'template', asignar una plantilla diferente
        if template_param == 'entrada':
            return ['AdminVideos/entrada_update.html']
        elif template_param == 'dip':
            return ['AdminVideos/dip_update.html']
        elif template_param == 'principal':
            return ['AdminVideos/plato_update.html']
        elif template_param == 'trago':
            return ['AdminVideos/trago_update.html']
        elif template_param == 'salsa':
            return ['AdminVideos/salsa_update.html']
        elif template_param == 'guarnicion':
            return ['AdminVideos/guarnicion_update.html']
        elif template_param == 'postre':
            return ['AdminVideos/postre_update.html']
        else:
            # Plantilla por defecto
            return [self.template_name]


    success_url = reverse_lazy("videos-create")
    # fields = ["nombre_plato","receta","descripcion_plato","ingredientes","medios","categoria","preparacion", "tipo","calorias", "image"]
#    fields = '__all__'

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

        return redirect(self.success_url)











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
    fields = ["nombre_completo","avatar"]

    def form_valid(self, form):
        el_user = form.save(commit=False)
        el_user.user = self.request.user
        el_user.save()
        return redirect(self.success_url)

class ProfileUpdate(LoginRequiredMixin, UserPassesTestMixin,  UpdateView):
    model = Profile
    success_url = reverse_lazy("filtro-de-platos")
    fields = ["nombre_completo","avatar"]

    def test_func(self):
        return Profile.objects.filter(user=self.request.user).exists()


# class PaginaInicial (TemplateView):  # LoginRequiredMixin?????
#     model = Plato

@login_required(login_url=reverse_lazy('login'), redirect_field_name=None)
def FiltroDePlatos (request):

    # Establecer la configuración regional a español
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')

    # Obtiene la fecha actual
    # fecha_actual = datetime.now().date()

    # Obtener la fecha y hora actuales
    fecha_actual = datetime.datetime.now().date()

    # Lista para almacenar los días y sus nombres
    dias_desde_hoy = []

    # Obtener el nombre del día de la semana para la fecha actual
    nombre_dia_semana = fecha_actual.strftime('%A')

    # Agregar la fecha actual y su nombre al inicio de la lista
    dias_desde_hoy.append((fecha_actual, nombre_dia_semana))

    # Calcular y agregar las fechas y nombres de los días para los próximos 6 días
    for i in range(1, 7):
        fecha = fecha_actual + timedelta(days=i)
        nombre_dia = fecha.strftime('%A')
        dias_desde_hoy.append((fecha, nombre_dia))

    cantidad_platos_sugeribles = 0

    tipo_de_vista_estable = request.session.get('tipo_de_vista_estable', "Todos")

    medios = request.session.get('medios_estable', "None")
    categoria = request.session.get('categoria_estable', "None")
    preparacion = request.session.get('preparacion_estable', "None")
    # tipo = request.session.get('tipo_estable', "None")

    calorias = request.session.get('calorias_estable', "None")

    usuario = request.user
    cantidad_platos_sugeridos = 0
    platos_a_sugerir = ""
    tipo_de_vista = tipo_de_vista_estable

    platos_elegidos = Elegidos.objects.filter(usuario=usuario).values_list('nombre_plato_elegido', flat=True)

    if request.method == "POST":
            post_o_no = "POST, DEFINE INICIALES"

            form = PlatoFilterForm(request.POST)

            if form.is_valid():
                tipo_de_vista = form.cleaned_data.get('tipo_de_vista')
                medios = form.cleaned_data.get('medios')
                categoria = form.cleaned_data.get('categoria')
                preparacion = form.cleaned_data.get('preparacion')
                # tipo = form.cleaned_data.get('tipo')
                calorias = form.cleaned_data.get('calorias')

                # Guardar el valor de tipo_de_vista en la sesión
                request.session['tipo_de_vista_estable'] =  tipo_de_vista
                tipo_de_vista_estable = tipo_de_vista
                request.session['medios_estable'] = medios
                request.session['categoria_estable'] = categoria
                request.session['preparacion_estable'] = preparacion
                # request.session['tipo_estable'] = tipo
                request.session['calorias_estable'] = calorias

    else:
        pasa_por_aca = "PASA POR NO-POST"
        items_iniciales = {
                        'tipo_de_vista': tipo_de_vista_estable,
                        'medios': medios,
                        'categoria': categoria,
                        'preparacion': preparacion,
                        # 'tipo': tipo,
                        'calorias': calorias
                    }
        post_o_no = "NO POST, MANDA INICIALES"+tipo_de_vista_estable
        form = PlatoFilterForm(initial=items_iniciales)

    pasa_por_aca = "PASA"

    platos = Plato.objects.all()
  
    # TOMAR EL TIPO DEL MENÚ    !!!!!!!!!!!!!!
    # Obtener el valor del parámetro 'tipo' desde la URL
    tipo_parametro = request.GET.get('tipopag', '')
    if tipo_parametro:
       platos = platos.filter(tipo=tipo_parametro)

    if tipo_de_vista != 'Todos':
        if tipo_de_vista == 'solo-mios' or tipo_de_vista=="random-con-mios":
            platos = platos.filter(propietario_id=request.user.id)

        if tipo_de_vista == 'de-otros':
            platos =  platos.exclude(propietario_id=request.user.id)

        if tipo_de_vista == 'preseleccionados':
            nombres_platos_elegidos = Elegidos.objects.filter(usuario=usuario).values_list('nombre_plato_elegido', flat=True)
            platos = platos.filter(nombre_plato__in=nombres_platos_elegidos)

        if medios and medios != '-':
            platos = platos.filter(medios=medios)
        if categoria and categoria != '-':
                        platos = platos.filter(categoria=categoria)
        if preparacion and preparacion != '-':
            platos = platos.filter(preparacion=preparacion)

        if calorias and calorias != '-':
            platos = platos.filter(calorias=calorias)

        if tipo_de_vista=="random-todos" or tipo_de_vista=="random-con-mios":
            # Obtén los platos sugeridos asociados al usuario logueado
            platos_sugeridos_usuario = Sugeridos.objects.filter(usuario_de_sugeridos=usuario).values_list('nombre_plato_sugerido', flat=True)
            platos_a_sugerir = platos
            cantidad_platos_sugeribles = platos.count()
            # Excluye los platos sugeridos de la lista general de platos
            platos = platos.exclude(nombre_plato__in=platos_sugeridos_usuario)
            platos_a_sugerir = platos
            # cantidad_platos_sugeribles = platos.count()
            platos = platos.order_by('?')[:4]
            # Obtiene los primeros cuatro platos de la lista
            platos_sugeridos = platos[:4]
            platos = platos_sugeridos
            # Crea y guarda una instancia de Sugeridos para cada uno de los primeros platos
            for plato in platos_sugeridos:
                Sugeridos.objects.get_or_create(usuario_de_sugeridos=usuario, nombre_plato_sugerido=plato.nombre_plato)
    else:
        pasa_por_aca ="SUMA TODOS"+tipo_de_vista
        platos = Plato.objects.all()

    if usuario:
        platos_elegidos = Elegidos.objects.filter(usuario=usuario).values_list('nombre_plato_elegido', flat=True)
        
        principales_presel = Elegidos.objects.filter(usuario=usuario, tipo_plato="Principal").values_list('nombre_plato_elegido', flat=True)

        guarniciones_presel = Elegidos.objects.filter(usuario=usuario, tipo_plato="Guarnicion").values_list('nombre_plato_elegido', flat=True)

        salsas_presel = Elegidos.objects.filter(usuario=usuario, tipo_plato="Guarnicion").values_list('nombre_plato_elegido', flat=True)

        tragos_presel = Elegidos.objects.filter(usuario=usuario, tipo_plato="Trago").values_list('nombre_plato_elegido', flat=True)

        dips_presel = Elegidos.objects.filter(usuario=usuario, tipo_plato="Dip").values_list('nombre_plato_elegido', flat=True)

        postres_presel = Elegidos.objects.filter(usuario=usuario, tipo_plato="Postre").values_list('nombre_plato_elegido', flat=True)
                
        entradas_presel = Elegidos.objects.filter(usuario=usuario, tipo_plato="Entrada").values_list('nombre_plato_elegido', flat=True)


    # Obtén el número de platos sugeridos para el usuario actual
    cantidad_platos_sugeridos = Sugeridos.objects.filter(usuario_de_sugeridos=usuario).count()

    # Obtén los objetos ElegidosXDia asociados al usuario actual
    elegidos_por_dia = ElegidosXDia.objects.filter(user=request.user)

    platos_elegidos_por_dia = {}

        # Suponiendo que elegidos_por_dia sea tu diccionario

    for objeto_elegido in elegidos_por_dia:
        fecha = objeto_elegido.el_dia_en_que_comemos
        plato_almuerzo = objeto_elegido.platos_que_comemos.get("almuerzo", {}).get("plato", None)
        plato_cena = objeto_elegido.platos_que_comemos.get("cena", {}).get("plato", None)
        platos_elegidos_por_dia[fecha] = {"almuerzo": plato_almuerzo, "cena": plato_cena}

    platos_preseleccionados={}

    for i in range(7):
        fecha = fecha_actual + datetime.timedelta(days=i)
        if fecha in platos_elegidos_por_dia:  # Verificar si la fecha ya está en platos_elegidos_por_dia
            platos_preseleccionados[fecha] = platos_elegidos_por_dia[fecha]
        else:
            platos_preseleccionados[fecha] = {'almuerzo': None, 'cena': None}

    # Convertir el diccionario en una lista de tuplas
    platos_elegidos_por_dia_lista = list(platos_preseleccionados.items())

    contexto = {
                'formulario': form,
                'platos': platos,
                'elegidos': platos_elegidos,
                "tipo_de_vista_estable" :  tipo_de_vista_estable,
                "tipo_de_vista": tipo_de_vista,
                "tipo": tipo_parametro,
                "dias_desde_hoy": dias_desde_hoy,
                "nombre_dia_de_la_semana": nombre_dia_semana,
                "cantidad_platos_sugeridos": cantidad_platos_sugeridos,
                "cantidad_platos_sugeribles": cantidad_platos_sugeribles,
                "platos_a_sugerir":  platos_a_sugerir,
                "platos_elegidos_por_dia": platos_elegidos_por_dia,
                "platos_elegidos_por_dia_lista": platos_elegidos_por_dia_lista,
                "guarniciones_presel": guarniciones_presel,
                "entradas_presel": entradas_presel,
                "principales_presel": principales_presel,
                "tragos_presel": tragos_presel,
                "postres_presel": postres_presel,
                "salsa_presel": salsas_presel,
                "dips_presel": dips_presel
               }

    return render(request, 'AdminVideos/lista_filtrada.html', contexto)


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
    # dia = datetime.strptime(dia, "%Y-%m-%d").strftime("%d-%m-%Y")
    
    # Busca los datos del día seleccionado
    plato_dia = ElegidosXDia.objects.filter(user=request.user, el_dia_en_que_comemos=dia ).first()
    # dia_grabado = plato_dia.el_dia_en_que_comemos

    # platos_elegidos = Elegidos.objects.filter(usuario=request.user).values_list('nombre_plato_elegido', flat=True)
    
    principales_presel = Elegidos.objects.filter(usuario=request.user, tipo_plato="Principal").values_list('nombre_plato_elegido', flat=True)

    guarniciones_presel = Elegidos.objects.filter(usuario=request.user, tipo_plato="Guarnicion").values_list('nombre_plato_elegido', flat=True)

    salsas_presel = Elegidos.objects.filter(usuario=request.user, tipo_plato="Guarnicion").values_list('nombre_plato_elegido', flat=True)

    tragos_presel = Elegidos.objects.filter(usuario=request.user, tipo_plato="Trago").values_list('nombre_plato_elegido', flat=True)

    dips_presel = Elegidos.objects.filter(usuario=request.user, tipo_plato="Dip").values_list('nombre_plato_elegido', flat=True)

    postres_presel = Elegidos.objects.filter(usuario=request.user, tipo_plato="Postre").values_list('nombre_plato_elegido', flat=True)
            
    entradas_presel = Elegidos.objects.filter(usuario=request.user, tipo_plato="Entrada").values_list('nombre_plato_elegido', flat=True)
    
    context = {
        'menu_dia': plato_dia,
        'elegidos': ["Opción 1", "Opción 2", "Opción 3"],  # Ejemplo de lista de platos
        'dia_del_menu': dia,
        "guarniciones_presel": guarniciones_presel,
        "entradas_presel": entradas_presel,
        "principales_presel": principales_presel,
        "tragos_presel": tragos_presel,
        "postres_presel": postres_presel,
        "salsa_presel": salsas_presel,
        "dips_presel": dips_presel,
        
    }
    return render(request, 'AdminVideos/formulario_dia.html', context)

# class MensajeCreate(CreateView):
#   model = Mensaje
#   success_url = reverse_lazy('filtro-de-platos')
#   fields = '__all__'


#class MensajeDelete(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
#   model = Mensaje
#   context_object_name = "mensaje"
#   success_url = reverse_lazy("mensaje-list")

#   def test_func(self):
#       return Mensaje.objects.filter(destinatario=self.request.user).exists()


#class MensajeList(LoginRequiredMixin, ListView):
#   model = Mensaje
#   context_object_name = "mensajes"

 #  def get_queryset(self):
 #      import pdb; pdb.set_trace
 #      return Mensaje.objects.filter(destinatario=self.request.user).all()
