
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
    
    
    from django import forms
from .models import Plato


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
    # Legacy (lo vas a borrar después, pero no rompe nada ahora)
    # variedad1 = forms.CharField(max_length=100, required=False)
    # ingredientes_de_variedad1 = forms.CharField(max_length=120, required=False)
    # variedad2 = forms.CharField(max_length=100, required=False)
    # ingredientes_de_variedad2 = forms.CharField(max_length=120, required=False)
    # variedad3 = forms.CharField(max_length=100, required=False)
    # ingredientes_de_variedad3 = forms.CharField(max_length=120, required=False)
    # variedad4 = forms.CharField(max_length=100, required=False)
    # ingredientes_de_variedad4 = forms.CharField(max_length=120, required=False)
    # variedad5 = forms.CharField(max_length=100, required=False)
    # ingredientes_de_variedad5 = forms.CharField(max_length=120, required=False)
    # variedad6 = forms.CharField(max_length=100, required=False)
    # ingredientes_de_variedad6 = forms.CharField(max_length=120, required=False)

    # ✅ Tipos: lista durante validación, CSV al guardar
    tipos = forms.MultipleChoiceField(
        choices=Plato.TIPOS_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Tipos",
    )

    class Meta:
        model = Plato
        fields = [
            "nombre_plato",
            "receta",
            "ingredientes",
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
        super().__init__(*args, **kwargs)

        # ✅ Si en DB guardás "Principal,Guarnicion", convertimos a lista sin espacios
        if self.instance and self.instance.tipos:
            self.initial["tipos"] = [
                t.strip() for t in self.instance.tipos.split(",") if t.strip()
            ]

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

    def save(self, commit=True):
        obj = super().save(commit=False)

        # ✅ Convertimos lista → CSV recién al guardar
        tipos_lista = self.cleaned_data.get("tipos") or []
        obj.tipos = ",".join([t.strip() for t in tipos_lista if t.strip()])

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
        fields = ['ingrediente', 'cantidad', 'unidad']
        labels = {
            'ingrediente': '',
            'cantidad': '',
            'unidad': '',
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Ordenamos los campos
        self.order_fields(['nombre_ingrediente', 'cantidad', 'unidad'])

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
