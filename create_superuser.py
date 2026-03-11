# create_superuser.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'excel_extractor.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'qa_adwin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'eehernandez@buroidentidad.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

if password:
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username, email, password)
        print(f'✅ Superusuario {username} creado')
    else:
        print(f'ℹ️  Superusuario {username} ya existe')
else:
    print('⚠️  No se creó superusuario: DJANGO_SUPERUSER_PASSWORD no está configurada')