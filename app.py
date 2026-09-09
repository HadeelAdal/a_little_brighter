import os
import re
import secrets

from flask import (
    Flask,
    render_template,
    session,
    redirect,
    url_for,
    request,
    flash,
)


app = Flask(__name__)

# NEVER hard-code your production secret key.
# Set it as an environment variable instead:
# Windows PowerShell:
#   $env:FLASK_SECRET_KEY="your-long-random-secret"
#
# For local development, the fallback below is acceptable,
# but change it before deploying.
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "development-only-change-this-secret-key"
)


# ============================================================
# PRODUCTS
# ============================================================

PRODUCTS = [
    {
        "id": 1,
        "name": "Sunlit Thoughts",
        "category": "Prints",
        "price": 25.00,
        "description": (
            "A soft, hopeful art print designed to bring "
            "a little warmth to your space."
        ),
        "image": (
            "https://images.unsplash.com/"
            "photo-1549490349-8643362247b5"
            "?auto=format&fit=crop&w=900&q=85"
        ),
    },
    {
        "id": 2,
        "name": "Bloom",
        "category": "Prints",
        "price": 28.00,
        "description": (
            "A colorful reminder that growth can happen slowly "
            "and still be beautiful."
        ),
        "image": (
            "https://images.unsplash.com/"
            "photo-1577083552431-6e5fd01988a5"
            "?auto=format&fit=crop&w=900&q=85"
        ),
    },
    {
        "id": 3,
        "name": "A Little Brighter Tote",
        "category": "Tote Bags",
        "price": 18.00,
        "description": (
            "A reusable tote featuring an original "
            "A Little Brighter illustration."
        ),
        "image": (
            "https://images.unsplash.com/"
            "photo-1597484662317-9bd7bdda7781"
            "?auto=format&fit=crop&w=900&q=85"
        ),
    },
    {
        "id": 4,
        "name": "Good Things Mug",
        "category": "Mugs",
        "price": 16.00,
        "description": (
            "A cheerful everyday mug with a small reminder "
            "to keep going."
        ),
        "image": (
            "https://images.unsplash.com/"
            "photo-1514228742587-6b1558fcf93a"
            "?auto=format&fit=crop&w=900&q=85"
        ),
    },
    {
        "id": 5,
        "name": "Little Thoughts Notebook",
        "category": "Notebooks",
        "price": 14.00,
        "description": (
            "A simple notebook for thoughts, sketches, lists "
            "and everything in between."
        ),
        "image": (
            "https://images.unsplash.com/"
            "photo-1517842645767-c639042777db"
            "?auto=format&fit=crop&w=900&q=85"
        ),
    },
    {
        "id": 6,
        "name": "Hope in Color",
        "category": "Prints",
        "price": 30.00,
        "description": (
            "A bright illustrated print created around the idea "
            "that difficult days can change."
        ),
        "image": (
            "https://images.unsplash.com/"
            "photo-1579783902614-a3fb3927b6a5"
            "?auto=format&fit=crop&w=900&q=85"
        ),
    },
]


# ============================================================
# PRODUCTS
# ============================================================

def get_product(product_id):
    """Return a product by ID, or None if it doesn't exist."""

    return next(
        (
            product
            for product in PRODUCTS
            if product["id"] == product_id
        ),
        None,
    )


# ============================================================
# CART
# ============================================================

def cart_items():
    """
    Build the cart from the session.

    Invalid products and invalid quantities are ignored.
    """

    cart = session.get("cart", {})

    items = []
    total = 0.0

    for product_id, quantity in cart.items():

        try:
            product_id = int(product_id)
            quantity = int(quantity)
        except (ValueError, TypeError):
            continue

        # Never allow invalid quantities.
        if quantity <= 0:
            continue

        product = get_product(product_id)

        if not product:
            continue

        subtotal = round(
            product["price"] * quantity,
            2,
        )

        items.append(
            {
                **product,
                "quantity": quantity,
                "subtotal": subtotal,
            }
        )

        total += subtotal

    return items, round(total, 2)


@app.context_processor
def inject_cart():
    items, total = cart_items()

    return {
        "cart_count": sum(
            item["quantity"]
            for item in items
        ),
        "cart_total": total,
    }


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return render_template(
        "index.html",
        products=PRODUCTS[:4],
    )


# ============================================================
# SHOP
# ============================================================

