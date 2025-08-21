# listings/migrations/000Y_populate_categories.py
from django.db import migrations
from django.utils.text import slugify

# The original category structure from your filters.py
MARKETPLACE_CATEGORIES = {
    'Vehicles': [
        'Cars, Trucks & Motorcycles', 'Auto Parts', 'RVs, Boats & Trailers'
    ],
    'Property': [
        'Housing for Rent', 'Housing for Sale'
    ],
    'Electronics': [
        'Mobile Phones', 'Computers & Laptops', 'TVs & Home Entertainment',
        'Cameras & Photography', 'Video Games & Consoles'
    ],
    'Home & Garden': [
        'Furniture', 'Home Appliances', 'Garden & Outdoor',
        'Tools & Home Improvement'
    ],
    'Clothing, Shoes & Accessories': [
        "Women's Clothing & Shoes", "Men's Clothing & Shoes", 'Bags & Luggage',
        'Jewelry & Watches'
    ],
    'Family': [
        'Baby & Kids', 'Pet Supplies', 'Health & Beauty'
    ],
    'Hobbies & Entertainment': [
        'Books, Movies & Music', 'Sports & Outdoors', 'Musical Instruments',
        'Antiques & Collectibles', 'Arts & Crafts', 'Toys & Games'
    ],
}


def populate_categories(apps, schema_editor):
    """
    Populates the Category model with a hierarchical structure based on
    the MARKETPLACE_CATEGORIES dictionary.
    """
    Category = apps.get_model('listings', 'Category')

    for parent_name, children in MARKETPLACE_CATEGORIES.items():
        # Create or retrieve the parent category
        parent_cat, created = Category.objects.get_or_create(
            name=parent_name,
            defaults={'slug': slugify(parent_name), 'parent': None}
        )

        # Create child categories and associate them with the parent
        for child_name in children:
            Category.objects.get_or_create(
                name=child_name,
                defaults={
                    'slug': slugify(child_name),
                    'parent': parent_cat
                }
            )


class Migration(migrations.Migration):

    dependencies = [
        ('listings', '0002_alter_category_options_category_parent'),
    ]

    operations = [
        migrations.RunPython(populate_categories),
    ]