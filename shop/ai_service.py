import os
import json
from pathlib import Path
from dotenv import load_dotenv
try:
    from google import genai
except ImportError:
    genai = None
from .models import Product, Category, Coupon, Order

# Load .env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


def get_store_context(product_id=None):
    """
    Build a concise, live context snapshot of ShopKart products,
    categories, and active coupons to ground the AI's responses.
    """
    context_lines = [
        "You are the official AI Shopping & Product Assistant for 'ShopKart', a premier modern e-commerce store.",
        "Assist customers kindly, accurately, and concisely. When recommending products, prioritize items available in ShopKart.",
        "Currency: Indian Rupees (₹).",
        "Current Store Offers & Coupons:"
    ]

    # Active coupons
    coupons = Coupon.objects.filter(active=True)[:5]
    for c in coupons:
        cap_str = f" up to ₹{c.max_discount}" if c.max_discount else ""
        context_lines.append(f"- Code '{c.code}': {c.description} (Min order: ₹{c.min_order_amount}{cap_str})")

    # If asking about a specific product
    if product_id:
        try:
            p = Product.objects.get(pk=product_id)
            context_lines.append(f"\nCurrently viewing product: '{p.name}'")
            context_lines.append(f"- Brand: {p.brand}, Category: {p.category.name if p.category else 'General'}")
            context_lines.append(f"- Price: ₹{p.selling_price} (Original: ₹{p.original_price}, Discount: {p.discount_percent}%)")
            context_lines.append(f"- Stock: {'In Stock (' + str(p.quantity) + ' available)' if p.in_stock else 'Out of Stock'}")
            if p.highlights:
                context_lines.append(f"- Highlights: {p.highlights}")
            if p.description:
                context_lines.append(f"- Description: {p.description[:400]}")
            colors = p.colors.all()
            if colors.exists():
                c_names = ", ".join([f"{c.name} (₹{c.effective_price})" for c in colors])
                context_lines.append(f"- Available Colors/Variants: {c_names}")
        except Product.DoesNotExist:
            pass

    # Top popular products
    popular = Product.objects.filter(status=False).order_by('-trending', '-featured', '-quantity')[:10]
    context_lines.append("\nFeatured ShopKart Products:")
    for prod in popular:
        stock = "In Stock" if prod.in_stock else "Out of Stock"
        context_lines.append(f"- {prod.name} | ₹{prod.selling_price} ({stock}) | Brand: {prod.brand}")

    return "\n".join(context_lines)


def get_admin_context():
    """
    Context for Executive Admin AI Insights (revenue, stock, top sellers).
    """
    from django.db.models import Sum
    total_rev = Order.objects.exclude(status='cancelled').aggregate(Sum('total_amount'))['total_amount__sum'] or 0.0
    total_orders = Order.objects.count()
    low_stock = Product.objects.filter(quantity__lte=5, status=False).count()
    out_of_stock = Product.objects.filter(quantity=0, status=False).count()
    
    return (
        f"You are the executive e-commerce analytics copilot for ShopKart.\n"
        f"Store Metrics Snapshot:\n"
        f"- Total Net Revenue: ₹{int(total_rev):,}\n"
        f"- Total Orders Placed: {total_orders}\n"
        f"- Low Stock SKUs: {low_stock}\n"
        f"- Out of Stock SKUs: {out_of_stock}\n"
        f"Provide strategic, data-driven advice on revenue, promotions, and inventory reordering."
    )


def query_gemini_ai(user_prompt, context_type="shopping", product_id=None):
    """
    Executes a query to Google AI Studio Gemini API.
    Supports both client.interactions.create (per Google AI Studio App spec)
    and client.models.generate_content fallback.
    """
    load_dotenv(BASE_DIR / '.env', override=True)
    if genai is None:
        return {
            "success": False,
            "error": "The google-genai library is not installed in the active Python environment. Run 'pip install google-genai' or activate .venv.",
            "response": None,
        }
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {
            "success": False,
            "error": "GEMINI_API_KEY is not configured. Please add your Google Gemini API Key to the .env file.",
            "response": None,
        }

    # Prepare grounding context
    if context_type == "admin":
        system_context = get_admin_context()
    else:
        system_context = get_store_context(product_id=product_id)

    full_input = f"{system_context}\n\nCustomer / User Question: {user_prompt}\n\nAssistant Response:"

    client = genai.Client(api_key=api_key)
    model_name = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
    if not model_name or "2.5" in model_name:
        model_name = "gemini-3.8-flash"

    # Attempt 1: Standard Generate Content with Google Search Grounding
    try:
        clean_model = model_name.replace("models/", "")
        resp = client.models.generate_content(
            model=clean_model,
            contents=full_input,
            config={
                'tools': [{'google_search': {}}]
            }
        )
        if resp.text:
            return {
                "success": True,
                "response": resp.text.strip(),
                "model_used": clean_model,
                "method": "models.generate_content"
            }
    except Exception as exc1:
        pass

    # Attempt 2: Using client.interactions.create (per Google AI Studio App spec)
    try:
        interaction = client.interactions.create(
            model=model_name,
            input=full_input,
            tools=[{'type': 'google_search'}],
            generation_config={
                'max_output_tokens': 4096,
                'thinking_level': 'high',
            },
        )
        output_step = interaction.steps[-1] if interaction.steps else None
        
        result_text = ""
        if hasattr(output_step, 'content'):
            result_text = str(output_step.content)
        elif hasattr(output_step, 'text'):
            result_text = str(output_step.text)
        elif isinstance(output_step, dict):
            result_text = output_step.get('content') or output_step.get('text') or str(output_step)
        else:
            result_text = str(output_step)

        if result_text:
            return {
                "success": True,
                "response": result_text.strip(),
                "model_used": model_name,
                "method": "interactions"
            }
    except Exception as exc2:
        pass

    # Attempt 3: Direct fallback without tools if network/grounding blocked
    try:
        clean_model = model_name.replace("models/", "")
        resp = client.models.generate_content(
            model=clean_model,
            contents=full_input,
        )
        return {
            "success": True,
            "response": resp.text.strip() if resp.text else "Response received.",
            "model_used": clean_model,
            "method": "models.generate_content_direct"
        }
    except Exception as exc3:
        return {
            "success": False,
            "error": f"Gemini API Error: {str(exc3)}",
            "response": None
        }

