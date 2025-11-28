from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from models import User
from werkzeug.security import check_password_hash, generate_password_hash
from extensions import db
from forms import AdminLoginForm

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password) and not user.is_admin:
            login_user(user)
            flash("Logged in successfully as User!", "success")
            return redirect(url_for('product.home'))
        else:
            flash("Invalid credentials or not a regular user.", "danger")

    return render_template('login.html')


@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    form = AdminLoginForm()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = User.query.filter_by(email=email, is_admin=True).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash("Logged in successfully as Admin!", "success")
            return redirect(url_for('admin.dashboard'))
        else:
            flash("Invalid admin credentials.", "danger")

    return render_template('admin_login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!", "info")
    return redirect(url_for('product.home'))


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered.", "danger")
            return redirect(url_for('auth.signup'))

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            is_admin=False
        )

        db.session.add(user)
        db.session.commit()

        flash("Account created successfully! Please login.", "success")
        return redirect(url_for('auth.login'))

    return render_template('signup.html')
