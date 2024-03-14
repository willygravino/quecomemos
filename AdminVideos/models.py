from django.db import models
from django.contrib.auth.models import User

class Plato(models.Model):
    nombre_plato = models.CharField(max_length=30)
    receta = models.CharField(max_length=80, blank=False)
    descripcion_plato = models.CharField(max_length=300)
    ingredientes = models.CharField('Ingresá los ingredientes, separados por coma', max_length=120, blank=False)

    HORNO = 'horno'
    COCINA = 'cocina'
    PARRILA = 'parrilla'
    WOK = 'wok'
    SIN_COCCION = 'sin coccion'
    
    MEDIOS_CHOICES = [
        (HORNO, 'horno'),
        (COCINA, 'cocina'),
        (PARRILA, 'parrilla'),
        (WOK,'wok'),
        (SIN_COCCION,'sin cocción'),
    ]
    medios = models.CharField(max_length=20, choices=MEDIOS_CHOICES, null=True, blank=True)

    COMUN = 'Común'
    ESPECIAL = 'Especial'
       
    CATEGORIA_CHOICES = [
        (COMUN, 'Común'),
        (ESPECIAL, 'Especial'),
        
    ]
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, null=True, blank=True)

    MUCHO = 'Mucho'
    POCO = 'Poco'
    NADA = 'Nada'
       
    PREPA_CHOICES = [
        (MUCHO, 'Mucho'),
        (POCO, 'Poco'),
        (NADA, 'Nada'),
    ]
    preparacion = models.CharField(max_length=20, choices=PREPA_CHOICES, null=True, blank=True)

    ENTRADA = 'entrada'
    SALSA = 'salsa'
    PICADA = 'picada'
    PRINCIPAL = 'Plato principal'
    POSTRE = 'postre'
    TORTA = 'torta'
    UNTABLE = 'untable'
    TRAGO = 'trago'
    GUARNICION = 'guarnicion'

    TIPO_CHOICES = [
        (ENTRADA, 'Entrada'),
        (SALSA, 'Salsa'),
        (PICADA, 'Picada'),
        (PRINCIPAL,'Plato principal'),
        (POSTRE,'postre'),
        (TORTA,'torta'),
        (UNTABLE,'untable'),
        (TRAGO,'trago'),
        (GUARNICION,'guarnicion'),
    ]

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, null=True, blank=True)

    CALORICO = 'Calórico'
    LIVIANO = 'Liviano'
    NORMAL = 'Normal'
    INVIERNO = 'Plato de invierno'
  

    CALORIAS_CHOICES = [
        (CALORICO, 'Calórico'),
        (LIVIANO, 'Liviano'),
        (NORMAL, 'Normal'),
        (INVIERNO,'Plato de invierno'),
   
    ]

    calorias = models.CharField(max_length=20, choices=CALORIAS_CHOICES, null=True, blank=True)  

    propietario = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name="propietario")
    image = models.ImageField("Subí una imagen que identifique al plato (o un fotograma del mismo)", upload_to="videos/", null=True, blank=True)
    # fecha_video= models.DateTimeField("Fecha de captura del video:")

    @property
    def image_url(self):
        return self.image.url if self.image else '/media/videos/logo.png'

    def __str__(self):
        return f"{self.id} - {self.nombre_plato}"
    
class Elegidos(models.Model):
    usuario = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name="platos_elegidos", null=True, blank=True)
    nombre_plato_elegido = models.CharField(max_length=30)
    # usuario = models.OneToOneField(to=User, on_delete=models.CASCADE, related_name="platos_elegidos", null=True, blank=True)

class ElegidosXSemana(models.Model):
    elegidos_por_semana = models.JSONField(null=True, blank=True)


    def __str__(self):
         return f'Menu Elegido {self.id}' 

class Profile(models.Model):
     user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
     nombre_completo = models.CharField(max_length=80, blank=False)
     avatar = models.ImageField(upload_to="avatares", null=True, blank=True)

     @property
     def avatar_url(self):
        return self.avatar.url if self.avatar else '/media/avatares/logo.png'
     
     
class Mensaje(models.Model):
    mensaje = models.TextField(max_length=1000)
    email = models.EmailField()
    creado_el = models.DateTimeField(auto_now_add=True) 
    destinatario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="mensajes")


