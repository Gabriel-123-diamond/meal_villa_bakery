from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from users.models import UserProfile
from payroll.models import PayrollProfile

class Command(BaseCommand):
    help = 'DELETES ALL USERS and creates a fresh set of staff with predefined passwords and default salaries.'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.ERROR('WARNING: This will delete ALL existing users and replace them with a predefined list.'))
        confirm = input('Are you sure you want to continue? (yes/no): ')
        if confirm.lower() != 'yes':
            self.stdout.write(self.style.ERROR('Operation cancelled.'))
            return

        self.stdout.write("Deleting ALL existing Django users...")
        User.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("All users deleted."))

        self.stdout.write("Creating predefined staff accounts...")

        staff_to_create = [
            {'staff_id': '000000', 'name': 'Gabriel Developer', 'password': 'DevPassword1!', 'role': 'developer', 'is_active': True, 'salary': 500000},
            {'staff_id': '100001', 'name': 'Chris Manager', 'password': 'ManagerPass1!', 'role': 'manager', 'is_active': True, 'salary': 350000},
            {'staff_id': '200002', 'name': 'Vic Supervisor', 'password': 'SupervisorPass1!', 'role': 'supervisor', 'is_active': True, 'salary': 250000},
            {'staff_id': '300003', 'name': 'Favour Accountant', 'password': 'AccountantPass1!', 'role': 'accountant', 'is_active': True, 'salary': 200000},
            {'staff_id': '400004', 'name': 'Mfon Staff', 'password': 'StaffPass1!', 'role': 'staff', 'is_active': True, 'salary': 80000},
            {'staff_id': '400005', 'name': 'Akan Staff', 'password': 'StaffPass2!', 'role': 'staff', 'is_active': False, 'salary': 80000},
            {'staff_id': '500006', 'name': 'Blessing Baker', 'password': 'BakerPass1!', 'role': 'baker', 'is_active': True, 'salary': 150000},
            {'staff_id': '600007', 'name': 'John Cleaner', 'password': 'CleanerPass1!', 'role': 'cleaner', 'is_active': True, 'salary': 60000},
            {'staff_id': '700008', 'name': 'David Storekeeper', 'password': 'StorekeeperPass1!', 'role': 'storekeeper', 'is_active': True, 'salary': 100000},
        ]
        
        created_count = 0
        for user_data in staff_to_create:
            try:
                username = user_data['staff_id']
                parts = user_data['name'].split(' ', 1)
                first_name = parts[0]
                last_name = parts[1] if len(parts) > 1 else ''

                user = User.objects.create_user(
                    username=username,
                    email=f"{username}@mealvilla.com",
                    password=user_data['password'],
                    first_name=first_name,
                    last_name=last_name,
                    is_active=user_data['is_active']
                )
                
                if user_data['role'] in ['manager', 'developer', 'supervisor', 'accountant']:
                    user.is_staff = True
                if user_data['role'] == 'developer':
                    user.is_superuser = True
                
                user.save()

                profile = user.profile
                profile.role = user_data['role']
                profile.staff_id = username
                profile.save()
                
                # Set the default monthly salary
                payroll_profile = user.payroll_profile
                payroll_profile.monthly_salary = user_data['salary']
                payroll_profile.save()

                created_count += 1
                self.stdout.write(f"Successfully created user: {username} - {user_data['name']}")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to create user {user_data['staff_id']}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"\nOperation complete. Created {created_count} new users."))

