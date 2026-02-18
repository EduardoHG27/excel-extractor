# create_superuser.py
import os
import sys
import django
from django.contrib.auth import get_user_model

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'excel_extractor.settings')
django.setup()

User = get_user_model()

def create_superuser():
    """Crear superusuario desde variables de entorno"""
    
    # Obtener credenciales de variables de entorno
    username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
    email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
    password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
    
    # Verificar que las variables estén configuradas
    if not username or not password:
        print("⚠️  Variables DJANGO_SUPERUSER_USERNAME o DJANGO_SUPERUSER_PASSWORD no configuradas")
        print("   El superusuario NO fue creado automáticamente")
        return False
    
    # Verificar si el usuario ya existe
    if User.objects.filter(username=username).exists():
        print(f"✅ Superusuario '{username}' ya existe")
        return True
    
    # Crear el superusuario
    try:
        User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        print(f"🎉 Superusuario '{username}' creado exitosamente!")
        return True
    except Exception as e:
        print(f"❌ Error al crear superusuario: {e}")
        return False

if __name__ == '__main__':
    print("=== Creando superusuario automático ===")
    success = create_superuser()
    if not success:
        print("⚠️  Puedes crear un superusuario manualmente después:")
        print("   railway exec python manage.py createsuperuser")
    print("=====================================")