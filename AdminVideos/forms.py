
from django import forms
from .models import Plato

class PlatoFilterForm(forms.Form):
    medios = forms.ChoiceField(choices=Plato.MEDIOS_CHOICES, required=False)
    categoria = forms.ChoiceField(choices=Plato.CATEGORIA_CHOICES, required=False)
    preparacion = forms.ChoiceField(choices=Plato.PREPA_CHOICES, required=False)
    tipo = forms.ChoiceField(choices=Plato.TIPO_CHOICES, required=False)
    calorias = forms.ChoiceField(choices=Plato.CALORIAS_CHOICES, required=False)
    

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
  
    class Meta:
        model = Plato
        fields = ["nombre_plato", "receta", "descripcion_plato", "ingredientes", "medios", "categoria", "preparacion", "tipo", "calorias", "image"]
    
