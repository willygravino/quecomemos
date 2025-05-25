
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
    # tipo = forms.ChoiceField(choices=Plato.TIPO_CHOICES, required=False)
    calorias = forms.ChoiceField(choices=Plato.ESTACIONALIDAD_CHOICES, required=False)
    
    
class PlatoForm(forms.ModelForm):
    variedad1 = forms.CharField(max_length=100, required=False)
    ingredientes_de_variedad1 = forms.CharField(max_length=120, required=False)
    variedad2 = forms.CharField(max_length=100, required=False)
    ingredientes_de_variedad2 = forms.CharField(max_length=120, required=False)
    variedad3 = forms.CharField(max_length=100, required=False)
    ingredientes_de_variedad3 = forms.CharField(max_length=120, required=False)
    variedad4 = forms.CharField(max_length=100, required=False)
    ingredientes_de_variedad4 = forms.CharField(max_length=120, required=False)
    variedad5 = forms.CharField(max_length=100, required=False)
    ingredientes_de_variedad5 = forms.CharField(max_length=120, required=False)
    variedad6 = forms.CharField(max_length=100, required=False)
    ingredientes_de_variedad6 = forms.CharField(max_length=120, required=False)

    tipos = forms.MultipleChoiceField(
        choices=Plato.TIPOS_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Tipos"
    )

    class Meta:
        model = Plato
        fields = [
            "nombre_plato", "receta", "descripcion_plato", "ingredientes", 
            "porciones", "medios", "elaboracion", "coccion", "categoria", 
            "tipos", "enlace", "image"
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.tipos:
            self.initial['tipos'] = self.instance.tipos.split(',')

        # Placeholders
        self.fields['porciones'].widget.attrs.update({'placeholder': 'Porciones'})
        self.fields['elaboracion'].widget.attrs.update({'placeholder': 'Preparación (min)'})
        self.fields['coccion'].widget.attrs.update({'placeholder': 'Cocción (min)'})
        self.fields['enlace'].widget.attrs.update({'placeholder': 'Enlace al video o receta'})

    def clean_tipos(self):
        return ','.join(self.cleaned_data['tipos'])

    def clean(self):
        cleaned_data = super().clean()
        tipos = cleaned_data.get("tipos")
        if not tipos or len(tipos) == 0:
            self.add_error('tipos', 'Debés seleccionar al menos un tipo de plato.')


# class PlatoForm(forms.ModelForm):
#     variedad1 = forms.CharField(max_length=100, required=False)
#     ingredientes_de_variedad1 = forms.CharField( max_length=120, required=False)
#     variedad2 = forms.CharField(max_length=100, required=False)
#     ingredientes_de_variedad2 = forms.CharField(max_length=120, required=False)
#     variedad3 = forms.CharField(max_length=100, required=False)
#     ingredientes_de_variedad3 = forms.CharField( max_length=120, required=False)
#     variedad4 = forms.CharField(max_length=100, required=False)
#     ingredientes_de_variedad4 = forms.CharField( max_length=120, required=False)
#     variedad5 = forms.CharField(max_length=100, required=False)
#     ingredientes_de_variedad5 = forms.CharField( max_length=120, required=False)
#     variedad6 = forms.CharField(max_length=100, required=False)
#     ingredientes_de_variedad6 = forms.CharField( max_length=120, required=False)

#     # tipos = forms.ModelMultipleChoiceField(
#     #     queryset=TipoPlato.objects.all(),
#     #     widget=forms.CheckboxSelectMultiple,
#     #     required=False
#     # )

#     tipos = forms.MultipleChoiceField(
#         choices=Plato.TIPOS_CHOICES,
#         widget=forms.CheckboxSelectMultiple,
#         required=False,
#         label="Tipos"
#     )

#     class Meta:
#         model = Plato
#         fields = '__all__'

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         if self.instance and self.instance.tipos:
#             self.initial['tipos'] = self.instance.tipos.split(',')

#     def clean_tipos(self):
#         return ','.join(self.cleaned_data['tipos'])
  
#     class Meta:
#         model = Plato
#         fields = ["nombre_plato", "receta", "descripcion_plato", "ingredientes", "porciones", "medios", "elaboracion", "coccion", "estacionalidad", "tipos", "enlace", "image"]

#     def clean(self):
#         super().clean()
        
#         tipos = self.cleaned_data.get("tipos")
#         if not tipos or tipos.count() == 0:
#             raise forms.ValidationError({'tipos': 'Debés seleccionar al menos un tipo de plato.'})
        

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#         # Quitar los labels
#         # for field in ['porciones', 'medios', 'elaboracion', 'coccion', 'enlace']:
#         #     self.fields[field].label = ''

#         # Agregar placeholders
#         self.fields['porciones'].widget.attrs.update({'placeholder': 'Porciones'})
#         # self.fields['medios'].empty_label = "Medios de cocción"
#         self.fields['elaboracion'].widget.attrs.update({'placeholder': 'Preparación (min)'})
#         self.fields['coccion'].widget.attrs.update({'placeholder': 'Cocción (min)'})
#         # self.fields['estacionalidad'].empty_label = "Estacionalidad"
#         self.fields['enlace'].widget.attrs.update({'placeholder': 'Enlace al video o receta'})
#         # self.fields['estacionalidad'].choices = [('', 'Estaciyyyonialidad')] + list(self.fields['estacionalidad'].choices)




class IngredienteEnPlatoForm(forms.ModelForm):
    # nombre_ingrediente = forms.CharField(
    #     max_length=100,
    #     label="",
    #     help_text="Escribí el nombre del ingrediente",
    # )

    nombre_ingrediente = forms.CharField(
        max_length=100,
        label="",
        required=False,   # <-- Esto hace que no sea obligatorio
        help_text="Escribí el nombre del ingrediente",
    )


    class Meta:
        model = IngredienteEnPlato
        fields = ['ingrediente','cantidad', 'unidad']
        labels = {
            'ingrediente': '',
            'cantidad': '',     # Podés modificar o quitar la etiqueta
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
        self.fields['cantidad'].widget.attrs.update({'placeholder': 'Cantidad'})
        # self.fields['unidad'].empty_label = "Unidad de medida"
        self.fields['unidad'].choices = [('', 'Unidad de medida')] + list(self.fields['unidad'].choices)



        # # ⚠️ Evitamos que Django valide este campo automáticamente
        # self.fields['ingrediente'].required = False


    # def clean_nombre_ingrediente(self):
    #     nombre = self.cleaned_data['nombre_ingrediente'].strip()
    #     if not nombre:
    #         raise forms.ValidationError("El nombre del ingrediente no puede estar vacío.")
    #     return nombre

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
