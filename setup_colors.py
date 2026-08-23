import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ms_project.settings')
django.setup()

from PIL import Image, ImageEnhance, ImageOps
from django.conf import settings
from shop.models import Product, ProductColor, ProductColorImage

UPLOADS_DIR = os.path.join(settings.BASE_DIR, 'static', 'uploads')
os.makedirs(UPLOADS_DIR, exist_ok=True)

def generate_color_variant_image(src_filename, out_filename, target_hue, saturation_factor=1.0, brightness_factor=1.0):
    src_path = os.path.join(UPLOADS_DIR, src_filename)
    if not os.path.exists(src_path):
        print(f"Source not found: {src_path}")
        return None
    
    img = Image.open(src_path).convert('RGBA')
    # Convert to HSV to shift hue of non-white / non-black phone body
    r, g, b, a = img.split()
    rgb = Image.merge('RGB', (r, g, b))
    hsv = rgb.convert('HSV')
    h, s, v = hsv.split()
    
    # Process hue: mask areas that are colored (not pure white background, not pure black screen)
    h_data = list(h.getdata())
    s_data = list(s.getdata())
    v_data = list(v.getdata())
    
    new_h = []
    new_s = []
    new_v = []
    
    for hi, si, vi in zip(h_data, s_data, v_data):
        # If it's near-white background (vi > 248 and si < 15), keep as is
        if vi > 248 and si < 15:
            new_h.append(hi)
            new_s.append(si)
            new_v.append(vi)
        # If it's pure black screen / lens (vi < 35), keep as is
        elif vi < 35:
            new_h.append(hi)
            new_s.append(si)
            new_v.append(vi)
        else:
            # Color area: shift hue
            new_h.append(target_hue)
            new_s.append(int(min(255, max(0, si * saturation_factor))))
            new_v.append(int(min(255, max(0, vi * brightness_factor))))
            
    h.putdata(new_h)
    s.putdata(new_s)
    v.putdata(new_v)
    
    res_rgb = Image.merge('HSV', (h, s, v)).convert('RGB')
    res_img = Image.merge('RGBA', (res_rgb.split()[0], res_rgb.split()[1], res_rgb.split()[2], a)).convert('RGB')
    
    out_path = os.path.join(UPLOADS_DIR, out_filename)
    res_img.save(out_path, quality=95)
    print(f"Saved variant image: {out_filename}")
    return f"uploads/{out_filename}"

def setup_iphone_colors():
    iphone = Product.objects.filter(slug__icontains='iphone').first() or Product.objects.filter(name__icontains='iPhone').first()
    if not iphone:
        print("iPhone product not found!")
        return

    print(f"Configuring colors for: {iphone.name} (ID: {iphone.id})")
    
    # Clear existing colors to rebuild cleanly
    iphone.colors.all().delete()
    
    # 1. Lavender (Primary / Default)
    lavender_main = 'uploads/20260817215845_17.jpg' if os.path.exists(os.path.join(settings.BASE_DIR, 'static', 'uploads', '20260817215845_17.jpg')) else iphone.product_image.name
    c_lavender = ProductColor.objects.create(
        product=iphone,
        name="Lavender",
        color_code="#D8B4E2",
        image=lavender_main,
        price=79999,
        original_price=89999,
        quantity=15,
        is_default=True
    )
    for g_file in ['20260817215251_7.jpg', '20260817215409_11.jpg', '20260816114208_prod_phone_camera.jpg', '20260816114208_prod_phone_back.jpg']:
        full_p = os.path.join(settings.BASE_DIR, 'static', 'uploads', g_file)
        if os.path.exists(full_p):
            ProductColorImage.objects.create(color=c_lavender, image=f"uploads/{g_file}")

    # 2. Space Black
    black_main = generate_color_variant_image('20260817215845_17.jpg', 'iphone_17_black.jpg', target_hue=0, saturation_factor=0.05, brightness_factor=0.45)
    c_black = ProductColor.objects.create(
        product=iphone,
        name="Space Black",
        color_code="#1E2024",
        image=black_main or 'uploads/20260817215251_2.jpg',
        price=79999,
        original_price=89999,
        quantity=20,
        is_default=False
    )
    # Side angles for black
    black_angle = generate_color_variant_image('20260817215251_7.jpg', 'iphone_17_black_front.jpg', target_hue=0, saturation_factor=0.05, brightness_factor=0.45)
    black_side = generate_color_variant_image('20260817215409_11.jpg', 'iphone_17_black_side.jpg', target_hue=0, saturation_factor=0.05, brightness_factor=0.45)
    if os.path.exists(os.path.join(settings.BASE_DIR, 'static', 'uploads', '20260817215251_2.jpg')):
        ProductColorImage.objects.create(color=c_black, image='uploads/20260817215251_2.jpg')
    if black_angle:
        ProductColorImage.objects.create(color=c_black, image=black_angle)
    if black_side:
        ProductColorImage.objects.create(color=c_black, image=black_side)

    # 3. Ocean Blue
    blue_main = generate_color_variant_image('20260817215845_17.jpg', 'iphone_17_blue.jpg', target_hue=145, saturation_factor=0.9, brightness_factor=1.0)
    c_blue = ProductColor.objects.create(
        product=iphone,
        name="Ocean Blue",
        color_code="#7AA9C8",
        image=blue_main or iphone.product_image.name,
        price=79999,
        original_price=89999,
        quantity=12,
        is_default=False
    )
    blue_angle = generate_color_variant_image('20260817215251_7.jpg', 'iphone_17_blue_front.jpg', target_hue=145, saturation_factor=0.9, brightness_factor=1.0)
    blue_side = generate_color_variant_image('20260817215409_11.jpg', 'iphone_17_blue_side.jpg', target_hue=145, saturation_factor=0.9, brightness_factor=1.0)
    if blue_angle:
        ProductColorImage.objects.create(color=c_blue, image=blue_angle)
    if blue_side:
        ProductColorImage.objects.create(color=c_blue, image=blue_side)

    # 4. Starlight Silver
    silver_main = 'uploads/20260817215251_9.jpg' if os.path.exists(os.path.join(settings.BASE_DIR, 'static', 'uploads', '20260817215251_9.jpg')) else generate_color_variant_image('20260817215845_17.jpg', 'iphone_17_silver.jpg', target_hue=30, saturation_factor=0.08, brightness_factor=1.05)
    c_silver = ProductColor.objects.create(
        product=iphone,
        name="Starlight Silver",
        color_code="#E8E8E4",
        image=silver_main,
        price=79999,
        original_price=89999,
        quantity=18,
        is_default=False
    )
    silver_front = generate_color_variant_image('20260817215251_7.jpg', 'iphone_17_silver_front.jpg', target_hue=30, saturation_factor=0.08, brightness_factor=1.05)
    silver_side = generate_color_variant_image('20260817215409_11.jpg', 'iphone_17_silver_side.jpg', target_hue=30, saturation_factor=0.08, brightness_factor=1.05)
    if silver_front:
        ProductColorImage.objects.create(color=c_silver, image=silver_front)
    if silver_side:
        ProductColorImage.objects.create(color=c_silver, image=silver_side)

    # 5. Sage Green
    green_main = generate_color_variant_image('20260817215845_17.jpg', 'iphone_17_green.jpg', target_hue=75, saturation_factor=0.75, brightness_factor=0.98)
    c_green = ProductColor.objects.create(
        product=iphone,
        name="Sage Green",
        color_code="#8CA88E",
        image=green_main or iphone.product_image.name,
        price=79999,
        original_price=89999,
        quantity=10,
        is_default=False
    )
    green_angle = generate_color_variant_image('20260817215251_7.jpg', 'iphone_17_green_front.jpg', target_hue=75, saturation_factor=0.75, brightness_factor=0.98)
    green_side = generate_color_variant_image('20260817215409_11.jpg', 'iphone_17_green_side.jpg', target_hue=75, saturation_factor=0.75, brightness_factor=0.98)
    if green_angle:
        ProductColorImage.objects.create(color=c_green, image=green_angle)
    if green_side:
        ProductColorImage.objects.create(color=c_green, image=green_side)

    print(f"Successfully configured 5 color variants for iPhone 17!")

