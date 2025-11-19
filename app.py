from flask import Flask
from werkzeug.security import generate_password_hash

from config import Config
from models import db,User

def create_app():
    app=Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    with app.app_context():
        db.create_all()
        ensure_default_admin()
    @app.route('/')
    def home():
        return "hospital management system-db setup complete."
    return app
def ensure_default_admin():
    admin=User.query.filter_by(role="admin").first()
    if admin:
        print("Default admin already exists.")
        return
    admin_user=User(
        username="admin",
        password=generate_password_hash("admin123"),
        role="admin",
    )
    db.session.add(admin_user)
    db.session.commit()
    print("Created default admin -> username: admin,password: admin123")
app=create_app()

if __name__=="__main__":
    app.run(debug=True)