import os
import csv
import traceback
import pandas as pd
import zipfile
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db.models import Q, Count
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import ExcelData, Cliente ,TipoServicio, Proyecto, Ticket
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError, JsonResponse
from django.db import models
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows
from django.utils import timezone
from io import BytesIO

def extract_excel_data(file_path):
    """
    Extrae las celdas específicas según las reglas dadas
    """
    try:
        # Verificar que la hoja existe
        try:
            df = pd.read_excel(file_path, sheet_name='Solicitud de Pruebas V4', header=None)
        except ValueError as e:
            if "No sheet named" in str(e):
                raise Exception("El archivo no contiene la hoja 'Solicitud de Pruebas V4'")
            else:
                raise Exception(f"Error al leer el archivo: {str(e)}")
        
        # Inicializar diccionario para datos
        extracted_data = {}
        
        # Función auxiliar para limpiar valores numéricos con .0
        def clean_numeric_value(value):
            """Convierte valores como '6.0' a '6'"""
            if pd.isna(value):
                return ""
            
            str_value = str(value).strip()
            
            # Intentar convertir a número y eliminar .0 si es entero
            try:
                float_value = float(str_value)
                if float_value.is_integer():
                    return str(int(float_value))
                else:
                    return str(float_value)
            except ValueError:
                return str_value
        
        # LISTA DE VALIDACIONES OBLIGATORIAS
        campos_obligatorios = []
        
        # Extraer y validar CLIENTE (C5)
        try:
            cell_value = df.iat[4, 2] if pd.notna(df.iat[4, 2]) else ""
            cliente_valor = clean_numeric_value(cell_value)
            extracted_data['cliente'] = cliente_valor
            
            if not cliente_valor:
                campos_obligatorios.append("Cliente (celda C5)")
        except:
            extracted_data['cliente'] = ""
            campos_obligatorios.append("Cliente (celda C5)")
        
        # Extraer y validar PROYECTO (H5)
        try:
            cell_value = df.iat[4, 7] if pd.notna(df.iat[4, 7]) else ""
            proyecto_valor = clean_numeric_value(cell_value)
            extracted_data['proyecto'] = proyecto_valor
            
            if not proyecto_valor:
                campos_obligatorios.append("Proyecto (celda H5)")
        except:
            extracted_data['proyecto'] = ""
            campos_obligatorios.append("Proyecto (celda H5)")
        
        # Extraer y validar TIPO DE PRUEBAS (D8)
        try:
            cell_value = df.iat[7, 3] if pd.notna(df.iat[7, 3]) else ""
            tipo_pruebas_valor = clean_numeric_value(cell_value)
            extracted_data['tipo_pruebas'] = tipo_pruebas_valor
            
            if not tipo_pruebas_valor:
                campos_obligatorios.append("Tipo de Pruebas (celda D8)")
        except:
            extracted_data['tipo_pruebas'] = ""
            campos_obligatorios.append("Tipo de Pruebas (celda D8)")
        
        # Extraer responsable_solicitud (opcional)
        try:
            extracted_data['responsable_solicitud'] = str(df.iat[11, 3]) if pd.notna(df.iat[11, 3]) else ""
        except:
            extracted_data['responsable_solicitud'] = ""
        
        # Extraer lider_proyecto (opcional)
        try:
            extracted_data['lider_proyecto'] = str(df.iat[11, 9]) if pd.notna(df.iat[11, 9]) else ""
        except:
            extracted_data['lider_proyecto'] = ""
        
        # Extraer tipo_aplicacion (opcional)
        try:
            extracted_data['tipo_aplicacion'] = str(df.iat[16, 3]) if pd.notna(df.iat[16, 3]) else ""
        except:
            extracted_data['tipo_aplicacion'] = ""
        
        # Extraer numero_version (opcional)
        try:
            extracted_data['numero_version'] = str(df.iat[16, 12]) if pd.notna(df.iat[16, 12]) else ""
        except:
            extracted_data['numero_version'] = ""
        
        # Extraer funcionalidad_liberacion (opcional)
        try:
            funcionalidad = str(df.iat[19, 3]) if pd.notna(df.iat[19, 3]) else ""
            if pd.notna(df.iat[20, 3]):
                funcionalidad += "\n" + str(df.iat[20, 3])
            extracted_data['funcionalidad_liberacion'] = funcionalidad
        except:
            extracted_data['funcionalidad_liberacion'] = ""
        
        # Extraer detalle_cambios (opcional)
        try:
            detalle_cambios = ""
            row = 21
            while pd.notna(df.iat[row, 3]) and row < 30:
                detalle_cambios += str(df.iat[row, 3]) + "\n"
                row += 1
            extracted_data['detalle_cambios'] = detalle_cambios.strip()
        except:
            extracted_data['detalle_cambios'] = ""
        
        # Extraer justificacion_cambio (opcional)
        try:
            justificacion_row = None
            for row in range(21, 30):
                if pd.notna(df.iat[row, 2]) and "Justificación" in str(df.iat[row, 2]):
                    justificacion_row = row
                    break
            
            if justificacion_row is not None:
                content_row = justificacion_row + 1
                justificacion = ""
                while pd.notna(df.iat[content_row, 3]) and content_row < 40:
                    justificacion += str(df.iat[content_row, 3]) + "\n"
                    content_row += 1
                extracted_data['justificacion_cambio'] = justificacion.strip()
            else:
                extracted_data['justificacion_cambio'] = ""
        except:
            extracted_data['justificacion_cambio'] = ""
        
        # VALIDACIÓN FINAL: Si hay campos obligatorios faltantes, lanzar excepción
        if campos_obligatorios:
            mensaje_error = "El archivo no contiene los siguientes campos obligatorios:\n"
            mensaje_error += "\n".join(f"• {campo}" for campo in campos_obligatorios)
            raise Exception(mensaje_error)
        
        # DEPURACIÓN: Mostrar valores extraídos
        print("=== VALORES EXTRAÍDOS ===")
        for key, value in extracted_data.items():
            print(f"{key}: '{value}'")
        print("==========================")
        
        return extracted_data
        
    except Exception as e:
        print(f"Error al extraer datos: {e}")
        raise  # Re-lanzar la excepción para que la capture la vista

