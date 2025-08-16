# listings/filters.py
import django_filters
from django import forms
from django.db.models import Q
from .models import Listing

# A comprehensive, alphabetized list of all 149 cities in the Philippines
PHILIPPINE_CITIES = [
    ('Alaminos', 'Alaminos'), ('Angeles', 'Angeles'), ('Antipolo', 'Antipolo'), ('Bacolod', 'Bacolod'),
    ('Bacoor', 'Bacoor'), ('Bago', 'Bago'), ('Baguio', 'Baguio'), ('Bais', 'Bais'), ('Balanga', 'Balanga'),
    ('Batac', 'Batac'), ('Batangas City', 'Batangas City'), ('Bayawan', 'Bayawan'), ('Baybay', 'Baybay'),
    ('Bayugan', 'Bayugan'), ('Biñan', 'Biñan'), ('Bislig', 'Bislig'), ('Bogo', 'Bogo'), ('Borongan', 'Borongan'),
    ('Butuan', 'Butuan'), ('Cabadbaran', 'Cabadbaran'), ('Cabanatuan', 'Cabanatuan'), ('Cabuyao', 'Cabuyao'),
    ('Cadiz', 'Cadiz'), ('Cagayan de Oro', 'Cagayan de Oro'), ('Calaca', 'Calaca'), ('Calamba', 'Calamba'),
    ('Calapan', 'Calapan'), ('Calbayog', 'Calbayog'), ('Caloocan', 'Caloocan'), ('Candon', 'Candon'),
    ('Canlaon', 'Canlaon'), ('Carcar', 'Carcar'), ('Carmona', 'Carmona'), ('Catbalogan', 'Catbalogan'),
    ('Cauayan', 'Cauayan'), ('Cavite City', 'Cavite City'), ('Cebu City', 'Cebu City'), ('Cotabato City', 'Cotabato City'),
    ('Dagupan', 'Dagupan'), ('Danao', 'Danao'), ('Dapitan', 'Dapitan'), ('Dasmariñas', 'Dasmariñas'),
    ('Davao City', 'Davao City'), ('Digos', 'Digos'), ('Dipolog', 'Dipolog'), ('Dumaguete', 'Dumaguete'),
    ('El Salvador', 'El Salvador'), ('Escalante', 'Escalante'), ('Gapan', 'Gapan'), ('General Santos', 'General Santos'),
    ('General Trias', 'General Trias'), ('Gingoog', 'Gingoog'), ('Guihulngan', 'Guihulngan'), ('Himamaylan', 'Himamaylan'),
    ('Ilagan', 'Ilagan'), ('Iligan', 'Iligan'), ('Iloilo City', 'Iloilo City'), ('Imus', 'Imus'), ('Iriga', 'Iriga'),
    ('Isabela', 'Isabela'), ('Kabankalan', 'Kabankalan'), ('Kidapawan', 'Kidapawan'), ('Koronadal', 'Koronadal'),
    ('La Carlota', 'La Carlota'), ('Lamitan', 'Lamitan'), ('Laoag', 'Laoag'), ('Lapu-Lapu City', 'Lapu-Lapu City'),
    ('Las Piñas', 'Las Piñas'), ('Legazpi', 'Legazpi'), ('Ligao', 'Ligao'), ('Lipa', 'Lipa'), ('Lucena', 'Lucena'),
    ('Maasin', 'Maasin'), ('Mabalacat', 'Mabalacat'), ('Makati', 'Makati'), ('Malabon', 'Malabon'),
    ('Malaybalay', 'Malaybalay'), ('Malolos', 'Malolos'), ('Mandaue', 'Mandaue'), ('Mandaluyong', 'Mandaluyong'),
    ('Manila', 'Manila'), ('Marawi', 'Marawi'), ('Marikina', 'Marikina'), ('Masbate City', 'Masbate City'),
    ('Mati', 'Mati'), ('Meycauayan', 'Meycauayan'), ('Muñoz', 'Muñoz'), ('Muntinlupa', 'Muntinlupa'),
    ('Naga', 'Naga'), ('Navotas', 'Navotas'), ('Olongapo', 'Olongapo'), ('Ormoc', 'Ormoc'),
    ('Oroquieta', 'Oroquieta'), ('Ozamiz', 'Ozamiz'), ('Pagadian', 'Pagadian'), ('Palayan', 'Palayan'),
    ('Panabo', 'Panabo'), ('Parañaque', 'Parañaque'), ('Pasay', 'Pasay'), ('Pasig', 'Pasig'),
    ('Passi', 'Passi'), ('Puerto Princesa', 'Puerto Princesa'), ('Quezon City', 'Quezon City'), ('Roxas', 'Roxas'),
    ('Sagay', 'Sagay'), ('Samal', 'Samal'), ('San Carlos', 'San Carlos'), ('San Fernando', 'San Fernando'),
    ('San Jose', 'San Jose'), ('San Jose del Monte', 'San Jose del Monte'), ('San Juan', 'San Juan'),
    ('San Pablo', 'San Pablo'), ('San Pedro', 'San Pedro'), ('Santa Rosa', 'Santa Rosa'), ('Santiago', 'Santiago'),
    ('Silay', 'Silay'), ('Sipalay', 'Sipalay'), ('Sorsogon City', 'Sorsogon City'), ('Surigao City', 'Surigao City'),
    ('Tabaco', 'Tabaco'), ('Tabuk', 'Tabuk'), ('Tacloban', 'Tacloban'), ('Tacurong', 'Tacurong'),
    ('Tagaytay', 'Tagaytay'), ('Tagbilaran', 'Tagbilaran'), ('Taguig', 'Taguig'), ('Tagum', 'Tagum'),
    ('Talisay', 'Talisay'), ('Tanauan', 'Tanauan'), ('Tandag', 'Tandag'), ('Tangub', 'Tangub'),
    ('Tanjay', 'Tanjay'), ('Tarlac City', 'Tarlac City'), ('Tayabas', 'Tayabas'), ('Toledo', 'Toledo'),
    ('Trece Martires', 'Trece Martires'), ('Tuguegarao', 'Tuguegarao'), ('Urdaneta', 'Urdaneta'),
    ('Valencia', 'Valencia'), ('Valenzuela', 'Valenzuela'), ('Victorias', 'Victorias'), ('Vigan', 'Vigan'),
    ('Zamboanga City', 'Zamboanga City')
]

