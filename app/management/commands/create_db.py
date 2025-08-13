from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
import os


class Command(BaseCommand):
    help = 'Create database and run migrations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of database',
        )

    def handle(self, *args, **options):
        self.stdout.write('Starting database setup...')
        
        # Check if database exists
        db_path = 'db.sqlite3'
        db_exists = os.path.exists(db_path)
        
        if options['force'] and db_exists:
            self.stdout.write('Removing existing database...')
            os.remove(db_path)
            db_exists = False
        
        if not db_exists:
            self.stdout.write('Creating new database...')
            # Create database by running migrations
            call_command('migrate', verbosity=0)
            self.stdout.write(
                self.style.SUCCESS('Database created successfully!')
            )
        else:
            self.stdout.write('Database already exists.')
        
        # Run migrations
        self.stdout.write('Running migrations...')
        call_command('migrate', verbosity=1)
        self.stdout.write(
            self.style.SUCCESS('Migrations completed successfully!')
        )
        
        # Create superuser if none exists
        try:
            from django.contrib.auth.models import User
            if not User.objects.filter(is_superuser=True).exists():
                self.stdout.write('Creating superuser...')
                call_command('createsuperuser', interactive=False)
                self.stdout.write(
                    self.style.SUCCESS('Superuser created successfully!')
                )
            else:
                self.stdout.write('Superuser already exists.')
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Could not create superuser: {e}')
            )
        
        self.stdout.write(
            self.style.SUCCESS('Database setup completed successfully!')
        ) 