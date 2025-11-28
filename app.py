from flask import Flask, render_template, session
from config import Config
from extensions import db, login_manager, csrf
from flask_migrate import Migrate

migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)  # Ensure SECRET_KEY is set in Config

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)  # CSRF Protection is applied globally

    login_manager.login_view = 'auth.login'

    # Register blueprints
    from routes.auth_routes import auth_bp
    from routes.product_routes import product_bp
    from routes.admin_routes import admin_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Inject cart count globally into templates
    @app.context_processor
    def inject_cart_count():
        cart = session.get("cart", {})
        try:
            count = sum(int(qty) for qty in cart.values())
        except Exception:
            count = 0
        return {"cart_count": count}

    # Error handler
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('403.html'), 403

    return app


# Flask-Login User Loader
from models import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)

    from app import create_app
app = create_app()
with app.app_context():
    print(sorted(app.url_map.iter_rules(), key=lambda r: r.endpoint))

