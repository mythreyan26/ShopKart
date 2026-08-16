import os
import random
from django.core.files import File
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from shop.models import Category, Product, ProductImage, Review

REAL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), 'static', 'images', 'real')

CATEGORIES = [
    ("Electronics", "Phones, laptops, audio and everyday tech.", "cat_electronics.jpg"),
    ("Fashion", "Clothing, footwear and accessories for everyone.", "cat_fashion.jpg"),
    ("Home & Kitchen", "Furniture, decor and kitchen essentials.", "cat_home_and_kitchen.jpg"),
    ("Beauty & Personal Care", "Skincare, fragrance and grooming.", "cat_beauty_and_personal_care.jpg"),
    ("Sports & Fitness", "Gear and equipment to keep you moving.", "cat_sports_and_fitness.jpg"),
    ("Books", "Bestsellers, fiction and non-fiction reads.", "cat_books.jpg"),
    ("Grocery", "Daily essentials delivered to your door.", "cat_grocery.jpg"),
    ("Toys & Games", "Fun for kids and kids-at-heart.", "cat_toys_and_games.jpg"),
]

SUBCATEGORIES = [
    ("Mobiles", "Electronics", "Latest smartphones, 5G devices and mobile accessories.", "prod_smartphone.jpg"),
    ("Laptops & Computers", "Electronics", "High-performance laptops, ultrabooks and computing gear.", "prod_laptop.jpg"),
    ("Audio & Headphones", "Electronics", "Noise-cancelling headphones, wireless earbuds and audio gear.", "prod_headphones.jpg"),
    ("Cameras", "Electronics", "Mirrorless, DSLR and digital cameras.", "prod_camera.jpg"),
    ("Smartwatches", "Electronics", "Fitness trackers, health monitors and smart wearables.", "prod_smartwatch.jpg"),
]

