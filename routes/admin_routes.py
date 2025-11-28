from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from extensions import db
from models import Order, User, Product, Inquiry, Review, Category, OrderItem
from sqlalchemy import func
import os

admin_bp = Blueprint('admin', __name__)

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


# ---------------- Utility Functions ----------------
def ensure_admin():
    if not current_user.is_authenticated or not current_user.is_admin:
        abort(403)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------------- Admin Dashboard ----------------
@admin_bp.route('/admin')
@admin_bp.route('/admin_dashboard')
@login_required
def dashboard():
    ensure_admin()
    total_users = User.query.count()
    total_products = Product.query.count()
    total_orders = Order.query.count()
    total_inquiries = Inquiry.query.count() if 'Inquiry' in globals() else 0
    total_reviews = Review.query.count() if 'Review' in globals() else 0

    return render_template(
        'admin_dashboard.html',
        total_users=total_users,
        total_products=total_products,
        total_orders=total_orders,
        total_inquiries=total_inquiries,
        total_reviews=total_reviews
    )


# ---------------- Orders ----------------
@admin_bp.route('/admin_orders')
@login_required
def orders():
    ensure_admin()
    orders = Order.query.order_by(Order.id.desc()).all()
    return render_template('admin_orders.html', orders=orders)


@admin_bp.post("/admin_orders/<int:oid>/status")
@login_required
def update_order_status(oid):
    ensure_admin()
    o = Order.query.get_or_404(oid)
    new_status = request.form.get("status")
    allowed = {"PLACED", "PAID", "SHIPPED", "DELIVERED", "CANCELLED"}
    if new_status in allowed:
        o.status = new_status
        db.session.commit()
        flash("Order status updated!", "success")
    else:
        flash("Invalid status.", "error")
    return redirect(url_for("admin.orders"))


# ---------------- Products ----------------
@admin_bp.route('/admin/products')
@login_required
def products_list():
    ensure_admin()
    products = Product.query.order_by(Product.id.desc()).all()
    return render_template('product_list.html', products=products)


@admin_bp.route('/admin/products/new', methods=['GET', 'POST'])
@login_required
def product_create():
    ensure_admin()
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        stock = request.form.get('stock')
        description = request.form.get('description')
        file = request.files.get('image_file')
        filename = None
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(current_app.root_path, UPLOAD_FOLDER, filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            file.save(save_path)

        image_url = request.form.get('image') if not filename else None

        if not name or not price or not stock:
            flash('Name, price, and stock are required', 'danger')
            return redirect(url_for('admin.product_create'))

        p = Product(
            name=name.strip(),
            price=float(price),
            stock=int(stock),
            description=description or '',
            image=f"/{UPLOAD_FOLDER}/{filename}" if filename else (image_url or '')
        )
        db.session.add(p)
        db.session.commit()
        flash('Product created', 'success')
        return redirect(url_for('admin.products_list'))

    return render_template('product_form.html', mode='create', product=None)


@admin_bp.route('/admin/products/<int:pid>/edit', methods=['GET', 'POST'])
@login_required
def product_edit(pid):
    ensure_admin()
    product = Product.query.get_or_404(pid)
    if request.method == 'POST':
        product.name = request.form.get('name') or product.name
        product.price = float(request.form.get('price') or product.price)
        product.stock = int(request.form.get('stock') or product.stock)
        product.description = request.form.get('description') or ''

        file = request.files.get('image_file')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(current_app.root_path, UPLOAD_FOLDER, filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            file.save(save_path)
            product.image = f"/{UPLOAD_FOLDER}/{filename}"
        else:
            product.image = request.form.get('image') or product.image

        db.session.commit()
        flash('Product updated', 'success')
        return redirect(url_for('admin.products_list'))

    return render_template('product_form.html', mode='edit', product=product)


@admin_bp.route('/admin/products/<int:pid>/delete', methods=['POST'])
@login_required
def product_delete(pid):
    ensure_admin()
    product = Product.query.get_or_404(pid)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted', 'warning')
    return redirect(url_for('admin.products_list'))


# ---------------- Customers ----------------
@admin_bp.route('/admin/customers')
@login_required
def customers():
    ensure_admin()
    customers = User.query.all()
    return render_template('admin_customers.html', customers=customers)


# ---------------- Categories ----------------
from forms import CategoryForm

@admin_bp.route('/admin_categories/add', methods=['GET', 'POST'])
@login_required
def add_category():
    ensure_admin()
    form = CategoryForm()
    if form.validate_on_submit():
        new_cat = Category(name=form.name.data)
        db.session.add(new_cat)
        db.session.commit()
        flash('Category added successfully!', 'success')
        return redirect(url_for('admin.view_categories'))

    return render_template('add_category.html', form=form)


@admin_bp.route('/admin_categories')
@login_required
def view_categories():
    ensure_admin()
    categories = Category.query.all()
    return render_template('view_category.html', categories=categories)


@admin_bp.route('/admin_categories/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    ensure_admin()
    category = Category.query.get_or_404(category_id)

    if request.method == 'POST':
        category.name = request.form.get('name')
        db.session.commit()
        flash('Category updated successfully!', 'success')
        return redirect(url_for('admin.view_categories'))

    return render_template('edit_category.html', category=category)


@admin_bp.route('/admin_categories/delete/<int:category_id>', methods=['POST'])
@login_required
def delete_category(category_id):
    ensure_admin()
    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    flash('Category deleted successfully!', 'success')
    return redirect(url_for('admin.view_categories'))


# ---------------- Reports ----------------
@admin_bp.route("/admin_reports")
@login_required
def view_reports():
    ensure_admin()

    total_products = Product.query.count()
    total_users = User.query.count()
    total_orders = Order.query.count()
    total_revenue = db.session.query(func.sum(Order.total_amount)).scalar() or 0

    # Top selling products
    top_products = (
        db.session.query(
            Product.name,
            func.sum(OrderItem.quantity).label("quantity"),
            func.sum(OrderItem.quantity * Product.price).label("revenue")
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .group_by(Product.id)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(5)
        .all()
    )

    # Recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()

    # Sales trend (monthly)
    sales = (
        db.session.query(
            func.strftime("%m", Order.created_at).label("month"),
            func.sum(Order.total_amount).label("total")
        )
        .group_by("month")
        .all()
    )
    sales_labels = [s.month for s in sales]
    sales_data = [float(s.total) for s in sales]

    # Category distribution
    category_stats = (
        db.session.query(
            Category.name,
            func.count(Product.id)
        )
        .outerjoin(Product)
        .group_by(Category.id)
        .all()
    )
    category_labels = [c[0] for c in category_stats]
    category_data = [c[1] for c in category_stats]

    return render_template(
        "admin_reports.html",
        total_products=total_products,
        total_users=total_users,
        total_orders=total_orders,
        total_revenue=total_revenue,
        top_products=top_products,
        recent_orders=recent_orders,
        sales_labels=sales_labels,
        sales_data=sales_data,
        category_labels=category_labels,
        category_data=category_data
    )
