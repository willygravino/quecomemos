from django.db import models
from django.contrib.auth.models import User

class Plato(models.Model):
    nombre_plato = models.CharField(max_length=30)
    receta = models.CharField(max_length=80, blank=False)
    descripcion_plato = models.CharField(max_length=300)
    ingredientes = models.CharField('Ingresá los ingredientes, separados por coma', max_length=120, blank=False)
    propietario = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name="propietario")
    image = models.ImageField("Subí una imagen que identifique al plato (o un fotograma del mismo)", upload_to="videos/", null=True, blank=True)
    # fecha_video= models.DateTimeField("Fecha de captura del video:")

    @property
    def image_url(self):
        return self.image.url if self.image else '/media/videos/nuestrotubo.png'

    def __str__(self):
        return f"{self.id} - {self.nombre_plato}"
    
    
class Profile(models.Model):
     user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
     nombre_completo = models.CharField(max_length=80, blank=False)
     avatar = models.ImageField(upload_to="avatares", null=True, blank=True)

     @property
     def avatar_url(self):
        return self.avatar.url if self.avatar else '/media/avatares/default-avatar.png'
     
     
class Mensaje(models.Model):
    mensaje = models.TextField(max_length=1000)
    email = models.EmailField()
    creado_el = models.DateTimeField(auto_now_add=True) 
    destinatario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="mensajes")