# Comprehensive list of marketplace categories with subcategories
MARKETPLACE_CATEGORIES = [
    ('Vehicles', (
        ('Cars, Trucks & Motorcycles', 'Cars, Trucks & Motorcycles'),
        ('Auto Parts', 'Auto Parts'),
        ('RVs, Boats & Trailers', 'RVs, Boats & Trailers'),
    )),
    ('Property', (
        ('Housing for Rent', 'Housing for Rent'),
        ('Housing for Sale', 'Housing for Sale'),
    )),
    ('Electronics', (
        ('Mobile Phones', 'Mobile Phones'),
        ('Computers & Laptops', 'Computers & Laptops'),
        ('TVs & Home Entertainment', 'TVs & Home Entertainment'),
        ('Cameras & Photography', 'Cameras & Photography'),
        ('Video Games & Consoles', 'Video Games & Consoles'),
    )),
    ('Home & Garden', (
        ('Furniture', 'Furniture'),
        ('Home Appliances', 'Home Appliances'),
        ('Garden & Outdoor', 'Garden & Outdoor'),
        ('Tools & Home Improvement', 'Tools & Home Improvement'),
    )),
    ('Clothing, Shoes & Accessories', (
        ('Women\'s Clothing & Shoes', 'Women\'s Clothing & Shoes'),
        ('Men\'s Clothing & Shoes', 'Men\'s Clothing & Shoes'),
        ('Bags & Luggage', 'Bags & Luggage'),
        ('Jewelry & Watches', 'Jewelry & Watches'),
    )),
    ('Family', (
        ('Baby & Kids', 'Baby & Kids'),
        ('Pet Supplies', 'Pet Supplies'),
        ('Health & Beauty', 'Health & Beauty'),
    )),
    ('Hobbies & Entertainment', (
        ('Books, Movies & Music', 'Books, Movies & Music'),
        ('Sports & Outdoors', 'Sports & Outdoors'),
        ('Musical Instruments', 'Musical Instruments'),
        ('Antiques & Collectibles', 'Antiques & Collectibles'),
        ('Arts & Crafts', 'Arts & Crafts'),
        ('Toys & Games', 'Toys & Games'),
    )),
]

class ListingFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method="search_filter",
        label="Search",
        widget=forms.TextInput(attrs={"placeholder":"Search items...", "class":"form-control"})
    )
    category = django_filters.ChoiceFilter(
        choices=MARKETPLACE_CATEGORIES,
        empty_label="All Categories",
        label="Category",
        widget=forms.Select(attrs={"class":"form-control"})
    )
    city = django_filters.ChoiceFilter(
        choices=PHILIPPINE_CITIES,
        empty_label="All Cities",
        label="City",
        widget=forms.Select(attrs={"class":"form-control"})
    )

    class Meta:
        model = Listing
        fields = ["q", "category", "city"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Exclude 'sold' listings from the main queryset by default
        self.queryset = self.queryset.filter(status='available')

    def search_filter(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(Q(title__icontains=value) | Q(description__icontains=value))