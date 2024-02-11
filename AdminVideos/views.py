# from contextvars import Context AGREGADO POR MI PARA VER LA QUERY
from contextvars import Context
from django.shortcuts import render, redirect
from AdminVideos.models import Plato, Profile, Mensaje
from django.urls import reverse_lazy
from django.contrib.auth.forms import UserCreationForm
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

def index(request):
    return render(request, "AdminVideos/index.html")

def about(request):
    return render(request, "AdminVideos/about.html")

class PlatoList(ListView):
    model = Plato
    context_object_name = "platos"
    # query = "tomatelas"

    def get_queryset(self):
        # self.query = "tomatelas"

        if self.request.user.is_authenticated:
            try:
                if self.request.user.profile:
                        # self.query = "higo"
                        self.query = self.request.GET.get("la-busqueda")
                        # query = self.request.user.profile.nombre_completo
                        if self.query:
                            object_list = Plato.objects.filter(ingredientes__icontains=self.query)
                        return object_list
            except Exception:
               object_list = Plato.objects.filter(ingredientes__icontains="%%")
            return object_list
        else:
            object_list = Plato.objects.filter(ingredientes__icontains="%%")
        return object_list

    def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            # Pasar query al contexto
            context['query'] = self.query
            return context


class PlatosMineList(LoginRequiredMixin, PlatoList):
    template_name = 'AdminVideos/videosmine_list.html'

    def get_queryset(self):
      return Plato.objects.filter(propietario=self.request.user.id)

class PlatoDetail(DetailView):
    model = Plato
    context_object_name = "plato"


class PlatoUpdate(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Plato
    success_url = reverse_lazy("videos-list")
    fields = ["nombre_plato","receta","descripcion_plato","ingredientes","image"]
    #fields = '__all__'

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
    fields = ["nombre_plato","receta","descripcion_plato","ingredientes","image"]
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

