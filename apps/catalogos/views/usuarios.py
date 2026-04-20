"""
Vistas para gestión de Usuarios
"""
import csv
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
import logging

from extractor.models import Usuario, Cliente, Ticket

logger = logging.getLogger(__name__)


@login_required
def usuarios_list(request):
    """
    Lista todos los usuarios registrados en el sistema
    Solo accesible para superusuarios o usuarios con permisos especiales
    """
    if not request.user.is_superuser and not request.user.has_perm('auth.view_user'):
        messages.error(request, 'No tienes permiso para ver la lista de usuarios')
        return redirect('extractor:solicitud_list')
    
    usuarios = Usuario.objects.all().select_related('cliente_asociado')
    
    # Filtros
    rol = request.GET.get('rol')
    cliente_id = request.GET.get('cliente')
    search = request.GET.get('q')
    is_active = request.GET.get('activo')
    
    if rol:
        if rol == 'admin':
            usuarios = usuarios.filter(is_superuser=True)
        elif rol == 'staff':
            usuarios = usuarios.filter(is_staff=True, is_superuser=False)
        elif rol == 'user':
            usuarios = usuarios.filter(is_staff=False, is_superuser=False)
    
    if cliente_id:
        usuarios = usuarios.filter(cliente_asociado_id=cliente_id)
    
    if search:
        usuarios = usuarios.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(puesto__icontains=search)
        )
    
    if is_active == 'si':
        usuarios = usuarios.filter(is_active=True)
    elif is_active == 'no':
        usuarios = usuarios.filter(is_active=False)
    
    # Ordenamiento
    orden = request.GET.get('orden', '-date_joined')
    usuarios = usuarios.order_by(orden)
    
    # Paginación
    por_pagina = request.GET.get('por_pagina', 20)
    try:
        por_pagina = int(por_pagina)
    except ValueError:
        por_pagina = 20
    
    paginator = Paginator(usuarios, por_pagina)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'usuarios': page_obj,
        'page_obj': page_obj,
        'total_usuarios': Usuario.objects.count(),
        'usuarios_activos': Usuario.objects.filter(is_active=True).count(),
        'usuarios_inactivos': Usuario.objects.filter(is_active=False).count(),
        'admins': Usuario.objects.filter(is_superuser=True).count(),
        'staff': Usuario.objects.filter(is_staff=True, is_superuser=False).count(),
        'clientes': Cliente.objects.filter(activo=True),
        'filtro_rol': rol,
        'filtro_cliente': cliente_id,
        'filtro_activo': is_active,
        'busqueda': search or '',
        'orden_actual': orden,
        'por_pagina': por_pagina,
    }
    return render(request, 'catalogos/usuarios_list.html', context)


@login_required
def usuario_detail(request, id):
    """Ver detalle de un usuario específico"""
    if not request.user.is_superuser and request.user.id != id:
        messages.error(request, 'No tienes permiso para ver este perfil')
        return redirect('extractor:usuarios_list')
    
    usuario = get_object_or_404(Usuario, id=id)
    
    tickets_creados = Ticket.objects.filter(creado_por=usuario).order_by('-fecha_creacion')[:10]
    tickets_asignados = Ticket.objects.filter(asignado_a=usuario).order_by('-fecha_creacion')[:10]
    
    context = {
        'usuario': usuario,
        'tickets_creados': tickets_creados,
        'tickets_asignados': tickets_asignados,
        'total_tickets_creados': Ticket.objects.filter(creado_por=usuario).count(),
        'total_tickets_asignados': Ticket.objects.filter(asignado_a=usuario).count(),
    }
    return render(request, 'catalogos/usuario_detail.html', context)


