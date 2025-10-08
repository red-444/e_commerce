from flask import Blueprint, render_template, redirect, url_for, request, session, flash, jsonify
from ..models import Product, Cart, CartItem, User
from ..extensions import db
from datetime import datetime

cart_bp = Blueprint("cart", __name__, url_prefix="/cart")

# 🔑 Helper: Get logged-in user
def get_user_from_session():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)

# 🔑 Helper: Get or create active cart
def get_or_create_cart(user):
    cart = Cart.query.filter_by(user_id=user.userid, status="active").first()
    if not cart:
        cart = Cart(user_id=user.userid, status="active", created_at=datetime.utcnow())
        db.session.add(cart)
        db.session.commit()
    return cart


# 🛒 View Cart
@cart_bp.route("/")
def view_cart():
    user = get_user_from_session()
    if not user:
        flash("You must log in to view your cart.", "warning")
        return redirect(url_for("auth.login"))

    cart = Cart.query.filter_by(user_id=user.userid, status="active").first()
    items = []
    total = 0

    if cart:
        for item in cart.items:
            subtotal = item.quantity * (item.product.price or 0)
            total += subtotal
            items.append({
                "id": item.item_id,
                "product_id": item.product.product_id,
                "title": item.product.name,
                "price": item.product.price,
                "quantity": item.quantity,
                "subtotal": subtotal,
            })

    return render_template("cart.html", items=items, total=total)


# 🛒 Add to Cart
@cart_bp.route("/add/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    user = get_user_from_session()
    if not user:
        flash("Please log in first!", "warning")
        return redirect(url_for("auth.login"))

    qty = int(request.form.get("quantity", 1))
    product = Product.query.get_or_404(product_id)
    cart = get_or_create_cart(user)

    item = CartItem.query.filter_by(cart_id=cart.cart_id, product_id=product_id).first()
    if item:
        item.quantity += qty
    else:
        item = CartItem(cart_id=cart.cart_id, product_id=product_id, quantity=qty)
        db.session.add(item)

    db.session.commit()
    flash(f"{product.name} added to cart!", "success")
    return redirect(url_for("cart.view_cart"))


# ❌ Remove Item
@cart_bp.route("/remove/<int:item_id>", methods=["POST"])
def remove_item(item_id):
    user = get_user_from_session()
    if not user:
        return redirect(url_for("auth.login"))

    cart = get_or_create_cart(user)
    item = CartItem.query.filter_by(item_id=item_id, cart_id=cart.cart_id).first_or_404()

    db.session.delete(item)
    db.session.commit()
    flash("Item removed from cart.", "info")

    return redirect(url_for("cart.view_cart"))


# 🔄 JSON API (AJAX Add to Cart)
@cart_bp.route("/api/add", methods=["POST"])
def api_add():
    data = request.get_json() or {}
    user = get_user_from_session()
    if not user:
        return jsonify({"error": "auth required"}), 401

    product_id = int(data.get("product_id"))
    qty = int(data.get("quantity", 1))

    product = Product.query.get_or_404(product_id)
    cart = get_or_create_cart(user)

    item = CartItem.query.filter_by(cart_id=cart.cart_id, product_id=product_id).first()
    if item:
        item.quantity += qty
    else:
        item = CartItem(cart_id=cart.cart_id, product_id=product_id, quantity=qty)
        db.session.add(item)

    db.session.commit()
    return jsonify({"message": f"{product.name} added to cart!", "cart_id": cart.cart_id})
