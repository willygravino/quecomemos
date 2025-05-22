
from django import forms
from .models import Ingrediente, IngredienteEnPlato, Lugar, Plato, TipoPlato
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
    tipo = forms.ChoiceField(choices=Plato.TIPO_CHOICES, required=False)
    calorias = forms.ChoiceField(choices=Plato.ESTACIONALIDAD_CHOICES, required=False)
    

class PlatoForm(forms.ModelForm):
    variedad1 = forms.CharField(max_length=100, required=False)
    ingredientes_de_variedad1 = forms.CharField( max_length=120, required=False)
    variedad2 = forms.CharField(max_length=100, required=False)
    ingredientes_de_variedad2 = forms.CharField(max_length=120, required=False)
    variedad3 = forms.CharField(max_length=100, required=False)
    ingredientes_de_variedad3 = forms.CharField( max_length=120, required=False)
    variedad4 = forms.CharField(max_length=100, required=False)
    ingredientes_de_variedad4 = forms.CharField( max_length=120, required=False)
    variedad5 = forms.CharField(max_length=100, required=False)
    ingredientes_de_variedad5 = forms.CharField( max_length=120, required=False)
    variedad6 = forms.CharField(max_length=100, required=False)
    ingredientes_de_variedad6 = forms.CharField( max_length=120, required=False)

    tipos = forms.ModelMultipleChoiceField(
        queryset=TipoPlato.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

#     tipos = forms.ModelMultipleChoiceField(
#     queryset=TipoPlato.objects.all(),
#     widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
#     required=False
# )
  
    class Meta:
        model = Plato
        fields = ["nombre_plato", "receta", "descripcion_plato", "ingredientes", "porciones", "medios", "elaboracion", "coccion", "estacionalidad", "tipo", "tipos", "enlace", "image"]

    def clean(self):
        super().clean()
        
        tipos = self.cleaned_data.get("tipos")
        if not tipos or tipos.count() == 0:
            raise forms.ValidationError({'tipos': 'Debés seleccionar al menos un tipo de plato.'})


# class IngredienteEnPlatoForm(forms.ModelForm):
#     class Meta:
#         model = IngredienteEnPlato
#         fields = ['ingrediente', 'cantidad', 'unidad']


class IngredienteEnPlatoForm(forms.ModelForm):
    nombre_ingrediente = forms.CharField(
        max_length=100,
        label="Ingrediente",
        help_text="Escribí el nombre del ingrediente",
    )

    # class Meta:
    #     model = IngredienteEnPlato
    #     fields = ['cantidad', 'unidad']  # No mostramos el campo FK directamente

    class Meta:
        model = IngredienteEnPlato
        fields = ['cantidad', 'unidad']
        labels = {
            'cantidad': 'Cantidad',     # Podés modificar o quitar la etiqueta
            'unidad': '',               # Esto quita la etiqueta de 'unidad'
        }

    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Ordenamos los campos incluyendo el manual
        self.order_fields(['nombre_ingrediente', 'cantidad', 'unidad'])

        # Si se está editando una instancia existente, precargamos el nombre del ingrediente
        if self.instance and self.instance.pk and self.instance.ingrediente:
            self.fields['nombre_ingrediente'].initial = self.instance.ingrediente.nombre

        # Agregamos clases Bootstrap como placeholder opcional
        self.fields['nombre_ingrediente'].widget.attrs.update({'placeholder': 'Ingrediente'})

    def clean_nombre_ingrediente(self):
        nombre = self.cleaned_data['nombre_ingrediente'].strip()
        if not nombre:
            raise forms.ValidationError("El nombre del ingrediente no puede estar vacío.")
        return nombre

    def save(self, commit=True):
        nombre = self.cleaned_data['nombre_ingrediente']
        ingrediente_obj, created = Ingrediente.objects.get_or_create(nombre__iexact=nombre, defaults={'nombre': nombre})
        self.instance.ingrediente = ingrediente_obj
        return super().save(commit=commit)
  
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
