"""
Vistas para gestión de Tipos de Servicio
"""
import csv
import traceback
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
import logging

from extractor.models import TipoServicio

logger = logging.getLogger(__name__)


@login_required
def tipos_servicio_list(request):
    try:
        tipos = TipoServicio.objects.filter(activo=True)
        
        orden = request.GET.get('orden', 'id')
        campos_validos = ['id', 'nombre', 'nomenclatura', 'activo', 'fecha_creacion']
        
        orden_final = 'id'
        if orden:
            orden_limpio = orden.lstrip('-')
            if orden_limpio in campos_validos:
                orden_final = orden
        
        tipos = tipos.order_by(orden_final)
        
        context = {'tipos': tipos}
        return render(request, 'catalogos/tipos_servicio_list.html', context)
        
    except Exception as e:
        logger.error(f"ERROR en tipo_servicio_list: {str(e)}")
        context = {
            'tipos': TipoServicio.objects.none(),
            'error': str(e)
        }
        return render(request, 'catalogos/tipos_servicio_list.html', context)


@login_required
def tipo_servicio_create(request):
    """Crear un nuevo tipo de servicio"""
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        nomenclatura = request.POST.get('nomenclatura', '').strip().upper()
        
        if not nombre or not nomenclatura:
            messages.error(request, 'Todos los campos son obligatorios')
            return render(request, 'catalogos/tipo_servicio_form.html')
        
        if len(nomenclatura) > 10:
            messages.error(request, 'La nomenclatura no puede tener más de 10 caracteres')
            return render(request, 'catalogos/tipo_servicio_form.html')
        
        if TipoServicio.objects.filter(nomenclatura=nomenclatura).exists():
            messages.error(request, f'La nomenclatura "{nomenclatura}" ya existe')
            return render(request, 'catalogos/tipo_servicio_form.html')
        
        try:
            tipo_servicio = TipoServicio.objects.create(
                nombre=nombre,
                nomenclatura=nomenclatura,
                activo=request.POST.get('activo', 'on') == 'on'
            )
            messages.success(request, f'Tipo de servicio "{tipo_servicio.nombre}" creado exitosamente')
            return redirect('extractor:tipos_servicio_list')
        except Exception as e:
            messages.error(request, f'Error al crear tipo de servicio: {str(e)}')
    
    return render(request, 'catalogos/tipo_servicio_form.html')


@login_required
def tipo_servicio_edit(request, id):
    """Editar un tipo de servicio existente"""
    tipo = get_object_or_404(TipoServicio, id=id)
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        nomenclatura = request.POST.get('nomenclatura', '').strip().upper()
        
        if not nombre or not nomenclatura:
            messages.error(request, 'Todos los campos son obligatorios')
            return render(request, 'catalogos/tipo_servicio_form.html', {'tipo': tipo})
        
        if len(nomenclatura) > 10:
            messages.error(request, 'La nomenclatura no puede tener más de 10 caracteres')
            return render(request, 'catalogos/tipo_servicio_form.html', {'tipo': tipo})
        
        if TipoServicio.objects.filter(nomenclatura=nomenclatura).exclude(id=id).exists():
            messages.error(request, f'La nomenclatura "{nomenclatura}" ya existe')
            return render(request, 'catalogos/tipo_servicio_form.html', {'tipo': tipo})
        
        try:
            tipo.nombre = nombre
            tipo.nomenclatura = nomenclatura
            tipo.activo = request.POST.get('activo', 'on') == 'on'
            tipo.save()
            
            messages.success(request, f'Tipo de servicio "{tipo.nombre}" actualizado exitosamente')
            return redirect('extractor:tipos_servicio_list')
        except Exception as e:
            messages.error(request, f'Error al actualizar tipo de servicio: {str(e)}')
    
    return render(request, 'catalogos/tipo_servicio_form.html', {'tipo': tipo})


@login_required
def tipo_servicio_delete(request, id):
    """Eliminar un tipo de servicio"""
    tipo = get_object_or_404(TipoServicio, id=id)
    
    if request.method == 'POST':
        try:
            nombre = tipo.nombre
            tipo.delete()
            messages.success(request, f'Tipo de servicio "{nombre}" eliminado exitosamente')
        except Exception as e:
            messages.error(request, f'Error al eliminar tipo de servicio: {str(e)}')
    
    return redirect('extractor:tipos_servicio_list')


@login_required
def export_tipos_servicio_csv(request):
    """Exporta tipos de servicio a CSV"""
    try:
        tipos = TipoServicio.objects.all()
        
        response = HttpResponse(content_type='text/csv')
        response.write('\ufeff'.encode('utf-8'))
        
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f"tipos_servicio_{timestamp}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'Nombre', 'Nomenclatura', 'Activo', 'Fecha Creación'])
        
        for tipo in tipos:
            writer.writerow([
                tipo.id,
                tipo.nombre,
                tipo.nomenclatura,
                'Sí' if tipo.activo else 'No',
                tipo.fecha_creacion.strftime('%d/%m/%Y %H:%M') if tipo.fecha_creacion else ''
            ])
        
        return response
        
    except Exception as e:
        logger.error(f"Error exportando tipos de servicio: {str(e)}")
        messages.error(request, "Error al exportar tipos de servicio")
        return redirect('extractor:tipos_servicio_list')