@app.route("/shop")
def shop():

    category = request.args.get(
        "category",
        "All",
    )

    categories = [
        "All",
        "Prints",
        "Tote Bags",
        "Mugs",
        "Notebooks",
    ]

    if category == "All":

        products = PRODUCTS

    else:

        products = [
            product
            for product in PRODUCTS
            if product["category"] == category
        ]

    return render_template(
        "shop.html",
        products=products,
        categories=categories,
        active_category=category,
    )


# ============================================================
# PRODUCT
# ============================================================

@app.route("/product/<int:product_id>")
def product(product_id):

    item = get_product(product_id)

    if not item:
        return "Product not found", 404

    return render_template(
        "product.html",
        product=item,
    )


# ============================================================
# ADD TO CART
# ============================================================

@app.post("/add-to-cart/<int:product_id>")
def add_to_cart(product_id):

    if not get_product(product_id):
        return "Product not found", 404

    cart = session.get("cart", {})

    key = str(product_id)

    try:
        current_quantity = int(
            cart.get(key, 0)
        )
    except (ValueError, TypeError):
        current_quantity = 0

    # Maximum quantity per product.
    # This prevents someone from accidentally
    # creating a huge cart.
    new_quantity = min(
        current_quantity + 1,
        99,
    )

    cart[key] = new_quantity

    session["cart"] = cart
    session.modified = True

    flash("Added to your cart.")

    return redirect(
        request.referrer
        or url_for("shop")
    )


# ============================================================
# CART
# ============================================================

@app.route("/cart")
def cart():

    items, total = cart_items()

    return render_template(
        "cart.html",
        items=items,
        total=total,
    )


@app.post("/cart/update")
def update_cart():

    cart = session.get("cart", {})

    for key, value in request.form.items():

        if not key.startswith("qty_"):
            continue

        product_id = key.replace(
            "qty_",
            "",
            1,
        )

        # Make sure the product actually exists.
        try:
            product = get_product(
                int(product_id)
            )
        except ValueError:
            product = None

        if not product:
            cart.pop(product_id, None)
            continue

        try:
            quantity = int(value)
        except (ValueError, TypeError):
            quantity = 1

        # Allow 0 to remove an item.
        quantity = max(
            0,
            min(quantity, 99),
        )

        if quantity == 0:
            cart.pop(
                product_id,
                None,
            )
        else:
            cart[product_id] = quantity

    session["cart"] = cart
    session.modified = True

    flash("Your cart has been updated.")

    return redirect(
        url_for("cart")
    )


# ============================================================
# CHECKOUT
# ============================================================

@app.route("/checkout")
def checkout():

    items, total = cart_items()

    if not items:

        flash("Your cart is empty.")

        return redirect(
            url_for("cart")
        )

    return render_template(
        "checkout.html",
        items=items,
        total=total,
    )


# ============================================================
# VALIDATION HELPERS
# ============================================================

def valid_email(email):
    """
    Basic email validation.

    This is not intended to replace email verification.
    """

    return bool(
        re.match(
            r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
            email,
        )
    )


# ============================================================
# PLACE ORDER
# ============================================================

