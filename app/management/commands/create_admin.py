"""
Django management command to create an admin user
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Create an admin user for the application'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Username for the admin user (default: admin)',
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@kcdd.org',
            help='Email for the admin user (default: admin@kcdd.org)',
        )
        parser.add_argument(
            '--password',
            type=str,
            default='admin123',
            help='Password for the admin user (default: admin123)',
        )
        parser.add_argument(
            '--first-name',
            type=str,
            default='Admin',
            help='First name for the admin user (default: Admin)',
        )
        parser.add_argument(
            '--last-name',
            type=str,
            default='User',
            help='Last name for the admin user (default: User)',
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']

        # Check if user already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'User "{username}" already exists. Skipping creation.')
            )
            return

        # Create superuser
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            user_type='admin',
            is_vetted=True,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created admin user:\n'
                f'  Username: {username}\n'
                f'  Email: {email}\n'
                f'  Password: {password}\n'
                f'  Name: {first_name} {last_name}'
            )
        )
