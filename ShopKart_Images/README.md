# ShopKart Image Assets

## Assets Overview

- **categories/** - 8 high-resolution (1000x1000) PNG images, one per category, matching categories configured in the Django admin (e.g. `Electronics.png`).
- **products/** - 33 high-resolution PNG images, one per seeded product, named `Category__ProductName.png` for quick reference.

These images are the gradient and icon studio placeholders used across the storefront, provided as PNG files for review or external presentation.

## How to Apply Them

1. Open `/admin` on your running instance.
2. Select a Category or Product.
3. In the image field, select "Choose File" and upload the corresponding PNG from this directory.
4. Save the record.

## Using Custom Product Photography

These graphics serve as visual placeholders. To use real photography, standard sources with free licenses include:

- Unsplash: https://unsplash.com
- Pexels: https://www.pexels.com
- Pixabay: https://pixabay.com

Recommended dimensions:
- Products: portrait aspect ratio (approximately 4:5) with neutral backgrounds.
- Categories: square aspect ratio (1:1).
