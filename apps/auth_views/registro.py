"""
Vista de registro de usuarios
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from extractor.forms import RegistroUsuarioForm


def registro_view(request):
    """Vista para registro de nuevos usuarios"""
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'¡Bienvenido {user.username}! Tu cuenta ha sido creada exitosamente.')
            return redirect('extractor:solicitud_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Error en {field}: {error}')
    else:
        form = RegistroUsuarioForm()
    
    return render(request, 'extractor/registro.html', {'form': form})