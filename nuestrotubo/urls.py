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

from AdminVideos.views import index, PlatoUpdate, PlatoDelete, PlatoCreate, Login, SignUp, ProfileCreate, ProfileUpdate, about, PlatoDetail, lista_de_compras, menu_elegido, plato_elegido, grabar_menu_elegido,SugerenciasRandom, FiltroDePlatos, reiniciar_sugeridos, user_logout # VistaInicial ,Logout, MensajeCreate, MensajeList, MensajeDelete, PlatoList, PlatosMineList, PlatosElegidosMenu, elecion_de_lista, PlatosDeOtros,, LogtViews, MenuElegido
from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name="index"),
    path('plato/elegido', plato_elegido, name="plato-elegido"),
    path('plato/grabar', grabar_menu_elegido, name="grabar-menu"),
    path('menu/elegido',  menu_elegido, name="menu-elegido"),
    path('lista/compras', lista_de_compras, name="lista-compras"),
    path('menu/random', SugerenciasRandom.as_view(), name="random"),
    # path('pagina/inicial', pagina_inicial, name="pagina-inicial"),
    path('videos/list/filtro', FiltroDePlatos, name="filtro-de-platos"),
    path('videos/reiniciar/sugeridos', reiniciar_sugeridos, name="reiniciar-sugeridos"),
    path('videos/<pk>/update', PlatoUpdate.as_view(), name="videos-update"),
    # path('videos/<pk>/delete',plato_delete, name="videos-delete"),
    path('videos/<pk>/delete', PlatoDelete.as_view(), name="videos-delete"),

    path('videos/<pk>/detail', PlatoDetail.as_view(), name="videos-detail"),
    path('videos/create', PlatoCreate.as_view(), name="videos-create"),
    path('login', Login.as_view(), name="login"),
    path('registration/logout/', user_logout, name='logout'),
    path('signup', SignUp.as_view(), name="signup"),
    path('perfil/crear', ProfileCreate.as_view(), name="profile-create"),
    path('profile/<pk>/update', ProfileUpdate.as_view(), name="profile-update"),
    path('about', about, name="about"),
   # path('mensaje/list', MensajeList.as_view(), name="mensaje-list" ),
   # path('mensaje/create', MensajeCreate.as_view(), name="mensaje-create" ),
   # path('mensaje/<pk>/delete', MensajeDelete.as_view(), name="mensaje-delete"),

     
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

