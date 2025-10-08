from datetime import datetime
import razorpay
from flask import Blueprint, flash, redirect, request, jsonify, render_template, session, url_for
from ..extensions import db
from ..models import Cart, Order, OrderItem, Product, User

order_bp = Blueprint("order", __name__, url_prefix="/orders")

# Razorpay client (use your test keys)
razorpay_client = razorpay.Client(auth=("YOUR_KEY_ID", "YOUR_KEY_SECRET"))


@order_bp.route("/place", methods=["POST"])
def place_order():
    data = request.get_json()
    name = data.get("name")
    address = data.get("address")
    phone = data.get("phone")
    user_id = session.get("user_id") or 1  # demo fallback

    # For demo: calculate total from cart/products
    products = Product.query.limit(1).all()  # TODO: fetch from cart
    if not products:
        return jsonify({"error": "No products"}), 400

    total_amt = sum(p.price for p in products)

    # Create Order in DB (status=pending)
    order = Order(
        user_id=user_id,
        name=name,
        address=address,
        phone=phone,
        total_amt=total_amt,
        status="pending",
    )
    db.session.add(order)
    db.session.commit()

    # Create Razorpay Order
    razorpay_order = razorpay_client.order.create(
        dict(amount=int(total_amt * 100), currency="INR", payment_capture="1")
    )

    return jsonify(
        {
            "order_id": order.id,
            "razorpay_order_id": razorpay_order["id"],
            "total_amt": total_amt,
        }
    )



@order_bp.route("/success", methods=["POST"])
def payment_success():
    data = request.get_json()
    order_id = data.get("order_id")
    payment_id = data.get("payment_id")

    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    order.payment_id = payment_id
    order.status = "paid"
    db.session.commit()

    return jsonify({"message": "Order placed successfully!"})


@order_bp.route("/checkout")
def checkout():
    return render_template("checkout.html")

@order_bp.route("/place_order", methods=["GET", "POST"])
def user_place_order():
    if not session.get("user_id"):
        flash("Please log in first", "warning")
        return redirect(url_for("auth.login"))

    user = User.query.get(session["user_id"])

    if request.method == "POST":
        try:
            # ✅ Get cart items of the user
            cart_items = Cart.query.filter_by(user_id=user.user_id).all()
            if not cart_items:
                flash("Your cart is empty!", "danger")
                return redirect(url_for("cart.view_cart"))

            # ✅ Create a new Order
            new_order = Order(
                user_id=user.user_id,
                status="Paid",   # since you said paid orders
                created_at=datetime.utcnow()
            )
            db.session.add(new_order)
            db.session.commit()

            # ✅ Move cart items to order items
            for item in cart_items:
                order_item = OrderItem(
                    order_id=new_order.order_id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    price=item.product.price
                )
                db.session.add(order_item)
                db.session.delete(item)  # clear from cart

            db.session.commit()

            flash("Order placed successfully!", "success")
            return redirect(url_for("user.dashboard"))

        except Exception as e:
            db.session.rollback()
            flash(f"Error placing order: {str(e)}", "danger")
            return redirect(url_for("cart.view_cart"))

    # ===================
    # GET request → show order page
    # ===================
    cart_items = Cart.query.filter_by(user_id=user.user_id).all()
    return render_template("place_order.html", user=user, cart_items=cart_items)


# ======================
# Show User Orders
# ======================


@order_bp.route("/orders", methods=["GET"])
def view_orders():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))   # or wherever your login page is

    orders = Order.query.filter_by(user_id=session["user_id"]).order_by(Order.created_at.desc()).all()
    return render_template("orders.html", orders=orders)