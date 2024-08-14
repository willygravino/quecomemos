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
from django.urls import reverse_lazy
from django.contrib.auth.forms import UserCreationForm
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from datetime import datetime, timedelta
from .forms import PlatoFilterForm, PlatoForm
from django.views.generic import TemplateView
from datetime import date
import datetime




class SugerenciasRandom(TemplateView):
    template_name = 'AdminVideos/random.html'


def index(request):
     return render(request, "AdminVideos/lista_filtrada.html")

# def index(request: HttpRequest):
#     # Ejecuta la función FiltroDePlatos y obtén el resultado
#     resultado_filtro = FiltroDePlatos(request)

#     # Devuelve el resultado obtenido
#     return resultado_filtro

def about(request):
    return render(request, "AdminVideos/about.html")

def plato_elegido(request):
    if request.method == 'GET':
        nombre_plato = request.GET.get('opcion1')
        borrar = request.GET.get('borrar')

        usuario = request.user  # Obtener el usuario logueado

        if borrar == "borrar":
            # Eliminar el plato de la lista de platos elegidos
            Elegidos.objects.filter(usuario=usuario, nombre_plato_elegido=nombre_plato).delete()
        else:
            # Agregar el plato a la lista de platos elegidos
            Elegidos.objects.get_or_create(usuario=usuario, nombre_plato_elegido=nombre_plato)

        # Redirigir a la página deseada
        return redirect(reverse_lazy("filtro-de-platos"))
    else:
        # Manejar solicitudes POST u otras solicitudes que no sean GET
        return JsonResponse({"error": "Método no permitido"}, status=405)


