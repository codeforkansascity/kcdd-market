"""
Django management command to migrate data from SQLite to PostgreSQL
"""
import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connections
from django.core.management import call_command
from app.models import User, Organization, DonorProfile, Request, CauseArea, IdentityCategory, ChallengeCategory


class Command(BaseCommand):
    help = 'Migrate data from SQLite to PostgreSQL'

    def add_arguments(self, parser):
        parser.add_argument(
            '--export-only',
            action='store_true',
            help='Only export data from SQLite, do not import to PostgreSQL',
        )
        parser.add_argument(
            '--import-only',
            action='store_true',
            help='Only import data to PostgreSQL, do not export from SQLite',
        )
        parser.add_argument(
            '--export-file',
            type=str,
            default='sqlite_export.json',
            help='File to export/import data (default: sqlite_export.json)',
        )

    def handle(self, *args, **options):
        export_file = options['export_file']
        
        if options['import_only']:
            self.import_to_postgresql(export_file)
        elif options['export_only']:
            self.export_from_sqlite(export_file)
        else:
            self.stdout.write('Starting full migration from SQLite to PostgreSQL...')
            self.export_from_sqlite(export_file)
            self.import_to_postgresql(export_file)

    def export_from_sqlite(self, export_file):
        """Export data from SQLite database"""
        self.stdout.write('Exporting data from SQLite...')
        
        # Check if we're connected to SQLite
        if 'sqlite3' not in settings.DATABASES['default']['ENGINE']:
            self.stdout.write(self.style.ERROR('Not connected to SQLite database'))
            return
        
        data = {}
        
        # Export all models
        models_to_export = [
            (User, 'users'),
            (CauseArea, 'cause_areas'),
            (IdentityCategory, 'identity_categories'),
            (Organization, 'organizations'),
            (DonorProfile, 'donor_profiles'),
            (ChallengeCategory, 'challenge_categories'),
            (Request, 'requests'),
        ]
        
        for model, key in models_to_export:
            try:
                # Get all objects and convert to dict, handling missing fields
                objects = []
                for obj in model.objects.all():
                    obj_dict = {}
                    for field in obj._meta.fields:
                        try:
                            value = getattr(obj, field.name)
                            if hasattr(value, 'isoformat'):  # Handle datetime fields
                                value = value.isoformat()
                            obj_dict[field.name] = value
                        except Exception as e:
                            # Skip fields that don't exist
                            continue
                    
                    # Handle many-to-many fields if they exist
                    for field in obj._meta.many_to_many:
                        try:
                            related_objects = getattr(obj, field.name).all()
                            if related_objects.exists():
                                obj_dict[f'{field.name}_ids'] = [str(rel.id) for rel in related_objects]
                        except Exception as e:
                            # Skip many-to-many fields that don't exist
                            continue
                    
                    objects.append(obj_dict)
                
                data[key] = objects
                self.stdout.write(f'  Exported {len(objects)} {key}')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  Failed to export {key}: {e}'))
        
        # Save to file
        with open(export_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        self.stdout.write(self.style.SUCCESS(f'Data exported to {export_file}'))

    def import_to_postgresql(self, export_file):
        """Import data to PostgreSQL database"""
        self.stdout.write('Importing data to PostgreSQL...')
        
        # Check if we're connected to PostgreSQL
        if 'postgresql' not in settings.DATABASES['default']['ENGINE']:
            self.stdout.write(self.style.ERROR('Not connected to PostgreSQL database'))
            return
        
        # Check if export file exists
        if not os.path.exists(export_file):
            self.stdout.write(self.style.ERROR(f'Export file {export_file} not found'))
            return
        
        # Load data
        with open(export_file, 'r') as f:
            data = json.load(f)
        
        # Import in dependency order
        import_order = [
            ('users', User),
            ('cause_areas', CauseArea),
            ('identity_categories', IdentityCategory),
            ('organizations', Organization),
            ('donor_profiles', DonorProfile),
            ('challenge_categories', ChallengeCategory),
            ('requests', Request),
        ]
        
        for key, model in import_order:
            if key in data:
                try:
                    self._import_model_data(model, data[key])
                    self.stdout.write(f'  Imported {len(data[key])} {key}')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  Failed to import {key}: {e}'))
        
        self.stdout.write(self.style.SUCCESS('Data import completed'))

    def _import_model_data(self, model, objects_data):
        """Import data for a specific model"""
        # Clear existing data (be careful with this in production!)
        model.objects.all().delete()
        
        for obj_data in objects_data:
            try:
                # Handle special cases
                if 'password' in obj_data and obj_data['password']:
                    # Don't import hashed passwords, they'll be reset
                    obj_data['password'] = 'password123'
                
                # Create object
                obj = model(**obj_data)
                obj.save()
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'    Failed to import {obj_data}: {e}'))

    def _reset_sequences(self):
        """Reset PostgreSQL sequences after import"""
        try:
            with connections['default'].cursor() as cursor:
                cursor.execute("""
                    SELECT setval(pg_get_serial_sequence('app_user', 'id'), 
                                COALESCE((SELECT MAX(id) FROM app_user), 1) + 1, false);
                """)
                cursor.execute("""
                    SELECT setval(pg_get_serial_sequence('app_causearea', 'id'), 
                                COALESCE((SELECT MAX(id) FROM app_causearea), 1) + 1, false);
                """)
                # Add more sequences as needed
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Failed to reset sequences: {e}'))
