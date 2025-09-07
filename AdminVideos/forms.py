
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
            "tipos", "estacionalidad", "enlace", "image"
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





# class IngredienteEnPlatoForm(forms.ModelForm):
  
#     nombre_ingrediente = forms.CharField(
#         max_length=100,
#         label="",
#         required=False,   # <-- Esto hace que no sea obligatorio
#         help_text="Escribí el nombre del ingrediente",
#     )


#     class Meta:
#         model = IngredienteEnPlato
#         fields = ['ingrediente','cantidad', 'unidad']
#         labels = {
#             'ingrediente': '',
#             'cantidad': '',     # Podés modificar o quitar la etiqueta
#             'unidad': '',               # Esto quita la etiqueta de 'unidad'
#         }
        
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#         # Ordenamos los campos incluyendo el manual
#         self.order_fields(['nombre_ingrediente', 'cantidad', 'unidad'])

#         # Si se está editando una instancia existente, precargamos el nombre del ingrediente
#         if self.instance and self.instance.pk and self.instance.ingrediente:
#             self.fields['nombre_ingrediente'].initial = self.instance.ingrediente.nombre

#         # Manejar cantidad para que muestre "9" en vez de "9.0", pero manteniendo decimales
#         if self.instance and self.instance.pk and self.instance.cantidad is not None:
#             cantidad = self.instance.cantidad
#             if cantidad == int(cantidad):
#                 cantidad = str(int(cantidad))
#             else:
#                 cantidad = str(cantidad)
#             self.fields['cantidad'].initial = cantidad

#         # Agregamos clases Bootstrap como placeholder opcional
#         self.fields['nombre_ingrediente'].widget.attrs.update({'placeholder': 'Ingrediente'})
#         self.fields['cantidad'].widget.attrs.update({'placeholder': 'Cantidad'})
#         # self.fields['unidad'].empty_label = "Unidad de medida"
#         self.fields['unidad'].choices = [('', 'Unidad de medida')] + list(self.fields['unidad'].choices)


#     def save(self, commit=True):
#         nombre = self.cleaned_data['nombre_ingrediente']
#         ingrediente_obj, created = Ingrediente.objects.get_or_create(nombre__iexact=nombre, defaults={'nombre': nombre})
#         self.instance.ingrediente = ingrediente_obj
#         return super().save(commit=commit)
    
#     def clean_cantidad(self):
#         cantidad = self.cleaned_data.get('cantidad')
#         if cantidad is None:
#             return None
#         # Reemplazar coma por punto
#         cantidad_str = str(cantidad).replace(',', '.')
#         try:
#             return float(cantidad_str)
#         except ValueError:
#             raise forms.ValidationError("Cantidad inválida")
        
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
        nombre = self.cleaned_data.get('nombre_ingrediente')
        if nombre:
            ingrediente_obj, created = Ingrediente.objects.get_or_create(
                nombre__iexact=nombre, defaults={'nombre': nombre}
            )
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
