
from django import forms
from .models import Plato

class PlatoFilterForm(forms.Form):
    # nombre_plato = forms.CharField(required=False)
    medios = forms.ChoiceField(choices=Plato.MEDIOS_CHOICES, required=False)
    categoria = forms.ChoiceField(choices=Plato.CATEGORIA_CHOICES, required=False)
    # ingredientes = forms.CharField('Ingresá los ingredientes, separados por coma', max_length=120, blank=False)
    preparacion = forms.ChoiceField(choices=Plato.PREPA_CHOICES, required=False)
    tipo = forms.ChoiceField(choices=Plato.TIPO_CHOICES, required=False)
    calorias = forms.ChoiceField(choices=Plato.CALORIAS_CHOICES, required=False)
