from collections import defaultdict
from itertools import groupby
import locale
from django.contrib import messages  # Para mostrar mensajes al usuario
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.forms import inlineformset_factory
from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from AdminVideos.models import IngredienteEnPlato, Lugar, Plato, Profile, Mensaje,  ElegidosXDia, Sugeridos, TipoPlato
from django.http import Http404, HttpResponseForbidden, JsonResponse
from django.urls import reverse, reverse_lazy
from django.contrib.auth.forms import UserCreationForm
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from datetime import datetime, timedelta
from .forms import IngredienteEnPlatoForm, LugarForm, PlatoFilterForm, PlatoForm, CustomAuthenticationForm
from django.views.generic import TemplateView
from datetime import date, datetime
from django.contrib.auth.models import User  # Asegúrate de importar el modelo User
from django.db.models import Q, Subquery, OuterRef

from django.shortcuts import redirect, reverse
from django.shortcuts import redirect
from django.urls import reverse
import datetime
from django.utils import timezone
from django.views.decorators.http import require_POST




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

class SugerenciasRandom(TemplateView):
    template_name = 'AdminVideos/random.html'

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

    # Obtener el perfil del usuario actual
    perfil = get_object_or_404(Profile, user=request.user)

    # VARIABLES PARA PRUEBAS
    clave_fecha = ""
    variedades_seleccionadas = ""

    if request.method == 'POST':
    
         # Diccionarios auxiliares
        variedades_seleccionadas = defaultdict(set)

        platos_seleccionados = set(request.POST.getlist("plato_seleccionado"))  # Captura todos los valores correctamente
        ingredientes_elegidos = set(request.POST.getlist("ingrediente_a_comprar"))

        # Procesar el formulario - variedades
        for key, value in request.POST.items():
            if key.startswith("variedad_seleccionada"):
                plato_id, variedad = value.split("|")
                variedades_seleccionadas[plato_id].add(variedad)  # No convertir a int
        
        # Recorrer los menús del usuario y actualizar datos
        for menu in menues_del_usuario:
            platos = menu.platos_que_comemos or {}  # Obtener el diccionario de comidas

            for comida, lista_platos in platos.items():

               for plato in lista_platos:  # Recorrer cada plato dentro de la comida
                    plato_id = plato["id_plato"]  # Ahora puedes acceder al ID correctamente
                    clave_fecha = f"{plato_id}_{menu.el_dia_en_que_comemos.strftime('%Y%m%d')}"

                    if clave_fecha in platos_seleccionados:
                        # Marcar como elegido
                        plato["elegido"] = True
                    
                        for variedad_id, variedad_data in plato.get("variedades", {}).items():
                            if variedad_data["nombre"] in variedades_seleccionadas[plato_id]:
                                variedad_data["elegido"] = True
                            
                            else:
                                variedad_data["elegido"] = False
                    else:
                        # Si no fue seleccionado, marcar como no elegido
                        plato["elegido"] = False
                        for variedad in plato.get("variedades", {}).values():
                            variedad["elegido"] = False

            # Guardar cambios en el modelo
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
                if datos.get("elegido"):
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
  

    context = {
        'menues_del_usuario': menues_del_usuario,
        'ingredientes_con_tengo_y_comentario': ingredientes_unicos, # DICT TODOS LOS INGREDIENTES, CON TENGO Y COMENTARIO
        "lista_de_compras": lista_de_compras, # LISTA DE COMPRAS PARA VERLO EN ENVAR A WHATS APP
        "mensaje_whatsapp": mensaje_whatsapp, # MENSAJE FORMATEADO PARA WHATSAPP
        "parametro" : "lista-compras",
        "clave_fecha": clave_fecha,
        # "platos": platos,
        # "variedades_seleccionadas": variedades_seleccionadas,
    
    }

    return render(request, 'AdminVideos/lista_de_compras.html', context)