def upload_excel(request):
    if request.method == 'POST':
            # Obtener el tipo de servicio del formulario
            tipo_servicio_form = request.POST.get('tipo_servicio', '').strip()
            excel_file = request.FILES.get('excel_file')
            
            # Validar tipo de servicio
            if not tipo_servicio_form:
                messages.error(request, 'Por favor selecciona un tipo de servicio')
                return render(request, 'extractor/upload.html')
            
            if not excel_file:
                messages.error(request, 'Por favor selecciona un archivo Excel')
                return render(request, 'extractor/upload.html')
            
            # Validar extensión del archivo
            allowed_extensions = ['.xlsx', '.xls']
            file_extension = os.path.splitext(excel_file.name)[1].lower()
            
            if file_extension not in allowed_extensions:
                messages.error(request, 'Formato de archivo no válido. Solo se permiten archivos .xlsx y .xls')
                return render(request, 'extractor/upload.html')
            
            fs = FileSystemStorage()
            file_path = None
            
            try:
                # Guardar el archivo temporalmente
                filename = fs.save(excel_file.name, excel_file)
                file_path = os.path.join(settings.MEDIA_ROOT, filename)
                
                # VALIDACIÓN 1: Intentar extraer datos (esto lanzará excepción si faltan campos)
                extracted_data = extract_excel_data(file_path)
                
                # VALIDACIÓN 2: Verificar que los IDs existan en la base de datos
                campos_invalidos = []
                
                # Validar Cliente
                cliente_id_str = extracted_data.get('cliente', '').strip()
                cliente_obj = None
                if cliente_id_str:
                    try:
                        cliente_id = int(cliente_id_str)
                        cliente_obj = Cliente.objects.filter(id=cliente_id).first()
                        if not cliente_obj:
                            campos_invalidos.append(f"Cliente con ID {cliente_id} no existe en el catálogo")
                    except ValueError:
                        campos_invalidos.append(f"El valor del Cliente '{cliente_id_str}' no es un ID válido")
                else:
                    campos_invalidos.append("El campo Cliente está vacío")
                
                # Validar Proyecto
                proyecto_id_str = extracted_data.get('proyecto', '').strip()
                proyecto_obj = None
                if proyecto_id_str:
                    try:
                        proyecto_id = int(proyecto_id_str)
                        proyecto_obj = Proyecto.objects.filter(id=proyecto_id).first()
                        if not proyecto_obj:
                            campos_invalidos.append(f"Proyecto con ID {proyecto_id} no existe en el catálogo")
                    except ValueError:
                        campos_invalidos.append(f"El valor del Proyecto '{proyecto_id_str}' no es un ID válido")
                else:
                    campos_invalidos.append("El campo Proyecto está vacío")
                
                # Validar Tipo de Pruebas
                tipo_pruebas_id_str = extracted_data.get('tipo_pruebas', '').strip()
                tipo_servicio_obj = None
                if tipo_pruebas_id_str:
                    try:
                        tipo_pruebas_id = int(tipo_pruebas_id_str)
                        tipo_servicio_obj = TipoServicio.objects.filter(id=tipo_pruebas_id).first()
                        if not tipo_servicio_obj:
                            campos_invalidos.append(f"Tipo de Pruebas con ID {tipo_pruebas_id} no existe en el catálogo")
                    except ValueError:
                        campos_invalidos.append(f"El valor de Tipo de Pruebas '{tipo_pruebas_id_str}' no es un ID válido")
                else:
                    campos_invalidos.append("El campo Tipo de Pruebas está vacío")
                
                # Si hay campos inválidos, mostrar error y NO guardar
                if campos_invalidos:
                    mensaje_error = "❌ El archivo contiene errores que impiden generar el ticket:\n"
                    mensaje_error += "\n".join(f"• {campo}" for campo in campos_invalidos)
                    messages.error(request, mensaje_error)
                    
                    # Eliminar archivo temporal
                    if file_path and os.path.exists(file_path):
                        os.remove(file_path)
                        
                    return render(request, 'extractor/upload.html')
                
                # DEPURACIÓN: Mostrar qué se extrajo
                print("=== DATOS EXTRAÍDOS DEL EXCEL ===")
                print(f"Cliente ID (C5): '{extracted_data.get('cliente', '')}'")
                print(f"Proyecto ID (H5): '{extracted_data.get('proyecto', '')}'")
                print(f"Tipo prueba ID (D8): '{extracted_data.get('tipo_pruebas', '')}'")
                print(f"Tipo Servicio (formulario): '{tipo_servicio_form}'")
                print("==================================")
                
                # Inicializar nomenclaturas
                nomenclaturas = {
                    'cliente_nomenclatura': cliente_obj.nomenclatura if cliente_obj else '',
                    'proyecto_nomenclatura': proyecto_obj.codigo if proyecto_obj else '',
                    'tipo_pruebas_nomenclatura': tipo_servicio_obj.nomenclatura if tipo_servicio_obj else '',
                    'tipo_servicio_nomenclatura': tipo_servicio_form
                }
                
                # Inicializar objetos encontrados
                objetos_encontrados = {
                    'cliente_obj': cliente_obj,
                    'proyecto_obj': proyecto_obj,
                    'tipo_servicio_obj': tipo_servicio_obj
                }
                
                # Mostrar resumen de búsqueda
                print("\n=== RESUMEN DE BÚSQUEDA ===")
                print(f"Nomenclatura Cliente: {nomenclaturas['cliente_nomenclatura']}")
                print(f"Nomenclatura Proyecto: {nomenclaturas['proyecto_nomenclatura']}")
                print(f"Nomenclatura Tipo Pruebas: {nomenclaturas['tipo_pruebas_nomenclatura']}")
                print(f"Nomenclatura Tipo Servicio (formulario): {nomenclaturas['tipo_servicio_nomenclatura']}")
                print("===========================\n")
                
                # Generar ticket
                ticket_code, ticket_obj = generate_and_save_ticket(
                    extracted_data=extracted_data,
                    tipo_servicio_form=tipo_servicio_form,
                    nomenclaturas=nomenclaturas,
                    objetos_encontrados=objetos_encontrados
                )
                
                ticket_parts = generate_ticket_parts(ticket_code)
                
                # Guardar en la base de datos ExcelData
                excel_data = ExcelData.objects.create(
                    cliente=extracted_data.get('cliente', ''),
                    proyecto=extracted_data.get('proyecto', ''),
                    tipo_pruebas=extracted_data.get('tipo_pruebas', ''),
                    tipo_servicio=tipo_servicio_form,
                    responsable_solicitud=extracted_data.get('responsable_solicitud', ''),
                    lider_proyecto=extracted_data.get('lider_proyecto', ''),
                    tipo_aplicacion=extracted_data.get('tipo_aplicacion', ''),
                    numero_version=extracted_data.get('numero_version', ''),
                    funcionalidad_liberacion=extracted_data.get('funcionalidad_liberacion', ''),
                    detalle_cambios=extracted_data.get('detalle_cambios', ''),
                    justificacion_cambio=extracted_data.get('justificacion_cambio', ''),
                    ticket_code=ticket_code
                )
                
                # Asociar el ticket con los datos del Excel
                if ticket_obj:
                    ticket_obj.excel_data = excel_data
                    ticket_obj.save()
                
                # Mensaje de éxito
                messages.success(request, f'✅ Archivo procesado exitosamente. Ticket generado: {ticket_code}')
                
                # Preparar datos para la plantilla
                data_for_template = {
                    'cliente': excel_data.cliente,
                    'proyecto': excel_data.proyecto,
                    'tipo_pruebas': excel_data.tipo_pruebas,
                    'tipo_servicio': excel_data.tipo_servicio,
                    'responsable_solicitud': excel_data.responsable_solicitud,
                    'lider_proyecto': excel_data.lider_proyecto,
                    'tipo_aplicacion': excel_data.tipo_aplicacion,
                    'numero_version': excel_data.numero_version,
                    'funcionalidad_liberacion': excel_data.funcionalidad_liberacion,
                    'detalle_cambios': excel_data.detalle_cambios,
                    'justificacion_cambio': excel_data.justificacion_cambio,
                    'extracted_date': excel_data.extracted_date
                }
                
                return render(request, 'extractor/result.html', {
                    'data': data_for_template,
                    'excel_data': excel_data,
                    'nomenclaturas': nomenclaturas,
                    'objetos_encontrados': objetos_encontrados,
                    'ticket_code': ticket_code,
                    'ticket_parts': ticket_parts,
                    'ticket': ticket_obj,
                    'tipo_servicio_form': tipo_servicio_form
                })
                
            except Exception as e:
                print(f"❌ ERROR en procesamiento: {str(e)}")
                import traceback
                traceback.print_exc()
                
                # Mensaje de error amigable para el usuario
                error_message = str(e)
                if "no contiene los siguientes campos obligatorios" in error_message:
                    messages.error(request, error_message)
                else:
                    messages.error(request, f'Error al procesar el archivo: {error_message}')
                
                # Eliminar archivo temporal en caso de error
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
                    
                return render(request, 'extractor/upload.html')
            
    return render(request, 'extractor/upload.html')

# Añade esta función para generar el código del ticket
def generate_ticket_code(extracted_data, tipo_servicio):
    """Genera el código del ticket basado en los datos"""
    # Aquí puedes implementar tu lógica para generar el código del ticket
    # Ejemplo: BID-PRU-F&REG-10-TEL-OTR-001
    
    cliente_nom = "TEL"  # Obtener de la base de datos
    proyecto_nom = "OTR"  # Obtener de la base de datos
    version = extracted_data.get('numero_version', '10')
    
    # Determinar el código del tipo de servicio
    tipo_servicio_code = tipo_servicio  # Ya viene del formulario: PRU, EST, G&A
    
    consecutivo = "001"  # Deberías obtener este de la base de datos (último + 1)
    
    return f"BID-{tipo_servicio_code}-F&REG-{version}-{cliente_nom}-{proyecto_nom}-{consecutivo}"

