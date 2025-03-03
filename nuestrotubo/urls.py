"""nuestrotubo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from AdminVideos.views import EnviarMensaje, agregar_a_mi_lista, agregar_plato_compartido, amigue_borrar, amigues, compartir_plato, descartar_sugerido, eliminar_plato, index, PlatoUpdate, PlatoCreate, Login, SignUp, ProfileCreate, ProfileUpdate, about, PlatoDetail, lista_de_compras, SugerenciasRandom, FiltroDePlatos, reiniciar_sugeridos, sumar_amigue, user_logout, SolicitarAmistad, MensajeDelete, AsignarPlato 
from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name="index"),
    path('menu/elegido',lista_de_compras, name="menu-elegido"),
    path('menu/amigues',amigues, name="amigues"),
    path('menu/amigues/sumar',sumar_amigue, name="sumar-amigue"),
    path('compartir/',  compartir_plato.as_view(), name="compartir-plato"),
    path('agregar-a-mi-lista/<int:plato_id>/', agregar_a_mi_lista, name='agregar-a-mi-lista'),
    path('descartar-sugerido/<str:nombre_plato>/', descartar_sugerido, name='descartar-sugerido'),
    path('agregar-compartido/<int:pk>/', agregar_plato_compartido, name='agregar-plato-compartido'),
    path('videos/list/filtro', FiltroDePlatos, name="filtro-de-platos"),
    path('videos/reiniciar/sugeridos', reiniciar_sugeridos, name="reiniciar-sugeridos"),
    path('videos/<pk>/update', PlatoUpdate.as_view(), name="videos-update"),
    path('eliminar-plato/<int:plato_id>/', eliminar_plato, name='eliminar-plato'),
    # path('eliminar-programado/<str:nombre_plato>/', eliminar_programado, name='eliminar-programado'),

    path('videos/<pk>/detail', PlatoDetail.as_view(), name="videos-detail"),
    path('videos/create', PlatoCreate.as_view(), name="videos-create"),
    path('login', Login.as_view(), name="login"),
    path('registration/logout/', user_logout, name='logout'),
    path('signup', SignUp.as_view(), name="signup"),
    path('perfil/crear', ProfileCreate.as_view(), name="profile-create"),
    path('profile/<pk>/update', ProfileUpdate.as_view(), name="profile-update"),
    path('about', about, name="about"),
    path('solicitar/amistad', SolicitarAmistad.as_view(), name="solicitar-amistad" ),
    path('mensaje/<str:usuario>/enviar', EnviarMensaje.as_view(), name="enviar-mensaje" ),
    path('mensaje/<pk>/delete', MensajeDelete.as_view(), name="mensaje-delete"),
    path('menu/amigue/<pk>/borrar', amigue_borrar, name="amigue-borrar"),
    path('asignar/plato', AsignarPlato.as_view(), name="asignar-plato"), # type: ignore
     
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

