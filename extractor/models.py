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
    

class SolicitudPruebas(models.Model):
    """Modelo para almacenar las solicitudes de pruebas creadas manualmente"""
    
    # Relación con el ticket (opcional por si se genera después)
    ticket = models.OneToOneField(
        Ticket,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Ticket Asociado",
        related_name='solicitud'
    )

    tiene_ticket = models.BooleanField(
        default=False,
        verbose_name="¿Tiene ticket?",
        help_text="Indica si la solicitud tiene un ticket asociado",
        db_index=True  
    )

    fecha_asociacion_ticket = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de asociación con ticket"
    )

    nombre_archivo = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Nombre del archivo generado",
        help_text="Formato: BID-PMC-FOR-00017-nomenclatura_AAAAMMDD-XXX.xlsx",
        db_index=True
    )
    
    
    # Datos de Solicitud
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        verbose_name="Cliente"
    )
    proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.PROTECT,
        verbose_name="Proyecto"
    )
    fecha_solicitud = models.DateField(verbose_name="Fecha de Solicitud")
    hora_solicitud = models.TimeField(verbose_name="Hora de Solicitud")
    
    # Tipo de Servicio y Pruebas
    tipo_servicio_code = models.CharField(
        max_length=3,
        choices=[
            ('PRU', 'Pruebas'),
            ('EST', 'Estimación'),
            ('G&A', 'Gestión y administración')
        ],
        verbose_name="Tipo de Servicio"
    )
    tipo_prueba = models.ForeignKey(
        TipoServicio,
        on_delete=models.PROTECT,
        verbose_name="Tipo de Pruebas"
    )
    area_solicitante = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Área Solicitante"
    )
    numero_version = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Número de Versión"
    )
    
    # Responsables
    responsable_solicitud = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Responsable de Solicitud"
    )
    lider_proyecto = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Líder de Proyecto"
    )
    
    # Información de Aplicación
    tipo_aplicacion = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Tipo de Aplicación",
        choices=[
            ('Portal WEB', 'Portal WEB'),
            ('App - Android', 'App - Android'),
            ('App - IOS', 'App - IOS'),
            ('App - Android & IOS', 'App - Android & IOS'),
            ('Servicio', 'Servicio'),
            ('Otro', 'Otro')
        ]
    )
    
    # Descripción de Cambios
    funcionalidad_liberacion = models.TextField(
        blank=True,
        verbose_name="Funcionalidad de la liberación"
    )
    detalle_cambios = models.TextField(
        blank=True,
        verbose_name="Detalle de los cambios"
    )
    justificacion_cambio = models.TextField(
        blank=True,
        verbose_name="Justificación del cambio"
    )
    
    # Puntos a Considerar y Pendientes
    puntos_considerar = models.TextField(
        blank=True,
        verbose_name="Puntos a Considerar"
    )
    pendientes = models.TextField(
        blank=True,
        verbose_name="Pendientes"
    )
    
    # Insumos Requeridos
    insumos = models.TextField(
        blank=True,
        verbose_name="Insumos Requeridos"
    )
    
    # Metadatos
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de Actualización")
    creado_por = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Creado por"
    )
    
    class Meta:
        verbose_name = "Solicitud de Pruebas"
        verbose_name_plural = "Solicitudes de Pruebas"
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['fecha_solicitud']),
            models.Index(fields=['cliente', 'proyecto']),
            models.Index(fields=['tiene_ticket']), 
        ]
    
    def __str__(self):
        if self.ticket:
            return f"Solicitud {self.ticket.codigo} - {self.cliente.nombre}"
        return f"Solicitud #{self.id} - {self.cliente.nombre} ({self.fecha_solicitud})"
   
    def generar_nombre_archivo(self):
        """
        Genera el nombre del archivo según el formato:
        BID-PMC-FOR-00017-nomenclatura_AAAAMMDD-XXX.xlsx
        """
        from django.utils import timezone
        
        # 1. Base fija
        base = "BID-PMC-FOR-00017"
        
        # 2. Nomenclatura del cliente (o usar 'CLI' si no hay)
        nomenclatura_cliente = self.cliente.nomenclatura if self.cliente else "CLI"
        
        # 3. Fecha actual en formato AAAAMMDD
        fecha_actual = timezone.now().strftime('%Y%m%d')
        
        # 4. Número consecutivo (buscar el último para hoy)
        # Buscar solicitudes de hoy para obtener el consecutivo
        hoy = timezone.now().date()
        solicitudes_hoy = SolicitudPruebas.objects.filter(
            fecha_creacion__date=hoy
        ).exclude(id=self.id)  # Excluir la actual si ya tiene ID
        
        # Obtener el último consecutivo usado hoy
        ultimo_consecutivo = 0
        for solicitud in solicitudes_hoy:
            if solicitud.nombre_archivo:
                # Extraer el consecutivo del nombre (los últimos 3 dígitos antes de .xlsx)
                import re
                match = re.search(r'-(\d{3})\.xlsx$', solicitud.nombre_archivo)
                if match:
                    consecutivo = int(match.group(1))
                    if consecutivo > ultimo_consecutivo:
                        ultimo_consecutivo = consecutivo
        
        # Si es una solicitud existente y ya tiene nombre, mantener su consecutivo
        if self.id and self.nombre_archivo:
            import re
            match = re.search(r'-(\d{3})\.xlsx$', self.nombre_archivo)
            if match:
                return self.nombre_archivo
        
        # Generar nuevo consecutivo
        consecutivo = ultimo_consecutivo + 1
        consecutivo_str = f"{consecutivo:03d}"
        
        # 5. Armar nombre completo
        nombre_completo = f"{base}-{nomenclatura_cliente}_{fecha_actual}-{consecutivo_str}.xlsx"
        
        return nombre_completo
    
    def get_estado_solicitud(self):
        """Devuelve el estado de la solicitud basado en el ticket asociado"""
        if self.ticket:
            return self.ticket.get_estado_display()
        return "Sin ticket"
    
    def generar_ticket(self, tipo_servicio_code=None, tipo_prueba_id=None):
        """
        Genera un ticket a partir de la solicitud
        """
        from .views import generate_ticket_parts
        
        if self.ticket:
            return self.ticket
        
        # Usar los valores de la solicitud si no se proporcionan
        tipo_servicio = tipo_servicio_code or self.tipo_servicio_code
        tipo_prueba_obj = tipo_prueba_id or self.tipo_prueba
        
        # Generar consecutivo
        tickets_existentes = Ticket.objects.filter(
            empresa_code="BID",
            tipo_servicio_code=tipo_servicio,
            funcion_code=self.tipo_prueba.nomenclatura,
            version_code=str(self.tipo_prueba.id),
            cliente_code=self.cliente.nomenclatura,
            proyecto_code=self.proyecto.codigo
        )
        
        if tickets_existentes.exists():
            max_consecutivo = tickets_existentes.aggregate(models.Max('consecutivo'))['consecutivo__max']
            consecutivo_num = (max_consecutivo or 0) + 1
        else:
            consecutivo_num = 1
        
        consecutivo_str = f"{consecutivo_num:03d}"
        
        # Generar código del ticket
        ticket_code = f"BID-{tipo_servicio}-{self.tipo_prueba.nomenclatura}-{self.tipo_prueba.id}-{self.cliente.nomenclatura}-{self.proyecto.codigo}-{consecutivo_str}"
        
        # Crear ExcelData asociado
        excel_data = ExcelData.objects.create(
            cliente=str(self.cliente.id),
            proyecto=str(self.proyecto.id),
            tipo_pruebas=str(self.tipo_prueba.id),
            tipo_servicio=tipo_servicio,
            responsable_solicitud=self.responsable_solicitud,
            lider_proyecto=self.lider_proyecto,
            tipo_aplicacion=self.tipo_aplicacion,
            numero_version=self.numero_version,
            funcionalidad_liberacion=self.funcionalidad_liberacion,
            detalle_cambios=self.detalle_cambios,
            justificacion_cambio=self.justificacion_cambio,
            ticket_code=ticket_code
        )
        
        # Crear el ticket
        ticket = Ticket.objects.create(
            codigo=ticket_code,
            empresa_code="BID",
            tipo_servicio_code=tipo_servicio,
            funcion_code=self.tipo_prueba.nomenclatura,
            version_code=str(self.tipo_prueba.id),
            cliente_code=self.cliente.nomenclatura,
            proyecto_code=self.proyecto.codigo,
            consecutivo=consecutivo_num,
            cliente=self.cliente,
            proyecto=self.proyecto,
            tipo_servicio=self.tipo_prueba,
            responsable_solicitud=self.responsable_solicitud,
            lider_proyecto=self.lider_proyecto,
            numero_version=self.numero_version,
            estado='GENERADO',
            excel_data=excel_data
        )
        
        # Asociar el ticket a la solicitud
        self.ticket = ticket
        self.save()
        
        return ticket