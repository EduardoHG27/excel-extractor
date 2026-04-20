"""
Vistas públicas (sin autenticación)
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404
from django.urls import reverse

from extractor.models import Ticket


def consultar_ticket(request):
    """Vista pública para consultar tickets (sin autenticación)"""
    ticket = None
    error = None
    
    if request.method == 'POST':
        codigo_ticket = request.POST.get('codigo_ticket', '').strip().upper()
        
        if not codigo_ticket:
            error = 'Por favor ingresa un código de ticket'
        else:
            try:
                ticket = Ticket.objects.filter(codigo=codigo_ticket).first()
                
                if not ticket:
                    error = f'No se encontró ningún ticket con el código "{codigo_ticket}"'
                else:
                    if ticket.estado in ['CANCELADO']:
                        error = 'Este ticket no está disponible para consulta pública'
                        ticket = None
                    else:
                        if ticket.estado == 'COMPLETADO':
                            ticket.archivos = []
                            
                            if ticket.dictamen_pdf and str(ticket.dictamen_pdf):
                                url_dictamen = str(ticket.dictamen_pdf.url) if hasattr(ticket.dictamen_pdf, 'url') else str(ticket.dictamen_pdf)
                                nombre_dictamen = url_dictamen.split('/')[-1].split('?')[0]
                                extension = nombre_dictamen.split('.')[-1].lower() if '.' in nombre_dictamen else 'pdf'
                                
                                ticket.archivos.append({
                                    'nombre': f"Dictamen - {nombre_dictamen}",
                                    'tipo': extension,
                                    'tamanio': None,
                                    'fecha_subida': ticket.fecha_subida_dictamen,
                                    'url_descarga': reverse('extractor:descargar_archivo_publico', kwargs={
                                        'ticket_id': ticket.id, 
                                        'tipo': 'dictamen'
                                    })
                                })
                            
                            if ticket.evidencia_pdf and str(ticket.evidencia_pdf):
                                url_evidencia = str(ticket.evidencia_pdf.url) if hasattr(ticket.evidencia_pdf, 'url') else str(ticket.evidencia_pdf)
                                nombre_evidencia = url_evidencia.split('/')[-1].split('?')[0]
                                extension = nombre_evidencia.split('.')[-1].lower() if '.' in nombre_evidencia else 'pdf'
                                
                                ticket.archivos.append({
                                    'nombre': f"Evidencia - {nombre_evidencia}",
                                    'tipo': extension,
                                    'tamanio': None,
                                    'fecha_subida': ticket.fecha_subida_evidencia,
                                    'url_descarga': reverse('extractor:descargar_archivo_publico', kwargs={
                                        'ticket_id': ticket.id, 
                                        'tipo': 'evidencia'
                                    })
                                })
                        
            except Exception as e:
                error = f'Error al buscar el ticket: {str(e)}'
    
    total_tickets = Ticket.objects.count()
    tickets_abiertos = Ticket.objects.filter(estado__in=['GENERADO', 'ABIERTO', 'EN_PROCESO']).count()
    tickets_completados = Ticket.objects.filter(estado='COMPLETADO').count()
    
    context = {
        'ticket': ticket,
        'error': error,
        'total_tickets': total_tickets,
        'tickets_abiertos': tickets_abiertos,
        'tickets_completados': tickets_completados,
        'codigo_buscado': request.POST.get('codigo_ticket', '') if request.method == 'POST' else '',
    }
    return render(request, 'extractor/consultar_ticket.html', context)


def descargar_archivo_publico(request, ticket_id, tipo):
    """Vista pública para descargar archivos de un ticket completado"""
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    if ticket.estado != 'COMPLETADO':
        raise Http404("Este ticket no tiene archivos disponibles para descarga")
    
    if tipo == 'dictamen':
        archivo = ticket.dictamen_pdf
        nombre_base = "Dictamen"
    elif tipo == 'evidencia':
        archivo = ticket.evidencia_pdf
        nombre_base = "Evidencia"
    else:
        raise Http404("Tipo de archivo no válido")
    
    if not archivo:
        raise Http404("Archivo no encontrado")
    
    url = archivo.url
    if '?' in url:
        url += '&flags=attachment'
    else:
        url += '?flags=attachment'
    
    return redirect(url)