@login_required
def usuario_create(request):
    """Crear un nuevo usuario manualmente (solo superusuarios)"""
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permiso para crear usuarios')
        return redirect('extractor:usuarios_list')
    
    if request.method == 'POST':
        try:
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            password = request.POST.get('password', '')
            password_confirm = request.POST.get('password_confirm', '')
            
            if not username or not email:
                messages.error(request, 'Usuario y email son obligatorios')
                return redirect('extractor:usuario_create')
            
            if Usuario.objects.filter(username=username).exists():
                messages.error(request, f'El usuario "{username}" ya existe')
                return redirect('extractor:usuario_create')
            
            if Usuario.objects.filter(email=email).exists():
                messages.error(request, f'El email "{email}" ya está registrado')
                return redirect('extractor:usuario_create')
            
            if password != password_confirm:
                messages.error(request, 'Las contraseñas no coinciden')
                return redirect('extractor:usuario_create')
            
            if len(password) < 8:
                messages.error(request, 'La contraseña debe tener al menos 8 caracteres')
                return redirect('extractor:usuario_create')
            
            usuario = Usuario.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=request.POST.get('first_name', ''),
                last_name=request.POST.get('last_name', ''),
                telefono=request.POST.get('telefono', ''),
                puesto=request.POST.get('puesto', ''),
            )
            
            cliente_id = request.POST.get('cliente_asociado')
            if cliente_id:
                usuario.cliente_asociado_id = cliente_id
            
            usuario.is_active = request.POST.get('is_active', 'on') == 'on'
            usuario.is_staff = request.POST.get('is_staff', 'off') == 'on'
            usuario.is_superuser = request.POST.get('is_superuser', 'off') == 'on'
            usuario.puede_generar_tickets = request.POST.get('puede_generar_tickets', 'on') == 'on'
            usuario.puede_ver_todos_tickets = request.POST.get('puede_ver_todos_tickets', 'off') == 'on'
            usuario.save()
            
            messages.success(request, f'✅ Usuario "{usuario.username}" creado exitosamente')
            return redirect('extractor:usuarios_list')
            
        except Exception as e:
            messages.error(request, f'Error al crear usuario: {str(e)}')
            return redirect('extractor:usuario_create')
    
    context = {
        'clientes': Cliente.objects.filter(activo=True),
    }
    return render(request, 'catalogos/usuario_create_form.html', context)


@login_required
def usuario_edit(request, id):
    """Editar un usuario existente"""
    if not request.user.is_superuser and request.user.id != id:
        messages.error(request, 'No tienes permiso para editar este usuario')
        return redirect('extractor:usuarios_list')
    
    usuario = get_object_or_404(Usuario, id=id)
    
    if request.method == 'POST':
        try:
            usuario.first_name = request.POST.get('first_name', '')
            usuario.last_name = request.POST.get('last_name', '')
            usuario.email = request.POST.get('email', '')
            usuario.telefono = request.POST.get('telefono', '')
            usuario.puesto = request.POST.get('puesto', '')
            
            cliente_id = request.POST.get('cliente_asociado')
            if cliente_id:
                usuario.cliente_asociado_id = cliente_id
            else:
                usuario.cliente_asociado = None
            
            if request.user.is_superuser:
                usuario.is_active = request.POST.get('is_active', 'off') == 'on'
                usuario.is_staff = request.POST.get('is_staff', 'off') == 'on'
                usuario.is_superuser = request.POST.get('is_superuser', 'off') == 'on'
                usuario.puede_generar_tickets = request.POST.get('puede_generar_tickets', 'off') == 'on'
                usuario.puede_ver_todos_tickets = request.POST.get('puede_ver_todos_tickets', 'off') == 'on'
            
            nueva_password = request.POST.get('new_password')
            if nueva_password:
                if len(nueva_password) >= 8:
                    usuario.set_password(nueva_password)
                    messages.success(request, 'Contraseña actualizada exitosamente')
                else:
                    messages.error(request, 'La contraseña debe tener al menos 8 caracteres')
                    return redirect('extractor:usuario_edit', id=usuario.id)
            
            usuario.save()
            messages.success(request, f'Usuario "{usuario.username}" actualizado exitosamente')
            
            if request.user.is_superuser:
                return redirect('extractor:usuarios_list')
            else:
                return redirect('extractor:usuario_detail', id=usuario.id)
                
        except Exception as e:
            messages.error(request, f'Error al actualizar usuario: {str(e)}')
            return redirect('extractor:usuario_edit', id=usuario.id)
    
    context = {
        'usuario': usuario,
        'clientes': Cliente.objects.filter(activo=True),
        'es_superusuario': request.user.is_superuser,
    }
    return render(request, 'catalogos/usuario_form.html', context)


