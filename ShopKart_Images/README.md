# ShopKart Image Assets

## What's in here

- **categories/** — 8 high-res (1000x1000) PNG images, one per category, named to
  match exactly what's in your Django admin (e.g. `Electronics.png`).
- **products/** — 33 high-res PNG images, one per seeded product, named
  `Category__ProductName.png` so you can find the right one quickly.

These are the same premium gradient/icon "studio placeholder" images already used in
the site — exported here as plain PNG files so you can review them outside the browser,
or reuse the style elsewhere (e.g. presentation slides, a project report).

## How to use them

1. Go to `/admin` on your running site.
2. Open a Category or Product.
3. Under the image field, click "Choose File" and pick the matching PNG from this
   folder.
4. Save.

(Same steps as before — this folder just makes it easier to browse and pick the right
file per product instead of digging through the raw SVGs.)

## Want real product photos instead?

These are illustrative placeholders, not real photography. If you'd rather use actual
photos of real products, free, no-attribution-required sources include:

- https://unsplash.com — search the product name (e.g. "wireless headphones")
- https://www.pexels.com
- https://pixabay.com

Download whatever fits, then upload it through the admin the same way. Aim for:
- **Products** → portrait-ish (4:5) images, plain/light background
- **Categories** → square images

If you have access to an AI image generator (e.g. Midjourney, DALL-E, Bing Image
Creator), you can also prompt for photorealistic product shots — try something like:
"{product name}, studio product photography, white background, soft shadow, 4:5
aspect ratio" — and upload those instead.