def data_list(request):
    data = ExcelData.objects.all().order_by('-extracted_date')
    return render(request, 'extractor/list.html', {'data_list': data})

def clientes_list(request):
    try:
        clientes = Cliente.objects.all()
        
        # Debug: imprime los parámetros GET
        print(f"GET parameters: {request.GET}")
        
        # Ordenamiento
        orden = request.GET.get('orden', 'id')
        print(f"Orden solicitado: {orden}")
        
        # Diccionario de ordenamiento permitido
        orden_permitido = {
            'id': 'id', 
            '-id': '-id',
            'nomenclatura': 'nomenclatura', 
            '-nomenclatura': '-nomenclatura',
            'nombre': 'nombre', 
            '-nombre': '-nombre',
            'activo': 'activo', 
            '-activo': '-activo',
            'fecha_creacion': 'fecha_creacion', 
            '-fecha_creacion': '-fecha_creacion',
        }
        
        orden_final = orden_permitido.get(orden, 'id')
        print(f"Orden final: {orden_final}")
        
        clientes = clientes.order_by(orden_final)
        print(f"Query SQL: {clientes.query}")
        
        # Anotar con conteo de proyectos
        clientes = clientes.annotate(
            total_proyectos=Count('proyectos')
        )
        
        context = {
            'clientes': clientes,
        }
        return render(request, 'catalogos/clientes_list.html', context)
        
    except Exception as e:
        # Capturar el error completo
        error_traceback = traceback.format_exc()
        print(f"ERROR EN clientes_list: {str(e)}")
        print(f"Traceback: {error_traceback}")
        
        # Devolver el error en la respuesta para verlo en el navegador
        return HttpResponse(f"""
            <h1>Error en clientes_list</h1>
            <p><strong>Error:</strong> {str(e)}</p>
            <h2>Traceback:</h2>
            <pre>{error_traceback}</pre>
            <h2>GET parameters:</h2>
            <pre>{dict(request.GET)}</pre>
        """)

def cliente_create(request):
    """Crear un nuevo cliente"""
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        nomenclatura = request.POST.get('nomenclatura', '').strip().upper()
        
        # Validaciones
        if not nombre or not nomenclatura:
            messages.error(request, 'Todos los campos son obligatorios')
            return render(request, 'catalogos/cliente_form.html')
        
        if len(nomenclatura) > 5:
            messages.error(request, 'La nomenclatura no puede tener más de 5 caracteres')
            return render(request, 'catalogos/cliente_form.html')
        
        # Verificar si ya existe la nomenclatura
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
            return redirect('clientes_list')
        except Exception as e:
            messages.error(request, f'Error al crear cliente: {str(e)}')
    
    return render(request, 'catalogos/cliente_form.html')


def get_next_consecutivo(tipo_servicio_code, tipo_pruebas_nom, tipo_pruebas_id, cliente_nom, proyecto_nom):
    """Obtiene el siguiente número consecutivo para tickets con los mismos datos"""
    try:
        # Parámetros de búsqueda - CORREGIDO
        filtro = {
            'empresa_code': "BID",
            'tipo_servicio_code': tipo_servicio_code,
            'funcion_code': tipo_pruebas_nom,  # ← Esto es la nomenclatura
            'version_code': tipo_pruebas_id,    # ← Esto es el ID (valor numérico)
            'cliente_code': cliente_nom,
            'proyecto_code': proyecto_nom
        }
        
        print(f"🔍 Buscando tickets similares con filtro: {filtro}")
        
        # Buscar TODOS los tickets con los MISMOS parámetros
        tickets_similares = Ticket.objects.filter(**filtro)
        
        print(f"📊 Tickets encontrados: {tickets_similares.count()}")
        
        if tickets_similares.exists():
            for ticket in tickets_similares:
                print(f"   - {ticket.codigo} (consecutivo: {ticket.consecutivo})")
            
            max_consecutivo = tickets_similares.aggregate(models.Max('consecutivo'))['consecutivo__max']
            print(f"🎯 Máximo consecutivo encontrado: {max_consecutivo}")
            
            siguiente = max_consecutivo + 1
            print(f"🔄 Siguiente consecutivo: {siguiente}")
            return siguiente
        else:
            print(f"✨ No hay tickets similares, empezando en 1")
            return 1
    except Exception as e:
        print(f"⚠️ Error al obtener consecutivo: {str(e)}")
        traceback.print_exc()  # ← Añadir traceback completo
        return 1


def generate_ticket_parts(ticket_code):
    """Divide el código del ticket en partes para mostrar en el desglose"""
    parts = ticket_code.split('-')
    
    # Asegurar que tengamos 7 partes
    if len(parts) < 7:
        # Rellenar con valores por defecto si faltan partes
        default_parts = ['BID', 'PRU', 'F&REG', '10', 'TEL', 'OTR', '001']
        for i in range(7):
            if i >= len(parts) or not parts[i]:
                parts.append(default_parts[i])
    
    return parts


def cliente_edit(request, id):
    """Editar un cliente existente"""
    cliente = get_object_or_404(Cliente, id=id)
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        nomenclatura = request.POST.get('nomenclatura', '').strip().upper()
        
        # Validaciones
        if not nombre or not nomenclatura:
            messages.error(request, 'Todos los campos son obligatorios')
            return render(request, 'catalogos/cliente_form.html', {'cliente': cliente})
        
        if len(nomenclatura) > 5:
            messages.error(request, 'La nomenclatura no puede tener más de 5 caracteres')
            return render(request, 'catalogos/cliente_form.html', {'cliente': cliente})
        
        # Verificar si la nomenclatura ya existe (excluyendo el actual)
        if Cliente.objects.filter(nomenclatura=nomenclatura).exclude(id=id).exists():
            messages.error(request, f'La nomenclatura "{nomenclatura}" ya existe')
            return render(request, 'catalogos/cliente_form.html', {'cliente': cliente})
        
        try:
            cliente.nombre = nombre
            cliente.nomenclatura = nomenclatura
            cliente.activo = request.POST.get('activo', 'on') == 'on'
            cliente.save()
            
            messages.success(request, f'Cliente "{cliente.nombre}" actualizado exitosamente')
            return redirect('clientes_list')
        except Exception as e:
            messages.error(request, f'Error al actualizar cliente: {str(e)}')
    
    return render(request, 'catalogos/cliente_form.html', {'cliente': cliente})

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
    
    return redirect('clientes_list')

def tipos_servicio_list(request):
    try:
        tipos = TipoServicio.objects.filter(activo=True)
        
        # Ordenamiento - con validación EXTRA
        orden = request.GET.get('orden', 'id')
        
        # Solo permitir campos que existen en el modelo
        campos_validos = ['id', 'nombre', 'nomenclatura', 'activo', 'fecha_creacion']
        
        orden_final = 'id'  # Valor por defecto
        
        if orden:
            orden_limpio = orden.lstrip('-')
            if orden_limpio in campos_validos:
                # Si el campo es válido, mantener el prefijo de orden
                orden_final = orden
            else:
                orden_final = 'id'
        
        # Aplicar ordenamiento SOLO si es seguro
        tipos = tipos.order_by(orden_final)
        
        # NO imprimas el query SQL directamente en producción
        # print(f"Query SQL: {tipos.query}")  ← COMENTA ESTA LÍNEA
        
        context = {
            'tipos': tipos,
        }
        return render(request, 'catalogos/tipos_servicio_list.html', context)
        
    except Exception as e:
        # Manejo de error mejorado
        print(f"ERROR EN tipo_servicio_list: {str(e)}")
        # Devolver lista vacía en caso de error
        context = {
            'tipos': TipoServicio.objects.none(),
            'error': str(e)
        }
        return render(request, 'catalogos/tipos_servicio_list.html', context)
        
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"ERROR EN tipo_servicio_list: {str(e)}")
        print(f"Traceback: {error_traceback}")
        
        return HttpResponse(f"""
            <h1>Error en tipo_servicio_list</h1>
            <p><strong>Error:</strong> {str(e)}</p>
            <h2>Traceback:</h2>
            <pre>{error_traceback}</pre>
            <h2>GET parameters:</h2>
            <pre>{dict(request.GET)}</pre>
        """)