def grabar_menu_elegido(request):
    if request.method == 'POST':
        # Obtener el usuario logueado
        usuario = request.user

        # Obtener las fechas y platos elegidos del formulario
        for i in range(1, 8):
            fecha = request.POST.get(f"fecha-{i}")
            almuerzo = request.POST.get(f"{i}-a")
            cena = request.POST.get(f"{i}-c")

            registro_existente = ElegidosXDia.objects.filter(user=usuario, el_dia_en_que_comemos=fecha).first()

            if registro_existente:
                    registro_existente.delete()

            # Verificar si se recibieron datos del formulario
            if almuerzo != '-----' or cena != '-----':
                # Consultar si ya existe un registro para esta fecha y este usuario
                # registro_existente = ElegidosXDia.objects.filter(user=usuario, el_dia_en_que_comemos=fecha).first()

                almuerzo_queryset = Plato.objects.filter(nombre_plato=almuerzo).values("ingredientes", "variedades")
                almuerzo_result = almuerzo_queryset.first()
                almuerzo_variedades = almuerzo_result['variedades'] if almuerzo_result else None
                almuerzo_ingredientes = almuerzo_result['ingredientes'] if almuerzo_result else None
               
                #  BUCLE PARA SUMAR EL CAMPO "ELEGIDOS A CADA PLATO Y VARIEDAD"
                variedad_almuerzo_con_elegidos = {}
                if almuerzo_variedades:
                    for variedad, detalles_variedad in almuerzo_variedades.items():
                        # variedad es la clave y detalles_variedad es el valor (otro diccionario)
                        variedad_almuerzo_con_elegidos[variedad] = {
                            "variedad": detalles_variedad.get("variedad", ""),
                            "ingredientes_de_variedades": detalles_variedad.get("ingredientes_de_variedades", []),
                            "elegido": True
                        }

                # cena
                cena_queryset = Plato.objects.filter(nombre_plato=cena).values("ingredientes", "variedades")
                cena_result = cena_queryset.first()
                cena_variedades = cena_result['variedades'] if cena_result else None
                cena_ingredientes = cena_result['ingredientes'] if cena_result else None

                 
                #  BUCLE PARA SUMAR EL CAMPO "ELEGIDOS A CADA PLATO Y VARIEDAD"
                variedad_cena_con_elegidos = {}
                if cena_variedades:
                    for variedad, detalles_variedad in cena_variedades.items():
                        # variedad es la clave y detalles_variedad es el valor (otro diccionario)
                        variedad_cena_con_elegidos[variedad] = {
                            "variedad": detalles_variedad.get("variedad", ""),
                            "ingredientes_de_variedades": detalles_variedad.get("ingredientes_de_variedades", []),
                            "elegido": True
                        }

                # Crear una lista de platos para este día

                platos_del_dia = { "almuerzo": {"plato": almuerzo,"ingredientes": almuerzo_ingredientes,"elegido": True}, "variedades_almuerzo": variedad_almuerzo_con_elegidos,'cena':{"plato": cena,"ingredientes": cena_ingredientes, "elegido":True}, 'variedades_cena': variedad_cena_con_elegidos}

                        # Crear una instancia del modelo ElegidosXDia y guardar en la base de datos
                ElegidosXDia.objects.create(user=usuario,el_dia_en_que_comemos=fecha,platos_que_comemos=platos_del_dia)
                    
               # Redirigir al usuario a la página de menú elegido
        return redirect(reverse_lazy("menu-elegido"))
    else:
        # Retorna una respuesta JSON con un mensaje de error si el método no es POST
        return JsonResponse({'error': 'El método de solicitud debe ser POST'})








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

    # Obtener el perfil del usuario actual
    perfil = get_object_or_404(Profile, user=request.user)
    
    if request.method == 'POST':
                lista_de_compras = request.POST.getlist("ingrediente_a_comprar")

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
                          ingredientes = almuerzo_info
                          lista_de_ingredientes.update({ingrediente.strip() for ingrediente in ingredientes.split(',')})
                     
                    else: almuerzo_elegido = False

                    cena_que_comemos = platos_dia.get("cena", {}).get("plato", [])
                    cena_info = platos_dia.get("cena", {}).get("ingredientes", [])
                    # Convertir dia_en_que_comemos a cadena con un formato específico
                    dia_en_que_comemos_str = objeto.el_dia_en_que_comemos.strftime('%d %b. %Y')
                    # Concatenar el valor de 'dia_en_que_comemos' a 'variedad_value["variedad"]'
                    buscar_cena_por_dia = cena_que_comemos + dia_en_que_comemos_str
                    if buscar_cena_por_dia in request.POST:
                          cena_elegida = True
                          ingredientes = cena_info
                        #   lista_de_ingredientes = [ingrediente.strip() for ingrediente in ingredientes.split(',')]
                          lista_de_ingredientes.update({ingrediente.strip() for ingrediente in ingredientes.split(',')})
                          #   ingredientes_unicos.update(cena_info.split(", "))
                    else: cena_elegida = False

                    almuerzo_variedades = platos_dia.get("variedades_almuerzo", {})
                    if almuerzo_variedades:
                           
                            for variedad_key, variedad_value in almuerzo_variedades.items():
                                  # Convertir dia_en_que_comemos a cadena con un formato específico
                                dia_en_que_comemos_str = objeto.el_dia_en_que_comemos.strftime('%d %b. %Y')
                                 # Concatenar el valor de 'dia_en_que_comemos' a 'variedad_value["variedad"]'
                                buscar_variedad_por_dia = variedad_value["variedad"] + dia_en_que_comemos_str
                                if buscar_variedad_por_dia in request.POST:
                                   almuerzo_variedades[variedad_key]["elegido"] = True
                                   ingredientes = variedad_value['ingredientes_de_variedades']
                                #    lista_de_ingredientes = [ingrediente.strip() for ingrediente in ingredientes.split(',')]
                                   lista_de_ingredientes.update({ingrediente.strip() for ingrediente in ingredientes.split(',')})
                                #    ingredientes_unicos.update(variedad_value["ingredientes_de_variedades"].split(", "))
                                else: almuerzo_variedades[variedad_key]["elegido"] = False
                                                     
                    cena_variedades = platos_dia.get("variedades_cena", {})

                    if cena_variedades:

                            for variedad_key, variedad_value in cena_variedades.items():
                                 # Convertir dia_en_que_comemos a cadena con un formato específico
                                dia_en_que_comemos_str = objeto.el_dia_en_que_comemos.strftime('%d %b. %Y')
                                 # Concatenar el valor de 'dia_en_que_comemos' a 'variedad_value["variedad"]'
                                buscar_variedad_por_dia = variedad_value["variedad"] + dia_en_que_comemos_str
                                if buscar_variedad_por_dia in request.POST:                                
                                   cena_variedades[variedad_key]["elegido"] = True
                                   ingredientes = variedad_value['ingredientes_de_variedades']
                                #    lista_de_ingredientes = [ingrediente.strip() for ingrediente in ingredientes.split(',')]
                                   lista_de_ingredientes.update({ingrediente.strip() for ingrediente in ingredientes.split(',')}) 
                                 #    ingredientes_unicos.update(variedad_value["ingredientes_de_variedades"].split(", "))
                                else:  cena_variedades[variedad_key]["elegido"] = False
                    
                    set_compras = set(lista_de_compras)
                    # Identificar elementos que están en lista_de_ingredientes pero no en set_compras
                    ingredientes_no_comprados = lista_de_ingredientes - set_compras


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
            almuerzo_elegido = platos_dia.get("almuerzo", {}).get("elegido", [])

            cena_que_comemos = platos_dia.get("cena", {}).get("plato", [])
            cena_info = platos_dia.get("cena", {}).get("ingredientes", [])
            cena_elegida = platos_dia.get("cena", {}).get("elegido", [])
           
            almuerzo_variedades = platos_dia.get("variedades_almuerzo", {})

            # Iterar a través del diccionario y extraer los ingredientes
            if almuerzo_variedades:
                for key, value in almuerzo_variedades.items():
                    ingredientes = value['ingredientes_de_variedades']
                    lista_de_ingredientes.update({ingrediente.strip() for ingrediente in ingredientes.split(',')})
                        
            cena_variedades = platos_dia.get("variedades_cena", {})

            # Iterar a través del diccionario y extraer los ingredientes
            if cena_variedades:
                for key, value in cena_variedades.items():
                    ingredientes = value['ingredientes_de_variedades']
                    lista_de_ingredientes.update({ingrediente.strip() for ingrediente in ingredientes.split(',')})

           
            if almuerzo_info:
                     lista_de_ingredientes.update({ingrediente.strip() for ingrediente in almuerzo_info.split(',')})


                
            if cena_info:
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
                "almuerzo_elegido": almuerzo_elegido,
                "cena": cena_que_comemos,
                "cena_elegida": cena_elegida,
                "almuerzo_info": almuerzo_info,
                "cena_info": cena_info,
                "variedades": almuerzo_variedades,
                "variedades_cena": cena_variedades
            }
        
    context = {
        'platos_por_dia': platos_por_dia,
        'ingredientes_separados_por_comas': ingredientes_unicos,
        'post_data': request.POST,
        "lista_de_compras": lista_de_compras,
        "ingredientes_no_comprados": ingredientes_no_comprados
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
    success_url = reverse_lazy("filtro-de-platos")
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
    return render(request, 'registration/logout.html', {})

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
    tipo = request.session.get('tipo_estable', "None")
    calorias = request.session.get('calorias_estable', "None")

    # items_iniciales = ""

    # platos = Plato.objects.all()
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
                tipo = form.cleaned_data.get('tipo')
                calorias = form.cleaned_data.get('calorias')

                # Guardar el valor de tipo_de_vista en la sesión
                request.session['tipo_de_vista_estable'] =  tipo_de_vista
                tipo_de_vista_estable = tipo_de_vista
                request.session['medios_estable'] = medios
                request.session['categoria_estable'] = categoria
                request.session['preparacion_estable'] = preparacion
                request.session['tipo_estable'] = tipo
                request.session['calorias_estable'] = calorias

                # items_iniciales = {
                #         'tipo_de_vista_estable': tipo_de_vista_estable,
                #         'medios_estable': medios_estable,
                #         'categoria_estable': categoria, # OJO QUE ESTA FUNCIONA SIN NECESIDAD DE USAR "_ESTABLE, ESTOY DERROCHANDO VARIABLES ESTABLES (seguire usando así)?"
                #         'preparacion_estable': preparacion,
                #         'tipo_estable': tipo,
                #         # 'tipo_de_vista_estable': tipo_de_vista_estable,
                #         'calorias_estable': calorias
                #     }

    else:
        pasa_por_aca = "PASA POR NO-POST"
        items_iniciales = {
                        'tipo_de_vista': tipo_de_vista_estable,
                        'medios': medios,
                        'categoria': categoria,
                        'preparacion': preparacion,
                        'tipo': tipo,
                        'calorias': calorias
                    }
        post_o_no = "NO POST, MANDA INICIALES"+tipo_de_vista_estable
        form = PlatoFilterForm(initial=items_iniciales)

    pasa_por_aca = "PASA"

    platos = Plato.objects.all()

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
        if tipo and tipo != '-':
            platos = platos.filter(tipo=tipo)
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
                'form': form,
                'platos': platos,
                'elegidos': platos_elegidos,
                "tipo_de_vista_estable" :  tipo_de_vista_estable,
                "tipo_de_vista": tipo_de_vista,
                "por_donde_pasa": pasa_por_aca,
                "dias_desde_hoy": dias_desde_hoy,
                "nombre_dia_de_la_semana": nombre_dia_semana,
                "cantidad_platos_sugeridos": cantidad_platos_sugeridos,
                "cantidad_platos_sugeribles": cantidad_platos_sugeribles,
                "platos_a_sugerir":  platos_a_sugerir,
                "hubo_post_o_no": post_o_no,
                "platos_elegidos_por_dia": platos_elegidos_por_dia,
                "platos_elegidos_por_dia_lista": platos_elegidos_por_dia_lista
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
