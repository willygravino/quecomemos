from django.db import models
from django.contrib.auth.models import User


class Plato(models.Model):
    nombre_plato = models.CharField(max_length=30)
    receta = models.CharField(max_length=80, blank=True)
    descripcion_plato = models.CharField(max_length=300, blank=True)
    ingredientes = models.CharField('Ingresá los ingredientes, separados por coma', max_length=120, blank=True)
    proviene_de = models.CharField(max_length=20, null=True)

    INDISTINTO = '-'
    HORNO = 'Horno'
    COCINA = 'Cocina'
    PARRILA = 'Parrilla'
    WOK = 'Wok'
    SIN_COCCION = 'Sin coccion'
    
    MEDIOS_CHOICES = [
        (INDISTINTO, '-'),
        (HORNO, 'Horno'),
        (COCINA, 'Cocina'),
        (PARRILA, 'Parrilla'),
        (WOK,'Wok'),
        (SIN_COCCION,'Sin cocción'),
    ]
    medios = models.CharField(max_length=20, choices=MEDIOS_CHOICES, default=COCINA, null=True)
   
    INDISTINTO = '-'
    COMUN = 'Común'
    ESPECIAL = 'Especial'
       
    CATEGORIA_CHOICES = [
        (INDISTINTO, '-'),
        (COMUN, 'Común'),
        (ESPECIAL, 'Especial'),
        
    ]
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default=COMUN, null=True)

    INDISTINTO = '-'
    POCO = 'Poco'
    NADA = 'Nada'
    NORMAL = 'Normal'
       
    PREPA_CHOICES = [
        (INDISTINTO, '-'),
        (POCO, 'Poco'),
        (NADA, 'Nada'),
        (NORMAL, 'Normal'),

    ]
    dificultad = models.CharField(max_length=20, choices=PREPA_CHOICES, default=NORMAL, null=True)

    INDISTINTO = '-'
    ENTRADA = 'Entrada'
    SALSA = 'Salsa'
    PICADA = 'Picada'
    PRINCIPAL = 'Principal'
    POSTRE = 'Postre'
    TORTA = 'Torta'
    UNTABLE = 'Dip'
    TRAGO = 'Trago'
    GUARNICION = 'Guarnicion'

    TIPO_CHOICES = [
        (INDISTINTO, '-'),
        (ENTRADA, 'Entrada'),
        (SALSA, 'Salsa'),
        (PICADA, 'Picada'),
        (PRINCIPAL,'Plato Principal'),
        (POSTRE,'Postre'),
        (TORTA,'Torta'),
        (UNTABLE,'Dip'),
        (TRAGO,'Trago'),
        (GUARNICION,'Guarnicion'),
    ]
    
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, null=False, default="", blank=False)

    INDISTINTO = '-'
    CALORICO = 'Calórico'
    LIVIANO = 'Liviano'
    NORMAL = 'Normal'
    INVIERNO = 'Plato de invierno'
  
    CALORIAS_CHOICES = [
        (INDISTINTO, '-'),
        (CALORICO, 'Calórico'),
        (LIVIANO, 'Liviano'),
        (NORMAL, 'Normal'),
        (INVIERNO,'Plato de invierno'),
   
    ]

    calorias = models.CharField(max_length=20, choices=CALORIAS_CHOICES, default=NORMAL,null=True)  

    propietario = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name="propietario")
    image = models.ImageField("Subí una imagen que identifique al plato (o un fotograma del mismo)", upload_to="videos/", null=True, blank=True)
    # fecha_video= models.DateTimeField("Fecha de captura del video:")
    variedades = models.JSONField(null=True, blank=True)


    @property
    def image_url(self):
        return self.image.url if self.image else '/media/avatares/logo.jpg'

    def __str__(self):
        return f"{self.id} - {self.nombre_plato}"
    

class Sugeridos(models.Model):    
     usuario_de_sugeridos = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name="usuario_sugeridos", null=True, blank=True)
    #  usuario_de_sugeridos = models.OneToOneField(User, on_delete=models.CASCADE, related_name="usuario_sugeridos")
     nombre_plato_sugerido = models.CharField(max_length=30) 
     
# #     Uso de ForeignKey: En tus modelos PlatosSeleccionados y Elegidos, estás usando ForeignKey a User. Si estos modelos están relacionados con el usuario autenticado, considera usar OneToOneField en lugar de ForeignKey para garantizar que solo haya una instancia por usuario.
# En este ejemplo, el campo usuario en el modelo PerfilUsuario es un OneToOneField que apunta al modelo de usuario predeterminado de Django (User). Esto significa que cada instancia de PerfilUsuario está asociada a exactamente una instancia de User, y viceversa. La opción on_delete=models.CASCADE especifica que si se elimina el usuario, también se eliminará automáticamente su perfil de usuario asociado.

class ElegidosXDia(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="usuario_que_come", null=True)
    el_dia_en_que_comemos = models.DateField(null=True)  # Campo de fecha
    platos_que_comemos = models.JSONField(null=True, blank=True)

    def __str__(self):
         return f'Menu Elegido {self.el_dia_en_que_comemos}' 

class Profile(models.Model):
     user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
     nombre = models.CharField(max_length=50, null=True, blank=True)
     apellido = models.CharField(max_length=50, null=True, blank=True)
     telefono = models.CharField(max_length=15, null=True, blank=True)
     avatar = models.ImageField(upload_to="avatares", null=True, blank=True)
     ingredientes_que_tengo = models.JSONField(default=list, blank=True)
    #  por qué default list?
     comentarios = models.JSONField(default=list, blank=True)
     amigues = models.JSONField(default=list, blank=True)
     sugeridos_descartados = models.JSONField(default=list, blank=True)
     sugeridos_importados = models.JSONField(default=list, blank=True)

     @property
     def avatar_url(self):
        return self.avatar.url if self.avatar else '/media/avatares/logo.png'
     
     def __str__(self):
        return f"Perfil de {self.user}"
     
     
class Mensaje(models.Model):
    usuario_que_envia = models.CharField(max_length=15, null=True, blank=True)
    mensaje = models.TextField(max_length=1000)
    amistad = models.CharField(max_length=9, null=True, blank=True)
    nombre_plato_compartido =  models.CharField(max_length=30, null=True, blank=True)
    creado_el = models.DateTimeField(auto_now_add=True) 
    destinatario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="mensajes")
    # Nuevo campo para el estado de leído
    leido = models.BooleanField(default=False)  # Se marca como no leído por defecto


    def __str__(self):
        return f"Mensaje de {self.usuario_que_envia} a {self.destinatario.username}"