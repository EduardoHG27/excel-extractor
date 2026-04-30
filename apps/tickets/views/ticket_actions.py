"""
Vistas para acciones de Tickets (cambios de estado, asignación, comentarios)
"""
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils import timezone
import json
from extractor.jira_helper import JiraClient  # Cambiar de jira_integration a jira_helper
from extractor.models import Ticket, Usuario

@csrf_exempt
@login_required
def ticket_cambiar_estado(request, id):
    try:
        ticket = Ticket.objects.get(id=id)
        data = json.loads(request.body)
        nuevo_estado = data.get('estado')
        cerrar_en_jira = data.get('cerrar_en_jira', False)
        
        if not nuevo_estado:
            return JsonResponse({'success': False, 'error': 'Estado no proporcionado'})
        
        if nuevo_estado not in dict(Ticket.ESTADOS):
            return JsonResponse({'success': False, 'error': 'Estado inválido'})
        
        # Guardar estado anterior
        estado_anterior = ticket.estado
        
        # Cambiar estado del ticket
        ticket.estado = nuevo_estado
        
        # Si se completa o no es exitoso, cerrar en Jira
        jira_result = None
        if cerrar_en_jira and nuevo_estado in ['COMPLETADO', 'NO EXITOSO']:
            try:
                jira_client = JiraClient()
                # Verificar si el ticket tiene issue_key
                if hasattr(ticket, 'jira_issue_key') and ticket.jira_issue_key:
                    jira_result = jira_client.close_issue(
                        ticket.jira_issue_key,
                        resolution='Done' if nuevo_estado == 'COMPLETADO' else 'Cannot Reproduce'
                    )
                else:
                    jira_result = {
                        'success': False,
                        'warning': 'No se encontró issue_key asociado al ticket'
                    }
            except Exception as e:
                jira_result = {
                    'success': False,
                    'warning': f'Error al cerrar en Jira: {str(e)}'
                }
        
        # Si Jira falla, no impedimos el cambio de estado
        ticket.save()
        
        return JsonResponse({
            'success': True,
            'estado_display': ticket.get_estado_display(),
            'jira_result': jira_result
        })
        
    except Ticket.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Ticket no encontrado'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})



@login_required
def ticket_cambiar_asignado(request, id):
    """API para cambiar el usuario asignado a un ticket"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nuevo_asignado_id = data.get('asignado_a_id')
            
            ticket = get_object_or_404(Ticket, id=id)
            usuario_anterior = ticket.asignado_a
            
            if nuevo_asignado_id:
                nuevo_asignado = get_object_or_404(Usuario, id=nuevo_asignado_id)
                ticket.asignado_a = nuevo_asignado
            else:
                ticket.asignado_a = None
                nuevo_asignado = None
            
            ticket.save()
            
            usuario_actual = request.user.get_full_name() or request.user.username
            ahora_local = timezone.localtime(timezone.now())
            fecha_hora = ahora_local.strftime('%d/%m/%Y %H:%M')
            
            if usuario_anterior and nuevo_asignado:
                comentario = f"[{fecha_hora}] {usuario_actual} cambió la asignación de {usuario_anterior.get_full_name() or usuario_anterior.username} a {nuevo_asignado.get_full_name() or nuevo_asignado.username}"
            elif usuario_anterior and not nuevo_asignado:
                comentario = f"[{fecha_hora}] {usuario_actual} desasignó el ticket de {usuario_anterior.get_full_name() or usuario_anterior.username}"
            elif not usuario_anterior and nuevo_asignado:
                comentario = f"[{fecha_hora}] {usuario_actual} asignó el ticket a {nuevo_asignado.get_full_name() or nuevo_asignado.username}"
            else:
                comentario = f"[{fecha_hora}] {usuario_actual} actualizó la asignación del ticket"
            
            if ticket.comentarios_seguimiento:
                ticket.comentarios_seguimiento += f"\n{comentario}"
            else:
                ticket.comentarios_seguimiento = comentario
            ticket.save()
            
            return JsonResponse({
                'success': True,
                'asignado_nombre': nuevo_asignado.get_full_name() or nuevo_asignado.username if nuevo_asignado else None,
                'asignado_username': nuevo_asignado.username if nuevo_asignado else None
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@login_required
def ticket_agregar_comentario(request, id):
    """API para agregar comentario de seguimiento"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            comentario = data.get('comentario', '').strip()
            
            if not comentario:
                return JsonResponse({'success': False, 'error': 'Comentario vacío'})
            
            ticket = get_object_or_404(Ticket, id=id)
            
            usuario = request.user.get_full_name() or request.user.username
            ahora_local = timezone.localtime(timezone.now())
            fecha_hora = ahora_local.strftime('%d/%m/%Y %H:%M')
            
            comentario_formateado = f"[{fecha_hora}] {usuario}: {comentario}"
            
            if ticket.comentarios_seguimiento:
                ticket.comentarios_seguimiento += f"\n{comentario_formateado}"
            else:
                ticket.comentarios_seguimiento = comentario_formateado
            
            ticket.save()
            
            return JsonResponse({
                'success': True,
                'comentario_formateado': comentario_formateado
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@login_required
def ticket_cambiar_nombre(request, ticket_id):
    """API para cambiar el nombre de un ticket"""
    try:
        ticket = get_object_or_404(Ticket, id=ticket_id)
        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Datos inválidos'}, status=400)
        
        nuevo_nombre = data.get('nombre', '').strip()
        
        if nuevo_nombre:
            ticket.nombre = nuevo_nombre
        else:
            ticket.nombre = None
        
        ticket.save(update_fields=['nombre'])
        
        return JsonResponse({'success': True, 'nombre': ticket.nombre})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)