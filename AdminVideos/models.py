from django.db import models
from django.contrib.auth.models import User
from django.forms import ValidationError
import uuid
from django.conf import settings

class Lugar(models.Model):
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    enlace = models.URLField(max_length=200, blank=True, null=True)
    propietario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="lugares")
    dias_horarios = models.CharField(max_length=255, blank=True, null=True)  # Nuevo campo
    image = models.ImageField("Subí una imagen del lugar", upload_to="videos/", null=True, blank=True)
    delivery = models.BooleanField(default=True)  # Se marca como no delivery para distinguit el lugar de comerafuera (es false si es comerafuera)

    @property
    def image_url(self):
        try:
            return self.image.url
        except (ValueError, FileNotFoundError):
            return '/media/avatares/lugar.png'

    def __str__(self):
        # return f"{self.delivery} - {self.nombre} de {self.propietario}"
        tipo = "Delivery" if self.delivery else "Comerafuera"
        return f"{tipo} - {self.nombre} de {self.propietario}"

class TipoPlato(models.Model):
    nombre = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.nombre
    
class Plato(models.Model):
    nombre_plato = models.CharField(max_length=30)
    receta = models.CharField(max_length=80, blank=True)
    # descripcion_plato = models.CharField(max_length=300, blank=True)
    
    ingredientes = models.CharField('Ingresá los ingredientes, separados por coma', max_length=400, blank=True)

    # ingredientes_detallados = models.JSONField(null=True, blank=True,help_text="Estructura: [{'ingrediente': 'harina', 'cantidad': 200, 'unidad': 'g'}]")

    # Para campos de texto (CharField, TextField), se suele usar blank=True y no null=True, porque Django guarda vacío como "" en vez de NULL. Si no querés NULL en DB, podés hacer solo:
    proviene_de = models.CharField(max_length=20, blank=True, default="")
    id_original = models.IntegerField(null=True, blank=True)
    enlace = models.URLField(max_length=200, blank=True, null=True)
    porciones = models.PositiveIntegerField(null=True,blank=True, help_text="Cantidad de porciones que rinde este plato")

   
    # INDISTINTO = '-'
    HORNO = 'Horno'
    COCINA = 'Cocina'
    PARRILA = 'Parrilla'
    WOK = 'Wok'
    SIN_COCCION = 'Sin coccion'
    
    MEDIOS_CHOICES = [
        # (INDISTINTO, '-'),
        (HORNO, 'Horno'),
        (COCINA, 'Cocina'),
        (PARRILA, 'Parrilla'),
        (WOK,'Wok'),
        (SIN_COCCION,'Sin cocción'),
    ]
    medios = models.CharField(max_length=20, choices=MEDIOS_CHOICES, default=COCINA, null=True)
   
    INDISTINTO = 'Ambos'
    COTIDIANO = 'Cotidiano'
    ESPECIAL = 'Especial'  
       
    CATEGORIA_CHOICES = [
        (INDISTINTO, 'Ambos'),
        (COTIDIANO, 'Cotidiano'),
        (ESPECIAL, 'Especial'),
        
    ]
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default=COTIDIANO, null=True)
 
    elaboracion = models.IntegerField(null=True, blank=True)
    coccion = models.IntegerField(null=True, blank=True)

    # tipos = models.ManyToManyField(TipoPlato, related_name="platos")

    TIPOS_CHOICES = [
        ('Entrada', 'Entrada'),
        ('Guarnicion', 'Guarnición'),
        ('Trago', 'Trago'),
        ('Dip', 'Dip'),
        ('Torta', 'Torta'),
        ('Postre', 'Postre'),
        ('Principal', 'Principal'),
        ('Picada', 'Picada'),
        ('Salsa', 'Salsa'),
    ]

    tipos = models.CharField(
        max_length=200,
        blank=True,
        help_text="Seleccioná los tipos (Ej: Entrada,Principal,Postre)"
    )

    # INDISTINTO = '-'
    VERANO = 'Verano'
    INVIERNO = 'Invierno'
    TODO_EL_AÑO = 'Todo el año'
  
    ESTACIONALIDAD_CHOICES = [
        # (INDISTINTO, '-'),
        (VERANO, 'Verano'),
        (INVIERNO, 'Invierno'),
        (TODO_EL_AÑO, 'Todo el año'),
       ]

    estacionalidad = models.CharField(max_length=20, choices=ESTACIONALIDAD_CHOICES, default=TODO_EL_AÑO,null=True)  

    propietario = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name="propietario")

    image = models.ImageField("Subí una imagen que identifique al plato (o un fotograma del mismo)", upload_to="videos/", null=True, blank=True)
    # fecha_video= models.DateTimeField("Fecha de captura del video:")

    variedades = models.JSONField(null=True, blank=True)

    # @property
    # def image_url(self):
    #     return self.image.url if self.image else '/media/avatares/logo.png'
    
    @property
    def image_url(self):
        try:
            return self.image.url
        except (ValueError, FileNotFoundError):
            # return '/media/avatares/logo.png'
            return '/media/avatares/hoja_thumbnail.png'
        

    def __str__(self):
        return f"{self.id} - {self.nombre_plato} de {self.propietario}"
    
