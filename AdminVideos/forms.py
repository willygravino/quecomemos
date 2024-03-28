
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
    
    tipo_de_vista = forms.ChoiceField(choices=[('todos', 'Todos'), ('solo-mios', 'Solo mis platos'), ('de-otros', 'Solo platos de otros'), ('preseleccionados', 'Preseleccionados'), ("random-todos", "< Random con todos >"), ("random-con-mios", "< Random con los mios>")], required=True)


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
    

    # Si quieres personalizar la forma en que se muestra un campo, puedes hacerlo así:
    # def __init__(self, *args, **kwargs):
    #     super(PlatoForm, self).__init__(*args, **kwargs)
    #     self.fields['ingredientes'].widget.attrs['placeholder'] = 'Ingresá los ingredientes, separados por coma'

        # Personaliza otros campos aquí si es necesario

    # Si deseas agregar validaciones personalizadas para algún campo, puedes hacerlo así:
    # def clean_nombre_plato(self):
    #     nombre_plato = self.cleaned_data.get('nombre_plato')
    #     # Agrega aquí tu validación personalizada si es necesario
    #     return nombre_plato
