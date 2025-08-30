"""
Django management command to create sample data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from app.models import CauseArea, IdentityCategory, Organization, DonorProfile, Request, ChallengeCategory

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample data for development'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing sample data before creating new data',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('Deleting existing sample data...')
            # Delete in reverse dependency order
            Request.objects.all().delete()
            DonorProfile.objects.all().delete()
            Organization.objects.all().delete()
            IdentityCategory.objects.all().delete()
            CauseArea.objects.all().delete()
            # Don't delete superusers, just regular users
            User.objects.filter(is_superuser=False).delete()

        self.stdout.write('Creating sample data...')

        # Create Cause Areas
        cause_areas = [
            {'name': 'Education', 'description': 'Educational programs and resources'},
            {'name': 'Healthcare', 'description': 'Health and medical services'},
            {'name': 'Housing', 'description': 'Shelter and housing assistance'},
            {'name': 'Food Security', 'description': 'Nutrition and food access'},
            {'name': 'Job Training', 'description': 'Employment and skills development'},
            {'name': 'Mental Health', 'description': 'Mental health and wellness'},
            {'name': 'Youth Services', 'description': 'Programs for children and youth'},
            {'name': 'Senior Services', 'description': 'Programs for elderly populations'},
            {'name': 'Technology Access', 'description': 'Digital equity and technology access'},
            {'name': 'Environmental', 'description': 'Environmental and sustainability programs'},
        ]

        for cause_data in cause_areas:
            cause_area, created = CauseArea.objects.get_or_create(
                name=cause_data['name'],
                defaults={'description': cause_data['description']}
            )
            if created:
                self.stdout.write(f'  Created cause area: {cause_area.name}')

        # Create Identity Categories
        identity_categories = [
            'Youth (Under 18)',
            'Young Adults (18-25)',
            'Adults (26-64)',
            'Seniors (65+)',
            'Women',
            'LGBTQ+',
            'Veterans',
            'Immigrants/Refugees',
            'People with Disabilities',
            'Low-Income Families',
            'Homeless Individuals',
            'Students',
        ]

        for identity_name in identity_categories:
            identity_category, created = IdentityCategory.objects.get_or_create(
                name=identity_name
            )
            if created:
                self.stdout.write(f'  Created identity category: {identity_category.name}')

        # Create Challenge Categories
        challenge_categories = [
            'Housing Insecure',
            'Transportation Insecure',
            'Low Income',
            'Unemployment/Underemployment',
            'Food Insecure',
            'English Language Learner',
            'Low Literacy',
            'Mental/Physical Health Issues',
            'Substance Use Issues',
            'Immigrants/Refugees',
        ]

        for challenge_name in challenge_categories:
            challenge_category, created = ChallengeCategory.objects.get_or_create(
                name=challenge_name
            )
            if created:
                self.stdout.write(f'  Created challenge category: {challenge_category.name}')

        # Create sample CBO users and organizations
        education_cause = CauseArea.objects.get(name='Education')
        healthcare_cause = CauseArea.objects.get(name='Healthcare')
        housing_cause = CauseArea.objects.get(name='Housing')
        food_cause = CauseArea.objects.get(name='Food Security')

        youth_category = IdentityCategory.objects.get(name='Youth (Under 18)')
        students_category = IdentityCategory.objects.get(name='Students')
        low_income_category = IdentityCategory.objects.get(name='Low-Income Families')

        # Sample CBOs
        cbo_data = [
            {
                'username': 'tech_for_all',
                'email': 'contact@techforall.org',
                'first_name': 'Maria',
                'last_name': 'Rodriguez',
                'org_name': 'Tech for All Community Center',
                'mission': 'Bridging the digital divide by providing technology access and training to underserved communities.',
                'email': 'programs@techforall.org',
                'phone': '(555) 123-4567',
                'address': '123 Community Lane, Seattle, WA',
                'zipcode': '98101',
                'website': 'https://techforall.org',
                'is_vetted': True,
            },
            {
                'username': 'learning_hub',
                'email': 'admin@learninghub.org',
                'first_name': 'David',
                'last_name': 'Kim',
                'org_name': 'Learning Hub Academy',
                'mission': 'Providing after-school educational programs and tutoring for K-12 students.',
                'email': 'tutoring@learninghub.org',
                'phone': '(555) 234-5678',
                'address': '456 Education Blvd, Portland, OR',
                'zipcode': '97201',
                'website': 'https://learninghub.org',
                'is_vetted': True,
            },
            {
                'username': 'safe_shelter',
                'email': 'intake@safeshelter.org',
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'org_name': 'Safe Harbor Shelter',
                'mission': 'Providing emergency housing and support services for families experiencing homelessness.',
                'email': 'services@safeshelter.org',
                'phone': '(555) 345-6789',
                'address': '789 Hope Street, San Francisco, CA',
                'zipcode': '94102',
                'website': 'https://safeshelter.org',
                'is_vetted': False,  # This one is pending approval
            },
        ]

        for cbo in cbo_data:
            # Create user
            user, created = User.objects.get_or_create(
                username=cbo['username'],
                defaults={
                    'email': cbo['email'],
                    'first_name': cbo['first_name'],
                    'last_name': cbo['last_name'],
                    'user_type': 'cbo',
                    'is_vetted': cbo['is_vetted'],
                }
            )
            if created:
                user.set_password('password123')  # Default password for demo
                user.save()
                self.stdout.write(f'  Created CBO user: {user.username}')

            # Create organization
            organization, created = Organization.objects.get_or_create(
                user=user,
                defaults={
                    'name': cbo['org_name'],
                    'mission': cbo['mission'],
                    'email': cbo['email'],
                    'phone': cbo['phone'],
                    'address': cbo['address'],
                    'zipcode': cbo['zipcode'],
                    'website': cbo['website'],
                }
            )
            if created:
                self.stdout.write(f'  Created organization: {organization.name}')

        # Create sample donor users
        donor_data = [
            {
                'username': 'john_donor',
                'user_email': 'john@email.com',
                'first_name': 'John',
                'last_name': 'Smith',
                'name': 'John S.',
                'email': 'john@email.com',
                'max_per_request': 500.00,
                'service_area_zipcode': '98101',
            },
            {
                'username': 'jane_philanthropist',
                'user_email': 'jane@email.com',
                'first_name': 'Jane',
                'last_name': 'Doe',
                'name': 'Jane D.',
                'email': 'jane@email.com',
                'max_per_request': 1000.00,
                'service_area_zipcode': '97201',
            },
        ]

        for donor in donor_data:
            # Create user
            user, created = User.objects.get_or_create(
                username=donor['username'],
                defaults={
                    'email': donor['user_email'],
                    'first_name': donor['first_name'],
                    'last_name': donor['last_name'],
                    'user_type': 'donor',
                    'is_vetted': True,  # Donors are auto-vetted
                }
            )
            if created:
                user.set_password('password123')  # Default password for demo
                user.save()
                self.stdout.write(f'  Created donor user: {user.username}')

            # Create donor profile
            donor_profile, created = DonorProfile.objects.get_or_create(
                user=user,
                defaults={
                    'name': donor['name'],
                    'email': donor['email'],
                    'max_per_request': donor['max_per_request'],
                    'service_area_zipcode': donor['service_area_zipcode'],
                }
            )
            if created:
                self.stdout.write(f'  Created donor profile: {donor_profile.name}')

        # Create sample requests (only for vetted CBOs)
        tech_for_all_org = Organization.objects.get(name='Tech for All Community Center')
        learning_hub_org = Organization.objects.get(name='Learning Hub Academy')

        # Get some challenge categories for the sample requests
        housing_insecure = ChallengeCategory.objects.get(name='Housing Insecure')
        low_income = ChallengeCategory.objects.get(name='Low Income')
        food_insecure = ChallengeCategory.objects.get(name='Food Insecure')

        sample_requests = [
            {
                'organization': tech_for_all_org,
                'description': 'We need 10 refurbished laptops for our computer literacy program. These will be used by low-income families to access online job training and educational resources. Our current computers are over 8 years old and can no longer run modern software effectively.',
                'amount': 2500.00,
                'urgency': 'high',
                'zipcode': '98101',
                'cause_area': education_cause,
                'status': 'open',
                'identity_categories': [youth_category, low_income_category],
                'challenge_categories': [low_income, food_insecure],
                'program_region_metro': 'all_kc_metro',
                'program_region_county': 'jackson_mo',
            },
            {
                'organization': learning_hub_org,
                'description': 'Request for educational tablets for our after-school tutoring program. We serve 25 K-8 students who need access to interactive learning apps and digital textbooks. Many of our students do not have technology access at home.',
                'amount': 1200.00,
                'urgency': 'medium',
                'zipcode': '97201',
                'cause_area': education_cause,
                'status': 'open',
                'identity_categories': [youth_category, students_category],
                'challenge_categories': [low_income, food_insecure],
                'program_region_metro': 'all_kc_metro',
                'program_region_county': 'johnson_ks',
            },
            {
                'organization': tech_for_all_org,
                'description': 'Funding needed for high-speed internet installation in our community center. This will enable us to offer virtual job training workshops and telehealth services to underserved community members.',
                'amount': 800.00,
                'urgency': 'medium',
                'zipcode': '98101',
                'cause_area': healthcare_cause,
                'status': 'claimed',
                'identity_categories': [low_income_category],
                'challenge_categories': [housing_insecure],
                'program_region_metro': 'kc_metro_mo',
                'program_region_county': 'clay_mo',
            },
        ]

        for req_data in sample_requests:
            identity_categories = req_data.pop('identity_categories')
            challenge_categories = req_data.pop('challenge_categories')
            request_obj, created = Request.objects.get_or_create(
                organization=req_data['organization'],
                description=req_data['description'],
                defaults=req_data
            )
            if created:
                request_obj.identity_categories.set(identity_categories)
                request_obj.challenge_categories.set(challenge_categories)
                self.stdout.write(f'  Created request: {request_obj.description[:50]}...')

        self.stdout.write(
            self.style.SUCCESS(
                '\nSample data created successfully!\n'
                'Default password for all users: password123\n'
                '\nCBO Users:\n'
                '- tech_for_all (Tech for All Community Center) - APPROVED\n'
                '- learning_hub (Learning Hub Academy) - APPROVED\n'
                '- safe_shelter (Safe Harbor Shelter) - PENDING APPROVAL\n'
                '\nDonor Users:\n'
                '- john_donor (John S.)\n'
                '- jane_philanthropist (Jane D.)\n'
            )
        )
