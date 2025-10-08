
import os
import hashlib
import hmac
from datetime import datetime

from flask import Flask, flash, jsonify, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
from dotenv import load_dotenv
import razorpay

# Load environment variables from .env
load_dotenv()

# Initialize Razorpay Client using env variables
RAZORPAY_KEY = os.getenv("RAZORPAY_KEY")
RAZORPAY_SECRET = os.getenv("RAZORPAY_SECRET")
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY, RAZORPAY_SECRET))

# Local imports
from .extensions import db, migrate
from .models import Cart, Order, OrderItem, CartItem, Product, OTPVerification, User, AdminActionLog, Inventory

def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    CORS(app)

    # Secure configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register Blueprints
    from .routes.product_routes import product_bp
    from .routes.cart_routes import cart_bp
    from .routes.order_routes import order_bp
    from .routes.auth_routes import auth_bp
    from backend.routes.user_routes import user_bp
    from .routes.adminroutes import admin_bp
    from backend.routes.payment_routes import payment_bp
    from backend.routes.otp_routes import otp_bp

    app.register_blueprint(product_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(otp_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(user_bp)

    # ------------------- ROUTES -------------------

    @app.route("/")
    def index():
        return render_template("index.html", year=datetime.utcnow().year)

    # ---------- AUTH ----------
    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            username = request.form.get("username")
            email = request.form.get("email")
            fullname = request.form.get("fullname")
            phone = request.form.get("phone")
            password = request.form.get("password")
            confirm_password = request.form.get("confirm_password")

            if password != confirm_password:
                return render_template("register.html", error="Passwords do not match.")

            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                return render_template("register.html", error="Email already registered.")

            hashed_password = generate_password_hash(password)
            new_user = User(
                username=username,
                email=email,
                fullname=fullname,
                phone=phone,
                password=hashed_password,
            )

            db.session.add(new_user)
            db.session.commit()

            return render_template("register.html", success="Registration successful! Redirecting to login...")

        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form["email"]
            password = request.form["password"]

            user = User.query.filter_by(email=email).first()
            if not user or not check_password_hash(user.password, password):
                return render_template("login.html", error="Invalid email or password")

            session["user_id"] = user.userid
            session["username"] = user.username
            session["profile_pic"] = getattr(user, "profile_pic", None)

            return redirect(url_for("index"))

        return render_template("login.html")

    # ---------- CART ----------
    @app.route("/cart/<int:cart_id>")
    def view_cart(cart_id):
        cart = Cart.query.get_or_404(cart_id)
        cart_summary = [
            {
                "name": item.product.name,
                "price": float(item.product.price),
                "quantity": item.quantity,
                "subtotal": float(item.product.price) * item.quantity,
            }
            for item in cart.items
        ]
        total = sum(entry["subtotal"] for entry in cart_summary)
        return render_template("cart.html", cart=cart, items=cart_summary, total=total)

    @app.route("/checkout/<int:cart_id>")
    def checkout(cart_id):
        cart = Cart.query.get_or_404(cart_id)
        cart_summary = [
            {
                "product": item.product.name,
                "price": float(item.product.price),
                "quantity": item.quantity,
                "subtotal": float(item.product.price) * item.quantity,
            }
            for item in cart.items
        ]
        total_amount = sum(entry["subtotal"] for entry in cart_summary)
        return render_template("checkout.html", cart=cart, summary=cart_summary, total=total_amount)

    # ---------- ADMIN REGISTER ----------
    @app.route("/admin/register", methods=["GET", "POST"])
    def admin_register():
        if request.method == "POST":
            username = request.form.get("username")
            email = request.form.get("email")
            fullname = request.form.get("fullname")
            phone = request.form.get("phone")
            password = request.form.get("password")
            confirm_password = request.form.get("confirm_password")

            if password != confirm_password:
                return render_template("admin_register.html", error="Passwords do not match.")

            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                return render_template("admin_register.html", error="Email already registered.")

            hashed_password = generate_password_hash(password)
            new_admin = User(
                username=username,
                email=email,
                fullname=fullname,
                phone=phone,
                password=hashed_password,
                is_admin=True,
            )

            try:
                db.session.add(new_admin)
                db.session.commit()
                return render_template("admin_register.html", success="Admin registered successfully! Redirecting to login...")
            except Exception as e:
                db.session.rollback()
                return render_template("admin_register.html", error=f"Error: {e}")

        return render_template("admin_register.html")

    # ---------- LOGOUT ----------
    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("index"))

    # ---------- PROFILE ----------
    @app.route("/profile")
    def profile():
        if "user_id" not in session:
            return redirect(url_for("login"))

        user = User.query.get(session["user_id"])
        return render_template("dashboard.html", user=user)

    return app

app = create_app()
if __name__ == "__main__":

    app.run(debug=True)

