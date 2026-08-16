import os
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_IMG_DIR = os.path.join(BASE_DIR, 'static', 'images')
REAL_DIR = os.path.join(STATIC_IMG_DIR, 'real')

os.makedirs(STATIC_IMG_DIR, exist_ok=True)
os.makedirs(REAL_DIR, exist_ok=True)

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

IMAGES = {
    # Hero Slider Banners
    os.path.join(STATIC_IMG_DIR, 'banner_electronics.jpg'): 'https://images.unsplash.com/photo-1498049794561-7780e7231661?auto=format&fit=crop&w=1200&h=600&q=85',
    os.path.join(STATIC_IMG_DIR, 'banner_fashion.jpg'): 'https://images.unsplash.com/photo-1445205170230-053b83016050?auto=format&fit=crop&w=1200&h=600&q=85',
    os.path.join(STATIC_IMG_DIR, 'banner_home.jpg'): 'https://images.unsplash.com/photo-1618221195710-dd6b41faaea6?auto=format&fit=crop&w=1200&h=600&q=85',

    # Categories (square / circle thumb 400x400)
    os.path.join(REAL_DIR, 'cat_electronics.jpg'): 'https://images.unsplash.com/photo-1550009158-9ebf69173e03?auto=format&fit=crop&w=400&h=400&q=85',
    os.path.join(REAL_DIR, 'cat_fashion.jpg'): 'https://images.unsplash.com/photo-1489987707025-afc232f7ea0f?auto=format&fit=crop&w=400&h=400&q=85',
    os.path.join(REAL_DIR, 'cat_home_and_kitchen.jpg'): 'https://images.unsplash.com/photo-1556911220-e15b29be8c8f?auto=format&fit=crop&w=400&h=400&q=85',
    os.path.join(REAL_DIR, 'cat_beauty_and_personal_care.jpg'): 'https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?auto=format&fit=crop&w=400&h=400&q=85',
    os.path.join(REAL_DIR, 'cat_sports_and_fitness.jpg'): 'https://images.unsplash.com/photo-1517838277536-f5f99be501cd?auto=format&fit=crop&w=400&h=400&q=85',
    os.path.join(REAL_DIR, 'cat_books.jpg'): 'https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=400&h=400&q=85',
    os.path.join(REAL_DIR, 'cat_grocery.jpg'): 'https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=400&h=400&q=85',
    os.path.join(REAL_DIR, 'cat_toys_and_games.jpg'): 'https://images.unsplash.com/photo-1566576912321-d58ddd7a6088?auto=format&fit=crop&w=400&h=400&q=85',

    # Electronics Products
    os.path.join(REAL_DIR, 'prod_headphones.jpg'): 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=600&h=750&q=85',
    os.path.join(REAL_DIR, 'prod_smartphone.jpg'): 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=600&h=750&q=85',
    os.path.join(REAL_DIR, 'prod_laptop.jpg'): 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=600&h=750&q=85',
    os.path.join(REAL_DIR, 'prod_camera.jpg'): 'https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=600&h=750&q=85',
    os.path.join(REAL_DIR, 'prod_smartwatch.jpg'): 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=600&h=750&q=85',
    os.path.join(REAL_DIR, 'prod_earbuds.jpg'): 'https://images.unsplash.com/photo-1590658268037-6bf12165a8df?auto=format&fit=crop&w=600&h=750&q=85',

    # Fashion Products
    os.path.join(REAL_DIR, 'prod_tshirt.jpg'): 'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=600&h=750&q=85',
    os.path.join(REAL_DIR, 'prod_running_shoes.jpg'): 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=600&h=750&q=85',
    os.path.join(REAL_DIR, 'prod_leather_bag.jpg'): 'https://images.unsplash.com/photo-1548036328-c9fa89d128fa?auto=format&fit=crop&w=600&h=750&q=85',
    os.path.join(REAL_DIR, 'prod_watch.jpg'): 'https://images.unsplash.com/photo-1524805444758-089113d48a6d?auto=format&fit=crop&w=600&h=750&q=85',
    os.path.join(REAL_DIR, 'prod_denim_jacket.jpg'): 'https://images.unsplash.com/photo-1576995853123-5a10305d93c0?auto=format&fit=crop&w=600&h=750&q=85',
    os.path.join(REAL_DIR, 'prod_sneakers.jpg'): 'https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?auto=format&fit=crop&w=600&h=750&q=85',

    # Home & Kitchen Products
    os.path.join(REAL_DIR, 'prod_sofa.jpg'): 'https://images.unsplash.com/photo-1555041469-a586c61ea9bc?auto=format&fit=crop&w=600&h=750&q=85',
    os.path.join(REAL_DIR, 'prod_floor_lamp.jpg'): 'https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=600&h=750&q=85',
    os.path.join(REAL_DIR, 'prod_kettle.jpg'): 'https://images.unsplash.com/photo-1588854337236-6889d631faa8?auto=format&fit=crop&w=600&h=750&q=85',
    os.path.join(REAL_DIR, 'prod_bookshelf.jpg'): 'https://images.unsplash.com/photo-1594980596870-8aa52a78d8cd?auto=format&fit=crop&w=600&h=750&q=85',
    os.path.join(REAL_DIR, 'prod_table_lamp.jpg'): 'https://images.unsplash.com/photo-1513506003901-1e6a229e2d15?auto=format&fit=crop&w=600&h=750&q=85',

    # Beauty & Personal Care Products
    os.path.join(REAL_DIR, 'prod_perfume.jpg'): 'https://images.unsplash.com/photo-1541643600914-78b084683601?auto=format&fit=crop&w=600&h=750&q=85',
    os.path.join(REAL_DIR, 'prod_lipstick.jpg'): 'https://images.unsplash.com/photo-1586495777744-4413f21062fa?auto=format&fit=crop&w=600&h=750&q=85',
    os.path.join(REAL_DIR, 'prod_cologne.jpg'): 'https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?auto=format&fit=crop&w=600&h=750&q=85',
    os.path.join(REAL_DIR, 'prod_lip_care.jpg'): 'https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?auto=format&fit=crop&w=600&h=750&q=85',

    # Sports & Fitness Products
    os.path.join(REAL_DIR, 'prod_dumbbells.jpg'): 'https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?auto=format&fit=crop&w=600&h=750&q=85',
    os.path.join(REAL_DIR, 'prod_football.jpg'): 'https://images.unsplash.com/photo-1614632537190-23e4146777db?auto=format&fit=crop&w=600&h=750&q=85',
    os.path.join(REAL_DIR, 'prod_resistance_bands.jpg'): 'https://images.unsplash.com/photo-1598289431512-b97b0917affc?auto=format&fit=crop&w=600&h=750&q=85',
    os.path.join(REAL_DIR, 'prod_basketball.jpg'): 'https://images.unsplash.com/photo-1546519638-68e109498ffc?auto=format&fit=crop&w=600&h=750&q=85',

    # Books Products
    os.path.join(REAL_DIR, 'prod_fiction_book.jpg'): 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=600&h=750&q=85',
    os.path.join(REAL_DIR, 'prod_focus_book.jpg'): 'https://images.unsplash.com/photo-1589829085413-56de8ae18c73?auto=format&fit=crop&w=600&h=750&q=85',
    os.path.join(REAL_DIR, 'prod_fantasy_book.jpg'): 'https://images.unsplash.com/photo-1516979187457-637abb4f9353?auto=format&fit=crop&w=600&h=750&q=85',

    # Grocery Products
    os.path.join(REAL_DIR, 'prod_rice.jpg'): 'https://images.unsplash.com/photo-1586201375761-83865001e31c?auto=format&fit=crop&w=600&h=750&q=85',
    os.path.join(REAL_DIR, 'prod_tea.jpg'): 'https://images.unsplash.com/photo-1576092768241-dec231879fc3?auto=format&fit=crop&w=600&h=750&q=85',

    # Toys & Games Products
    os.path.join(REAL_DIR, 'prod_teddy_bear.jpg'): 'https://images.unsplash.com/photo-1559454403-b8fb88521f11?auto=format&fit=crop&w=600&h=750&q=85',
    os.path.join(REAL_DIR, 'prod_puzzle.jpg'): 'https://images.unsplash.com/photo-1587654780291-39c9404d746b?auto=format&fit=crop&w=600&h=750&q=85',
    os.path.join(REAL_DIR, 'prod_play_balls.jpg'): 'https://images.unsplash.com/photo-1596461404969-9ae70f2830c1?auto=format&fit=crop&w=600&h=750&q=85',
}

def main():
    print(f"Downloading {len(IMAGES)} authentic product & category images...")
    count = 0
    for file_path, url in IMAGES.items():
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = resp.read()
                with open(file_path, 'wb') as f:
                    f.write(data)
                count += 1
                print(f"[{count}/{len(IMAGES)}] Downloaded: {os.path.basename(file_path)} ({len(data)//1024} KB)")
        except Exception as e:
            print(f"Error downloading {file_path}: {e}")

    print(f"\nSuccessfully downloaded {count}/{len(IMAGES)} images!")

if __name__ == '__main__':
    main()