@app.post("/place-order")
def place_order():

    # --------------------------------------------------------
    # CUSTOMER INFORMATION
    # --------------------------------------------------------

    first_name = request.form.get(
        "first_name",
        "",
    ).strip()

    last_name = request.form.get(
        "last_name",
        "",
    ).strip()

    phone = request.form.get(
        "phone",
        "",
    ).strip()

    email = request.form.get(
        "email",
        "",
    ).strip()

    address = request.form.get(
        "address",
        "",
    ).strip()

    city = request.form.get(
        "city",
        "",
    ).strip()

    country = request.form.get(
        "country",
        "",
    ).strip()

    notes = request.form.get(
        "notes",
        "",
    ).strip()

    payment_method = request.form.get(
        "payment_method",
        "",
    ).strip()


    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not first_name or not last_name:

        flash("Please enter your name.")

        return redirect(
            url_for("checkout")
        )


    if not phone:

        flash("Please enter your phone number.")

        return redirect(
            url_for("checkout")
        )


    if not email or not valid_email(email):

        flash("Please enter a valid email address.")

        return redirect(
            url_for("checkout")
        )


    if not address or not city:

        flash(
            "Please enter your delivery address."
        )

        return redirect(
            url_for("checkout")
        )


    allowed_payment_methods = {
        "cod",
        "card",
        "whish",
    }

    if payment_method not in allowed_payment_methods:

        flash(
            "Please select a payment method."
        )

        return redirect(
            url_for("checkout")
        )


    # --------------------------------------------------------
    # GET CART
    # --------------------------------------------------------

    items, total = cart_items()

    if not items:

        flash("Your cart is empty.")

        return redirect(
            url_for("cart")
        )


    # --------------------------------------------------------
    # CREATE ORDER
    # --------------------------------------------------------

    order_number = (
        "ALB-"
        + secrets.token_hex(4).upper()
    )


    if payment_method == "cod":

        payment_name = "Cash on Delivery"

        payment_status = "pending"


    elif payment_method == "card":

        payment_name = "Card"

        # IMPORTANT:
        # The order is NOT paid yet.
        payment_status = "pending"


    else:

        payment_name = "Whish Money"

        payment_status = "pending"


    order = {
        "order_number": order_number,

        "first_name": first_name,
        "last_name": last_name,

        "phone": phone,
        "email": email,

        "address": address,
        "city": city,
        "country": country,

        "notes": notes,

        "payment_method": payment_name,
        "payment_status": payment_status,

        "items": items,
        "total": total,
    }


    # --------------------------------------------------------
    # TEMPORARY STORAGE
    # --------------------------------------------------------
    #
    # This is okay for testing.
    #
    # For production we should move orders to a database.
    #

    session["last_order"] = order


    # --------------------------------------------------------
    # CASH ON DELIVERY
    # --------------------------------------------------------

    if payment_method == "cod":

        session.pop(
            "cart",
            None,
        )

        return render_template(
            "order_success.html",
            order=order,
        )


    # --------------------------------------------------------
    # CARD PAYMENT
    # --------------------------------------------------------

    if payment_method == "card":

        try:

            payment_url = create_card_payment(
                order
            )

        except PaymentConfigurationError:

            flash(
                "Card payments are not available yet. "
                "Please choose another payment method."
            )

            return redirect(
                url_for("checkout")
            )

        return redirect(
            payment_url
        )


    # --------------------------------------------------------
    # WHISH
    # --------------------------------------------------------

    if payment_method == "whish":

        return render_template(
            "payment_pending.html",
            order=order,
        )

    # This should never be reached.
    flash("Unable to process your order.")

    return redirect(
        url_for("checkout")
    )


# ============================================================
# CARD PAYMENT
# ============================================================

class PaymentConfigurationError(Exception):
    """
    Raised when the payment gateway has not been configured.
    """
    pass


def create_card_payment(order):
    """
    Create a payment with the card payment provider.

    IMPORTANT:
    This function intentionally does NOT contain fake API
    calls or invented NetCommerce endpoints.

    NetCommerce provides Hosted Checkout and API integrations,
    but your merchant account needs to be approved and you
    need the actual integration credentials/documentation
    supplied for your account.

    Once you receive those credentials, this is the function
    we will implement.
    """

    raise PaymentConfigurationError(
        "Card payment gateway is not configured."
    )


# ============================================================
# PAYMENT RETURN
# ============================================================

@app.route("/payment/success")
def payment_success():

    """
    The payment provider should redirect the customer here
    after payment.

    DO NOT mark the order as paid merely because this URL
    was visited.

    The transaction must first be verified with the payment
    provider.
    """

    order = session.get("last_order")

    if not order:

        flash(
            "We couldn't find your order."
        )

        return redirect(
            url_for("shop")
        )


    # --------------------------------------------------------
    # TODO:
    #
    # 1. Get the transaction/reference from the gateway.
    # 2. Send it to the gateway's verification API.
    # 3. Confirm:
    #
    #       amount
    #       currency
    #       order number
    #       transaction status
    #
    # 4. ONLY THEN set:
    #
    #       order["payment_status"] = "paid"
    #
    # 5. Save the order to the database.
    # 6. Clear the cart.
    #
    # --------------------------------------------------------

    flash(
        "Payment verification is not configured yet."
    )

    return render_template(
        "payment_pending.html",
        order=order,
    )


# ============================================================
# PAYMENT CANCELLED
# ============================================================

@app.route("/payment/cancelled")
def payment_cancelled():

    order = session.get("last_order")

    if not order:

        return redirect(
            url_for("cart")
        )

    return render_template(
        "payment_cancelled.html",
        order=order,
    )


# ============================================================
# OTHER PAGES
# ============================================================

@app.route("/mission")
def mission():

    return render_template(
        "mission.html"
    )


@app.route("/impact")
def impact():

    return render_template(
        "impact.html"
    )


@app.route("/contact")
def contact():

    return render_template(
        "contact.html"
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )