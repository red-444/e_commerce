# backend/routes/payment_routes.py
import os
import razorpay
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from backend.models import Cart, Order, db
from dotenv import load_dotenv
from .api import api_bp
load_dotenv()

# ===== Razorpay config =====
RAZORPAY_KEY = os.getenv("RAZORPAY_KEY", "rzp_test_RH6n0VjLPp4cd7")
RAZORPAY_SECRET = os.getenv("RAZORPAY_SECRET", "ei5ZQbwEyJ8nsPE86a71AHeD")
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY, RAZORPAY_SECRET))

payment_bp = Blueprint("payment", __name__, url_prefix="/payment")

# ===== Create Razorpay Order =====
@payment_bp.route("/create-order", methods=["POST"])
def create_order():
    data = request.get_json()
    shipping_address = data.get("shipping_address", "")

    try:
        # 🔹 Get current user's active cart
        user_id = session.get("user_id")
        cart = Cart.query.filter_by(user_id=user_id, status="active").first()

        if not cart or not cart.items:
            return jsonify({"status": "error", "message": "Cart is empty"}), 400

        # 🔹 Calculate total (paise for Razorpay)
        total_amount = 0
        for item in cart.items:  
            total_amount += float(item.product.price) * item.quantity  

        order_amount = int(total_amount * 100)  # convert ₹ to paise
        order_currency = "INR"
        order_receipt = f"order_rcptid_{datetime.now().timestamp()}"

        # 🔹 Create Razorpay order
        razorpay_order = razorpay_client.order.create({
            "amount": order_amount,
            "currency": order_currency,
            "receipt": order_receipt,
            "payment_capture": 1
        })

        return jsonify({
            "status": "success",
            "order_id": order_receipt,
            "razorpay_order_id": razorpay_order["id"],
            "amount": order_amount,
            "currency": order_currency,
            "key": RAZORPAY_KEY
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400



# ===== Verify Razorpay Payment =====
@payment_bp.route("/verify", methods=["POST"])
def verify_payment():
    try:
        data = request.get_json(force=True)
        razorpay_order_id = data.get("razorpay_order_id")
        razorpay_payment_id = data.get("razorpay_payment_id")
        razorpay_signature = data.get("razorpay_signature")

        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            return jsonify({"status": "error", "message": "Missing payment details"}), 400

        # 🔹 Verify signature
        params_dict = {
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature
        }
        razorpay_client.utility.verify_payment_signature(params_dict)

        # 🔹 Update order status in DB
        order = Order.query.filter_by(razorpay_order_id=razorpay_order_id).first()
        if order:
            order.payment_id = razorpay_payment_id
            order.order_status = "paid"
            db.session.commit()

        return jsonify({"status": "success", "message": "Payment verified"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400
