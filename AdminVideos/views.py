from contextvars import Context
from django.shortcuts import render, redirect
from AdminVideos.models import Plato, Profile, Mensaje, Elegidos, ElegidosXSemana
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.contrib.auth.forms import UserCreationForm
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from datetime import datetime
from .forms import PlatoFilterForm
from django.views.generic import TemplateView


def index(request):
    return render(request, "AdminVideos/index.html")

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
        return redirect(reverse_lazy("videos-list"))
    else:
        # Manejar solicitudes POST u otras solicitudes que no sean GET
        return JsonResponse({"error": "Método no permitido"}, status=405)


class PlatoList(ListView):
    model = Plato
    context_object_name = "platos"
    template_name = 'AdminVideos/lista_filtrada.html'

    # query = None

    def get_queryset(self):
        # self.query = "tomatelas"
        if self.request.user.is_authenticated:
            try:
                if self.request.user.profile:
                        self.query = self.request.GET.get("la-busqueda")
                        if self.query:
                            object_list = Plato.objects.filter(ingredientes__icontains=self.query)
                        return object_list
            except Exception:
            #    object_list = Plato.objects.filter(ingredientes__icontains="%%")
               object_list = Plato.objects.all()
            return object_list
        else:
            # object_list = Plato.objects.filter(ingredientes__icontains="%%")
            object_list = Plato.objects.all()
        return object_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obtener objetos de Elegidos asociados al usuario logueado
        usuario = self.request.user
        elegidos = Elegidos.objects.filter(usuario=usuario)

        # Obtener solo los nombres de los platos seleccionados
        nombres_platos_elegidos = [e.nombre_plato_elegido for e in elegidos]

        # Pasar query y nombres de platos seleccionados al contexto
        # context['query'] = self.query if self.query else "tomate"
        context['elegidos'] = nombres_platos_elegidos

        return context


def grabar_menu_elegido(request):
    if request.method == 'POST':
        # Obtén los datos del formulario
        fecha_actual = request.POST.get('fecha_actual')
        datos = {
            'lunes_a': request.POST.get('lunes-a'),
            'lunes_c': request.POST.get('lunes-c'),
            'martes_a': request.POST.get('martes-a'),
            'martes_c': request.POST.get('martes-c'),
            'miercoles_a': request.POST.get('miercoles-a'),
            'miercoles_c': request.POST.get('miercoles-c'),
            'jueves_a': request.POST.get('jueves-a'),
            'jueves_c': request.POST.get('jueves-c'),
            'viernes_a': request.POST.get('viernes-a'),
            'viernes_c': request.POST.get('viernes-c'),
            'sabado_a': request.POST.get('sabado-a'),
            'sabado_c': request.POST.get('sabado-c'),
            'domingo_a': request.POST.get('domingo-a'),
            'domingo_c': request.POST.get('domingo-c')
        }

        # Crea un diccionario con la fecha como clave y los datos como valor
        datos_por_dia = {fecha_actual: datos}

        # Crea una instancia del modelo ElegidosPorDia con el diccionario de datos
        elegidos_por_semana_objeto = ElegidosXSemana(elegidos_por_semana=datos_por_dia)

        # Guarda la instancia del modelo en la base de datos
        elegidos_por_semana_objeto.save()

        # Retorna una respuesta JSON
        return redirect(reverse_lazy("menu-elegido"))
    else:
        # Retorna una respuesta JSON con un mensaje de error si el método no es POST
        return JsonResponse({'error': 'El método de solicitud debe ser POST'})

class MenuElegido (CreateView):
    model = ElegidosXSemana
    fields = ["elegidos_por_semana"]
    template_name = 'AdminVideos/menu_elegido.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ultimo_objeto = ElegidosXSemana.objects.latest('id')
        context['ultimo_elegido'] = "seleccionados"
        if ultimo_objeto is not None:
           datos_json = ultimo_objeto.elegidos_por_semana
           context['elegidos_semanal'] = datos_json
        else: context['elegidos_semanal'] = "poroto"
        return context

def elecion_de_lista (request):
    if request.method == 'GET':
        tipo_de_vista = request.GET.get('tipo-de-vista', None)
        if tipo_de_vista == 'todos':
            return redirect('videos-list')
        elif tipo_de_vista == 'seleccionados':
            return redirect('platos-elegidos')
        elif tipo_de_vista == 'de-otros':
            return redirect('platos-de-otros')
        elif tipo_de_vista == 'solo-mios':
            return redirect('videos-mine')
        else:
            # Redirige a alguna vista predeterminada si el tipo de vista no está definido
            return redirect('videos-list')

class PlatosMineList(LoginRequiredMixin, PlatoList):
    model = Plato
    # template_name = 'AdminVideos/videosmine_list.html'
    template_name = 'AdminVideos/lista_filtrada.html'


    def get_queryset(self):
      platos_elegidos = Plato.objects.filter(propietario_id=self.request.user.id)
      return platos_elegidos

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ultimo_elegido'] = 'solo-mios'
        return context