class PlatoDetail(DetailView):
    model = Plato
    template_name = 'AdminVideos/plato_detail.html'
    context_object_name = "plato"

    def get_context_data(self, **kwargs):
        # Llamar al método original para obtener el contexto base
        context = super().get_context_data(**kwargs)

        # Obtener el perfil del usuario actual
        perfil = get_object_or_404(Profile, user=self.request.user)

        # Pasar la lista de amigues al contexto
        context["amigues"] = perfil.amigues  # Lista JSONField desde Profile

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
    if plato.id_original in perfil.sugeridos_descartados:
        perfil.sugeridos_descartados.remove(plato.id_original)
        perfil.save()

  # Eliminar el plato de la lista de sugeridos_importados si está allí
    if plato.id_original in perfil.sugeridos_importados:
        perfil.sugeridos_importados.remove(plato.id_original)
        perfil.save()

    # Eliminar el plato de la base de datos
    plato.delete()

    # # Eliminar el plato de la base de datos
    # plato.delete()

    return redirect('filtro-de-platos')  # Redirigir a la página de filtro de platos




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


class PlatoUpdate(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Plato
    form_class = PlatoForm
    template_name = 'AdminVideos/plato_ppal_update.html'
    success_url = reverse_lazy("filtro-de-platos")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        variedades_en_base = self.object.variedades or {}

        variedades = {}
        ingredientes_por_variedad = {}

        for key, value in variedades_en_base.items():
            variedad = value.get('nombre', '')
            ingredientes = value.get('ingredientes', '')
            variedades[key] = variedad
            ingredientes_por_variedad[key] = ingredientes

        context['variedades_en_base'] = variedades
        context['ingredientes_variedad'] = ingredientes_por_variedad
        return context

    def test_func(self):
        user_id = self.request.user.id
        plato_id = self.kwargs.get("pk")
        return Plato.objects.filter(propietario=user_id, id=plato_id).exists()

    def form_valid(self, form):
        plato = form.save(commit=False)
        plato.propietario = self.request.user

        # Procesar las variedades del formulario
        variedades = {}
        for i in range(1, 7):
            variedad = form.cleaned_data.get(f'variedad{i}')
            ingredientes = form.cleaned_data.get(f'ingredientes_de_variedad{i}')
            if variedad:
                variedades[f'variedad{i}'] = {
                    'nombre': variedad,
                    'ingredientes': ingredientes
                }

        plato.variedades = variedades
        plato.save()

        # Guardar relaciones ManyToMany (como 'tipos')
        form.save_m2m()

        # return redirect(self.success_url)
        return redirect(f"{reverse('videos-update', kwargs={'pk': plato.pk})}?modificado=ok")



# class PlatoUpdate(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
#     model = Plato
#     form_class = PlatoForm
#     template_name = 'AdminVideos/plato_ppal_update.html'
#     success_url = reverse_lazy("filtro-de-platos")

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)

#         variedades_en_base = self.object.variedades or {}

#         # Crear diccionario para las variedades
#         variedades = {}
#        # Crear diccionario para los ingredientes
#         ingredientes_por_variedad = {}
#         # ingredientes_separados_por_comas = []

#         for key, value in variedades_en_base.items():
#             variedad = value.get('nombre', '')
#             ingredientes_variedad = value.get('ingredientes',"")

#             # Agregar la variedad al diccionario de variedades
#             variedades[key] = variedad

#             # Convertir la lista de ingredientes en una cadena separada por comas
#             # ingredientes_separados_por_comas = ', '.join(ingredientes_variedad)
#             ingredientes_separados_por_comas = ingredientes_variedad


#             # Agregar los ingredientes de esta variedad al diccionario de ingredientes
#             ingredientes_por_variedad[key] = ingredientes_separados_por_comas

#         context['variedades_en_base'] = variedades
#         context['ingredientes_variedad'] = ingredientes_por_variedad

#         return context

#     def test_func(self):
#         user_id = self.request.user.id
#         plato_id = self.kwargs.get("pk")
#         return Plato.objects.filter(propietario=user_id, id=plato_id).exists()


#     def form_valid(self, form):
#         # Guardar el formulario y obtener la instancia del plato
#         plato = form.save(commit=False)
#         plato.propietario = self.request.user

#         # Procesar las variedades ingresadas en el formulario
#         variedades = {}
#         for key, value in self.request.POST.items():
#             if key.startswith('variedad'):
#                 numero_variedad = key.replace('variedad', '')
#                 ingredientes_key = 'ingredientes_de_variedad' + numero_variedad
#                 # if value:
#                 #    ingredientes_variedades = self.request.POST.get(ingredientes_key)

