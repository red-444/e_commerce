from decimal import Decimal
from flask import Blueprint, request, jsonify
from backend.database import db
from backend.models import Cart, Order, OrderItem, Product, User

import razorpay

api_bp = Blueprint("api", __name__)

# Razorpay client (test mode)
razorpay_client = razorpay.Client(auth=("rzp_test_xxxxx", "your_secret"))


# ✅ GET all products
@api_bp.route("/products", methods=["GET"])
def get_products():
    products = Product.query.all()
    return jsonify([{
        "id": p.id,
        "name": p.name,
        "price": p.price,
        "description": p.description,
        "image": p.image,
        "category": p.category
    } for p in products]), 200


# ✅ Register new user
@api_bp.route("/register", methods=["POST"])
def register_user():
    data = request.json
    new_user = User(
        name=data["name"],
        email=data["email"],
        password=data["password"]
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User registered successfully"}), 201


# ✅ Checkout with Razorpay (sum of cart items)
# ✅ Checkout with Razorpay (old /checkout route)
@api_bp.route("/checkout", methods=["POST"])
def checkout_cart():
    data = request.json
    user_id = data.get("user_id")

    cart = Cart.query.filter_by(user_id=user_id, status="active").first()
    if not cart or not cart.items:
        return jsonify({"error": "Cart is empty"}), 400

    total_amount = sum(item.quantity * float(item.product.price) for item in cart.items)
    amount_in_paise = int(total_amount * 100)

    razorpay_order = razorpay_client.order.create({
        "amount": amount_in_paise,
        "currency": "INR",
        "payment_capture": 1
    })

    new_order = Order(
        user_id=user_id,
        cart_id=cart.cart_id,
        total_amt=total_amount,
        payment_method="razorpay",
        order_status="pending"
    )
    db.session.add(new_order)
    db.session.commit()

    for item in cart.items:
        order_item = OrderItem(
            order_id=new_order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.product.price
        )
        db.session.add(order_item)
    db.session.commit()

    return jsonify({
        "razorpay_order_id": razorpay_order["id"],
        "db_order_id": new_order.id,
        "amount": amount_in_paise,
        "currency": "INR"
    })


# ✅ Another checkout route (/orders/checkout)
@api_bp.route("/orders/checkout", methods=["POST"])
def checkout_with_address():
    data = request.json
    user_id = data.get("user_id")

    cart = Cart.query.filter_by(user_id=user_id, status="active").first()
    if not cart or not cart.items:
        return jsonify({"error": "Cart is empty"}), 400

    total_amount = sum(float(item.quantity) * float(item.product.price) for item in cart.items)

    razorpay_order = razorpay_client.order.create({
        "amount": int(total_amount * 100),
        "currency": "INR",
        "payment_capture": "1"
    })

    order = Order(
        user_id=user_id,
        cart_id=cart.cart_id,
        total_amt=Decimal(total_amount),
        payment_method="razorpay",
        order_status="pending",
        shipping_address=data.get("shipping_address")
    )
    db.session.add(order)
    db.session.commit()

    return jsonify({
        "razorpay_order_id": razorpay_order["id"],
        "amount": total_amount,
        "currency": "INR"
    })