def tipo_servicio_create(request):
    """Crear un nuevo tipo de servicio"""
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        nomenclatura = request.POST.get('nomenclatura', '').strip().upper()
        
        # Validaciones
        if not nombre or not nomenclatura:
            messages.error(request, 'Todos los campos son obligatorios')
            return render(request, 'catalogos/tipo_servicio_form.html')
        
        if len(nomenclatura) > 10:
            messages.error(request, 'La nomenclatura no puede tener más de 10 caracteres')
            return render(request, 'catalogos/tipo_servicio_form.html')
        
        # Verificar si ya existe la nomenclatura
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
            return redirect('tipos_servicio_list')
        except Exception as e:
            messages.error(request, f'Error al crear tipo de servicio: {str(e)}')
    
    return render(request, 'catalogos/tipo_servicio_form.html')

def tipo_servicio_edit(request, id):
    """Editar un tipo de servicio existente"""
    tipo = get_object_or_404(TipoServicio, id=id)
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        nomenclatura = request.POST.get('nomenclatura', '').strip().upper()
        
        # Validaciones
        if not nombre or not nomenclatura:
            messages.error(request, 'Todos los campos son obligatorios')
            return render(request, 'catalogos/tipo_servicio_form.html', {'tipo': tipo})
        
        if len(nomenclatura) > 10:
            messages.error(request, 'La nomenclatura no puede tener más de 10 caracteres')
            return render(request, 'catalogos/tipo_servicio_form.html', {'tipo': tipo})
        
        # Verificar si la nomenclatura ya existe (excluyendo el actual)
        if TipoServicio.objects.filter(nomenclatura=nomenclatura).exclude(id=id).exists():
            messages.error(request, f'La nomenclatura "{nomenclatura}" ya existe')
            return render(request, 'catalogos/tipo_servicio_form.html', {'tipo': tipo})
        
        try:
            tipo.nombre = nombre
            tipo.nomenclatura = nomenclatura
            tipo.activo = request.POST.get('activo', 'on') == 'on'
            tipo.save()
            
            messages.success(request, f'Tipo de servicio "{tipo.nombre}" actualizado exitosamente')
            return redirect('tipos_servicio_list')
        except Exception as e:
            messages.error(request, f'Error al actualizar tipo de servicio: {str(e)}')
    
    return render(request, 'catalogos/tipo_servicio_form.html', {'tipo': tipo})

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
    
    return redirect('tipos_servicio_list')

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

def proyecto_create(request):
    """Crear un nuevo proyecto"""
    clientes = Cliente.objects.filter(activo=True).order_by('nombre')
    
    if request.method == 'POST':
        cliente_id = request.POST.get('cliente', '')
        nombre = request.POST.get('nombre', '').strip()
        codigo = request.POST.get('codigo', '').strip().upper()
        
        # Validaciones
        if not cliente_id or not nombre or not codigo:
            messages.error(request, 'Todos los campos obligatorios deben completarse')
            return render(request, 'catalogos/proyecto_form.html', {'clientes': clientes})
        
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            messages.error(request, 'Cliente no válido')
            return render(request, 'catalogos/proyecto_form.html', {'clientes': clientes})
        
        # Verificar si ya existe el código
        if Proyecto.objects.filter(codigo=codigo).exists():
            messages.error(request, f'El código "{codigo}" ya existe')
            return render(request, 'catalogos/proyecto_form.html', {'clientes': clientes})
        
        # Verificar si el cliente ya tiene un proyecto con el mismo nombre
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
            return redirect('proyectos_list')
        except Exception as e:
            messages.error(request, f'Error al crear proyecto: {str(e)}')
    
    return render(request, 'catalogos/proyecto_form.html', {'clientes': clientes})

def proyecto_edit(request, id):
    """Editar un proyecto existente"""
    proyecto = get_object_or_404(Proyecto, id=id)
    clientes = Cliente.objects.filter(activo=True).order_by('nombre')
    
    if request.method == 'POST':
        cliente_id = request.POST.get('cliente', '')
        nombre = request.POST.get('nombre', '').strip()
        codigo = request.POST.get('codigo', '').strip().upper()
        
        # Validaciones
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
        
        # Verificar si ya existe el código (excluyendo el actual)
        if Proyecto.objects.filter(codigo=codigo).exclude(id=id).exists():
            messages.error(request, f'El código "{codigo}" ya existe')
            return render(request, 'catalogos/proyecto_form.html', {
                'proyecto': proyecto,
                'clientes': clientes
            })
        
        # Verificar si el cliente ya tiene un proyecto con el mismo nombre (excluyendo el actual)
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
            return redirect('proyectos_list')
        except Exception as e:
            messages.error(request, f'Error al actualizar proyecto: {str(e)}')
    
    return render(request, 'catalogos/proyecto_form.html', {
        'proyecto': proyecto,
        'clientes': clientes
    })

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
    
    return redirect('proyectos_list')

    
def generate_and_save_ticket(extracted_data, tipo_servicio_form, nomenclaturas, objetos_encontrados):
    """Genera y guarda un ticket en la base de datos"""
    
    # Obtener valores para los argumentos
    tipo_servicio_code = tipo_servicio_form
    tipo_pruebas_nom = nomenclaturas.get('tipo_pruebas_nomenclatura', '???')
    tipo_pruebas_id = extracted_data.get('tipo_pruebas', '??')
    cliente_nom = nomenclaturas.get('cliente_nomenclatura', '???')
    proyecto_nom = nomenclaturas.get('proyecto_nomenclatura', '???')
    
    # 1. Obtener el siguiente consecutivo (PASA LOS ARGUMENTOS)
    consecutivo = get_next_consecutivo(
        tipo_servicio_code=tipo_servicio_code,
        tipo_pruebas_nom=tipo_pruebas_nom,
        tipo_pruebas_id=tipo_pruebas_id,
        cliente_nom=cliente_nom,
        proyecto_nom=proyecto_nom
    )
    
    # Convertir a entero y formatear
    consecutivo_num = int(consecutivo)
    consecutivo_str = f"{consecutivo_num:03d}"
    
    # 2. Generar las partes del código
    # Estructura: BID-PRU-F&REG-10-TEL-OTR-001
    
    # Empresa (fija)
    empresa_code = "BID"
    
    # 3. Generar el código completo
    ticket_code = f"{empresa_code}-{tipo_servicio_code}-{tipo_pruebas_nom}-{tipo_pruebas_id}-{cliente_nom}-{proyecto_nom}-{consecutivo_str}"
    
    print(f"🎫 Código de ticket generado: {ticket_code}")
    
    # 4. Buscar los objetos relacionados
    cliente_obj = objetos_encontrados.get('cliente_obj')
    proyecto_obj = objetos_encontrados.get('proyecto_obj')
    tipo_servicio_obj = objetos_encontrados.get('tipo_servicio_obj')
    
    # 5. Buscar o crear un TipoServicio basado en el código del formulario
    if tipo_servicio_code and not tipo_servicio_obj:
        # Intentar encontrar el TipoServicio por nomenclatura
        tipo_servicio_obj = TipoServicio.objects.filter(
            nomenclatura=tipo_servicio_code
        ).first()
    
    # 6. Crear el ticket en la base de datos
    try:
        ticket = Ticket.objects.create(
            codigo=ticket_code,
            
            # Partes del código
            empresa_code=empresa_code,
            tipo_servicio_code=tipo_servicio_code,
            funcion_code=tipo_pruebas_nom,
            version_code=tipo_pruebas_id,
            cliente_code=cliente_nom,
            proyecto_code=proyecto_nom,
            consecutivo=consecutivo_num,
            
            # Relaciones
            cliente=cliente_obj,
            proyecto=proyecto_obj,
            tipo_servicio=tipo_servicio_obj,
            
            # Datos adicionales
            responsable_solicitud=extracted_data.get('responsable_solicitud', ''),
            lider_proyecto=extracted_data.get('lider_proyecto', ''),
            numero_version=extracted_data.get('numero_version', '')
        )
        
        print(f"✅ Ticket guardado en BD con ID: {ticket.id}")
        return ticket_code, ticket
        
    except Exception as e:
        print(f"❌ Error al guardar ticket: {str(e)}")
        # Si hay error, devolver solo el código sin ticket guardado
        return ticket_code, None


