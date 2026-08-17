
import json
import re

from django import forms
from .models import Ingrediente, IngredienteEnPlato, Lugar, MenuItem, MenuItemExtra, Plato, TipoPlato
from django.contrib.auth.forms import AuthenticationForm


class PlatoFilterForm(forms.Form):
    medios = forms.ChoiceField(choices=Plato.MEDIOS_CHOICES, required=False)
    categoria = forms.ChoiceField(choices=Plato.CATEGORIA_CHOICES, required=False)
    # dificultad = forms.ChoiceField(choices=Plato.PREPA_CHOICES, required=False)
    palabra_clave = forms.CharField(
        max_length=30, 
        required=False, 
        widget=forms.TextInput(attrs={'placeholder': 'Buscar por palabra clave'})
    )    
    # tipo = forms.ChoiceField(choices=Plato.TIPO_CHOICES, required=False)
    calorias = forms.ChoiceField(choices=Plato.ESTACIONALIDAD_CHOICES, required=False)
    
    

class ElegirPlatoForm(forms.Form):
    plato = forms.ChoiceField(choices=())

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        padres = Plato.objects.filter(propietario=user, plato_padre__isnull=True)
        hijos = Plato.objects.filter(propietario=user, plato_padre__isnull=False).select_related("plato_padre")

        # armamos un mapa padre -> hijos
        hijos_por_padre = {}
        for h in hijos:
            hijos_por_padre.setdefault(h.plato_padre_id, []).append(h)

        choices = []
        for p in padres:
            choices.append((str(p.id), p.nombre_plato))
            for h in hijos_por_padre.get(p.id, []):
                choices.append((str(h.id), f"   ↳ {h.nombre_plato}"))

        self.fields["plato"].choices = choices
        

