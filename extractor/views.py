import os
import traceback
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.db.models import Q, Count
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import ExcelData, Cliente ,TipoServicio, Proyecto, Ticket
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.db import models
import pandas as pd
import json

def extract_excel_data(file_path):
    """
    Extrae las celdas específicas según las reglas dadas
    """
    try:
        # Leer el archivo Excel
        df = pd.read_excel(file_path, sheet_name='Solicitud de Pruebas V4', header=None)
        
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
                # Si es un número flotante
                float_value = float(str_value)
                # Verificar si es un entero (ej: 6.0, 7.0)
                if float_value.is_integer():
                    return str(int(float_value))
                else:
                    return str(float_value)
            except ValueError:
                # Si no se puede convertir a número, devolver el string original
                return str_value
        
        # Extraer celdas directamente sin reglas condicionales
        # Siempre extraer celda C5 (fila 5, columna C) - CLIENTE
        try:
            cell_value = df.iat[4, 2] if pd.notna(df.iat[4, 2]) else ""
            extracted_data['cliente'] = clean_numeric_value(cell_value)
        except:
            extracted_data['cliente'] = ""
        
        # Siempre extraer celda H5 (fila 5, columna H) - PROYECTO
        try:
            cell_value = df.iat[4, 7] if pd.notna(df.iat[4, 7]) else ""
            extracted_data['proyecto'] = clean_numeric_value(cell_value)
        except:
            extracted_data['proyecto'] = ""
        
        # Extraer otras celdas directamente - TIPO DE PRUEBAS
        try:
            cell_value = df.iat[7, 3] if pd.notna(df.iat[7, 3]) else ""  # d8
            extracted_data['tipo_pruebas'] = clean_numeric_value(cell_value)
        except:
            extracted_data['tipo_pruebas'] = ""
        
        # El resto de los campos no necesitan limpieza numérica especial
        try:
            extracted_data['responsable_solicitud'] = str(df.iat[11, 3]) if pd.notna(df.iat[11, 3]) else ""  # d12
        except:
            extracted_data['responsable_solicitud'] = ""
        
        try:
            extracted_data['lider_proyecto'] = str(df.iat[11, 9]) if pd.notna(df.iat[11, 9]) else ""  # j12
        except:
            extracted_data['lider_proyecto'] = ""
        
        try:
            extracted_data['tipo_aplicacion'] = str(df.iat[16, 3]) if pd.notna(df.iat[16, 3]) else ""  # d17
        except:
            extracted_data['tipo_aplicacion'] = ""
        
        try:
            extracted_data['numero_version'] = str(df.iat[16, 12]) if pd.notna(df.iat[16, 12]) else ""  # m17
        except:
            extracted_data['numero_version'] = ""
        
        # Extraer los nuevos campos según el formato del Excel
        # "Funcionalidad de la liberación del producto desarrollado" está en D20 (fila 19, columna 3)
        try:
            funcionalidad = str(df.iat[19, 3]) if pd.notna(df.iat[19, 3]) else ""
            # Si hay texto adicional en D21, concatenarlo
            if pd.notna(df.iat[20, 3]):
                funcionalidad += "\n" + str(df.iat[20, 3])
            extracted_data['funcionalidad_liberacion'] = funcionalidad
        except:
            extracted_data['funcionalidad_liberacion'] = ""
        
        # "Detalle de los cambios" está en D22 (fila 21, columna 3)
        try:
            detalle_cambios = ""
            # Extraer múltiples filas para detalle de cambios (D22, D23, D24, etc.)
            row = 21
            while pd.notna(df.iat[row, 3]) and row < 30:  # Hasta fila 30 máximo
                detalle_cambios += str(df.iat[row, 3]) + "\n"
                row += 1
            extracted_data['detalle_cambios'] = detalle_cambios.strip()
        except:
            extracted_data['detalle_cambios'] = ""
        
        # "Justificación del cambio" está después de "Detalle de los cambios"
        try:
            # Buscar la fila que contiene "Justificación del cambio"
            justificacion_row = None
            for row in range(21, 30):
                if pd.notna(df.iat[row, 2]) and "Justificación" in str(df.iat[row, 2]):
                    justificacion_row = row
                    break
            
            if justificacion_row is not None:
                # El contenido está en la columna D (índice 3) de la siguiente fila
                content_row = justificacion_row + 1
                justificacion = ""
                while pd.notna(df.iat[content_row, 3]) and content_row < 40:  # Hasta fila 40 máximo
                    justificacion += str(df.iat[content_row, 3]) + "\n"
                    content_row += 1
                extracted_data['justificacion_cambio'] = justificacion.strip()
            else:
                extracted_data['justificacion_cambio'] = ""
        except:
            extracted_data['justificacion_cambio'] = ""
        
        # DEPURACIÓN: Mostrar valores extraídos antes y después de la limpieza
        print("=== VALORES LIMPIADOS ===")
        print(f"Cliente original: {df.iat[4, 2] if pd.notna(df.iat[4, 2]) else 'Vacío'} -> Limpio: '{extracted_data['cliente']}'")
        print(f"Proyecto original: {df.iat[4, 7] if pd.notna(df.iat[4, 7]) else 'Vacío'} -> Limpio: '{extracted_data['proyecto']}'")
        print(f"Tipo pruebas original: {df.iat[7, 3] if pd.notna(df.iat[7, 3]) else 'Vacío'} -> Limpio: '{extracted_data['tipo_pruebas']}'")
        print("==========================")
        
        return extracted_data
        
    except Exception as e:
        print(f"Error al extraer datos: {e}")
        return {}

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
        
        try:
            # Guardar el archivo temporalmente
            filename = fs.save(excel_file.name, excel_file)
            file_path = os.path.join(settings.MEDIA_ROOT, filename)
            
            # Extraer datos del Excel
            extracted_data = extract_excel_data(file_path)
            
            # DEPURACIÓN: Mostrar qué se extrajo
            print("=== DATOS EXTRAÍDOS DEL EXCEL ===")
            print(f"Cliente ID (C5): '{extracted_data.get('cliente', '')}'")
            print(f"Proyecto ID (H5): '{extracted_data.get('proyecto', '')}'")
            print(f"Tipo prueba ID (D8): '{extracted_data.get('tipo_pruebas', '')}'")
            print(f"Tipo Servicio (formulario): '{tipo_servicio_form}'")
            print("==================================")
            
            # Inicializar nomenclaturas
            nomenclaturas = {
                'cliente_nomenclatura': '',
                'proyecto_nomenclatura': '',
                'tipo_pruebas_nomenclatura': '',
                'tipo_servicio_nomenclatura': tipo_servicio_form
            }
            
            # Inicializar objetos encontrados para usar en la plantilla si es necesario
            objetos_encontrados = {
                'cliente_obj': None,
                'proyecto_obj': None,
                'tipo_servicio_obj': None
            }
            
            # 1. BUSCAR CLIENTE POR ID en tabla Cliente
            cliente_id_str = extracted_data.get('cliente', '').strip()
            if cliente_id_str:
                try:
                    cliente_id = int(cliente_id_str)
                    print(f"🔍 Buscando Cliente con ID: {cliente_id}")
                    
                    cliente = Cliente.objects.filter(id=cliente_id).first()
                    if cliente:
                        nomenclaturas['cliente_nomenclatura'] = cliente.nomenclatura
                        objetos_encontrados['cliente_obj'] = cliente
                        print(f"✅ Cliente encontrado: ID={cliente.id}, Nombre='{cliente.nombre}', Nomenclatura='{cliente.nomenclatura}'")
                    else:
                        print(f"❌ No se encontró Cliente con ID {cliente_id}")
                        nomenclaturas['cliente_nomenclatura'] = f"ID {cliente_id} no encontrado"
                        
                except ValueError:
                    print(f"⚠️ El valor '{cliente_id_str}' no es un ID válido para Cliente")
                    nomenclaturas['cliente_nomenclatura'] = "ID inválido"
            
            # 2. BUSCAR PROYECTO POR ID en tabla Proyecto
            proyecto_id_str = extracted_data.get('proyecto', '').strip()
            if proyecto_id_str:
                try:
                    proyecto_id = int(proyecto_id_str)
                    print(f"🔍 Buscando Proyecto con ID: {proyecto_id}")
                    
                    proyecto = Proyecto.objects.filter(id=proyecto_id).first()
                    if proyecto:
                        nomenclaturas['proyecto_nomenclatura'] = proyecto.codigo
                        objetos_encontrados['proyecto_obj'] = proyecto
                        print(f"✅ Proyecto encontrado: ID={proyecto.id}, Nombre='{proyecto.nombre}', Nomenclatura='{proyecto.codigo}'")
                    else:
                        print(f"❌ No se encontró Proyecto con ID {proyecto_id}")
                        nomenclaturas['proyecto_nomenclatura'] = f"ID {proyecto_id} no encontrado"
                        
                except ValueError:
                    print(f"⚠️ El valor '{proyecto_id_str}' no es un ID válido para Proyecto")
                    nomenclaturas['proyecto_nomenclatura'] = "ID inválido"
            
            # 3. BUSCAR TIPO DE SERVICIO POR ID en tabla TipoServicio
            tipo_pruebas_id_str = extracted_data.get('tipo_pruebas', '').strip()
            if tipo_pruebas_id_str:
                try:
                    tipo_pruebas_id = int(tipo_pruebas_id_str)
                    print(f"🔍 Buscando Tipo de Servicio con ID: {tipo_pruebas_id}")
                    
                    tipo_servicio = TipoServicio.objects.filter(id=tipo_pruebas_id).first()
                    if tipo_servicio:
                        nomenclaturas['tipo_pruebas_nomenclatura'] = tipo_servicio.nomenclatura
                        objetos_encontrados['tipo_servicio_obj'] = tipo_servicio
                        print(f"✅ Tipo de Servicio encontrado: ID={tipo_servicio.id}, Nombre='{tipo_servicio.nombre}', Nomenclatura='{tipo_servicio.nomenclatura}'")
                    else:
                        print(f"❌ No se encontró Tipo de Servicio con ID {tipo_pruebas_id}")
                        nomenclaturas['tipo_pruebas_nomenclatura'] = f"ID {tipo_pruebas_id} no encontrado"
                        
                except ValueError:
                    print(f"⚠️ El valor '{tipo_pruebas_id_str}' no es un ID válido para Tipo de Servicio")
                    nomenclaturas['tipo_pruebas_nomenclatura'] = "ID inválido"
            

            ticket_code, ticket_obj = generate_and_save_ticket(
                extracted_data=extracted_data,
                tipo_servicio_form=tipo_servicio_form,
                nomenclaturas=nomenclaturas,
                objetos_encontrados=objetos_encontrados)

            ticket_parts = generate_ticket_parts(ticket_code)

            # Mostrar resumen de búsqueda
            print("\n=== RESUMEN DE BÚSQUEDA ===")
            print(f"Nomenclatura Cliente: {nomenclaturas['cliente_nomenclatura']}")
            print(f"Nomenclatura Proyecto: {nomenclaturas['proyecto_nomenclatura']}")
            print(f"Nomenclatura Tipo Pruebas: {nomenclaturas['tipo_pruebas_nomenclatura']}")
            print(f"Nomenclatura Tipo Servicio (formulario): {nomenclaturas['tipo_servicio_nomenclatura']}")
            print("===========================\n")
    
            
            # Guardar en la base de datos ExcelData - AGREGAR CAMPO TIPO_SERVICIO
            excel_data = ExcelData.objects.create(
                cliente=extracted_data.get('cliente', ''),
                proyecto=extracted_data.get('proyecto', ''),
                tipo_pruebas=extracted_data.get('tipo_pruebas', ''),
                tipo_servicio=tipo_servicio_form,  # <-- NUEVO: Guardar tipo servicio del formulario
                responsable_solicitud=extracted_data.get('responsable_solicitud', ''),
                lider_proyecto=extracted_data.get('lider_proyecto', ''),
                tipo_aplicacion=extracted_data.get('tipo_aplicacion', ''),
                numero_version=extracted_data.get('numero_version', ''),
                funcionalidad_liberacion=extracted_data.get('funcionalidad_liberacion', ''),
                detalle_cambios=extracted_data.get('detalle_cambios', ''),
                justificacion_cambio=extracted_data.get('justificacion_cambio', ''),
                ticket_code=ticket_code 
            )
            
            if ticket_obj:
               ticket_obj.excel_data = excel_data
               ticket_obj.save()

            # Eliminar archivo temporal
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Preparar datos para la plantilla
            # Crear un diccionario con todos los datos para pasar a la plantilla
            data_for_template = {
                'cliente': excel_data.cliente,
                'proyecto': excel_data.proyecto,
                'tipo_pruebas': excel_data.tipo_pruebas,
                'tipo_servicio': excel_data.tipo_servicio,  # <-- NUEVO
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
                'data': data_for_template,  # Diccionario con todos los datos
                'excel_data': excel_data,  # También pasar el objeto completo si lo necesitas
                'nomenclaturas': nomenclaturas,
                'objetos_encontrados': objetos_encontrados,
                'ticket_code': ticket_code,  # Si implementas la función de generar ticket
                'ticket_parts': ticket_parts, 
                'tipo_servicio_form': tipo_servicio_form  # Opcional, para uso específico
            })
            
        except Exception as e:
            print(f"❌ ERROR en procesamiento: {str(e)}")
            messages.error(request, f'Error al procesar el archivo: {str(e)}')
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
        tipos = TipoServicio.objects.all()
        
        # Debug
        print(f"GET parameters: {request.GET}")
        
        # Ordenamiento
        orden = request.GET.get('orden', 'id')
        print(f"Orden solicitado: {orden}")
        
        # Diccionario de ordenamiento permitido
        orden_permitido = {
            'id': 'id', 
            '-id': '-id',
            'nombre': 'nombre', 
            '-nombre': '-nombre',
            'nomenclatura': 'nomenclatura', 
            '-nomenclatura': '-nomenclatura',
            'activo': 'activo', 
            '-activo': '-activo',
            'fecha_creacion': 'fecha_creacion', 
            '-fecha_creacion': '-fecha_creacion',
        }
        
        orden_final = orden_permitido.get(orden, 'id')
        print(f"Orden final: {orden_final}")
        
        tipos = tipos.order_by(orden_final)
        print(f"Query SQL: {tipos.query}")
        
        context = {
            'tipos': tipos,
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

def proyectos_por_cliente(request, cliente_id):
    """Obtener proyectos de un cliente específico (para AJAX)"""
    try:
        cliente = get_object_or_404(Cliente, id=cliente_id)
        proyectos = Proyecto.objects.filter(cliente=cliente, activo=True).order_by('nombre')
        
        proyectos_list = [
            {'id': p.id, 'nombre': p.nombre, 'codigo': p.codigo}
            for p in proyectos
        ]
        
        return JsonResponse({'proyectos': proyectos_list})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    
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