#                 if value:
#                   variedades['variedad' + numero_variedad] = {
#                     'nombre': value,
#                     'ingredientes': self.request.POST.get(ingredientes_key)
#                    }

#         plato.variedades = variedades

#         plato.save()


#         return redirect(self.success_url)


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
    

# IngredienteFormSet = inlineformset_factory(
#     Plato,
#     IngredienteEnPlato,
#     form=IngredienteEnPlatoForm,
#     extra=1,  # Cantidad de formularios vacíos que querés mostrar
#     can_delete=True
# )

# class PlatoCreate(LoginRequiredMixin, CreateView):
#     model = Plato
#     form_class = PlatoForm
#     template_name = 'AdminVideos/platos_update.html'
#     success_url = reverse_lazy("videos-create")

#     def get_template_names(self):
#         template_param = self.request.GET.get('tipopag')

#         templates = {
#             'Entrada': 'AdminVideos/entrada_update.html',
#             'Dip': 'AdminVideos/dip_update.html',
#             'Principal': 'AdminVideos/plato_ppal_update.html',
#             'Dash': 'AdminVideos/plato_ppal_update.html',
#             'Trago': 'AdminVideos/trago_update.html',
#             'Salsa': 'AdminVideos/salsa_update.html',
#             'Guarnicion': 'AdminVideos/guarnicion_update.html',
#             'Postre': 'AdminVideos/postre_update.html',
#             'Delivery': 'AdminVideos/delivery.html',
#             'Comerafuera': 'AdminVideos/comerafuera.html',
#         }

#         return [templates.get(template_param, self.template_name)]

#     def get_initial(self):
#         initial = super().get_initial()
#         template_param = self.request.GET.get('tipopag')

#         # Asignar el valor exacto del choice en "tipo"
#         if template_param in dict(Plato.TIPO_CHOICES).keys():
#             initial['tipo'] = template_param
#         return initial

#     def get_form(self, form_class=None):
#         form = super().get_form(form_class)
#         template_param = self.request.GET.get('tipopag')

#         # Inicializar el campo ManyToMany "tipos" si existe un TipoPlato con ese nombre
#         try:
#             tipo_rel = TipoPlato.objects.get(nombre=template_param)
#             form.fields['tipos'].initial = [tipo_rel.pk]
#         except TipoPlato.DoesNotExist:
#             pass  # No pasa nada si no existe

#         return form

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         if self.request.POST:
#             context['ingrediente_formset'] = IngredienteFormSet(self.request.POST)
#         else:
#             context['ingrediente_formset'] = IngredienteFormSet()
#         return context

#     def form_valid(self, form):
#         # plato = form.save(commit=False)
#         # plato.propietario = self.request.user
#         context = self.get_context_data()
#         ingrediente_formset = context['ingrediente_formset']

#         if ingrediente_formset.is_valid():
#             plato = form.save(commit=False)
#             plato.propietario = self.request.user

#             # Preparar las variedades antes de guardar el objeto
#             variedades = {}
#             for i in range(1, 7):
#                 variedad = form.cleaned_data.get(f'variedad{i}')
#                 ingredientes_variedad_str = form.cleaned_data.get(f'ingredientes_de_variedad{i}')
#                 if variedad:
#                     variedades[f"variedad{i}"] = {
#                         "nombre": variedad,
#                         "ingredientes": ingredientes_variedad_str,
#                         "elegido": True
#                     }

#             plato.variedades = variedades
#             plato.save()
#             form.save_m2m()

#             # Guardar los ingredientes
#             ingrediente_formset.instance = plato
#             ingrediente_formset.save()

#             template_param = self.request.GET.get('tipopag')

#             return redirect(f"{reverse('videos-create')}?tipopag={template_param}&guardado=ok")
#         else:
#            return self.form_invalid(form)
    
#     def form_invalid(self, form):
#         print("Errores en el formulario:", form.errors)
#         return super().form_invalid(form)



# IngredienteFormSet = inlineformset_factory(
#     Plato,
#     IngredienteEnPlato,
#     form=IngredienteEnPlatoForm,
#     extra=1,  # Mostrar solo 1 formulario al inicio
#     can_delete=True
# )