class PlatoForm(forms.ModelForm):
   
    # ✅ Tipos: lista durante validación, CSV al guardar
    tipos = forms.MultipleChoiceField(
        choices=Plato.TIPOS_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Tipos",
    )

    componentes = forms.ModelMultipleChoiceField(
        queryset=Plato.objects.none(),
        required=False,
        widget=forms.MultipleHiddenInput,
    )

    partes_receta_json = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"id": "partesRecetaJson"}),
    )

    class Meta:
        model = Plato
        fields = [
            "nombre_plato",
            "receta",
            "ingredientes",
            "componentes",
            "porciones",
            "medios",
            "elaboracion",
            "coccion",
            "categoria",
            "tipos",
            "estacionalidad",
            "enlace",
            "image",
        ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # ✅ Componentes: platos que se pueden asociar a este plato
        if "componentes" in self.fields:
            qs = Plato.objects.none()

            if self.user and self.user.is_authenticated:
                qs = Plato.objects.filter(propietario=self.user)

            # Evitamos que un plato pueda asociarse a sí mismo
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            self.fields["componentes"].queryset = qs

        # ✅ Si en DB guardás "Principal,Guarnicion", convertimos a lista sin espacios
        if self.instance and self.instance.tipos:
            self.initial["tipos"] = [
                t.strip() for t in self.instance.tipos.split(",") if t.strip()
            ]

        if not self.is_bound and not self.initial.get("partes_receta_json"):
            self.initial["partes_receta_json"] = json.dumps(
                getattr(self.instance, "partes_receta", []) or [],
                ensure_ascii=False,
            )

        # Área amplia para escribir la receta completa
        if "receta" in self.fields:
            self.fields["receta"].widget.attrs.update({
                "rows": 8,
                "placeholder": "Escribí aquí la receta completa, con todos los pasos que necesites",
            })

        # Placeholders
        if "porciones" in self.fields:
            self.fields["porciones"].widget.attrs.update({"placeholder": "Porciones"})

        if "elaboracion" in self.fields:
            self.fields["elaboracion"].widget.attrs.update({"placeholder": "Preparación (min)"})

        if "coccion" in self.fields:
            self.fields["coccion"].widget.attrs.update({"placeholder": "Cocción (min)"})

        if "enlace" in self.fields:
            self.fields["enlace"].widget.attrs.update({"placeholder": "Enlace al video o receta"})

    def clean(self):
        cleaned_data = super().clean()

        # ✅ Acá `tipos` es lista (MultipleChoiceField), no string
        tipos = cleaned_data.get("tipos") or []
        if len(tipos) == 0:
            self.add_error("tipos", "Debés seleccionar al menos un tipo de plato.")

        return cleaned_data

    def clean_partes_receta_json(self):
        raw = self.cleaned_data.get("partes_receta_json")

        if raw in (None, ""):
            return getattr(self.instance, "partes_receta", []) or []

        try:
            partes = json.loads(raw) if isinstance(raw, str) else raw
        except (TypeError, ValueError, json.JSONDecodeError):
            raise forms.ValidationError("No se pudieron interpretar las partes de la receta.")

        if not isinstance(partes, list):
            raise forms.ValidationError("Las partes de la receta tienen un formato inválido.")

        normalizadas = []
        claves = set()

        for indice, parte in enumerate(partes):
            if not isinstance(parte, dict):
                raise forms.ValidationError("Una parte de la receta tiene un formato inválido.")

            clave = str(parte.get("clave") or "").strip()
            nombre = str(parte.get("nombre") or "").strip()
            instrucciones = str(parte.get("instrucciones") or "").strip()

            if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", clave):
                raise forms.ValidationError("Una parte de la receta tiene una clave inválida.")
            if clave in claves:
                raise forms.ValidationError("Hay partes de la receta repetidas.")
            if not nombre:
                raise forms.ValidationError("Todas las partes deben tener un nombre.")
            if len(nombre) > 60:
                raise forms.ValidationError("El nombre de una parte no puede superar 60 caracteres.")
            if len(instrucciones) > 5000:
                raise forms.ValidationError("Las instrucciones de una parte son demasiado extensas.")

            claves.add(clave)
            normalizadas.append({
                "clave": clave,
                "nombre": nombre,
                "instrucciones": instrucciones,
                "orden": indice,
            })

        return normalizadas

    def save(self, commit=True):
        obj = super().save(commit=False)

        # ✅ Convertimos lista → CSV recién al guardar
        tipos_lista = self.cleaned_data.get("tipos") or []
        obj.tipos = ",".join([t.strip() for t in tipos_lista if t.strip()])
        obj.partes_receta = self.cleaned_data.get("partes_receta_json") or []

        if commit:
            obj.save()
            self.save_m2m()

        return obj


        
class IngredienteEnPlatoForm(forms.ModelForm):
  
    nombre_ingrediente = forms.CharField(
        max_length=100,
        label="",
        required=False,  # No obligatorio
        help_text="Escribí el nombre del ingrediente",
    )

    class Meta:
        model = IngredienteEnPlato
        fields = ['ingrediente', 'cantidad', 'unidad', 'parte_clave']
        widgets = {
            'parte_clave': forms.HiddenInput(),
        }
        labels = {
            'ingrediente': '',
            'cantidad': '',
            'unidad': '',
            'parte_clave': '',
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Ordenamos los campos
        self.order_fields(['nombre_ingrediente', 'cantidad', 'unidad', 'parte_clave'])

        # Precargar nombre del ingrediente si existe
        if self.instance and self.instance.pk and self.instance.ingrediente:
            self.fields['nombre_ingrediente'].initial = self.instance.ingrediente.nombre

        # Mostrar cantidad sin .0 si es entero
        if self.instance and self.instance.pk and self.instance.cantidad is not None:
            cantidad = self.instance.cantidad
            self.fields['cantidad'].initial = str(int(cantidad)) if cantidad == int(cantidad) else str(cantidad)

        # Agregar placeholders y clases Bootstrap
        self.fields['nombre_ingrediente'].widget.attrs.update({'placeholder': 'Ingrediente'})
        self.fields['cantidad'].widget.attrs.update({'placeholder': 'Cantidad'})
        self.fields['unidad'].choices = [('', 'Unidad de medida')] + list(self.fields['unidad'].choices)

    def save(self, commit=True):
        # 1️⃣ Si viene ingrediente_id desde el hidden (Select2), usarlo
        ingrediente_id = self.data.get(self.add_prefix("ingrediente"))
        if ingrediente_id:
            self.instance.ingrediente_id = ingrediente_id
            return super().save(commit=commit)

        # 2️⃣ Fallback: si no vino ID, usar nombre_ingrediente
        nombre = (self.cleaned_data.get("nombre_ingrediente") or "").strip()
        if nombre:
            ingrediente_obj = Ingrediente.objects.filter(
                nombre__iexact=nombre
            ).first()
            if not ingrediente_obj:
                ingrediente_obj = Ingrediente.objects.create(nombre=nombre)
            self.instance.ingrediente = ingrediente_obj

        return super().save(commit=commit)

    
    def clean_cantidad(self):
        cantidad = self.cleaned_data.get('cantidad')
        if cantidad in [None, '']:
            return None
        # Reemplazar coma por punto y convertir a float
        cantidad_str = str(cantidad).replace(',', '.')
        try:
            return float(cantidad_str)
        except ValueError:
            raise forms.ValidationError("Cantidad inválida")


IngredienteEnPlatoFormSet = forms.inlineformset_factory(
    Plato,
    IngredienteEnPlato,
    form=IngredienteEnPlatoForm,
    extra=0,         # antes estaba en 1, siempre un form vacío al final
    can_delete=True, # checkbox para borrar
)
  

class LugarForm(forms.ModelForm):
    class Meta:
        model = Lugar
        fields = ['nombre', 'direccion', 'telefono', 'enlace', 'dias_horarios', 'image']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del lugar'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dirección'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono'}),
            'enlace': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Página web o enlace'}),
            'dias_horarios': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Días y horarios de atención'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class CustomAuthenticationForm(AuthenticationForm):
        error_messages = {
        'invalid_login': (
            "Usuario o contraseña incorrectos. Por favor, volvé a intentarlo."
        ),
        'inactive': ("Esta cuenta está inactiva."),
    }
