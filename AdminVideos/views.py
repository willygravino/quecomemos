from contextvars import Context
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

            # Verificar si se recibieron datos del formulario
            if almuerzo != '-----' or cena != '-----':
                # Consultar si ya existe un registro para esta fecha y este usuario
                registro_existente = ElegidosXDia.objects.filter(user=usuario, el_dia_en_que_comemos=fecha).first()

                if registro_existente:
                    # Actualizar el registro existente
                    registro_existente.platos_que_comemos = {'almuerzo': almuerzo, 'cena': cena}
                    registro_existente.save()
                else:
                    # Crear una lista de platos para este día
                    platos_del_dia = {'almuerzo': almuerzo, 'cena': cena}

                    # Crear una instancia del modelo ElegidosXDia y guardar en la base de datos
                    ElegidosXDia.objects.create(
                        user=usuario,
                        el_dia_en_que_comemos=fecha,
                        platos_que_comemos=platos_del_dia
                    )

        # Redirigir al usuario a la página de menú elegido
        return redirect(reverse_lazy("menu-elegido"))
    else:
        # Retorna una respuesta JSON con un mensaje de error si el método no es POST
        return JsonResponse({'error': 'El método de solicitud debe ser POST'})







@login_required
def menu_elegido(request):
    # Obtener la fecha actual
    today = date.today()
    # Filtrar los objetos de ElegidosXDia para excluir aquellos cuya fecha sea anterior a la fecha actual
    objetos_del_usuario = ElegidosXDia.objects.filter(user=request.user, el_dia_en_que_comemos__gte=today).order_by('el_dia_en_que_comemos')
    platos_por_dia = {}
    ingredientes_unicos = set()  # Conjunto para almacenar ingredientes únicos
    # Inicializar las listas de ingredientes a excluir
    ingredientes_a_excluir_almuerzo = []
    ingredientes_a_excluir_cena = []

    for objeto in objetos_del_usuario:
        platos_dia = objeto.platos_que_comemos
        almuerzo_que_comemos = platos_dia.get("almuerzo", [])
        cena_que_comemos = platos_dia.get("cena", [])

        almuerzo_info_queryset = Plato.objects.filter(nombre_plato=almuerzo_que_comemos).values("ingredientes", "variedades")
        almuerzo_info_result = almuerzo_info_queryset.first()
        almuerzo_info = almuerzo_info_queryset.first()['ingredientes'] if almuerzo_info_queryset.exists() else ""

        almuerzo_variedades = almuerzo_info_result['variedades'] if almuerzo_info_result else None


        cena_info_queryset = Plato.objects.filter(nombre_plato=cena_que_comemos).values("ingredientes")
        cena_info = cena_info_queryset.first()['ingredientes'] if cena_info_queryset.exists() else ""

        if almuerzo_info:
            ingredientes_unicos.update(almuerzo_info.split(", "))
        if cena_info:
            ingredientes_unicos.update(cena_info.split(", "))

        if not cena_info:
            cena_info = ""
        if not almuerzo_info:
            almuerzo_info = ""


        platos_por_dia[objeto.el_dia_en_que_comemos] = {
            "almuerzo": almuerzo_que_comemos,
            "cena": cena_que_comemos,
            "almuerzo_info": almuerzo_info,
            "cena_info": cena_info,
            "variedades": almuerzo_variedades
        }

    lista_de_compras = []

    if request.method == 'POST':
        for key, value in request.POST.items():
            if key.startswith('incluir'):
                # Aquí obtienes los ingredientes seleccionados del formulario
                ingredientes_variedades_a_sumar = request.POST.getlist(key)  # Obtener la lista completa de ingredientes
                  # Convertir la cadena de ingredientes a una lista separada por comas
                    # Eliminar corchetes y comillas de la cadena si es necesario
                ingredientes_variedades_a_sumar = [ingrediente.strip("[]' ") for ingrediente in ingredientes_variedades_a_sumar]

                ingredientes_variedades_a_sumar = ",".join(ingredientes_variedades_a_sumar)
                # Dividir la cadena en elementos individuales
                ingredientes_variedades_a_sumar = [ingrediente.strip() for ingrediente in ingredientes_variedades_a_sumar.split(",")]
                # Agregar los ingredientes seleccionados a la lista de ingredientes únicos
                ingredientes_unicos.update(ingredientes_variedades_a_sumar)

        ingredientes_seleccionados = request.POST.getlist('ingrediente_a_comprar')
        ingredientes_a_excluir_almuerzo_str = request.POST.get('excluir_almuerzo')
        ingredientes_a_excluir_cena_str = request.POST.get('excluir_cena')

        # Convertir las cadenas de ingredientes a excluir en listas si existen
        ingredientes_a_excluir_almuerzo = ingredientes_a_excluir_almuerzo_str.split(', ') if ingredientes_a_excluir_almuerzo_str else []
        ingredientes_a_excluir_cena = ingredientes_a_excluir_cena_str.split(', ') if ingredientes_a_excluir_cena_str else []

        # Agrega los ingredientes seleccionados que no están excluidos a la lista de compras
        for ingrediente in ingredientes_seleccionados:
            if ingrediente not in ingredientes_a_excluir_almuerzo and ingrediente not in ingredientes_a_excluir_cena:
                lista_de_compras.append(ingrediente)


    # Excluir los ingredientes de las listas de exclusión del conjunto de ingredientes únicos
    for ingrediente_excluir in ingredientes_a_excluir_almuerzo + ingredientes_a_excluir_cena:
        ingredientes_unicos.discard(ingrediente_excluir)

    context = {
        'platos_por_dia': platos_por_dia,
        'ingredientes_separados_por_comas': ingredientes_unicos,
        "lista_de_compras": lista_de_compras,
        "ingredientes_a_excluir_cena": ingredientes_a_excluir_cena,
        "ingredientes_a_excluir_almuerzo": ingredientes_a_excluir_almuerzo,
    }

    return render(request, 'AdminVideos/menu_elegido.html', context)





