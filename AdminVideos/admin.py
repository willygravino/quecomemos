from django.contrib import admin
from AdminVideos.models import HistoricoDia, HistoricoItem, Ingrediente, IngredienteEnPlato, MenuDia, MenuItem, Plato, Profile, Mensaje, ElegidosXDia, Lugar

# admin.site.register(Plato)
admin.site.register(Profile)
admin.site.register(Mensaje)
admin.site.register(ElegidosXDia)
# admin.site.register(Sugeridos)
admin.site.register(Lugar)
# admin.site.register(ComidaDelDia)
admin.site.register(HistoricoDia)
admin.site.register(HistoricoItem)
admin.site.register(MenuDia)
admin.site.register(MenuItem)
 
# admin.site.register(TipoPlato)

class IngredienteEnPlatoInline(admin.TabularInline):  # o StackedInline si preferís
    model = IngredienteEnPlato
    extra = 0  # cantidad de formularios extra

class PlatoAdmin(admin.ModelAdmin):
    inlines = [IngredienteEnPlatoInline]

admin.site.register(Plato, PlatoAdmin)
admin.site.register(Ingrediente)