def ticket_list(request):
    """Listado de tickets con filtros (similar a clientes_list)"""
    tickets = Ticket.objects.all().select_related('cliente', 'proyecto', 'tipo_servicio')

    # Filtros
    estado = request.GET.get('estado')
    cliente_id = request.GET.get('cliente')
    proyecto_id = request.GET.get('proyecto')
    busqueda = request.GET.get('q')

    if estado:
        tickets = tickets.filter(estado=estado)
    if cliente_id:
        tickets = tickets.filter(cliente_id=cliente_id)
    if proyecto_id:
        tickets = tickets.filter(proyecto_id=proyecto_id)
    if busqueda:
        tickets = tickets.filter(
            Q(codigo__icontains=busqueda) |
            Q(responsable_solicitud__icontains=busqueda) |
            Q(lider_proyecto__icontains=busqueda)
        )

    # Ordenamiento (igual que en clientes)
    orden = request.GET.get('orden', '-fecha_creacion')
    tickets = tickets.order_by(orden)

    # Estadísticas
    context = {
        'tickets': tickets,
        'total_tickets': Ticket.objects.count(),
        'tickets_generados': Ticket.objects.filter(estado='GENERADO').count(),
        'tickets_proceso': Ticket.objects.filter(estado='EN_PROCESO').count(),
        'tickets_completados': Ticket.objects.filter(estado='COMPLETADO').count(),
        'tickets_cancelados': Ticket.objects.filter(estado='CANCELADO').count(),
        'clientes': Cliente.objects.filter(activo=True),
        'tipos_servicio': TipoServicio.objects.filter(activo=True),
        'proyectos': Proyecto.objects.filter(activo=True).select_related('cliente'),
        'estados_disponibles': Ticket.ESTADOS_TICKET,
        # Filtros actuales
        'estado_selected': estado,
        'cliente_selected': int(cliente_id) if cliente_id else 0,
        'proyecto_selected': int(proyecto_id) if proyecto_id else 0,
        'busqueda': busqueda or '',
        'orden_actual': orden,
        'tickets_count': tickets.count(),
    }
    return render(request, 'catalogos/ticket_list.html', context)



def ticket_detail(request, id):
    """Ver detalle de un ticket"""
    ticket = get_object_or_404(Ticket, id=id)
    context = {
        'ticket': ticket,
        'partes_codigo': ticket.get_detalle_partes(),
        'estados_disponibles': Ticket.ESTADOS_TICKET,
    }
    return render(request, 'catalogos/ticket_detail.html', context)

def ticket_create(request):
    """Crear un nuevo ticket manualmente"""
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            cliente_id = request.POST.get('cliente')
            proyecto_id = request.POST.get('proyecto')
            tipo_servicio_id = request.POST.get('tipo_servicio')
            responsable = request.POST.get('responsable_solicitud', '').strip()
            lider = request.POST.get('lider_proyecto', '').strip()
            numero_version = request.POST.get('numero_version', '').strip()
            
            # NUEVO: Obtener el consecutivo del formulario
            consecutivo_manual = request.POST.get('consecutivo', '').strip()
            
            # Validaciones básicas
            if not all([cliente_id, proyecto_id, tipo_servicio_id]):
                messages.error(request, 'Los campos Cliente, Proyecto y Tipo de Servicio son obligatorios')
                return redirect('ticket_create')
            
            # Obtener los objetos relacionados
            cliente = get_object_or_404(Cliente, id=cliente_id)
            proyecto = get_object_or_404(Proyecto, id=proyecto_id)
            tipo_servicio = get_object_or_404(TipoServicio, id=tipo_servicio_id)
            
            # Verificar que el proyecto pertenezca al cliente
            if proyecto.cliente_id != cliente.id:
                messages.error(request, 'El proyecto seleccionado no pertenece al cliente')
                return redirect('ticket_create')
            
            # Validar consecutivo si se proporcionó
            consecutivo_num = None
            consecutivo_str = None
            
            if consecutivo_manual:
                try:
                    consecutivo_num = int(consecutivo_manual)
                    if consecutivo_num < 1 or consecutivo_num > 999:
                        messages.error(request, 'El consecutivo debe estar entre 1 y 999')
                        return redirect('ticket_create')
                    
                    # Verificar si ya existe un ticket con ese consecutivo para la misma combinación
                    ticket_existente = Ticket.objects.filter(
                        empresa_code="BID",
                        tipo_servicio_code=tipo_servicio.nomenclatura,
                        funcion_code=tipo_servicio.nomenclatura,
                        version_code=str(tipo_servicio.id),
                        cliente_code=cliente.nomenclatura,
                        proyecto_code=proyecto.codigo,
                        consecutivo=consecutivo_num
                    ).exists()
                    
                    if ticket_existente:
                        messages.error(request, f'Ya existe un ticket con el consecutivo {consecutivo_num:03d} para esta combinación')
                        return redirect('ticket_create')
                    
                    consecutivo_str = f"{consecutivo_num:03d}"
                    
                except ValueError:
                    messages.error(request, 'El consecutivo debe ser un número válido')
                    return redirect('ticket_create')
            
            # Preparar los datos para generar el ticket
            extracted_data = {
                'cliente': str(cliente.id),
                'proyecto': str(proyecto.id),
                'tipo_pruebas': str(tipo_servicio.id),
                'responsable_solicitud': responsable,
                'lider_proyecto': lider,
                'numero_version': numero_version,
                'funcionalidad_liberacion': request.POST.get('funcionalidad_liberacion', ''),
                'detalle_cambios': request.POST.get('detalle_cambios', ''),
                'justificacion_cambio': request.POST.get('justificacion_cambio', ''),
            }
            
            # Nomenclaturas
            nomenclaturas = {
                'cliente_nomenclatura': cliente.nomenclatura,
                'proyecto_nomenclatura': proyecto.codigo,
                'tipo_pruebas_nomenclatura': tipo_servicio.nomenclatura,
                'tipo_servicio_nomenclatura': tipo_servicio.nomenclatura
            }
            
            # Objetos encontrados
            objetos_encontrados = {
                'cliente_obj': cliente,
                'proyecto_obj': proyecto,
                'tipo_servicio_obj': tipo_servicio
            }
            
            # Generar y guardar el ticket
            if consecutivo_num:
                # Usar el consecutivo manual
                ticket_code = f"BID-{tipo_servicio.nomenclatura}-{tipo_servicio.nomenclatura}-{tipo_servicio.id}-{cliente.nomenclatura}-{proyecto.codigo}-{consecutivo_str}"
                
                # Crear el ticket manualmente con el consecutivo específico
                ticket = Ticket.objects.create(
                    codigo=ticket_code,
                    empresa_code="BID",
                    tipo_servicio_code=tipo_servicio.nomenclatura,
                    funcion_code=tipo_servicio.nomenclatura,
                    version_code=str(tipo_servicio.id),
                    cliente_code=cliente.nomenclatura,
                    proyecto_code=proyecto.codigo,
                    consecutivo=consecutivo_num,
                    cliente=cliente,
                    proyecto=proyecto,
                    tipo_servicio=tipo_servicio,
                    responsable_solicitud=responsable,
                    lider_proyecto=lider,
                    numero_version=numero_version
                )
                
                messages.info(request, f'✅ Ticket creado con consecutivo manual: {consecutivo_num:03d}')
            else:
                # Usar el generador automático
                ticket_code, ticket = generate_and_save_ticket(
                    extracted_data=extracted_data,
                    tipo_servicio_form=tipo_servicio.nomenclatura,
                    nomenclaturas=nomenclaturas,
                    objetos_encontrados=objetos_encontrados
                )
            
            # Si se proporcionaron datos adicionales, crear un registro ExcelData asociado
            if any([extracted_data['funcionalidad_liberacion'], 
                   extracted_data['detalle_cambios'], 
                   extracted_data['justificacion_cambio']]):
                
                excel_data = ExcelData.objects.create(
                    cliente=str(cliente.id),
                    proyecto=str(proyecto.id),
                    tipo_pruebas=str(tipo_servicio.id),
                    tipo_servicio=tipo_servicio.nomenclatura,
                    responsable_solicitud=responsable,
                    lider_proyecto=lider,
                    numero_version=numero_version,
                    funcionalidad_liberacion=extracted_data['funcionalidad_liberacion'],
                    detalle_cambios=extracted_data['detalle_cambios'],
                    justificacion_cambio=extracted_data['justificacion_cambio'],
                    ticket_code=ticket_code
                )
                
                if ticket:
                    ticket.excel_data = excel_data
                    ticket.save()
            
            messages.success(request, f'🎫 Ticket creado exitosamente: {ticket_code}')
            return redirect('ticket_detail', id=ticket.id)
            
        except Exception as e:
            messages.error(request, f'Error al crear ticket: {str(e)}')
            return redirect('ticket_create')
    
    # GET request - mostrar formulario
    clientes = Cliente.objects.filter(activo=True).order_by('nombre')
    
    # ✅ FORZAR que sea un QuerySet válido
    tipos_servicio = TipoServicio.objects.filter(activo=True)
    tipos_servicio = tipos_servicio.order_by('nombre')
    
    # ✅ VERIFICACIÓN - Agrega estos prints para debuggear
    print("\n=== DEBUG TICKET CREATE GET ===")
    print(f"Tipo de tipos_servicio: {type(tipos_servicio)}")
    print(f"Es QuerySet? {isinstance(tipos_servicio, models.QuerySet)}")
    print(f"SQL: {tipos_servicio.query}")
    print(f"Cantidad: {tipos_servicio.count()}")
    print("===============================\n")
    
    # Obtener el último consecutivo
    ultimo_ticket = Ticket.objects.order_by('-consecutivo').first()
    ultimo_consecutivo = ultimo_ticket.consecutivo if ultimo_ticket else 0
    
    context = {
        'clientes': clientes,
        'tipos_servicio': tipos_servicio,  # ✅ Esto SÍ es un QuerySet
        'proyectos': [],  # Vacío inicialmente
        'ultimo_consecutivo': ultimo_consecutivo,
    }
    return render(request, 'catalogos/new_ticket_form.html', context)