def lista_de_compras(request):
    if request.method == 'POST':
        ingredientes_seleccionados = request.POST.getlist('ingrediente_a_comprar')

        lista_de_compras = []
        for ingrediente in ingredientes_seleccionados:
            # Por ejemplo, aquí podrías guardar los ingredientes en la variable lista_de_compras
            lista_de_compras.append(ingrediente)

        # Ahora puedes hacer lo que necesites con la lista_de_compras, como guardarla en la base de datos o realizar otras operaciones

        # Finalmente, puedes redirigir a una página de éxito o renderizar un nuevo template
        return render(request, 'AdminVideos/menu_elegido.html', {'lista_de_compras': lista_de_compras})
    else:
        # Si es una solicitud GET, simplemente renderiza el formulario
        return redirect('menu-elegido', lista_compras=','.join(lista_de_compras))











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

        for key, value in variedades_en_base.items():
            variedad = value.get('variedad', '')
            ingredientes_variedad = value.get('ingredientes_variedades', [])

            # Agregar la variedad al diccionario de variedades
            variedades[key] = variedad

            # Convertir la lista de ingredientes en una cadena separada por comas
            ingredientes_separados_por_comas = ', '.join(ingredientes_variedad)

            # Agregar los ingredientes de esta variedad al diccionario de ingredientes
            ingredientes_por_variedad[key] = ingredientes_separados_por_comas

        context['variedades_en_base'] = variedades
        context['ingredientes_variedad'] = ingredientes_por_variedad

        return context

    # def get_context_data(self, **kwargs):
    #      context = super().get_context_data(**kwargs)
    #      context['variedades_en_base'] = self.object.variedades or {}
    #      return context


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
                if value:
                   ingredientes_variedades = self.request.POST.get(ingredientes_key)
                    # Convertir la cadena de ingredientes en una lista
                    # Convertir la cadena de ingredientes en una lista
                   lista_ingredientes = [ingrediente.strip() for ingrediente in ingredientes_variedades.split(',')] if ingredientes_variedades else []

                   variedades['variedad' + numero_variedad] = {
                        'variedad': value,
                        'ingredientes_variedades': lista_ingredientes
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
            ingredientes_variedad = [ingrediente.strip() for ingrediente in ingredientes_variedad_str.split(',')] if ingredientes_variedad_str else []

            if variedad:  # Verificar si la variedad no está vacía
                variedades[f"variedad{i}"] = {"variedad": variedad, "ingredientes_de_variedades": ingredientes_variedad}

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


class PaginaInicial (TemplateView):  # LoginRequiredMixin?????
    model = Plato


def FiltroDePlatos (request):

    # Establecer la configuración regional a español
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')

    # Obtiene la fecha actual
    fecha_actual = datetime.now().date()

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
                "hubo_post_o_no": post_o_no
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
