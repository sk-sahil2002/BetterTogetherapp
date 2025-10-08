from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Fix donation table schema by removing created_at column if it exists'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Check database type
            db_type = connection.vendor
            self.stdout.write(f"Database type: {db_type}")
            
            if db_type == 'sqlite':
                # SQLite syntax
                cursor.execute("""
                    SELECT COUNT(*) FROM pragma_table_info('campaign_donation') 
                    WHERE name = 'created_at'
                """)
                column_exists = cursor.fetchone()[0] > 0
                
                if column_exists:
                    self.stdout.write("Removing created_at column from SQLite database...")
                    cursor.execute("ALTER TABLE campaign_donation DROP COLUMN created_at")
                    self.stdout.write(self.style.SUCCESS("Successfully removed created_at column"))
                else:
                    self.stdout.write("created_at column does not exist in SQLite database")
                    
            elif db_type == 'postgresql':
                # PostgreSQL syntax
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.columns 
                    WHERE table_name = 'campaign_donation' AND column_name = 'created_at'
                """)
                column_exists = cursor.fetchone()[0] > 0
                
                if column_exists:
                    self.stdout.write("Removing created_at column from PostgreSQL database...")
                    cursor.execute("ALTER TABLE campaign_donation DROP COLUMN created_at")
                    self.stdout.write(self.style.SUCCESS("Successfully removed created_at column"))
                else:
                    self.stdout.write("created_at column does not exist in PostgreSQL database")
            else:
                self.stdout.write(self.style.WARNING(f"Unsupported database type: {db_type}"))