def proyectos_por_cliente(request, cliente_id):
    """Obtener proyectos de un cliente específico (para AJAX)"""
    try:
        cliente = get_object_or_404(Cliente, id=cliente_id)
        # CORREGIDO: activo=True en lugar de activo=1
        proyectos = Proyecto.objects.filter(
            cliente=cliente, 
            activo=True
        ).order_by('nombre')
        
        proyectos_list = [
            {'id': p.id, 'nombre': p.nombre, 'codigo': p.codigo}
            for p in proyectos
        ]
        
        return JsonResponse({'proyectos': proyectos_list})
    except Exception as e:
        print(f"Error en proyectos_por_cliente: {e}")
        return JsonResponse({'error': str(e), 'proyectos': []}, status=200)

def ticket_create_simple(request):
    """VERSIÓN SIMPLIFICADA - Crear un nuevo ticket manualmente"""
    
    # GET - Mostrar formulario
    if request.method == 'GET':
        context = {
            'clientes': Cliente.objects.filter(activo=True).order_by('nombre'),
            'tipos_servicio': TipoServicio.objects.filter(activo=True).order_by('nombre'),
        }
        return render(request, 'catalogos/new_ticket_form_simple.html', context)
    
    # POST - Procesar formulario
    if request.method == 'POST':
        try:
            # 1. OBTENER DATOS BÁSICOS
            cliente_id = request.POST.get('cliente')
            proyecto_id = request.POST.get('proyecto')
            tipo_servicio_id = request.POST.get('tipo_servicio')
            
            # Validación MÍNIMA
            if not cliente_id or not proyecto_id or not tipo_servicio_id:
                messages.error(request, 'Cliente, Proyecto y Tipo de Servicio son obligatorios')
                return redirect('ticket_create_simple')
            
            # 2. OBTENER OBJETOS
            try:
                cliente = Cliente.objects.get(id=cliente_id, activo=True)
                proyecto = Proyecto.objects.get(id=proyecto_id, activo=True)
                tipo_servicio = TipoServicio.objects.get(id=tipo_servicio_id, activo=True)
            except (Cliente.DoesNotExist, Proyecto.DoesNotExist, TipoServicio.DoesNotExist):
                messages.error(request, 'Uno de los elementos seleccionados no existe')
                return redirect('ticket_create_simple')
            
            # 3. VALIDAR QUE EL PROYECTO PERTENEZCA AL CLIENTE
            if proyecto.cliente_id != cliente.id:
                messages.error(request, 'El proyecto no pertenece al cliente seleccionado')
                return redirect('ticket_create_simple')
            
            # 4. PROCESAR CONSECUTIVO
            consecutivo_manual = request.POST.get('consecutivo', '').strip()
            
            if consecutivo_manual:
                # USAR CONSECUTIVO MANUAL
                try:
                    consecutivo_num = int(consecutivo_manual)
                    if consecutivo_num < 1 or consecutivo_num > 999:
                        messages.error(request, 'El consecutivo debe ser entre 1 y 999')
                        return redirect('ticket_create_simple')
                    
                    # Verificar si ya existe
                    existe = Ticket.objects.filter(
                        empresa_code="BID",
                        tipo_servicio_code=tipo_servicio.nomenclatura,
                        funcion_code=tipo_servicio.nomenclatura,
                        version_code=str(tipo_servicio.id),
                        cliente_code=cliente.nomenclatura,
                        proyecto_code=proyecto.codigo,
                        consecutivo=consecutivo_num
                    ).exists()
                    
                    if existe:
                        messages.error(request, f'Ya existe un ticket con consecutivo {consecutivo_num:03d}')
                        return redirect('ticket_create_simple')
                    
                    consecutivo_str = f"{consecutivo_num:03d}"
                    
                except ValueError:
                    messages.error(request, 'El consecutivo debe ser un número')
                    return redirect('ticket_create_simple')
            else:
                # AUTO-GENERAR CONSECUTIVO
                tickets_existentes = Ticket.objects.filter(
                    empresa_code="BID",
                    tipo_servicio_code=tipo_servicio.nomenclatura,
                    funcion_code=tipo_servicio.nomenclatura,
                    version_code=str(tipo_servicio.id),
                    cliente_code=cliente.nomenclatura,
                    proyecto_code=proyecto.codigo
                )
                
                if tickets_existentes.exists():
                    max_consecutivo = tickets_existentes.aggregate(models.Max('consecutivo'))['consecutivo__max']
                    consecutivo_num = (max_consecutivo or 0) + 1
                else:
                    consecutivo_num = 1
                
                consecutivo_str = f"{consecutivo_num:03d}"
            
            # 5. GENERAR CÓDIGO DEL TICKET
            ticket_code = f"BID-{tipo_servicio.nomenclatura}-{tipo_servicio.nomenclatura}-{tipo_servicio.id}-{cliente.nomenclatura}-{proyecto.codigo}-{consecutivo_str}"
            
            # 6. CREAR TICKET
            ticket = Ticket.objects.create(
                codigo=ticket_code,
                empresa_code="BID",
                tipo_servicio_code=tipo_servicio.nomenclatura,
                funcion_code=tipo_servicio.nomenclatura,
                version_code=str(tipo_servicio.id),
                cliente_code=cliente.nomenclatura,
                proyecto_code=proyecto.codigo,
                consecutivo=consecutivo_num,
                cliente=cliente,
                proyecto=proyecto,
                tipo_servicio=tipo_servicio,
                responsable_solicitud=request.POST.get('responsable_solicitud', '')[:255],
                lider_proyecto=request.POST.get('lider_proyecto', '')[:255],
                numero_version=request.POST.get('numero_version', '')[:255],
                estado='GENERADO'
            )
            
            # 7. CREAR DATOS EXCEL ASOCIADOS (si hay información adicional)
            if any([
                request.POST.get('funcionalidad_liberacion'),
                request.POST.get('detalle_cambios'),
                request.POST.get('justificacion_cambio')
            ]):
                excel_data = ExcelData.objects.create(
                    cliente=str(cliente.id),
                    proyecto=str(proyecto.id),
                    tipo_pruebas=str(tipo_servicio.id),
                    tipo_servicio=tipo_servicio.nomenclatura,
                    responsable_solicitud=request.POST.get('responsable_solicitud', ''),
                    lider_proyecto=request.POST.get('lider_proyecto', ''),
                    numero_version=request.POST.get('numero_version', ''),
                    funcionalidad_liberacion=request.POST.get('funcionalidad_liberacion', ''),
                    detalle_cambios=request.POST.get('detalle_cambios', ''),
                    justificacion_cambio=request.POST.get('justificacion_cambio', ''),
                    ticket_code=ticket_code
                )
                ticket.excel_data = excel_data
                ticket.save()
            
            # 8. MENSAJE DE ÉXITO
            messages.success(request, f'✅ Ticket creado exitosamente: {ticket_code}')
            
            # Redirigir al detalle o al listado
            return redirect('ticket_detail', id=ticket.id)
            
        except Exception as e:
            # CAPTURAR CUALQUIER ERROR
            import traceback
            print(f"ERROR EN TICKET CREATE SIMPLE: {str(e)}")
            print(traceback.format_exc())
            
            messages.error(request, f'Error al crear ticket: {str(e)}')
            return redirect('ticket_create_simple')