class VariedadPlato(models.Model):
    plato_base = models.ForeignKey(
        'Plato',
        on_delete=models.CASCADE,
        related_name='variedades_nuevas'
    )
    nombre = models.CharField(max_length=100)
    # descripcion = models.CharField(max_length=300, blank=True)
    ingredientes = models.CharField(max_length=400, blank=True)
    elaboracion = models.IntegerField(null=True, blank=True)
    coccion = models.IntegerField(null=True, blank=True)
    image = models.ImageField(upload_to="variedades/", null=True, blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.plato_base.nombre_plato} – {self.nombre}"


class Ingrediente(models.Model):
     # ===== Nivel 1: categoría (lugar de compra) =====
    VERDULERIA = "verduleria"
    FIAMBRERIA = "fiambreria"
    CARNICERIA = "carniceria"
    PESCADERIA = "pescaderia"
    PANADERIA = "panaderia"
    ALMACEN = "almacen"
    LACTEOS = "lacteos"
    BEBIDAS = "bebidas"
    OTRO = "otro"

    TIPO_CHOICES = [
        (VERDULERIA, "Verdulería"),
        (FIAMBRERIA, "Fiambriería"),
        (CARNICERIA, "Carnicería"),
        (PESCADERIA, "Pescadería"),
        (PANADERIA, "Panadería"),
        (ALMACEN, "Almacén"),
        (LACTEOS, "Lácteos"),
        (BEBIDAS, "Bebidas"),
        (OTRO, "Otro"),
    ]

    # ===== Nivel 2: detalle (subcategoría) =====
    VERDURA = "verdura"
    FRUTA = "fruta"
    TUBERCULO = "tuberculo"
    HIERBA_FRESCA = "hierba_fresca"

    CARNE_ROJA = "carne_roja"
    AVE = "ave"
    CERDO = "cerdo"
    CORDERO = "cordero"
    ACHURAS = "achuras"

    FIAMBRE = "fiambre"
    QUESO = "queso"
    EMBUTIDO = "embutido" 

    PESCADO = "pescado"
    MARISCO = "marisco"

    PAN = "pan"

    LEGUMBRE = "legumbre"
    CEREAL = "cereal"
    HARINA_BLANCA = "harina_blanca"
    ACEITE = "aceite"
    CONSERVA = "conserva"
    AZUCAR = "azucar"

    CONDIMENTO = "Condimento"
    ESPECIA = "especia"

    DETALLE_CHOICES_GROUPED = [
        ("Verdulería", [
            (VERDURA, "Verdura"),
            (FRUTA, "Fruta"),
            (TUBERCULO, "Tubérculo"),
            (HIERBA_FRESCA, "Hierba fresca"),
        ]),
        ("Carnicería", [
            (CARNE_ROJA, "Carne roja"),
            (AVE, "Ave"),
            (CERDO, "Cerdo"),
            (CORDERO, "Cordero"),
            (ACHURAS, "Achuras"),
        ]),
        ("Pescadería", [
            (PESCADO, "Pescado"),
            (MARISCO, "Marisco"),
        ]),
        ("Panadería", [
            (PAN, "Pan"),
        ]),
        ("Almacén", [
            (LEGUMBRE, "Legumbre"),
            (CEREAL, "Cereal"),
            (HARINA_BLANCA, "Harina Blanca"),
            (ACEITE, "Aceite"),
            (CONSERVA, "Conserva"),
            (AZUCAR, "Azúcar"),
            (ESPECIA, "Especia"),
        ]),
     
        ("Condimentos", [
            (ESPECIA, "Especia"),
            (CONDIMENTO, "Condimento"),
        ]),
      
        ("Otro", [
            (OTRO, "Otro"),
        ]),
    ]

    DETALLE_POR_TIPO = {
        VERDULERIA: {VERDURA, FRUTA, TUBERCULO, HIERBA_FRESCA},
        CARNICERIA: {CARNE_ROJA, AVE, CERDO, CORDERO, ACHURAS},
        PESCADERIA: {PESCADO, MARISCO},
        PANADERIA: {PAN},
        ALMACEN: {LEGUMBRE, CEREAL, HARINA_BLANCA, ACEITE, CONSERVA, AZUCAR, ESPECIA},
        FIAMBRERIA: {FIAMBRE, QUESO, EMBUTIDO},
        OTRO: {OTRO},
    }
    # ===== Campos =====
    nombre = models.CharField(
        max_length=100,
        unique=True,
        help_text="Nombre del ingrediente (p. ej., Zanahoria, Lentejas)."
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default=OTRO,
        help_text="Lugar de compra / categoría general."
    )
    detalle = models.CharField(
        max_length=30,
        choices=DETALLE_CHOICES_GROUPED,
        blank=True,
        help_text="Subcategoría (p. ej., Verdura, Fruta, Legumbre…)."
    )

    class Meta:
        ordering = ["nombre"]
        indexes = [
            models.Index(fields=["nombre"]),
        ]

    def clean(self):
        """
        Asegura que 'detalle' pertenezca al grupo correcto según 'tipo'.
        Permite dejar 'detalle' vacío si no lo querés usar.
        """
        super().clean()
        if self.detalle:
            permitidos = self.DETALLE_POR_TIPO.get(self.tipo, set())
            if self.detalle not in permitidos:
                raise ValidationError({
                    "detalle": f"El detalle “{self.get_detalle_display()}” no corresponde al tipo “{self.get_tipo_display()}”."
                })

    def __str__(self):
        det = f" – {self.get_detalle_display()}" if self.detalle else ""
        return f"{self.id} - {self.nombre} ({self.get_tipo_display()}{det})"
    

