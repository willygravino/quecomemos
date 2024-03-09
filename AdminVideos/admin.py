from django.contrib import admin
from AdminVideos.models import Plato, Profile, Mensaje, Elegidos, ElegidosXSemana

admin.site.register(Plato)
admin.site.register(Profile)
admin.site.register(Mensaje)
admin.site.register(Elegidos)
admin.site.register(ElegidosXSemana)


