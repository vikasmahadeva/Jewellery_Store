# reset_password.py
from app import create_app
from extensions import db
from models import User
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    target_email = "admin@example.com"   # change if needed
    new_password = "NewStrongPassword1!" # change to something secure

    user = User.query.filter_by(email=target_email).first()
    if user:
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        print(f"Password for {target_email} set to: {new_password}")
    else:
        print(f"User {target_email} not found. Create it first or change the email.")