def generar_excel_dictamen(request, ticket_id):
    """
    Genera el Dictamen de Pruebas usando la plantilla
    """
    import io
    import os
    from django.conf import settings
    from openpyxl import load_workbook
    from datetime import datetime
    from django.contrib import messages
    
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    # Ruta a la plantilla
    plantilla_path = os.path.join(
        settings.BASE_DIR,
        'static',
        'plantillas',
        'XXX-XXX-XXX-X-XXX-XXX-XXX DictamenPruebas PRUEBAS.xlsx'
    )
    
    # Verificar que la plantilla existe
    if not os.path.exists(plantilla_path):
        messages.error(
            request, 
            f"No se encontró la plantilla. Por favor, coloca el archivo en: {plantilla_path}"
        )
        return redirect('ticket_detail', id=ticket.id)
    
    try:
        # Cargar la plantilla
        wb = load_workbook(plantilla_path)
        
        # Seleccionar la hoja de Dictamen
        if 'Dictamen' in wb.sheetnames:
            ws = wb['Dictamen']
        else:
            ws = wb.active
        
        # Desglosar código del ticket
        partes = ticket.codigo.split('-')
        print(f"Partes del ticket: {partes}")
        
        # MAPEO SEGÚN SYS.TXT - Usando coordenadas de celda
        if len(partes) >= 7:
            # MODIFICACIÓN: Verificar si la celda está fusionada antes de asignar
            try:
                # Verificar si G2 está en un rango fusionado
                is_merged = False
                for merged_range in ws.merged_cells.ranges:
                    if ws['G2'].coordinate in merged_range:
                        is_merged = True
                        print(f"✅ G2 está fusionada en el rango: {merged_range}")
                        # Obtener la celda superior izquierda del rango fusionado
                        top_left_cell = ws[merged_range.start_cell.coordinate]
                        top_left_cell.value = partes[1]
                        print(f"✅ Celda fusionada {merged_range.start_cell.coordinate} = {partes[1]}")
                        break
                
                if not is_merged:
                    # Si no está fusionada, asignar directamente
                    ws['G2'] = partes[1]
                    print(f"✅ G2 = {partes[1]}")
            except Exception as e:
                print(f"❌ Error al asignar G2: {e}")
            
            # I2 = Tipo de pruebas
            try:
                ws['I2'] = partes[2]
                print(f"✅ I2 = {partes[2]}")
            except Exception as e:
                print(f"❌ Error en I2: {e}")
            
            # K2 = No. Pruebas
            try:
                ws['K2'] = partes[3]
                print(f"✅ K2 = {partes[3]}")
            except Exception as e:
                print(f"❌ Error en K2: {e}")
            
            # M2 = Cliente
            try:
                ws['M2'] = partes[4]
                print(f"✅ M2 = {partes[4]}")
            except Exception as e:
                print(f"❌ Error en M2: {e}")
            
            # ✅ NUEVO: O2 = Nomenclatura del Proyecto (parte 5 del código)
            try:
                ws['O2'] = partes[5]
                print(f"✅ O2 = {partes[5]}")
            except Exception as e:
                print(f"❌ Error en O2: {e}")
            
            # Q2 = Consecutivo
            try:
                ws['Q2'] = partes[6]
                print(f"✅ Q2 = {partes[6]}")
            except Exception as e:
                print(f"❌ Error en Q2: {e}")
        
        # Otros campos
        campos = [
            ('B5', ticket.cliente.nombre if ticket.cliente else ''),
            ('B6', ticket.proyecto.nombre if ticket.proyecto else ''),
            ('C7', ticket.tipo_servicio.nombre if ticket.tipo_servicio else ''),
            ('H6', datetime.now().strftime('%d/%m/%Y')),
            ('B24', ticket.responsable_solicitud or ''),
            ('H24', ticket.lider_proyecto or ''),
        ]
        
        for celda, valor in campos:
            try:
                ws[celda] = valor
                print(f"✅ {celda} = {valor}")
            except Exception as e:
                print(f"❌ Error en {celda}: {e}")
        
        ws.row_dimensions[37].height = 32.6
        # Guardar en buffer
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        # Crear respuesta
        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{ticket.codigo} Dictamen Pruebas.xlsx"'
        
        return response
        
    except Exception as e:
        print(f"❌ Error al generar dictamen: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, f"Error al generar dictamen: {str(e)}")
        return redirect('ticket_detail', id=ticket.id)

def verificar_plantilla(request):
    import os
    from django.conf import settings
    from django.http import HttpResponse
    
    # Posibles rutas a verificar
    rutas = [
        os.path.join(settings.BASE_DIR, 'static', 'plantillas', 'XXX-XXX-XXX-X-XXX-XXX-XXX DictamenPruebas PRUEBAS.xlsx'),
        os.path.join(settings.BASE_DIR, 'extractor', 'static', 'plantillas', 'XXX-XXX-XXX-X-XXX-XXX-XXX DictamenPruebas PRUEBAS.xlsx'),
        os.path.join(settings.MEDIA_ROOT, 'plantillas', 'XXX-XXX-XXX-X-XXX-XXX-XXX DictamenPruebas PRUEBAS.xlsx'),
    ]
    
    resultado = "<h1>Verificación de Plantilla</h1>"
    resultado += f"<p>BASE_DIR: {settings.BASE_DIR}</p>"
    
    for ruta in rutas:
        existe = os.path.exists(ruta)
        resultado += f"<p>Ruta: {ruta}<br>Existe: {existe}</p>"
        if existe:
            resultado += f"<p>✅ ¡ENCONTRADA AQUÍ!</p>"
    
    return HttpResponse(resultado)


def generar_excel_resultados(request, ticket_id):
    """
    Genera el archivo Excel de Documentación de Resultados de Pruebas con la información del ticket
    """
    import io
    import os
    from datetime import datetime
    from openpyxl import Workbook, load_workbook
    from openpyxl.styles import Font, PatternFill, Border, Side
    from django.conf import settings
    
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    # Ruta a la plantilla de resultados
    plantilla_resultados_path = os.path.join(
        settings.BASE_DIR,
        'static',
        'plantillas',
        'XXX-XXX-XXX-X-XXX-XXX-XXX Documentación de Resultados.xlsx'
    )
    
    # Verificar si existe la plantilla
    if os.path.exists(plantilla_resultados_path):
        # Usar la plantilla
        wb = load_workbook(plantilla_resultados_path)
        ws = wb.active
        ws.title = "Resultados Pruebas"
    else:
        # Crear un nuevo workbook si no existe la plantilla
        wb = Workbook()
        ws = wb.active
        ws.title = "Resultados Pruebas"
        
        # Configurar anchos de columna básicos
        ws.column_dimensions['A'].width = 8
        ws.column_dimensions['B'].width = 30
        ws.column_dimensions['L'].width = 15
        ws.column_dimensions['M'].width = 30
    
    # Definir estilos (solo si creamos el documento desde cero, si usamos plantilla se mantienen los estilos)
    if not os.path.exists(plantilla_resultados_path):
        header_font = Font(bold=True)
        ticket_font = Font(bold=True, size=14, color="2563EB")
        
        # TICKET - SOLO SI ES DOCUMENTO NUEVO
        ws.cell(row=2, column=1, value="TICKET:")
        ws.cell(row=2, column=1).font = header_font
    
    # AGREGAR EL TICKET EN C2 (esto funciona tanto en plantilla como en documento nuevo)
    ws['C2'] = ticket.codigo
    
    # Si es documento nuevo, aplicar estilo al ticket
    if not os.path.exists(plantilla_resultados_path):
        ws['C2'].font = Font(bold=True, size=14, color="2563EB")
    
    # Versión (si no existe en la plantilla)
    if ws['M3'].value is None or "Versión" not in str(ws['M3'].value):
        ws['M3'] = f"VERSIÓN: Versión {ticket.numero_version or '1.0.0'}"
    
    # Guardar en buffer
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    # Crear respuesta con el nombre del archivo basado en el ticket
    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    
    # ✅ RENOMBRAR EL ARCHIVO con el código del ticket
    filename = f"{ticket.codigo} Documentación de Resultados.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response['Content-Length'] = len(buffer.getvalue())
    
    return response

def export_tickets_excel(request):
    """
    Exporta los tickets filtrados a un archivo Excel
    """
    # Obtener los mismos filtros que en ticket_list
    tickets = Ticket.objects.all().select_related('cliente', 'proyecto', 'tipo_servicio', 'excel_data')
    
    # Aplicar los mismos filtros que en la vista list
    estado = request.GET.get('estado')
    cliente_id = request.GET.get('cliente')
    proyecto_id = request.GET.get('proyecto')
    busqueda = request.GET.get('q')
    
    if estado:
        tickets = tickets.filter(estado=estado)
    if cliente_id:
        tickets = tickets.filter(cliente_id=cliente_id)
    if proyecto_id:
        tickets = tickets.filter(proyecto_id=proyecto_id)
    if busqueda:
        tickets = tickets.filter(
            Q(codigo__icontains=busqueda) |
            Q(responsable_solicitud__icontains=busqueda) |
            Q(lider_proyecto__icontains=busqueda)
        )
    
    # Crear workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Tickets"
    
    # Definir estilos
    header_font = Font(bold=True)
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font_white = Font(bold=True, color="FFFFFF")
    
    # Definir encabezados
    headers = [
        'ID', 'Código Ticket', 'Estado', 'Cliente', 'Proyecto', 
        'Tipo Servicio', 'Responsable Solicitud', 'Líder Proyecto',
        'Versión', 'Funcionalidad', 'Detalle Cambios', 'Justificación',
        'Fecha Creación', 'Fecha Actualización'
    ]
    
    # Escribir encabezados
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font_white
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')
    
    # Escribir datos
    for row, ticket in enumerate(tickets, 2):
        ws.cell(row=row, column=1, value=ticket.id)
        ws.cell(row=row, column=2, value=ticket.codigo)
        ws.cell(row=row, column=3, value=ticket.get_estado_display())
        ws.cell(row=row, column=4, value=ticket.cliente.nombre if ticket.cliente else '')
        ws.cell(row=row, column=5, value=ticket.proyecto.nombre if ticket.proyecto else '')
        ws.cell(row=row, column=6, value=ticket.tipo_servicio.nombre if ticket.tipo_servicio else '')
        ws.cell(row=row, column=7, value=ticket.responsable_solicitud)
        ws.cell(row=row, column=8, value=ticket.lider_proyecto)
        ws.cell(row=row, column=9, value=ticket.numero_version)
        
        # Datos del Excel asociado
        excel_data = ticket.excel_data
        ws.cell(row=row, column=10, value=excel_data.funcionalidad_liberacion if excel_data else '')
        ws.cell(row=row, column=11, value=excel_data.detalle_cambios if excel_data else '')
        ws.cell(row=row, column=12, value=excel_data.justificacion_cambio if excel_data else '')
        
        ws.cell(row=row, column=13, value=ticket.fecha_creacion.strftime('%d/%m/%Y %H:%M'))
        ws.cell(row=row, column=14, value=ticket.fecha_actualizacion.strftime('%d/%m/%Y %H:%M'))
    
    # Ajustar ancho de columnas
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column].width = adjusted_width
    
    # Crear respuesta
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    filename = f"tickets_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