IngredienteFormSet = inlineformset_factory(
    Plato,
    IngredienteEnPlato,
    form=IngredienteEnPlatoForm,
    extra=1,
    can_delete=True
)

class PlatoCreate(LoginRequiredMixin, CreateView):
    model = Plato
    form_class = PlatoForm

    template_name = 'AdminVideos/platos_update.html'
    success_url = reverse_lazy("videos-create")

    def get_template_names(self):
        template_param = self.request.GET.get('tipopag')
        templates = {
            'Entrada': 'AdminVideos/entrada_update.html',
            'Dip': 'AdminVideos/dip_update.html',
            'Principal': 'AdminVideos/plato_ppal_update.html',
            'Dash': 'AdminVideos/plato_ppal_update.html',
            'Trago': 'AdminVideos/trago_update.html',
            'Salsa': 'AdminVideos/salsa_update.html',
            'Guarnicion': 'AdminVideos/guarnicion_update.html',
            'Postre': 'AdminVideos/postre_update.html',
            'Delivery': 'AdminVideos/delivery.html',
            'Comerafuera': 'AdminVideos/comerafuera.html',
        }
        return [templates.get(template_param, self.template_name)]

    def get_initial(self):
        initial = super().get_initial()
        template_param = self.request.GET.get('tipopag')
        if template_param in dict(Plato.TIPO_CHOICES).keys():
            initial['tipo'] = template_param
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        template_param = self.request.GET.get('tipopag')
        try:
            tipo_rel = TipoPlato.objects.get(nombre=template_param)
            form.fields['tipos'].initial = [tipo_rel.pk]
        except TipoPlato.DoesNotExist:
            pass
        return form
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.method == 'POST':
            context['ingrediente_formset'] = IngredienteFormSet(self.request.POST)
        else:
            context['ingrediente_formset'] = IngredienteFormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        ingrediente_formset = context['ingrediente_formset']

        if ingrediente_formset.is_valid():
            plato = form.save(commit=False)
            plato.propietario = self.request.user

            # Preparar variedades
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

            template_param = self.request.GET.get('tipopag')
            return redirect(f"{reverse('videos-create')}?tipopag={template_param}&guardado=ok")
        else:
            return self.render_to_response(self.get_context_data(form=form))
        
    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        print("Errores del formulario principal:")
        print(form.errors)

        ingrediente_formset = context.get('ingrediente_formset')
        if ingrediente_formset:
            print("Errores del formset de ingredientes:")
            for i, f in enumerate(ingrediente_formset.forms):
                if f.errors:
                    print(f"Errores en el formulario #{i}: {f.errors}")
        
        return self.render_to_response(context)

        
    # def form_invalid(self, form):
    #     context = self.get_context_data(form=form)

    #     print("Errores del formulario principal:")
    #     print(form.errors)

    #     ingrediente_formset = context.get('ingrediente_formset')
    #     if ingrediente_formset:
    #         print("Errores del formset de ingredientes:")
    #         print(ingrediente_formset.errors)

    #     return self.render_to_response(context)
        

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

        if tipo_parametro and tipo_parametro != "Dash":
            query &= Q(tipo=tipo_parametro)

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
    # locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')

    locale.setlocale(locale.LC_TIME, 'C')

    
    # Obtener la fecha y hora actuales
    fecha_actual = datetime.datetime.now().date()

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
            "descripcion": los_platos_compartidos[msg.id_elemento].descripcion_plato if msg.id_elemento in los_platos_compartidos else "",
            "ingredientes": los_platos_compartidos[msg.id_elemento].ingredientes if msg.id_elemento in los_platos_compartidos else "",
            "tipo": los_platos_compartidos[msg.id_elemento].tipo if msg.id_elemento in los_platos_compartidos else "",
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

        for comida, lista_platos in pla.items():  # Iterar comidas (desayuno, almuerzo, etc.)
            for plato in lista_platos:  # Iterar cada plato dentro de la lista
                plato_nombre = plato.get('plato', 'Desconocido')

                # Añadir a la lista de la comida correspondiente
                if comida in platos_dia_x_dia[fec]:  
                    platos_dia_x_dia[fec][comida].append(plato_nombre)

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
                "lugares": lugares

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
        descripcion_plato=plato_original.descripcion_plato,
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


