from django.core.management.base import BaseCommand
from bakery_management.db import get_mongo_db

class Command(BaseCommand):
    help = 'Seeds the database with initial products for sale.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Connecting to MongoDB...")
        db = get_mongo_db()
        products_collection = db.products
        
        # Clear existing products to avoid duplicates
        self.stdout.write("Clearing existing products...")
        products_collection.delete_many({})

        products_to_seed = [
            {'name': 'Burger Bread', 'price': 300.00, 'current_stock': 100, 'category': 'Bread', 'description': 'Soft and fluffy buns perfect for burgers.'},
            {'name': 'Jumbo Bread', 'price': 600.00, 'current_stock': 80, 'category': 'Bread', 'description': 'An extra-large loaf for the whole family.'},
            {'name': 'Family Loaf', 'price': 1200.00, 'current_stock': 50, 'category': 'Bread', 'description': 'A large, classic white loaf.'},
            {'name': 'Short Bread', 'price': 800.00, 'current_stock': 70, 'category': 'Pastries', 'description': 'Buttery and crumbly shortbread cookies.'},
            {'name': 'Croissant', 'price': 450.00, 'current_stock': 60, 'category': 'Pastries', 'description': 'Flaky, buttery, and delicious.'},
            {'name': 'Doughnut', 'price': 350.00, 'current_stock': 120, 'category': 'Sweets', 'description': 'Glazed and filled with sweet cream.'},
            {'name': 'Meat Pie', 'price': 700.00, 'current_stock': 90, 'category': 'Savory', 'description': 'A rich pastry filled with seasoned minced meat.'},
            {'name': 'Sausage Roll', 'price': 500.00, 'current_stock': 100, 'category': 'Savory', 'description': 'Seasoned sausage wrapped in flaky pastry.'},
            {'name': 'Cake Slice', 'price': 1500.00, 'current_stock': 40, 'category': 'Sweets', 'description': 'A generous slice of our cake of the day.'},
            {'name': 'Full Loaf', 'price': 1000.00, 'current_stock': 60, 'category': 'Bread', 'description': 'Our signature whole wheat full loaf.'},
        ]

        self.stdout.write(f"Seeding {len(products_to_seed)} products...")
        products_collection.insert_many(products_to_seed)
        
        self.stdout.write(self.style.SUCCESS("Successfully seeded the product catalog."))