class PlatosDeOtros(LoginRequiredMixin, PlatoList):
    model = Plato
    # template_name = 'AdminVideos/videosmine_list.html'
    template_name = 'AdminVideos/lista_filtrada.html'


    def get_queryset(self):
      platos_de_otros = Plato.objects.exclude(propietario_id=self.request.user.id)
      return platos_de_otros

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ultimo_elegido'] = 'de-otros'
        return context

class PlatosElegidosMenu(LoginRequiredMixin, PlatoList):
    # template_name = 'AdminVideos/plato_list.html'
    # template_name = 'AdminVideos/videosmine_list.html'
    template_name = 'AdminVideos/lista_filtrada.html'
    context_object_name = 'platos'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener el usuario logueado
        usuario = self.request.user
        
        # Obtener los nombres de los platos elegidos por el usuario logueado
        nombres_platos_elegidos = Elegidos.objects.filter(usuario=usuario).values_list('nombre_plato_elegido', flat=True)
        
        # Filtrar los platos según los nombres obtenidos
        platos_elegidos = Plato.objects.filter(nombre_plato__in=nombres_platos_elegidos)
        
        context['platos'] = platos_elegidos
        context['ultimo_elegido'] = 'seleccionados'
        
        return context

class PlatoDetail(DetailView):
    model = Plato
    context_object_name = "plato"

class PlatoUpdate(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Plato
    success_url = reverse_lazy("videos-list")
    fields = ["nombre_plato","receta","descripcion_plato","ingredientes","medios","categoria","tipo","calorias","image"]

    def test_func(self):
        user_id = self.request.user.id
        plato_id =  self.kwargs.get("pk")
        return Plato.objects.filter(propietario=user_id, id=plato_id).exists()

class PlatoDelete(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Plato
    context_object_name = "plato"
    success_url = reverse_lazy("videos-list")

    def test_func(self):
        user_id = self.request.user.id
        plato_id =  self.kwargs.get("pk")
        return Plato.objects.filter(propietario=user_id, id=plato_id).exists()


class PlatoCreate(LoginRequiredMixin, CreateView):
    model = Plato
    success_url = reverse_lazy("videos-list")
    fields = ["nombre_plato","receta","descripcion_plato","ingredientes","medios","categoria","preparacion", "tipo","calorias","image"]
#    fields = '__all__'

    def form_valid(self, form):
        el_propietario = form.save(commit=False)
        el_propietario.propietario = self.request.user
        el_propietario.save()
        return redirect(self.success_url)

class Login(LoginView):
    next_page = reverse_lazy("videos-list")


class SignUp(CreateView):
    form_class = UserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('videos-list')


class Logout(LogoutView):
    template_name = "registration/logout.html"


class ProfileCreate(LoginRequiredMixin, CreateView):
    model = Profile
    success_url = reverse_lazy("videos-list")
    fields = ["nombre_completo","avatar"]

    def form_valid(self, form):
        el_user = form.save(commit=False)
        el_user.user = self.request.user
        el_user.save()
        return redirect(self.success_url)


class ProfileUpdate(LoginRequiredMixin, UserPassesTestMixin,  UpdateView):
    model = Profile
    success_url = reverse_lazy("videos-list")
    fields = ["nombre_completo","avatar"]

    def test_func(self):
        return Profile.objects.filter(user=self.request.user).exists()
    
class FiltrarPlatos(LoginRequiredMixin, PlatoList):
    def get(self, request):
        form = PlatoFilterForm(request.GET)
        platos = Plato.objects.all()
        platos_elegidos = None
        usuario = self.request.user

        if form.is_valid():
            tipo_de_vista = form.cleaned_data.get('tipo_de_vista')
            medios = form.cleaned_data.get('medios')
            categoria = form.cleaned_data.get('categoria')
            preparacion = form.cleaned_data.get('preparacion')
            tipo = form.cleaned_data.get('tipo')
            calorias = form.cleaned_data.get('calorias')

            if tipo_de_vista == 'solo-mios':
                platos = platos.filter(propietario_id=self.request.user.id)

            if tipo_de_vista == 'de-otros':
                platos =  platos.exclude(propietario_id=self.request.user.id)
   
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

            if usuario:
                platos_elegidos = Elegidos.objects.filter(usuario=usuario).values_list('nombre_plato_elegido', flat=True)

        contexto = {
            'form': form,
            'platos': platos,
            'elegidos': platos_elegidos,
       }

        return render(request, 'AdminVideos/lista_filtrada.html', contexto)



# class MensajeCreate(CreateView):
#   model = Mensaje
#   success_url = reverse_lazy('videos-list')
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

