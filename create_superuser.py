# create_superuser.py
import os
import django
from django.contrib.auth import get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'excel_extractor.settings')
django.setup()

User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'qa_adwin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'eehernandez@buroidentidad.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

if not User.objects.filter(username=username).exists():
    if not password:
        print("⚠️ No se encontró DJANGO_SUPERUSER_PASSWORD. Usando contraseña por defecto.")
        password = 'pa55w00rd_qa'  # Cambia esto
    
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"✅ Superusuario '{username}' creado exitosamente")
else:
    print(f"ℹ️ El superusuario '{username}' ya existe")