@login_required
def usuario_delete(request, id):
    """Eliminar (desactivar) un usuario"""
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permiso para eliminar usuarios')
        return redirect('extractor:usuarios_list')
    
    usuario = get_object_or_404(Usuario, id=id)
    
    if usuario.id == request.user.id:
        messages.error(request, 'No puedes eliminarte a ti mismo')
        return redirect('extractor:usuarios_list')
    
    if request.method == 'POST':
        try:
            username = usuario.username
            usuario.is_active = False
            usuario.save()
            messages.success(request, f'Usuario "{username}" desactivado exitosamente')
        except Exception as e:
            messages.error(request, f'Error al desactivar usuario: {str(e)}')
    
    return redirect('extractor:usuarios_list')


@login_required
def usuario_activar(request, id):
    """Reactivar un usuario desactivado"""
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permiso para activar usuarios')
        return redirect('extractor:usuarios_list')
    
    usuario = get_object_or_404(Usuario, id=id)
    
    if request.method == 'POST':
        try:
            usuario.is_active = True
            usuario.save()
            messages.success(request, f'Usuario "{usuario.username}" activado exitosamente')
        except Exception as e:
            messages.error(request, f'Error al activar usuario: {str(e)}')
    
    return redirect('extractor:usuarios_list')


@login_required
def usuario_cambiar_rol(request, id):
    """Cambiar rol de usuario (API AJAX)"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'Permiso denegado'})
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            usuario = get_object_or_404(Usuario, id=id)
            nuevo_rol = data.get('rol')
            
            if nuevo_rol == 'admin':
                usuario.is_superuser = True
                usuario.is_staff = True
            elif nuevo_rol == 'staff':
                usuario.is_superuser = False
                usuario.is_staff = True
            elif nuevo_rol == 'user':
                usuario.is_superuser = False
                usuario.is_staff = False
            else:
                return JsonResponse({'success': False, 'error': 'Rol no válido'})
            
            usuario.save()
            
            return JsonResponse({
                'success': True,
                'rol_display': nuevo_rol
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@login_required
def export_usuarios_csv(request):
    """Exportar usuarios a CSV"""
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permiso para exportar usuarios')
        return redirect('extractor:usuarios_list')
    
    try:
        usuarios = Usuario.objects.all().select_related('cliente_asociado')
        
        response = HttpResponse(content_type='text/csv')
        response.write('\ufeff'.encode('utf-8'))
        
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f"usuarios_{timestamp}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Usuario', 'Email', 'Nombre', 'Apellido', 'Teléfono', 
            'Puesto', 'Cliente Asociado', 'Activo', 'Staff', 'Superusuario',
            'Puede Generar Tickets', 'Puede Ver Todos Tickets', 'Fecha Registro'
        ])
        
        for usuario in usuarios:
            writer.writerow([
                usuario.id,
                usuario.username,
                usuario.email,
                usuario.first_name,
                usuario.last_name,
                usuario.telefono or '',
                usuario.puesto or '',
                usuario.cliente_asociado.nombre if usuario.cliente_asociado else '',
                'Sí' if usuario.is_active else 'No',
                'Sí' if usuario.is_staff else 'No',
                'Sí' if usuario.is_superuser else 'No',
                'Sí' if usuario.puede_generar_tickets else 'No',
                'Sí' if usuario.puede_ver_todos_tickets else 'No',
                usuario.date_joined.strftime('%d/%m/%Y %H:%M') if usuario.date_joined else ''
            ])
        
        return response
        
    except Exception as e:
        logger.error(f"Error exportando usuarios: {str(e)}")
        messages.error(request, "Error al exportar usuarios")
        return redirect('extractor:usuarios_list')