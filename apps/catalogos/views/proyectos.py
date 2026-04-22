"""
Vistas para gestión de Proyectos
"""
import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
import logging

from extractor.models import Cliente, Proyecto

logger = logging.getLogger(__name__)


@login_required
def proyectos_list(request):
    """Lista todos los proyectos con filtro por cliente opcional"""
    cliente_id = request.GET.get('cliente', '')
    
    if cliente_id:
        cliente = get_object_or_404(Cliente, id=cliente_id)
        proyectos = Proyecto.objects.filter(cliente=cliente).order_by('nombre')
    else:
        proyectos = Proyecto.objects.all().order_by('cliente__nombre', 'nombre')
    
    clientes = Cliente.objects.filter(activo=True).order_by('nombre')
    
    return render(request, 'catalogos/proyectos_list.html', {
        'proyectos': proyectos,
        'clientes': clientes,
        'cliente_filtro': cliente_id
    })


@login_required
def proyecto_create(request):
    """Crear un nuevo proyecto"""
    clientes = Cliente.objects.filter(activo=True).order_by('nombre')
    
    if request.method == 'POST':
        cliente_id = request.POST.get('cliente', '')
        nombre = request.POST.get('nombre', '').strip()
        codigo = request.POST.get('codigo', '').strip().upper()
        
        if not cliente_id or not nombre or not codigo:
            messages.error(request, 'Todos los campos obligatorios deben completarse')
            return render(request, 'catalogos/proyecto_form.html', {'clientes': clientes})
        
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            messages.error(request, 'Cliente no válido')
            return render(request, 'catalogos/proyecto_form.html', {'clientes': clientes})
        
        if Proyecto.objects.filter(codigo=codigo).exists():
            messages.error(request, f'El código "{codigo}" ya existe')
            return render(request, 'catalogos/proyecto_form.html', {'clientes': clientes})
        
        if Proyecto.objects.filter(cliente=cliente, nombre=nombre).exists():
            messages.error(request, f'Este cliente ya tiene un proyecto con el nombre "{nombre}"')
            return render(request, 'catalogos/proyecto_form.html', {'clientes': clientes})
        
        try:
            proyecto = Proyecto.objects.create(
                cliente=cliente,
                nombre=nombre,
                codigo=codigo,
                descripcion=request.POST.get('descripcion', '').strip(),
                activo=request.POST.get('activo', 'on') == 'on',
                fecha_inicio=request.POST.get('fecha_inicio') or None,
                fecha_fin=request.POST.get('fecha_fin') or None
            )
            messages.success(request, f'Proyecto "{proyecto.nombre}" creado exitosamente')
            return redirect('extractor:proyectos_list')
        except Exception as e:
            messages.error(request, f'Error al crear proyecto: {str(e)}')
    
    return render(request, 'catalogos/proyecto_form.html', {'clientes': clientes})


@login_required
def proyecto_edit(request, id):
    """Editar un proyecto existente"""
    proyecto = get_object_or_404(Proyecto, id=id)
    clientes = Cliente.objects.filter(activo=True).order_by('nombre')
    
    if request.method == 'POST':
        cliente_id = request.POST.get('cliente', '')
        nombre = request.POST.get('nombre', '').strip()
        codigo = request.POST.get('codigo', '').strip().upper()
        
        if not cliente_id or not nombre or not codigo:
            messages.error(request, 'Todos los campos obligatorios deben completarse')
            return render(request, 'catalogos/proyecto_form.html', {
                'proyecto': proyecto,
                'clientes': clientes
            })
        
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            messages.error(request, 'Cliente no válido')
            return render(request, 'catalogos/proyecto_form.html', {
                'proyecto': proyecto,
                'clientes': clientes
            })
        
        if Proyecto.objects.filter(codigo=codigo).exclude(id=id).exists():
            messages.error(request, f'El código "{codigo}" ya existe')
            return render(request, 'catalogos/proyecto_form.html', {
                'proyecto': proyecto,
                'clientes': clientes
            })
        
        if Proyecto.objects.filter(cliente=cliente, nombre=nombre).exclude(id=id).exists():
            messages.error(request, f'Este cliente ya tiene un proyecto con el nombre "{nombre}"')
            return render(request, 'catalogos/proyecto_form.html', {
                'proyecto': proyecto,
                'clientes': clientes
            })
        
        try:
            proyecto.cliente = cliente
            proyecto.nombre = nombre
            proyecto.codigo = codigo
            proyecto.descripcion = request.POST.get('descripcion', '').strip()
            proyecto.activo = request.POST.get('activo', 'on') == 'on'
            proyecto.fecha_inicio = request.POST.get('fecha_inicio') or None
            proyecto.fecha_fin = request.POST.get('fecha_fin') or None
            proyecto.save()
            
            messages.success(request, f'Proyecto "{proyecto.nombre}" actualizado exitosamente')
            return redirect('extractor:proyectos_list')
        except Exception as e:
            messages.error(request, f'Error al actualizar proyecto: {str(e)}')
    
    return render(request, 'catalogos/proyecto_form.html', {
        'proyecto': proyecto,
        'clientes': clientes
    })


@login_required
def proyecto_delete(request, id):
    """Eliminar un proyecto"""
    proyecto = get_object_or_404(Proyecto, id=id)
    
    if request.method == 'POST':
        try:
            nombre = proyecto.nombre
            proyecto.delete()
            messages.success(request, f'Proyecto "{nombre}" eliminado exitosamente')
        except Exception as e:
            messages.error(request, f'Error al eliminar proyecto: {str(e)}')
    
    return redirect('extractor:proyectos_list')


@login_required
def export_proyectos_csv(request):
    """Exporta proyectos a CSV"""
    try:
        proyectos = Proyecto.objects.all().select_related('cliente')
        
        response = HttpResponse(content_type='text/csv')
        response.write('\ufeff'.encode('utf-8'))
        
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f"proyectos_{timestamp}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'Cliente', 'Nombre', 'Código', 'Descripción', 'Activo', 'Fecha Inicio', 'Fecha Fin'])
        
        for proyecto in proyectos:
            writer.writerow([
                proyecto.id,
                proyecto.cliente.nombre if proyecto.cliente else '',
                proyecto.nombre,
                proyecto.codigo,
                proyecto.descripcion or '',
                'Sí' if proyecto.activo else 'No',
                proyecto.fecha_inicio.strftime('%d/%m/%Y') if proyecto.fecha_inicio else '',
                proyecto.fecha_fin.strftime('%d/%m/%Y') if proyecto.fecha_fin else ''
            ])
        
        return response
        
    except Exception as e:
        logger.error(f"Error exportando proyectos: {str(e)}")
        messages.error(request, "Error al exportar proyectos")
        return redirect('extractor:proyectos_list')



def proyectos_por_cliente(request, cliente_id):
    """Obtener proyectos de un cliente específico (para AJAX)"""
    try:
        proyectos = Proyecto.objects.filter(
            cliente_id=cliente_id, 
            activo=True
        ).order_by('nombre').values('id', 'nombre', 'codigo', 'nomenclatura')
        
        return JsonResponse({'proyectos': list(proyectos)})
        
    except Exception as e:
        return JsonResponse({'error': str(e), 'proyectos': []})