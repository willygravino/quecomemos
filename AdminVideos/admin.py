from django.contrib import admin
from .models import (
    HistoricoDia, HistoricoItem,
    Ingrediente, IngredienteEnPlato,
    MenuDia, MenuItem,
    Plato, Profile, Mensaje, Lugar
)

# =====================================================
# Registros simples (sin relaciones inline)
# =====================================================
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "nombre", "apellido", "telefono")
    search_fields = ("user__username", "nombre", "apellido", "telefono")


@admin.register(Mensaje)
class MensajeAdmin(admin.ModelAdmin):
    list_display = ("id", "destinatario", "tipo_mensaje", "usuario_que_envia", "leido", "importado", "creado_el")
    list_filter = ("tipo_mensaje", "leido", "importado", "creado_el")
    search_fields = ("destinatario__username", "usuario_que_envia", "mensaje", "nombre_elemento_compartido")
    date_hierarchy = "creado_el"


@admin.register(Lugar)
class LugarAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "propietario", "delivery", "telefono")
    list_filter = ("delivery", "propietario")
    search_fields = ("nombre", "direccion", "telefono", "propietario__username")


@admin.register(Ingrediente)
class IngredienteAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "tipo", "detalle")
    list_filter = ("tipo", "detalle")
    search_fields = ("nombre",)
    ordering = ("nombre",)


# =====================================================
# PLATO -> IngredienteEnPlato (INLINE)
# =====================================================
class IngredienteEnPlatoInline(admin.TabularInline):
    model = IngredienteEnPlato
    extra = 0
    fields = ("ingrediente", "cantidad", "unidad")
    autocomplete_fields = ("ingrediente",)


@admin.register(Plato)
class PlatoAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre_plato", "propietario", "plato_padre", "cant_ingredientes", "cant_variedades")
    list_filter = ("propietario", "categoria", "estacionalidad")
    search_fields = ("nombre_plato", "nombre_grupo", "propietario__username")
    autocomplete_fields = ("plato_padre",)
    inlines = [IngredienteEnPlatoInline]

    def cant_ingredientes(self, obj):
        return obj.ingredientes_en_plato.count()
    cant_ingredientes.short_description = "Ingredientes"

    def cant_variedades(self, obj):
        return obj.variedades_hijas.count()
    cant_variedades.short_description = "Variedades"


# =====================================================
# MENUDIA -> MenuItem (INLINE)
# =====================================================
class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 0
    fields = ("momento", "plato", "lugar", "elegido", "creado_el")
    readonly_fields = ("creado_el",)
    autocomplete_fields = ("plato", "lugar")


@admin.register(MenuDia)
class MenuDiaAdmin(admin.ModelAdmin):
    list_display = ("id", "propietario", "fecha", "ya_sugerido", "items_count")
    list_filter = ("ya_sugerido", "fecha", "propietario")
    search_fields = ("propietario__username",)
    date_hierarchy = "fecha"
    inlines = [MenuItemInline]

    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = "Items"


# (Opcional) si igual querés poder administrar MenuItem suelto:
@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("id", "menu", "momento", "plato", "lugar", "elegido", "creado_el")
    list_filter = ("momento", "elegido", "creado_el")
    search_fields = ("menu__propietario__username", "plato__nombre_plato", "lugar__nombre")
    autocomplete_fields = ("menu", "plato", "lugar")
    date_hierarchy = "creado_el"


# =====================================================
# HISTORICODIA -> HistoricoItem (INLINE)
# =====================================================
class HistoricoItemInline(admin.TabularInline):
    model = HistoricoItem
    extra = 0
    fields = ("momento", "plato_id_ref")


@admin.register(HistoricoDia)
class HistoricoDiaAdmin(admin.ModelAdmin):
    list_display = ("id", "propietario", "fecha", "dia_semana", "ya_sugerido", "items_count")
    list_filter = ("ya_sugerido", "fecha", "propietario")
    search_fields = ("propietario__username",)
    date_hierarchy = "fecha"
    inlines = [HistoricoItemInline]

    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = "Items"


# (Opcional) mantener HistoricoItem suelto
@admin.register(HistoricoItem)
class HistoricoItemAdmin(admin.ModelAdmin):
    list_display = ("id", "historico", "momento", "plato_id_ref")
    list_filter = ("momento",)
    search_fields = ("historico__propietario__username", "plato_id_ref")
