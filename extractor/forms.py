# extractor/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario, Cliente

class RegistroUsuarioForm(UserCreationForm):
    """Formulario personalizado para registro de usuarios"""
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    telefono = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    puesto = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'password1', 'password2', 'telefono', 'puesto', 'cliente_asociado']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'cliente_asociado': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Nombre de usuario'
        self.fields['email'].label = 'Correo electrónico'
        self.fields['password1'].label = 'Contraseña'
        self.fields['password2'].label = 'Confirmar contraseña'
        self.fields['cliente_asociado'].queryset = Cliente.objects.filter(activo=True)
        self.fields['cliente_asociado'].required = False
        self.fields['cliente_asociado'].label = 'Cliente asociado (opcional)'
        
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'