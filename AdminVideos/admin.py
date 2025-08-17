from django.contrib import admin
from AdminVideos.models import HistoricoDia, Ingrediente, IngredienteEnPlato, Plato, Profile, Mensaje, ElegidosXDia, Sugeridos, Lugar, ComidaDelDia

# admin.site.register(Plato)
admin.site.register(Profile)
admin.site.register(Mensaje)
admin.site.register(ElegidosXDia)
admin.site.register(Sugeridos)
admin.site.register(Lugar)
admin.site.register(ComidaDelDia)
admin.site.register(HistoricoDia)
# admin.site.register(TipoPlato)

class IngredienteEnPlatoInline(admin.TabularInline):  # o StackedInline si preferís
    model = IngredienteEnPlato
    extra = 0  # cantidad de formularios extra

class PlatoAdmin(admin.ModelAdmin):
    inlines = [IngredienteEnPlatoInline]

admin.site.register(Plato, PlatoAdmin)
admin.site.register(Ingrediente)