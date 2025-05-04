
from django import forms
from .models import Lugar, Plato, TipoPlato
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
  
    class Meta:
        model = Plato
        fields = ["nombre_plato", "receta", "descripcion_plato", "ingredientes", "ingredientes_detallados", "medios", "elaboracion", "coccion", "estacionalidad", "tipo", "tipos", "enlace", "image"]


    
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
