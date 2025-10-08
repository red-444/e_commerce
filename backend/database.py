from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
def init_db(app):
    db.init_app(app)
    with app.app_context():
        from backend import models  # Import all models here
        db.create_all()