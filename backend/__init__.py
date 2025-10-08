from flask import Flask
from .extensions import db, migrate, mail  # import mail too
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    # Flask-Mail config
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'lrred444@gmail.com'

    app.config['MAIL_PASSWORD'] = 'qwun bjnx byec cehe'


    # init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    # import models so tables are registered
    from . import models  

    # ✅ Import your blueprint here
    from .routes.payment_routes import payment_bp  
    app.register_blueprint(payment_bp, url_prefix="/payment")

    return app

# expose app, db, migrate
app = create_app()
__all__ = ["app", "db", "migrate"]