PRODUCTS = {
    "Mobiles": [
        ("Nimbus X12 Smartphone (128GB)", "Nimbus", 24999, 17999, "prod_smartphone.jpg", "A powerful everyday smartphone with a stunning AMOLED display and all-day battery.\n6.5-inch AMOLED display\n128GB storage, 8GB RAM\n5000mAh battery\n50MP triple camera"),
    ],
    "Laptops & Computers": [
        ("Vertex Pro 14 Laptop", "Vertex", 68999, 54999, "prod_laptop.jpg", "Slim and powerful laptop built for work and creativity.\n14-inch FHD display\n16GB RAM, 512GB SSD\nUp to 12 hours battery\nBacklit keyboard"),
    ],
    "Audio & Headphones": [
        ("AuraSound Wireless ANC Headphones", "AuraSound", 6999, 3499, "prod_headphones.jpg", "Immersive over-ear headphones with active noise cancellation and 40-hour battery life.\nActive Noise Cancellation\n40-hour battery life\nBluetooth 5.3\nFast charge: 10 min = 5 hrs playback"),
        ("Nimbus Buds Pro Earbuds", "Nimbus", 3999, 1799, "prod_earbuds.jpg", "True wireless earbuds with rich bass and a compact charging case.\nActive noise cancellation\n30-hour total battery\nIPX5 water resistant\nTouch controls"),
    ],
    "Cameras": [
        ("Lumen S1 Mirrorless Camera", "Lumen", 54999, 42999, "prod_camera.jpg", "Capture stunning photos and 4K video with this compact mirrorless camera.\n24MP sensor\n4K video recording\nIn-body stabilization\nWi-Fi transfer"),
    ],
    "Smartwatches": [
        ("Pulse Fit Smartwatch", "Pulse", 5999, 2999, "prod_smartwatch.jpg", "Track your health and stay connected on the go.\nHeart rate & SpO2 monitor\n7-day battery life\nAMOLED touch display\n100+ sport modes"),
    ],
    "Fashion": [
        ("Classic Fit Cotton T-Shirt", "Urban Thread", 999, 499, "prod_tshirt.jpg", "Everyday comfort in soft, breathable 100% cotton.\n100% pure cotton\nRegular fit\nMachine washable\nAvailable in multiple colors"),
        ("StrideMax Running Shoes", "StrideMax", 3499, 1999, "prod_running_shoes.jpg", "Lightweight running shoes with responsive cushioning.\nBreathable mesh upper\nShock-absorbing sole\nAnti-slip grip\nLightweight design"),
        ("Heritage Leather Tote Bag", "Heritage", 4999, 2799, "prod_leather_bag.jpg", "A timeless tote crafted from genuine leather.\nGenuine leather\nSpacious main compartment\nAdjustable strap\nInterior zip pocket"),
        ("Chrono Steel Analog Watch", "Chrono", 5999, 3299, "prod_watch.jpg", "A sleek analog watch with a stainless steel strap.\nStainless steel case\nWater resistant to 30m\nQuartz movement\n2-year warranty"),
        ("Slim Fit Denim Jacket", "Urban Thread", 2999, 1699, "prod_denim_jacket.jpg", "A versatile denim jacket for every season.\nPremium denim fabric\nSlim tailored fit\nButton closure\nMultiple pockets"),
        ("TrailBlaze Casual Sneakers", "StrideMax", 2799, 1499, "prod_sneakers.jpg", "Everyday sneakers that pair comfort with style.\nCushioned insole\nDurable rubber outsole\nBreathable lining\nClassic lace-up"),
    ],
    "Home & Kitchen": [
        ("Nordic 3-Seater Fabric Sofa", "Nordic Living", 34999, 24999, "prod_sofa.jpg", "A cozy 3-seater sofa that anchors any living room.\nHigh-density foam cushions\nSturdy wooden frame\nStain-resistant fabric\nEasy assembly"),
        ("Aria Modern Floor Lamp", "Aria", 3499, 1999, "prod_floor_lamp.jpg", "Add warm ambient lighting to any corner.\nAdjustable brightness\nEnergy-efficient LED\nMinimalist design\nStable weighted base"),
        ("SteelBrew Electric Kettle 1.5L", "SteelBrew", 1799, 999, "prod_kettle.jpg", "Boil water quickly and safely with auto shut-off.\n1.5 litre capacity\nAuto shut-off & boil-dry protection\nStainless steel body\n1500W fast heating"),
        ("Nordic Wooden Bookshelf", "Nordic Living", 7999, 5499, "prod_bookshelf.jpg", "A 5-tier bookshelf that blends function and style.\n5 spacious shelves\nEngineered wood\nEasy to assemble\nScratch-resistant finish"),
        ("Aria Table Lamp Duo Pack", "Aria", 2499, 1399, "prod_table_lamp.jpg", "Set of two bedside table lamps with soft-touch switch.\nSet of 2 lamps\nSoft ambient glow\nFabric shade\nCompact footprint"),
    ],
    "Beauty & Personal Care": [
        ("Velour Signature Eau de Parfum", "Velour", 3999, 2499, "prod_perfume.jpg", "A long-lasting fragrance with notes of amber and jasmine.\n50ml bottle\nUp to 8-hour longevity\nAmber & jasmine notes\nElegant glass bottle"),
        ("Blossom Matte Lipstick Set", "Blossom", 1499, 799, "prod_lipstick.jpg", "A set of 3 richly pigmented matte lipsticks.\nSet of 3 shades\nLong-lasting matte finish\nEnriched with vitamin E\nCruelty-free"),
        ("Velour Citrus Cologne Spray", "Velour", 2999, 1799, "prod_cologne.jpg", "A refreshing citrus cologne for daily wear.\n100ml bottle\nFresh citrus & musk\nLong-lasting spray\nTravel-friendly size"),
        ("Blossom Hydrating Lip Care Kit", "Blossom", 999, 599, "prod_lip_care.jpg", "Nourish and protect your lips with this hydrating kit.\n3-piece kit\nShea butter formula\nNon-sticky finish\nSuitable for daily use"),
    ],
    "Sports & Fitness": [
        ("PowerFlex Adjustable Dumbbell Set", "PowerFlex", 5999, 3999, "prod_dumbbells.jpg", "A space-saving adjustable dumbbell set for home workouts.\n5-25kg adjustable per dumbbell\nQuick-lock mechanism\nDurable cast iron\nCompact storage tray"),
        ("ProKick Match Football", "ProKick", 1499, 899, "prod_football.jpg", "A durable match-quality football for all surfaces.\nSize 5, FIFA-spec\nWater-resistant outer\nMachine-stitched panels\nHigh-visibility design"),
        ("PowerFlex Resistance Band Kit", "PowerFlex", 1299, 699, "prod_resistance_bands.jpg", "A 5-band resistance kit for strength and mobility training.\n5 resistance levels\nIncludes door anchor\nPortable carry bag\nSuitable for all fitness levels"),
        ("ProKick Basketball Pro", "ProKick", 1799, 999, "prod_basketball.jpg", "An indoor/outdoor basketball with excellent grip.\nComposite leather cover\nDeep channel grip\nOfficial size & weight\nIndoor/outdoor use"),
    ],
    "Books": [
        ("The Silent Horizon (Fiction)", "Penfield Press", 599, 349, "prod_fiction_book.jpg", "A gripping mystery novel that keeps you guessing until the last page.\n412 pages\nPaperback edition\nBestselling mystery\nAward-nominated author"),
        ("Atomic Focus: Mastering Deep Work", "Penfield Press", 499, 299, "prod_focus_book.jpg", "A practical guide to building focus in a distracted world.\n288 pages\nNon-fiction / self-help\nActionable frameworks\nBestseller"),
        ("Chronicles of the Northern Sky", "Wanderline Books", 699, 449, "prod_fantasy_book.jpg", "An epic fantasy adventure spanning three kingdoms.\n560 pages\nHardcover collector's edition\nFirst in a trilogy\nMaps included"),
    ],
    "Grocery": [
        ("Golden Harvest Basmati Rice 5kg", "Golden Harvest", 799, 599, "prod_rice.jpg", "Premium long-grain basmati rice, aged for aroma and taste.\n5kg pack\nAged for enhanced aroma\nLong-grain premium quality\nSourced from Himalayan foothills"),
        ("PureLeaf Assam Tea 500g", "PureLeaf", 399, 279, "prod_tea.jpg", "Rich and malty Assam tea leaves for the perfect cup.\n500g pack\nStrong malty flavor\nSingle-origin Assam\nResealable pack"),
    ],
    "Toys & Games": [
        ("CuddleCo Plush Teddy Bear (24-inch)", "CuddleCo", 1499, 899, "prod_teddy_bear.jpg", "An extra-soft, huggable teddy bear that makes the perfect gift.\n24-inch height\nUltra-soft plush fabric\nChild-safe stitching\nMachine washable"),
        ("BrainBox 500-Piece Puzzle", "BrainBox", 899, 499, "prod_puzzle.jpg", "A challenging 500-piece jigsaw puzzle for family game night.\n500 pieces\nPremium thick cardboard\nVivid print quality\nAges 8+"),
        ("SkyBounce Foam Play Ball Set", "SkyBounce", 699, 399, "prod_play_balls.jpg", "A set of 3 soft foam balls, safe for indoor and outdoor play.\nSet of 3 balls\nSoft foam, safe for indoors\nLightweight & durable\nAges 3+"),
    ],
}