class IngredienteEnPlato(models.Model):
    UNIDADES_CHOICES = [
        ('-', '-'),  # Por si no aplica o se cuenta de otra forma
        ('unidad', 'unidad'),
        ('gr', 'gramo'),
        ('kg', 'kilogramo'),
        ('mg', 'miligramo'),
        ('ml', 'mililitro'),
        ('l', 'litro'),
        ('cdita', 'cucharadita'),         # cucharadita de té
        ('cda', 'cucharada'),             # cucharada sopera
        ('taza', 'taza'),
        ('pizca', 'pizca'),]

    plato = models.ForeignKey(Plato, on_delete=models.CASCADE, related_name='ingredientes_en_plato')
    ingrediente = models.ForeignKey(Ingrediente, on_delete=models.CASCADE,null=True, blank=True)
    cantidad = models.FloatField(null=True, blank=True)
    unidad = models.CharField(max_length=20, choices=UNIDADES_CHOICES, default='-', blank=True)

    def __str__(self):
        return f"{self.cantidad or ''} {self.unidad} de {self.ingrediente} en {self.plato}"


# class Sugeridos(models.Model):    
#      usuario_de_sugeridos = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name="usuario_sugeridos", null=True, blank=True)
#     #  usuario_de_sugeridos = models.OneToOneField(User, on_delete=models.CASCADE, related_name="usuario_sugeridos")
#      nombre_plato_sugerido = models.CharField(max_length=30) 
     
