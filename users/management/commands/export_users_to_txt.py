import sys
import os
from django.core.management.base import BaseCommand

# Adjust path to import db_config from the project root
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
try:
    from db_config import DBHandler as OldDBHandler
except ImportError:
    OldDBHandler = None

class Command(BaseCommand):
    help = 'Exports all staff IDs and names from the original MongoDB database to a text file.'

    def handle(self, *args, **kwargs):
        if not OldDBHandler:
            self.stdout.write(self.style.ERROR('Could not import old DBHandler. Make sure db_config.py is in the project root.'))
            return

        self.stdout.write("Connecting to original MongoDB database...")
        old_db = OldDBHandler()
        if old_db.client is None:
            self.stdout.write(self.style.ERROR('Failed to connect to the database source.'))
            return
            
        try:
            # Fetch all users without any role exclusion
            all_users = list(old_db.get_collection(old_db.users_collection_name).find({}))
            
            if not all_users:
                self.stdout.write(self.style.WARNING("No users found in the 'users' collection."))
                return

            output_filename = 'staff_list.txt'
            with open(output_filename, 'w') as f:
                for user in all_users:
                    staff_id = user.get('staff_id', 'N/A')
                    name = user.get('name', 'N/A')
                    f.write(f"Staff ID: {staff_id}, Username: {name}\n")
            
            self.stdout.write(self.style.SUCCESS(f"Successfully exported {len(all_users)} users to '{output_filename}'."))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))