"""
Vistas de autenticación
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def login_view(request):
    """Vista personalizada de login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get('next', 'extractor:upload_excel')
            return redirect(next_url)
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
    return render(request, 'extractor/login.html')


def logout_view(request):
    """Vista personalizada de logout"""
    logout(request)
    return redirect('extractor:login')


def registro_view(request):
    """Vista para registro de nuevos usuarios"""
    from extractor.forms import RegistroUsuarioForm
    
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