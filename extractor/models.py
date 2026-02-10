from django.db import models

class Cliente(models.Model):
    nombre = models.CharField(max_length=255, verbose_name="Nombre del Cliente")
    nomenclatura = models.CharField(
        max_length=5, 
        verbose_name="Nomenclatura (máx. 5 caracteres)",
        unique=True
    )
    activo = models.BooleanField(default=True, verbose_name="¿Activo?")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.nomenclatura})"
    
class Proyecto(models.Model):
    cliente = models.ForeignKey(
        Cliente, 
        on_delete=models.CASCADE,
        verbose_name="Cliente",
        related_name='proyectos'
    )
    nombre = models.CharField(max_length=255, verbose_name="Nombre del Proyecto")
    codigo = models.CharField(
        max_length=20,
        verbose_name="Código del Proyecto",
        unique=True
    )

    nomenclatura = models.CharField(
        max_length=10,
        verbose_name="Nomenclatura del Proyecto",
        help_text="Abreviatura del proyecto (ej: B2C, DLW, SPM, etc.)"
    )
    
    # CAMPO NUEVO: Relación con TipoServicio (opcional, puedes usar choices si prefieres)
    tipo_servicio = models.ForeignKey(
        'TipoServicio',
        on_delete=models.SET_NULL,
        verbose_name="Tipo de Servicio",
        null=True,
        blank=True
    )
    descripcion = models.TextField(verbose_name="Descripción", blank=True)
    activo = models.BooleanField(default=True, verbose_name="¿Activo?")
    fecha_inicio = models.DateField(verbose_name="Fecha de Inicio", null=True, blank=True)
    fecha_fin = models.DateField(verbose_name="Fecha de Fin", null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Proyecto"
        verbose_name_plural = "Proyectos"
        ordering = ['cliente', 'nombre']
        unique_together = ['cliente', 'nombre']  # Un cliente no puede tener dos proyectos con el mismo nombre

    def __str__(self):
        return f"{self.nombre} - {self.cliente.nombre}"


class TipoServicio(models.Model):
    """Modelo para gestionar tipos de servicios"""
    id = models.AutoField(primary_key=True, verbose_name="ID")
    nombre = models.CharField(max_length=255, verbose_name="Nombre del Servicio")
    nomenclatura = models.CharField(
        max_length=10, 
        verbose_name="Nomenclatura (máx. 10 caracteres)",
        unique=True
    )
    activo = models.BooleanField(default=True, verbose_name="¿Activo?")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tipo de Servicio"
        verbose_name_plural = "Tipos de Servicio"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.nomenclatura})"

class ExcelData(models.Model):
    cliente = models.CharField(max_length=255, blank=True)
    proyecto = models.CharField(max_length=255, blank=True)
    tipo_servicio = models.CharField(max_length=10, blank=True, null=True)  
    tipo_pruebas = models.CharField(max_length=255, blank=True)
    responsable_solicitud = models.CharField(max_length=255, blank=True)
    lider_proyecto = models.CharField(max_length=255, blank=True)
    tipo_aplicacion = models.CharField(max_length=255, blank=True)
    numero_version = models.CharField(max_length=255, blank=True)
    funcionalidad_liberacion = models.TextField(blank=True)  # Nuevo campo
    detalle_cambios = models.TextField(blank=True)          # Nuevo campo
    justificacion_cambio = models.TextField(blank=True)  
    ticket_code = models.CharField(max_length=100, blank=True, null=True) 
    extracted_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Datos extraídos {self.extracted_date}"
    
class Ticket(models.Model):
    ESTADOS_TICKET = [
        ('GENERADO', 'Generado'),
        ('EN_PROCESO', 'En Proceso'),
        ('COMPLETADO', 'Completado'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    codigo = models.CharField(max_length=100, unique=True, verbose_name="Código del Ticket")
    
    # Relaciones con los modelos existentes
    excel_data = models.OneToOneField(
        ExcelData, 
        on_delete=models.CASCADE, 
        verbose_name="Datos del Excel",
        null=True,
        blank=True
    )
    cliente = models.ForeignKey(
        Cliente, 
        on_delete=models.SET_NULL, 
        verbose_name="Cliente",
        null=True,
        blank=True
    )
    proyecto = models.ForeignKey(
        Proyecto, 
        on_delete=models.SET_NULL, 
        verbose_name="Proyecto",
        null=True,
        blank=True
    )
    tipo_servicio = models.ForeignKey(
        TipoServicio, 
        on_delete=models.SET_NULL, 
        verbose_name="Tipo de Servicio",
        null=True,
        blank=True
    )
    
    # Partes del código del ticket (para búsqueda y filtrado)
    empresa_code = models.CharField(max_length=10, default="BID", verbose_name="Código Empresa")
    tipo_servicio_code = models.CharField(max_length=10, verbose_name="Código Tipo Servicio")
    funcion_code = models.CharField(max_length=20, verbose_name="Código Función")
    version_code = models.CharField(max_length=10, verbose_name="Código Versión")
    cliente_code = models.CharField(max_length=10, verbose_name="Código Cliente")
    proyecto_code = models.CharField(max_length=10, verbose_name="Código Proyecto")
    consecutivo = models.IntegerField(verbose_name="Consecutivo")
    
    # Datos adicionales del ticket
    responsable_solicitud = models.CharField(max_length=255, blank=True, verbose_name="Responsable")
    lider_proyecto = models.CharField(max_length=255, blank=True, verbose_name="Líder del Proyecto")
    numero_version = models.CharField(max_length=255, blank=True, verbose_name="Número de Versión")
    
    estado = models.CharField(
        max_length=20, 
        choices=ESTADOS_TICKET, 
        default='GENERADO',
        verbose_name="Estado del Ticket"
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de Actualización")

    class Meta:
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['codigo']),
            models.Index(fields=['estado']),
            models.Index(fields=['fecha_creacion']),
        ]
    
    def __str__(self):
        return f"{self.codigo} - {self.get_estado_display()} ({self.fecha_creacion.date()})"
    
    def get_detalle_partes(self):
        """Devuelve un diccionario con las partes del código"""
        return {
            'empresa': self.empresa_code,
            'tipo_servicio': self.tipo_servicio_code,
            'funcion': self.funcion_code,
            'version': self.version_code,
            'cliente': self.cliente_code,
            'proyecto': self.proyecto_code,
            'consecutivo': f"{self.consecutivo:03d}"
        }