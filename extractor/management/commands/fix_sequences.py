# extractor/management/commands/fix_sequences.py
from django.core.management.base import BaseCommand
from django.db import connection
from extractor.models import Cliente, Proyecto, TipoServicio, Ticket, ExcelData

class Command(BaseCommand):
    help = 'Fija las secuencias de las tablas después de inserciones manuales'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo muestra lo que haría sin ejecutar cambios',
        )

    def handle(self, *args, **options):
        tables = [
            ('extractor_cliente', Cliente, 'Clientes'),
            ('extractor_proyecto', Proyecto, 'Proyectos'),
            ('extractor_tiposervicio', TipoServicio, 'Tipos de Servicio'),
            ('extractor_ticket', Ticket, 'Tickets'),
            ('extractor_exceldata', ExcelData, 'Datos Excel'),
        ]
        
        dry_run = options['dry_run']
        
        self.stdout.write(self.style.WARNING('🔍 Verificando secuencias...\n'))
        
        with connection.cursor() as cursor:
            for table_name, model, display_name in tables:
                # Obtener el máximo ID
                max_obj = model.objects.all().order_by('-id').first()
                max_id = max_obj.id if max_obj else 0
                
                # Obtener valor actual de la secuencia
                cursor.execute(f"SELECT last_value FROM {table_name}_id_seq")
                current_seq = cursor.fetchone()[0]
                
                self.stdout.write(f"\n📊 {display_name}:")
                self.stdout.write(f"   - Máximo ID en tabla: {max_id}")
                self.stdout.write(f"   - Valor actual de secuencia: {current_seq}")
                
                if max_id >= current_seq:
                    if dry_run:
                        self.stdout.write(
                            self.style.WARNING(f"   ⚠️ [DRY RUN] Se resetearía a: {max_id}")
                        )
                    else:
                        cursor.execute(f"SELECT setval('{table_name}_id_seq', {max_id})")
                        self.stdout.write(
                            self.style.SUCCESS(f"   ✅ Secuencia actualizada a: {max_id}")
                        )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f"   ✅ Secuencia OK (máx: {max_id} < seq: {current_seq})")
                    )
        
        if not dry_run:
            self.stdout.write(self.style.SUCCESS('\n✅ Todas las secuencias han sido verificadas'))