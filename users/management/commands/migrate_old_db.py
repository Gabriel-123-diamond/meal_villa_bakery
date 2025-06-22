from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
try:
    from db_config import DBHandler as OldDBHandler
except ImportError:
    OldDBHandler = None

from users.models import CustomUser
from inventory.models import CleanerSupply, BakerSupply, StorekeeperSupply
from production.models import BakerDailyLog

class Command(BaseCommand):
    help = 'Migrates data from the old MongoDB database to the new Django models.'

    def handle(self, *args, **kwargs):
        if not OldDBHandler:
            self.stdout.write(self.style.ERROR('Could not import old DBHandler. Make sure db_config.py is in the project root.'))
            return

        old_db = OldDBHandler()
        if old_db.client is None:
            self.stdout.write(self.style.ERROR('Failed to connect to the old database source.'))
            return
            
        self.stdout.write(self.style.SUCCESS("Connection to old DB successful. Starting migration..."))

        self.migrate_users(old_db)
        self.migrate_inventory(old_db, 'cleaner_inventory_items', CleanerSupply)
        self.migrate_inventory(old_db, 'baker_production_supplies', BakerSupply)
        self.migrate_inventory(old_db, 'storekeeper_supplies_items', StorekeeperSupply)
        self.migrate_baker_logs(old_db)

        self.stdout.write(self.style.SUCCESS('Data migration process finished.'))

    def migrate_users(self, old_db):
        self.stdout.write("\n--- Migrating Users ---")
        CustomUser.objects.all().delete() # Clear existing users
        old_users = list(old_db.get_collection(old_db.users_collection_name).find())
        old_auths = {rec['staff_id']: rec for rec in old_db.get_collection(old_db.staff_auth_collection_name).find()}
        
        for user_data in old_users:
            staff_id = user_data.get('staff_id')
            if not staff_id: continue
            
            auth_rec = old_auths.get(staff_id)
            if not auth_rec: continue

            # We use Django's make_password to ensure compatibility
            new_user = CustomUser(
                staff_id=staff_id,
                name=user_data.get('name'),
                email=user_data.get('email'),
                role=user_data.get('roleName', 'staff'),
                is_active=user_data.get('isActive', True)
            )
            # IMPORTANT: Set a default temporary password
            new_user.set_password('password123') 
            new_user.save()
        self.stdout.write(self.style.SUCCESS(f"Migrated {len(old_users)} users with a temporary password."))

    def migrate_inventory(self, old_db, collection_name, MongoEngineModel):
        self.stdout.write(f"\n--- Migrating {MongoEngineModel.__name__} ---")
        MongoEngineModel.objects.all().delete()
        old_items = list(old_db.get_collection(collection_name).find())
        
        for item_data in old_items:
            updated_by_user = None
            if item_data.get('updated_by_staff_id'):
                updated_by_user = CustomUser.objects(staff_id=item_data['updated_by_staff_id']).first()

            MongoEngineModel(
                name=item_data.get('name'),
                quantity=item_data.get('quantity', 0),
                unit=item_data.get('unit', ''),
                updated_by=updated_by_user
            ).save()
        self.stdout.write(self.style.SUCCESS(f"Migrated {len(old_items)} {MongoEngineModel.__name__} items."))

    def migrate_baker_logs(self, old_db):
        self.stdout.write("\n--- Migrating Baker Daily Logs ---")
        BakerDailyLog.objects.all().delete()
        old_logs = list(old_db.get_collection(old_db.baker_daily_logs_collection_name).find())
        
        for log_data in old_logs:
            baker_user = CustomUser.objects(staff_id=log_data.get('staff_id')).first()
            if not baker_user: continue
            
            prod = log_data.get('production', {})
            dmg = log_data.get('damages', {})
            
            BakerDailyLog(
                date=log_data.get('date'),
                baker=baker_user,
                production_burger=prod.get('burger', 0),
                production_jumbo=prod.get('jumbo', 0),
                production_family=prod.get('family', 0),
                production_short=prod.get('short', 0),
                damages_burger=dmg.get('burger', 0),
                damages_jumbo=dmg.get('jumbo', 0),
                damages_family=dmg.get('family', 0),
                damages_short=dmg.get('short', 0),
            ).save()
        self.stdout.write(self.style.SUCCESS(f"Migrated {len(old_logs)} baker daily logs."))


