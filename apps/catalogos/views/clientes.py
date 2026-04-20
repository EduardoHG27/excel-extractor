"""
Vistas para gestión de Clientes
"""
import csv
import traceback
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpResponse
from django.utils import timezone
import logging

from extractor.models import Cliente

logger = logging.getLogger(__name__)


@login_required
def clientes_list(request):
    """Lista todos los clientes"""
    try:
        clientes = Cliente.objects.all()
        
        # Ordenamiento
        orden = request.GET.get('orden', 'id')
        orden_permitido = {
            'id': 'id', '-id': '-id',
            'nomenclatura': 'nomenclatura', '-nomenclatura': '-nomenclatura',
            'nombre': 'nombre', '-nombre': '-nombre',
            'activo': 'activo', '-activo': '-activo',
            'fecha_creacion': 'fecha_creacion', '-fecha_creacion': '-fecha_creacion',
        }
        
        orden_final = orden_permitido.get(orden, 'id')
        clientes = clientes.order_by(orden_final)
        clientes = clientes.annotate(total_proyectos=Count('proyectos'))
        
        return render(request, 'catalogos/clientes_list.html', {'clientes': clientes})
        
    except Exception as e:
        error_traceback = traceback.format_exc()
        logger.error(f"ERROR EN clientes_list: {str(e)}\n{error_traceback}")
        return HttpResponse(f"<h1>Error</h1><pre>{error_traceback}</pre>")


@login_required
def cliente_create(request):
    """Crear un nuevo cliente"""
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        nomenclatura = request.POST.get('nomenclatura', '').strip().upper()
        
        if not nombre or not nomenclatura:
            messages.error(request, 'Todos los campos son obligatorios')
            return render(request, 'catalogos/cliente_form.html')
        
        if len(nomenclatura) > 5:
            messages.error(request, 'La nomenclatura no puede tener más de 5 caracteres')
            return render(request, 'catalogos/cliente_form.html')
        
        if Cliente.objects.filter(nomenclatura=nomenclatura).exists():
            messages.error(request, f'La nomenclatura "{nomenclatura}" ya existe')
            return render(request, 'catalogos/cliente_form.html')
        
        try:
            cliente = Cliente.objects.create(
                nombre=nombre,
                nomenclatura=nomenclatura,
                activo=request.POST.get('activo', 'on') == 'on'
            )
            messages.success(request, f'Cliente "{cliente.nombre}" creado exitosamente')
            return redirect('extractor:clientes_list')
        except Exception as e:
            messages.error(request, f'Error al crear cliente: {str(e)}')
    
    return render(request, 'catalogos/cliente_form.html')


@login_required
def cliente_edit(request, id):
    """Editar un cliente existente"""
    cliente = get_object_or_404(Cliente, id=id)
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        nomenclatura = request.POST.get('nomenclatura', '').strip().upper()
        
        if not nombre or not nomenclatura:
            messages.error(request, 'Todos los campos son obligatorios')
            return render(request, 'catalogos/cliente_form.html', {'cliente': cliente})
        
        if len(nomenclatura) > 5:
            messages.error(request, 'La nomenclatura no puede tener más de 5 caracteres')
            return render(request, 'catalogos/cliente_form.html', {'cliente': cliente})
        
        if Cliente.objects.filter(nomenclatura=nomenclatura).exclude(id=id).exists():
            messages.error(request, f'La nomenclatura "{nomenclatura}" ya existe')
            return render(request, 'catalogos/cliente_form.html', {'cliente': cliente})
        
        try:
            cliente.nombre = nombre
            cliente.nomenclatura = nomenclatura
            cliente.activo = request.POST.get('activo', 'on') == 'on'
            cliente.save()
            messages.success(request, f'Cliente "{cliente.nombre}" actualizado exitosamente')
            return redirect('extractor:clientes_list')
        except Exception as e:
            messages.error(request, f'Error al actualizar cliente: {str(e)}')
    
    return render(request, 'catalogos/cliente_form.html', {'cliente': cliente})


@login_required
def cliente_delete(request, id):
    """Eliminar un cliente"""
    cliente = get_object_or_404(Cliente, id=id)
    
    if request.method == 'POST':
        try:
            nombre = cliente.nombre
            cliente.delete()
            messages.success(request, f'Cliente "{nombre}" eliminado exitosamente')
        except Exception as e:
            messages.error(request, f'Error al eliminar cliente: {str(e)}')
    
    return redirect('extractor:clientes_list')


@login_required
def export_clientes_csv(request):
    """Exporta clientes a CSV"""
    try:
        clientes = Cliente.objects.all()
        
        response = HttpResponse(content_type='text/csv')
        response.write('\ufeff'.encode('utf-8'))
        
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f"clientes_{timestamp}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        import csv
        writer = csv.writer(response)
        writer.writerow(['ID', 'Nombre', 'Nomenclatura', 'Activo', 'Fecha Creación'])
        
        for cliente in clientes:
            writer.writerow([
                cliente.id, cliente.nombre, cliente.nomenclatura,
                'Sí' if cliente.activo else 'No',
                cliente.fecha_creacion.strftime('%d/%m/%Y %H:%M') if cliente.fecha_creacion else ''
            ])
        
        return response
        
    except Exception as e:
        logger.error(f"Error exportando clientes: {str(e)}")
        messages.error(request, "Error al exportar clientes")
        return redirect('extractor:clientes_list')