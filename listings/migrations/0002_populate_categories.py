# listings/migrations/0002_populate_categories.py
from django.db import migrations
from django.utils.text import slugify

# A comprehensive list of categories for the marketplace
MARKETPLACE_CATEGORIES = [
    "Antiques & Collectibles",
    "Arts & Crafts",
    "Baby & Kids",
    "Bags & Luggage",
    "Books & Stationery",
    "Cars, Trucks & Motorcycles",
    "Clothing & Apparel",
    "Computers & Accessories",
    "Electronics & Gadgets",
    "Furniture & Home Living",
    "Health & Beauty",
    "Jewelry & Accessories",
    "Men's Fashion",
    "Mobile Phones & Tablets",
    "Musical Instruments",
    "Pet Supplies",
    "Photography & Videography",
    "Services",
    "Shoes & Footwear",
    "Sports & Outdoors",
    "Tickets & Vouchers",
    "Toys & Games",
    "Video Gaming",
    "Women's Fashion",
    "Other",
]

def populate_categories(apps, schema_editor):
    """
    Populates the Category model with a predefined list of categories.
    """
    Category = apps.get_model('listings', 'Category')
    for category_name in MARKETPLACE_CATEGORIES:
        # get_or_create prevents creating duplicates if the migration is run again
        Category.objects.get_or_create(
            name=category_name,
            defaults={'slug': slugify(category_name)}
        )

class Migration(migrations.Migration):

    dependencies = [
        # This migration depends on the initial migration that created the Category model.
        # Replace '0001_initial' with the actual name of your first migration file if it's different.
        ('listings', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(populate_categories),
    ]