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
from django.contrib.auth.views import LogoutView

from AdminVideos.views import amigue_borrar, amigues, compartir_plato, formulario_dia, index, PlatoUpdate, PlatoDelete, PlatoCreate, Login, SignUp, ProfileCreate, ProfileUpdate, about, PlatoDetail, lista_de_compras, plato_preseleccionado, grabar_menu_elegido,SugerenciasRandom, FiltroDePlatos, reiniciar_sugeridos, sumar_amigue, user_logout, desmarcar_todo, MensajeCreate, MensajeList, MensajeDelete # VistaInicial ,Logout, , PlatoList, PlatosMineList, PlatosElegidosMenu, elecion_de_lista, PlatosDeOtros,, LogtViews, MenuElegido, lista_de_compras
from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name="index"),
    path('plato/elegido', plato_preseleccionado, name="plato-preseleccionado"),
    path('plato/grabar', grabar_menu_elegido, name="grabar-menu"),
    path('menu/elegido',lista_de_compras, name="menu-elegido"),
    path('menu/amigues',amigues, name="amigues"),
    path('menu/amigues/sumar',sumar_amigue, name="sumar_amigue"),
    path('formulario/dia/<str:dia>/',  formulario_dia, name="formulario-dia"),
    path('desmarcar/',  desmarcar_todo, name="desmarcar-todo"),
    path('compartir/',  compartir_plato.as_view(), name="compartir-plato"),

    # path('lista/compras-y-plan', lista_y_plan, name="lista-y-plan"),
    # path('menu/random', SugerenciasRandom.as_view(), name="random"),
    path('videos/list/filtro', FiltroDePlatos, name="filtro-de-platos"),
    path('videos/reiniciar/sugeridos', reiniciar_sugeridos, name="reiniciar-sugeridos"),
    path('videos/<pk>/update', PlatoUpdate.as_view(), name="videos-update"),
    path('videos/<pk>/delete', PlatoDelete.as_view(), name="videos-delete"),
    path('videos/<pk>/detail', PlatoDetail.as_view(), name="videos-detail"),
    path('videos/create', PlatoCreate.as_view(), name="videos-create"),
    path('login', Login.as_view(), name="login"),
    path('registration/logout/', user_logout, name='logout'),
    path('signup', SignUp.as_view(), name="signup"),
    path('perfil/crear', ProfileCreate.as_view(), name="profile-create"),
    path('profile/<pk>/update', ProfileUpdate.as_view(), name="profile-update"),
    path('about', about, name="about"),
    path('mensaje/list', MensajeList.as_view(), name="mensaje-list" ),
    path('mensaje/create', MensajeCreate.as_view(), name="mensaje-create" ),
    path('mensaje/<pk>/delete', MensajeDelete.as_view(), name="mensaje-delete"),
    path('menu/amigue/<pk>/borrar', amigue_borrar, name="amigue-borrar"),


     
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