def export_table_csv(request, table_name):
    """
    Exporta una tabla específica a formato CSV
    """
    try:
        # Mapeo de nombres de tabla a modelos
        models_map = {
            'cliente': Cliente,
            'proyecto': Proyecto,
            'tiposervicio': TipoServicio,
            'ticket': Ticket,
            'exceldata': ExcelData,
        }
        
        if table_name.lower() not in models_map:
            return HttpResponse("Tabla no encontrada", status=404)
        
        model = models_map[table_name.lower()]
        queryset = model.objects.all()
        
        # Crear respuesta CSV
        response = HttpResponse(content_type='text/csv')
        # Agregar BOM para UTF-8 para que Excel lo abra correctamente
        response.write('\ufeff'.encode('utf-8'))  # BOM para UTF-8
        
        filename = f"{table_name}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        
        # Obtener nombres de campos
        headers = [field.name for field in model._meta.fields]
        writer.writerow(headers)
        
        # Escribir datos
        for obj in queryset:
            row = []
            for field in headers:
                value = getattr(obj, field)
                # Manejar fechas y relaciones
                if value is None:
                    row.append('')
                elif hasattr(value, 'strftime'):  # Es una fecha
                    row.append(value.strftime('%Y-%m-%d %H:%M:%S'))
                elif hasattr(value, 'pk'):  # Es una relación
                    row.append(value.pk)
                else:
                    row.append(str(value))
            writer.writerow(row)
        
        return response
        
    except Exception as e:
        print(f"ERROR en export_table_csv: {str(e)}")
        import traceback
        traceback.print_exc()
        return HttpResponseServerError(f"Error al exportar: {str(e)}")


def export_all_tables_backup(request):
    """
    Exporta todas las tablas como CSV en un archivo ZIP
    """
    try:
        # Crear archivo ZIP en memoria
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            models_to_export = {
                'clientes': Cliente,
                'proyectos': Proyecto,
                'tipos_servicio': TipoServicio,
                'tickets': Ticket,
                'datos_excel': ExcelData,
            }
            
            for filename, model in models_to_export.items():
                # Crear CSV en memoria usando StringIO para texto
                import io
                csv_buffer = io.StringIO()
                writer = csv.writer(csv_buffer)
                
                queryset = model.objects.all()
                
                # Escribir encabezados
                headers = [field.name for field in model._meta.fields]
                writer.writerow(headers)
                
                # Escribir datos
                for obj in queryset:
                    row = []
                    for field in headers:
                        value = getattr(obj, field)
                        if value is None:
                            row.append('')
                        elif hasattr(value, 'strftime'):
                            row.append(value.strftime('%Y-%m-%d %H:%M:%S'))
                        elif hasattr(value, 'pk'):
                            row.append(value.pk)
                        else:
                            row.append(str(value))
                    writer.writerow(row)
                
                # Convertir StringIO a bytes para el ZIP
                csv_content = csv_buffer.getvalue().encode('utf-8-sig')  # UTF-8 con BOM para Excel
                zip_file.writestr(f"{filename}.csv", csv_content)
        
        # Preparar respuesta
        zip_buffer.seek(0)
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        
        response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="backup_completo_{timestamp}.zip"'
        
        return response
        
    except Exception as e:
        print(f"ERROR en export_all_tables_backup: {str(e)}")
        import traceback
        traceback.print_exc()
        return HttpResponseServerError(f"Error al crear backup: {str(e)}")
