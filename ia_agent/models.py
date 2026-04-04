from django.db import models
from extractor.models import Ticket, SolicitudPruebas, Proyecto, Cliente
from django.utils import timezone
from django.conf import settings

class Requerimiento(models.Model):
    """Modelo para almacenar requerimientos extraídos de diferentes fuentes"""
    TIPO_FUENTE = [
        ('ticket', 'Ticket'),
        ('solicitud', 'Solicitud de Pruebas'),
        ('url', 'URL'),
        ('texto', 'Texto Libre'),
    ]
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('procesando', 'Procesando'),
        ('completado', 'Completado'),
        ('error', 'Error'),
    ]
    
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, null=True, blank=True, related_name='requerimientos')
    solicitud = models.ForeignKey(SolicitudPruebas, on_delete=models.CASCADE, null=True, blank=True, related_name='requerimientos')
    
    # 👇 AGREGAR ESTOS CAMPOS FALTANTES
    proyecto = models.ForeignKey('extractor.Proyecto', on_delete=models.SET_NULL, null=True, blank=True, related_name='requerimientos')
    cliente = models.ForeignKey('extractor.Cliente', on_delete=models.SET_NULL, null=True, blank=True, related_name='requerimientos')
    tipo_servicio = models.ForeignKey('extractor.TipoServicio', on_delete=models.SET_NULL, null=True, blank=True, related_name='requerimientos')
    
    titulo = models.CharField(max_length=500)
    descripcion = models.TextField()
    fuente = models.CharField(max_length=20, choices=TIPO_FUENTE)
    url_origen = models.URLField(null=True, blank=True)
    
    contenido_extraido = models.TextField(help_text="Contenido extraído de la fuente")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Requerimiento'
        verbose_name_plural = 'Requerimientos'
    
    def __str__(self):
        return f"{self.titulo} - {self.get_fuente_display()}"


class CasoPrueba(models.Model):
    """Modelo para almacenar casos de prueba generados por IA"""
    PRIORIDAD_CHOICES = [
        ('alta', 'Alta'),
        ('media', 'Media'),
        ('baja', 'Baja'),
    ]
    
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('modificado', 'Modificado'),
    ]
    
    requerimiento = models.ForeignKey(Requerimiento, on_delete=models.CASCADE, related_name='casos_prueba')
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, null=True, blank=True, related_name='casos_prueba')
    solicitud = models.ForeignKey(SolicitudPruebas, on_delete=models.CASCADE, null=True, blank=True, related_name='casos_prueba')
    proyecto = models.ForeignKey(Proyecto, on_delete=models.SET_NULL, null=True, blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Datos del caso de prueba
    identificador = models.CharField(max_length=50, help_text="Ej: TC-001")
    titulo = models.CharField(max_length=500)
    descripcion = models.TextField()
    
    # Detalles del caso de prueba
    precondiciones = models.TextField(blank=True, help_text="Condiciones que deben cumplirse antes de ejecutar")
    pasos = models.JSONField(default=list, help_text="Lista de pasos a seguir")
    resultados_esperados = models.JSONField(default=list, help_text="Resultados esperados por cada paso")
    
    # Datos de prueba
    datos_prueba = models.JSONField(default=dict, blank=True, help_text="Datos necesarios para la prueba")
    
    prioridad = models.CharField(max_length=10, choices=PRIORIDAD_CHOICES, default='media')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='borrador')
    
    # Metadatos
    version = models.IntegerField(default=1)
    created_by = models.ForeignKey(  # ← SOLO UNA VEZ
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['identificador']
        verbose_name = 'Caso de Prueba'
        verbose_name_plural = 'Casos de Prueba'
    
    def __str__(self):
        return f"{self.identificador} - {self.titulo}"


class EjecucionPrueba(models.Model):
    """Modelo para registrar ejecuciones de casos de prueba"""
    RESULTADO_CHOICES = [
        ('exitoso', 'Exitoso'),
        ('fallido', 'Fallido'),
        ('bloqueado', 'Bloqueado'),
        ('no_aplicable', 'No Aplicable'),
        ('pendiente', 'Pendiente'),
    ]
    
    caso_prueba = models.ForeignKey(CasoPrueba, on_delete=models.CASCADE, related_name='ejecuciones')
    ejecutado_por = models.ForeignKey(  # ← SOLO UNA VEZ
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    fecha_ejecucion = models.DateTimeField(default=timezone.now)
    
    resultado = models.CharField(max_length=20, choices=RESULTADO_CHOICES, default='pendiente')
    observaciones = models.TextField(blank=True)
    evidencias = models.JSONField(default=list, blank=True, help_text="URLs o rutas de evidencias")
    
    tiempo_ejecucion = models.DurationField(null=True, blank=True, help_text="Tiempo total de ejecución")
    entorno = models.CharField(max_length=100, blank=True, help_text="Entorno donde se ejecutó")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-fecha_ejecucion']
        verbose_name = 'Ejecución de Prueba'
        verbose_name_plural = 'Ejecuciones de Pruebas'
    
    def __str__(self):
        return f"{self.caso_prueba.identificador} - {self.get_resultado_display()} - {self.fecha_ejecucion}"