# #     Uso de ForeignKey: En tus modelos PlatosSeleccionados y Elegidos, estás usando ForeignKey a User. Si estos modelos están relacionados con el usuario autenticado, considera usar OneToOneField en lugar de ForeignKey para garantizar que solo haya una instancia por usuario.
# En este ejemplo, el campo usuario en el modelo PerfilUsuario es un OneToOneField que apunta al modelo de usuario predeterminado de Django (User). Esto significa que cada instancia de PerfilUsuario está asociada a exactamente una instancia de User, y viceversa. La opción on_delete=models.CASCADE especifica que si se elimina el usuario, también se eliminará automáticamente su perfil de usuario asociado.

class ElegidosXDia(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="usuario_que_come", null=True)
    el_dia_en_que_comemos = models.DateField(null=True)  # Campo de fecha
    platos_que_comemos = models.JSONField(null=True, blank=True)

    def __str__(self):
         return f'Menu Elegido {self.el_dia_en_que_comemos}'


class HistoricoDia(models.Model):
    fecha = models.DateField()
    dia_semana = models.CharField(max_length=2, blank=True)
    ya_sugerido = models.BooleanField(default=False)
    propietario = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('fecha', 'propietario')  # 👈 Esto es lo importante

    @property
    def nombre_dia(self):
        return self.fecha.strftime("%A").capitalize()

    def __str__(self):
        return f"Comidas del {self.fecha} ({self.nombre_dia})"


# class HistoricoDia(models.Model):
#     fecha = models.DateField(unique=True)
#     dia_semana = models.CharField(max_length=2, blank=True)  # "LU", "MA", ...
#     ya_sugerido = models.BooleanField(default=False)
#     propietario = models.ForeignKey(User, on_delete=models.CASCADE)

#     @property
#     def nombre_dia(self):
#         return self.fecha.strftime("%A").capitalize()

#     def __str__(self):
#         return f"Comidas del {self.fecha} ({self.nombre_dia})"




class HistoricoItem(models.Model):
    DESAYUNO = 'desayuno'
    ALMUERZO = 'almuerzo'
    MERIENDA = 'merienda'
    CENA = 'cena'

    MOMENTO_CHOICES = [
        (DESAYUNO, 'Desayuno'),
        (ALMUERZO, 'Almuerzo'),
        (MERIENDA, 'Merienda'),
        (CENA, 'Cena'),
    ]

    historico = models.ForeignKey(HistoricoDia, on_delete=models.CASCADE, related_name='items')

    # 👉 snapshot mínimo
    plato_id_ref = models.IntegerField()  # ID del Plato en el momento del guardado
    # plato_nombre_snapshot = models.CharField(max_length=100)  # nombre del Plato en ese momento (o lo que quieras “congelar”)

    momento = models.CharField(max_length=20, choices=MOMENTO_CHOICES)

    class Meta:
        unique_together = ('historico', 'plato_id_ref', 'momento')

    def __str__(self):
        return f"{self.historico.fecha} - {self.momento} - {self.plato_id_ref}"
        
        # ({self.plato_nombre_snapshot})"