def setup_other_products():
    # T-shirt
    tshirt = Product.objects.filter(slug__icontains='tshirt').first() or Product.objects.filter(name__icontains='t-shirt').first()
    if tshirt and not tshirt.colors.exists():
        ProductColor.objects.create(product=tshirt, name="Pure White", color_code="#FFFFFF", image=tshirt.product_image, price=tshirt.selling_price, quantity=25, is_default=True)
        ProductColor.objects.create(product=tshirt, name="Midnight Black", color_code="#18181B", image=tshirt.product_image, price=tshirt.selling_price, quantity=20, is_default=False)
        ProductColor.objects.create(product=tshirt, name="Navy Blue", color_code="#1E3A8A", image=tshirt.product_image, price=tshirt.selling_price, quantity=15, is_default=False)
        print(f"Added colors to {tshirt.name}")

    # Shoes
    shoes = Product.objects.filter(slug__icontains='shoes').first() or Product.objects.filter(name__icontains='shoes').first()
    if shoes and not shoes.colors.exists():
        ProductColor.objects.create(product=shoes, name="Crimson Red", color_code="#DC2626", image=shoes.product_image, price=shoes.selling_price, quantity=15, is_default=True)
        ProductColor.objects.create(product=shoes, name="Stealth Black", color_code="#111827", image=shoes.product_image, price=shoes.selling_price, quantity=18, is_default=False)
        ProductColor.objects.create(product=shoes, name="Royal Blue", color_code="#2563EB", image=shoes.product_image, price=shoes.selling_price, quantity=10, is_default=False)
        print(f"Added colors to {shoes.name}")

    # Headphones
    headphones = Product.objects.filter(slug__icontains='headphones').first() or Product.objects.filter(name__icontains='headphones').first()
    if headphones and not headphones.colors.exists():
        ProductColor.objects.create(product=headphones, name="Matte Black", color_code="#18181B", image=headphones.product_image, price=headphones.selling_price, quantity=12, is_default=True)
        ProductColor.objects.create(product=headphones, name="Silver Platinum", color_code="#E2E8F0", image=headphones.product_image, price=headphones.selling_price, quantity=8, is_default=False)
        ProductColor.objects.create(product=headphones, name="Midnight Navy", color_code="#1E293B", image=headphones.product_image, price=headphones.selling_price, quantity=6, is_default=False)
        print(f"Added colors to {headphones.name}")

if __name__ == '__main__':
    setup_iphone_colors()
    setup_other_products()