SAMPLE_REVIEWS = [
    (5, "Excellent quality!", "Exceeded my expectations, would definitely buy again."),
    (4, "Great value for money", "Works well, minor quirks but overall very satisfied."),
    (5, "Fast delivery, great product", "Arrived earlier than expected and packaging was solid."),
    (3, "Decent, not amazing", "Does the job but nothing extraordinary."),
    (5, "Highly recommend", "One of the best purchases I've made this year."),
]


class Command(BaseCommand):
    help = "Seed the database with demo categories, products and reviews"

    def add_arguments(self, parser):
        parser.add_argument('--flush', action='store_true', help='Delete existing catalog data first')

    def handle(self, *args, **options):
        if options['flush']:
            Product.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write("Cleared existing catalog data")

        demo_user, _ = User.objects.get_or_create(username='demo_buyer', defaults={'email': 'demo@shopkart.test'})
        if not demo_user.has_usable_password():
            demo_user.set_password('demopass123')
            demo_user.save()

        reviewer_names = ['Aarav', 'Priya', 'Rohan', 'Sneha', 'Kabir', 'Ananya']
        reviewers = []
        for rname in reviewer_names:
            uname = f"reviewer_{rname.lower()}"
            u, _ = User.objects.get_or_create(username=uname, defaults={'first_name': rname, 'email': f'{uname}@shopkart.test'})
            if not u.has_usable_password():
                u.set_password('demopass123')
                u.save()
            reviewers.append(u)

        cat_objs = {}
        for name, desc, img in CATEGORIES:
            cat, created = Category.objects.get_or_create(name=name, defaults={'description': desc, 'status': False, 'parent': None})
            if created or not cat.image:
                img_path = os.path.join(REAL_DIR, img)
                if os.path.exists(img_path):
                    with open(img_path, 'rb') as f:
                        cat.image.save(img, File(f), save=True)
            cat_objs[name] = cat

        for name, parent_name, desc, img in SUBCATEGORIES:
            parent_cat = cat_objs.get(parent_name)
            subcat, created = Category.objects.get_or_create(
                name=name,
                defaults={'description': desc, 'parent': parent_cat, 'status': False}
            )
            if not subcat.parent and parent_cat:
                subcat.parent = parent_cat
                subcat.save()
            if created or not subcat.image:
                img_path = os.path.join(REAL_DIR, img)
                if os.path.exists(img_path):
                    with open(img_path, 'rb') as f:
                        subcat.image.save(img, File(f), save=True)
            cat_objs[name] = subcat

        total_products = 0
        for cat_name, plist in PRODUCTS.items():
            category = cat_objs[cat_name]
            for i, (pname, brand, orig, sell, img, desc_block) in enumerate(plist):
                lines = desc_block.split('\n')
                description = lines[0]
                highlights = '\n'.join(lines[1:])
                product, created = Product.objects.get_or_create(
                    name=pname, category=category,
                    defaults={
                        'brand': brand, 'vendor': brand,
                        'quantity': random.randint(8, 60),
                        'original_price': orig, 'selling_price': sell,
                        'description': description, 'highlights': highlights,
                        'status': False,
                        'trending': i % 3 == 0,
                        'featured': i % 2 == 0,
                        'is_bestseller': i % 4 == 1,
                        'free_delivery': True,
                    }
                )
                if created or not product.product_image:
                    img_path = os.path.join(REAL_DIR, img)
                    if os.path.exists(img_path):
                        with open(img_path, 'rb') as f:
                            product.product_image.save(img, File(f), save=True)
                if 'Smartphone' in pname and not product.gallery.exists():
                    for side_img in ['prod_phone_back.jpg', 'prod_phone_side.jpg', 'prod_phone_camera.jpg']:
                        side_path = os.path.join(REAL_DIR, side_img)
                        if os.path.exists(side_path):
                            pi = ProductImage(product=product)
                            with open(side_path, 'rb') as f:
                                pi.image.save(side_img, File(f), save=True)
                if created:
                    total_products += 1
                    picked = random.sample(reviewers, k=random.randint(2, 4))
                    for reviewer in picked:
                        rating, title, comment = random.choice(SAMPLE_REVIEWS)
                        Review.objects.get_or_create(
                            product=product, user=reviewer,
                            defaults={'rating': rating, 'title': title, 'comment': comment}
                        )

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {len(cat_objs)} categories and {total_products} products."
        ))