class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    nombre = models.CharField(max_length=50, null=True, blank=True)
    apellido = models.CharField(max_length=50, null=True, blank=True)
    telefono = models.CharField(max_length=15, null=True, blank=True)
    avatar = models.ImageField(upload_to="avatares", null=True, blank=True)

    # Usamos default=list (callable) para evitar el problema de mutables como default
    ingredientes_que_tengo = models.JSONField(default=list, blank=True)
    comentarios = models.JSONField(default=list, blank=True)
    amigues = models.JSONField(default=list, blank=True)
    sugeridos_descartados = models.JSONField(default=list, blank=True)
    sugeridos_importados = models.JSONField(default=list, blank=True)


    # Para compartir la lista
    share_token = models.CharField(max_length=36, unique=True, blank=True, null=True)

    def ensure_share_token(self):
        """Genera un token si no existe y lo devuelve."""
        if not self.share_token:
            self.share_token = str(uuid.uuid4())
            # Si el modelo es nuevo y aún no fue guardado, no uses update_fields
            if self.pk:
                self.save(update_fields=["share_token"])
            else:
                self.save()
        return self.share_token

    @property
    def avatar_url(self):
        return self.avatar.url if self.avatar else "/media/avatares/user.png"

    def __str__(self):
        return f"Perfil de {self.user}"


# class Profile(models.Model):
#      user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
#      nombre = models.CharField(max_length=50, null=True, blank=True)
#      apellido = models.CharField(max_length=50, null=True, blank=True)
#      telefono = models.CharField(max_length=15, null=True, blank=True)
#      avatar = models.ImageField(upload_to="avatares", null=True, blank=True)
#      ingredientes_que_tengo = models.JSONField(default=list, blank=True)
#     #  por qué default list?
#      comentarios = models.JSONField(default=list, blank=True)
#      amigues = models.JSONField(default=list, blank=True)
#      sugeridos_descartados = models.JSONField(default=list, blank=True)
#      sugeridos_importados = models.JSONField(default=list, blank=True)

#      share_token = models.CharField(max_length=36, unique=True, blank=True, null=True)
#     # ingredientes_que_tengo: asumo que ya existe (lista en JSON/ArrayField/lo que uses)

#     def ensure_share_token(self):
#         if not self.share_token:
#             self.share_token = str(uuid.uuid4())
#             self.save(update_fields=["share_token"])
#         return self.share_token

#      @property
#      def avatar_url(self):
#         return self.avatar.url if self.avatar else '/media/avatares/user.png'
     
#      def __str__(self):
#         return f"Perfil de {self.user}"
     
    
     
     

class Mensaje(models.Model):
    usuario_que_envia = models.CharField(max_length=15, null=True, blank=True)
    
    mensaje = models.TextField(max_length=1000)

    AMISTAD = 'amistad'
    COMERAFUERA = 'comerafuera'
    DELIVERY = 'delivery'
    PLATO = 'plato'
    TEXTO = "texto"
        
    tipo_mensaje_CHOICES = [
        (AMISTAD, 'amistad'),
        (COMERAFUERA, 'comerafuera'),
        (DELIVERY, 'delivery'),
        (PLATO, 'plato'),
        (TEXTO,'texto')        
    ]
    tipo_mensaje = models.CharField(max_length=20, choices=tipo_mensaje_CHOICES, default=TEXTO, null=True)

    # tipo_mensaje = models.CharField(max_length=9, null=True, blank=True)
    id_elemento = models.IntegerField(null=True, blank=True)

    nombre_elemento_compartido =  models.CharField(max_length=30, null=True, blank=True)

    creado_el = models.DateTimeField(auto_now_add=True) 

    destinatario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="mensajes")
  
    # Nuevo campo para el estado de leído
    leido = models.BooleanField(default=False)  # Se marca como no leído por defecto

    importado = models.BooleanField(default=False)  # Se marca como no leído por defecto /// POR AHORA se marca TRUE cuando la amistad fue aceptada!!!

    # importado = models.BooleanField(default=False)  # Se marca como no leído por defecto
    borrado_antes = models.BooleanField(default=False)  # Se marca como no leído por defecto
       
    def __str__(self):
        return f"{self.id} - Mensaje de {self.usuario_que_envia} a {self.destinatario.username}"