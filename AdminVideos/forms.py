
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
    

    # def __init__(self, *args, **kwargs):
    #   tipo_de_vista_estable = kwargs.pop('tipo_de_vista_estable', None)
    #   super().__init__(*args, **kwargs)
    #   if tipo_de_vista_estable:
    #      self.fields['tipo_de_vista'].initial = tipo_de_vista_estable
    #   else:
    #      self.fields['tipo_de_vista'].initial = 'Preseleccionados'

            
   
 

# El primer elemento es el valor que se enviará cuando se seleccione esa opción. En este caso, se establece como una cadena vacía '', lo que significa que si el usuario selecciona "Seleccione", el valor enviado será una cadena vacía.
# El segundo elemento es la etiqueta que se mostrará al usuario en el formulario. En este caso, "Seleccione" es la etiqueta que aparecerá en la lista desplegable para indicar al usuario que debe seleccionar una opción.