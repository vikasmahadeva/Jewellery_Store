from app import create_app, db
from models import User

app = create_app()
with app.app_context():
    target_email = "admin@gmail.com"
    user = User.query.filter_by(email=target_email).first()
    if user:
        user.is_admin = True
        db.session.commit()
        print(f"✅ {target_email} is now admin.")
    else:
        print(f"❌ User with email {target_email} not found.")
