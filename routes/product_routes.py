from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from extensions import db
from models import Product, Order, OrderItem ,Category

product_bp = Blueprint('product', __name__)

# ---------- helpers ----------
def _get_cart():
    return session.get("cart", {})

def _save_cart(cart: dict):
    session["cart"] = cart
    session.modified = True

def _cart_items_and_total(cart: dict):
    items = []
    total = 0.0
    for pid_str, qty in cart.items():
        product = Product.query.get(int(pid_str))
        if not product:
            continue
        qty = int(qty)
        line_total = product.price * qty
        items.append({"product": product, "qty": qty, "line_total": line_total})
        total += line_total
    return items, total

def _get_recently_viewed():
    return session.get('recently_viewed', [])

def _save_recently_viewed(product_id):
    recently_viewed = session.get('recently_viewed', [])
    if product_id in recently_viewed:
        recently_viewed.remove(product_id)
    recently_viewed.insert(0, product_id)
    recently_viewed = recently_viewed[:5]  # Keep max 5 items
    session['recently_viewed'] = recently_viewed
    session.modified = True

# ---------- public pages ----------

@product_bp.route('/')
def home():
    categories = Category.query.with_entities(Category.name).distinct().all()
    subcategories = Category.query.with_entities(Category.subcategory).distinct().all()

    q = request.args.get('q')
    category_filter = request.args.get('category')
    subcategory_filter = request.args.get('subcategory')

    products = Product.query

    if q:
        products = products.filter(Product.name.ilike(f'%{q}%'))
    if category_filter:
        products = products.join(Category).filter(Category.name == category_filter)
    if subcategory_filter:
        products = products.join(Category).filter(Category.subcategory == subcategory_filter)

    products = products.all()

    return render_template(
        'home.html',
        products=products,
        categories=categories,
        subcategories=subcategories
    )


@product_bp.route("/product/<int:product_id>")
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    _save_recently_viewed(product_id)
    stock_status = "In Stock" if product.stock > 0 else "Out of Stock"
    return render_template("product_detail.html", product=product, stock_status=stock_status)

@product_bp.route("/cart")
def view_cart():
    cart = _get_cart()
    items, total = _cart_items_and_total(cart)
    return render_template("cart.html", items=items, total=total)

@product_bp.route('/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    qty_requested = int(request.form.get('qty', 1))

    if product.stock < qty_requested:
        flash(f"Only {product.stock} units available for {product.name}.", "error")
        return redirect(url_for('product.product_detail', product_id=product_id))

    cart = _get_cart()
    cart[str(product_id)] = cart.get(str(product_id), 0) + qty_requested
    _save_cart(cart)

    flash("Product added to cart!", "success")
    return redirect(url_for('product.view_cart'))

@product_bp.route("/cart/update", methods=["POST"])
def update_cart():
    cart = _get_cart()
    for key, val in request.form.items():
        if key.startswith("qty_"):
            pid = key.split("_", 1)[1]
            try:
                qty = int(val)
            except ValueError:
                qty = 1
            if qty <= 0:
                cart.pop(pid, None)
            else:
                cart[pid] = qty
    _save_cart(cart)
    flash("Cart updated.", "success")
    return redirect(url_for("product.view_cart"))

@product_bp.route("/cart/remove/<int:product_id>", methods=["POST"])
def remove_from_cart(product_id):
    cart = _get_cart()
    cart.pop(str(product_id), None)
    _save_cart(cart)
    flash("Item removed.", "info")
    return redirect(url_for("product.view_cart"))

@product_bp.route("/cart/clear", methods=["POST"])
def clear_cart():
    session.pop("cart", None)
    flash("Cart cleared.", "info")
    return redirect(url_for("product.home"))

@product_bp.route("/cart/checkout", methods=["POST"])
@login_required
def checkout():
    cart = _get_cart()
    items, total = _cart_items_and_total(cart)

    if not items:
        flash("Your cart is empty.", "info")
        return redirect(url_for("product.view_cart"))

    for it in items:
        if it["product"].stock < it["qty"]:
            flash(f"Not enough stock for {it['product'].name}", "error")
            return redirect(url_for("product.view_cart"))

    order = Order(user_id=current_user.id, total_amount=total, status="PLACED")
    db.session.add(order)
    db.session.flush()

    for it in items:
        p = it["product"]
        qty = it["qty"]
        db.session.add(OrderItem(
            order_id=order.id,
            product_id=p.id,
            quantity=qty,
            unit_price=p.price
        ))
        p.stock -= qty

    db.session.commit()
    session.pop("cart", None)
    flash(f"Order #{order.id} placed!", "success")
    return redirect(url_for("product.my_order_detail", order_id=order.id))

@product_bp.route("/my/orders")
@login_required
def my_orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.id.desc()).all()
    return render_template("my_orders.html", orders=orders)

@product_bp.route("/my/orders/<int:order_id>")
@login_required
def my_order_detail(order_id):
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    return render_template("order_detail.html", order=order)

@product_bp.route("/about")
def about():
    return render_template("about.html")

@product_bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")
        # Save contact message to database or send email logic here
        flash("Thank you for contacting us! We'll get back to you soon.", "success")
        return redirect(url_for("product.contact"))
    return render_template("contact.html")

@product_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    # Prevent admin from accessing profile page
    if current_user.is_admin:
        flash("Admin does not have a profile page.", "error")
        return redirect(url_for("product.home"))

    # Update profile on POST
    if request.method == "POST":
        current_user.username = request.form.get("username") or current_user.username
        current_user.email = request.form.get("email") or current_user.email
        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("product.profile"))

    # GET: Show profile and order history
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.id.desc()).all()
    return render_template('profile.html', user=current_user, orders=orders)


