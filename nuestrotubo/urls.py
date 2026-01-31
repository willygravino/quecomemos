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
from django import views
from django.contrib import admin
from django.urls import path

from AdminVideos.views import CrearLugar, EnviarMensaje, LugarDetail, LugarUpdate, PlatoDetail, PlatoVariedadCreate, PlatoVariedadDelete, PlatoVariedadUpdate,  agregar_a_mi_lista, agregar_plato_compartido, amigue_borrar, amigues, api_ingredientes, api_toggle_item, compartir_elemento, compartir_ing_plato, descartar_sugerido, eliminar_lugar, eliminar_plato, eliminar_programado, fijar_o_eliminar_habito, historial, index, PlatoUpdate, PlatoCreate, Login, SignUp, ProfileCreate, ProfileUpdate, about, lista_de_compras, FiltroDePlatos, plato_ingredientes, plato_opciones_asignar, random_dia, set_dia_activo, sumar_amigue, user_logout, SolicitarAmistad, MensajeDelete, AsignarPlato, compartir_lista
from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name="index"),
    path('login', Login.as_view(), name="login"),

    path('api/ingredientes/', api_ingredientes, name='api_ingredientes'),


    path('menu/elegido',lista_de_compras, name="menu-elegido"),
    path('menu/amigues',amigues, name="amigues"),
    path('menu/historial',historial, name="historial"),
    path('menu/amigues/sumar',sumar_amigue, name="sumar-amigue"),
    path('compartir/',  compartir_elemento.as_view(), name="compartir-plato"),
    # path('compartir/lugar',  compartir_lugar.as_view(), name="compartir-lugar"),

    path('agregar-a-mi-lista/<int:plato_id>/', agregar_a_mi_lista, name='agregar-a-mi-lista'),
    # path('descartar-sugerido/<str:nombre_plato>/', descartar_sugerido, name='descartar-sugerido'),
    path('descartar-sugerido/<int:plato_id>/', descartar_sugerido, name='descartar-sugerido'),
    path('agregar-compartido/<int:pk>/<int:mensaje_id>/', agregar_plato_compartido, name='agregar-plato-compartido'),
    path('videos/list/filtro', FiltroDePlatos, name="filtro-de-platos"),
    # path('lugares', Lugares, name="lugares"),
    # path('videos/reiniciar/sugeridos', reiniciar_sugeridos, name="reiniciar-sugeridos"),
    path('videos/<pk>/update', PlatoUpdate.as_view(), name="videos-update"),
    path('lugar/<pk>/update', LugarUpdate.as_view(), name="lugar-update"),
    # path("lista/compartir/", compartir_lista, name="compartir-lista"),
    # path("lista/compartir/<int:user_id>/", compartir_lista, name="compartir-lista"),
    path("lista/compartir/<uuid:token>/", compartir_lista, name="compartir-lista"),
    path("api/lista/<uuid:token>/toggle/", api_toggle_item, name="api-toggle-item"),



    path('random-dia/<str:dia_nombre>/', random_dia, name='random_dia'),

    path('eliminar-plato/<int:plato_id>/', eliminar_plato, name='eliminar-plato'),
    path('eliminar-lugar/<int:lugar_id>/', eliminar_lugar, name='eliminar-lugar'),
    # path('duplicar-plato/<int:plato_id>/', duplicar_plato, name='duplicar-plato'),

    path("eliminar-programado/<int:es_lugar>/<int:objeto_id>/<str:comida>/<str:fecha>/",eliminar_programado,name="eliminar-programado"),

    # path('eliminar-menu', eliminar_menu_programado, name='eliminar-menu'),


    path('plato/<int:pk>/detail/', PlatoDetail.as_view(), name="platos-detail"),
    path('lugar/<int:pk>/detail', LugarDetail.as_view(), name="lugar-detail"),

    path('videos/create/', PlatoCreate.as_view(), name="videos-create"),
    path('lugar/crear', CrearLugar.as_view(), name="crear-lugar"),
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
    path("set-dia-activo/", set_dia_activo, name="set-dia-activo"),
    path("platos/<int:padre_id>/variedades/create/", PlatoVariedadCreate.as_view(), name="plato_variedad_create"),
    path("variedades/<int:pk>/edit/", PlatoVariedadUpdate.as_view(), name="plato_variedad_update"),
    path("variedades/<int:pk>/delete/", PlatoVariedadDelete.as_view(), name="plato_variedad_delete"),
    path("platos/<int:pk>/ingredientes/", plato_ingredientes, name="plato_ingredientes"),
    path("platos/<int:pk>/opciones-asignar/", plato_opciones_asignar, name="plato_opciones_asignar"),
    path("s/<str:token>/plato/<int:pk>/", compartir_ing_plato, name="compartir-plato"),
    path('fijar-o-eliminar-habito/<int:plato_id>/<str:comida>/', fijar_o_eliminar_habito, name='fijar-o-eliminar-habito'),




     
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