def agregar_a_mi_lista(request, plato_id):
    # Obtener el plato a copiar
    plato_original = get_object_or_404(Plato, id=plato_id)

    # Obtener el perfil del usuario logueado
    profile = request.user.profile

    # Lee el parámetro GET
    duplicar = request.GET.get('duplicar') == 'true'

    # Determina el nombre del nuevo plato
    nombre_copia = f"Copia de {plato_original.nombre_plato}" if duplicar else plato_original.nombre_plato


    # Verificar si el plato original pertenece a otro usuario
    proviene_de = plato_original.propietario if plato_original.propietario != request.user else None
    

    # Crear una copia del plato, asignando el nuevo propietario
    nuevo_plato = Plato.objects.create(
        nombre_plato=nombre_copia,
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
        proviene_de= proviene_de,
        id_original=plato_original.id         
    )

  # Verificar si el plato_id ya está en la lista para evitar duplicados
    if plato_original.nombre_plato not in profile.sugeridos_importados:
        profile.sugeridos_importados.append(plato_id)  # Agregar el ID del plato a la lista
        profile.save()  # Guardar los cambios en el perfil

    # Redirigir a la vista para descartar el plato después de agregarlo
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
                    "tipo": plato.tipo,
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

        # menu_dia.save()
        # return redirect('filtro-de-platos')


# class AsignarPlato(View):
    
#     def post(self, request):
#         plato_id = request.POST.get('plato_id')
#         dia = request.POST.get('dia')
#         comida = request.POST.get('comida')

#         # Buscar el plato
#         try:
#             plato = Plato.objects.get(id=plato_id)
#         except Plato.DoesNotExist:
#             messages.error(request, "El plato no existe.")
#             return redirect('filtro-de-platos')

#         # Convertir el string de fecha a objeto date
#         fecha_comida = datetime.datetime.strptime(dia, "%Y-%m-%d").date()

#         # Guardar la fecha en la sesión para recordar la pestaña activa
#         request.session['dia_activo'] = dia  

#         # Buscar o crear el registro del día
#         menu_dia, created = ElegidosXDia.objects.get_or_create(
#             user=request.user,
#             el_dia_en_que_comemos=fecha_comida,
#             defaults={"platos_que_comemos": {}}
#         ) # menu_dia es un OBJETO DE LA BASE DE DATOS

#         # Verificar si ya hay un plato con la misma comida en ese día
#         platos_que_comemos = menu_dia.platos_que_comemos  # Diccionario almacenado en la BD - PLATOS QUE COMEMOS ES UN DICCIONARIO CON LOS DATOS DE ESE OBJETO DE LA BD

#         # Asegurar que `comida` sea una lista en `platos_que_comemos`
#         if not isinstance(platos_que_comemos.get(comida), list):
#             platos_que_comemos[comida] = []
       
#        # Verificar si el plato ya está en la lista
#         if any(plato["id_plato"] == plato_id for plato in platos_que_comemos[comida]):
#             messages.warning(request, f"El plato {plato.nombre_plato} ya está asignado a {comida}.")
#         else:
#             # Agregar el nuevo plato a la lista
#             platos_que_comemos[comida].append({
#                 "id_plato": plato_id,
#                 "plato": plato.nombre_plato,
#                 "tipo": plato.tipo,
#                 "ingredientes": plato.ingredientes,
#                 "variedades": {variedad_id: {"nombre": datos["nombre"], "ingredientes": datos["ingredientes"], "elegido": True}
#                    for variedad_id, datos in plato.variedades.items()},  # Agrega elegido: True a cada variedad
#                 "elegido": True
#             })
            
#         # Guardar los cambios en la base de datos
#         menu_dia.platos_que_comemos = platos_que_comemos
#         menu_dia.save()
#         messages.success(request, f"Plato {plato.nombre_plato} asignado correctamente a {comida}.")
            
#         return redirect('filtro-de-platos')




def eliminar_programado(request, nombre_plato, comida, fecha):
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
    
    return redirect('filtro-de-platos')

