from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_delete  # Agrega esta línea



class Plato(models.Model):
    nombre_plato = models.CharField(max_length=30)
    receta = models.CharField(max_length=80, blank=True)
    descripcion_plato = models.CharField(max_length=300, blank=True)
    ingredientes = models.CharField('Ingresá los ingredientes, separados por coma', max_length=120, blank=True)

    INDISTINTO = '-'
    HORNO = 'horno'
    COCINA = 'cocina'
    PARRILA = 'parrilla'
    WOK = 'wok'
    SIN_COCCION = 'sin coccion'
    
    MEDIOS_CHOICES = [
        (INDISTINTO, '-'),
        (HORNO, 'horno'),
        (COCINA, 'cocina'),
        (PARRILA, 'parrilla'),
        (WOK,'wok'),
        (SIN_COCCION,'sin cocción'),
    ]
    medios = models.CharField(max_length=20, choices=MEDIOS_CHOICES, default=INDISTINTO, null=True)
   
    INDISTINTO = '-'
    COMUN = 'Común'
    ESPECIAL = 'Especial'
       
    CATEGORIA_CHOICES = [
        (INDISTINTO, '-'),
        (COMUN, 'Común'),
        (ESPECIAL, 'Especial'),
        
    ]
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default=INDISTINTO, null=True)

    INDISTINTO = '-'
    POCO = 'Poco'
    NADA = 'Nada'
       
    PREPA_CHOICES = [
        (INDISTINTO, '-'),
        (POCO, 'Poco'),
        (NADA, 'Nada'),
    ]
    preparacion = models.CharField(max_length=20, choices=PREPA_CHOICES, default=INDISTINTO, null=True)

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

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, null=False, blank=False)

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

    calorias = models.CharField(max_length=20, choices=CALORIAS_CHOICES, default=INDISTINTO,null=True)  

    propietario = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name="propietario")
    image = models.ImageField("Subí una imagen que identifique al plato (o un fotograma del mismo)", upload_to="videos/", null=True, blank=True)
    # fecha_video= models.DateTimeField("Fecha de captura del video:")
    variedades = models.JSONField(null=True, blank=True)


    @property
    def image_url(self):
        return self.image.url if self.image else '/media/avatares/logo.jpg'

    def __str__(self):
        return f"{self.id} - {self.nombre_plato}"
    
# ESTO DEBERÍA BORRAR HAMBURGUESA DE TODOS LOS USUARIOS PORQUE SI ALGUIEN LA PRESELECCIONÓ, YA NO ESTARÁ
@receiver(post_delete, sender=Plato)
def eliminar_registros_relacionados(sender, instance, **kwargs):
    Preseleccionados.objects.filter(usuario=instance.propietario, nombre_plato_elegido=instance.nombre_plato).delete()
    
class Preseleccionados(models.Model):
    usuario = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name="platos_preseleccionados", null=True, blank=True)
    # EL SIGUIENTE CAMPO DEBERÍA LLAMARSE "PLATOS_PRESELECCIONADOS"
    nombre_plato_preseleccionado = models.CharField(max_length=30)
    # indica si es guarnicion, salsa, o lo que sea
    tipo_plato = models.CharField(max_length=30, null=True)


    # id_usuario_que_lo_cargo = models.CharField(max_length=30)
  
    # usuario = models.OneToOneField(to=User, on_delete=models.CASCADE, related_name="platos_elegidos", null=True, blank=True)

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
         return f'Menu Elegido {self.id}' 

class Profile(models.Model):
     user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
     nombre = models.CharField(max_length=50, null=True, blank=True)
     apellido = models.CharField(max_length=50, null=True, blank=True)
     telefono = models.CharField(max_length=15, null=True, blank=True)
     avatar = models.ImageField(upload_to="avatares", null=True, blank=True)
     ingredientes_que_tengo = models.JSONField(default=list, blank=True)
    #  por qué default list?
     comentarios = models.JSONField(default=list, blank=True) 

     @property
     def avatar_url(self):
        return self.avatar.url if self.avatar else '/media/avatares/logo.png'
     
     
class Mensaje(models.Model):
    mensaje = models.TextField(max_length=1000)
    email = models.EmailField()
    creado_el = models.DateTimeField(auto_now_add=True) 
    destinatario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="mensajes")


