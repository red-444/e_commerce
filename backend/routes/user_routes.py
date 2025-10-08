from flask import Blueprint, render_template, session, redirect, url_for, flash
from razorpay import Order
from backend.models import User, db
from backend.models import Order

# Create blueprint for user
user_bp = Blueprint("user", __name__, url_prefix="/user")

# ======================
# Dashboard (main user panel)
# ======================
@user_bp.route("/dashboard")
def dashboard():
    if not session.get("user_id"):
        flash("Please log in first", "warning")
        return redirect(url_for("auth.login"))

    user = User.query.get(session["user_id"])
    # ✅ Dashboard should render dashboard.html
    return render_template("profile.html", user=user)


# ======================
# Profile Page
# ======================
@user_bp.route("/profile")
def profile():
    if not session.get("user_id"):
        flash("Please log in first", "warning")
        return redirect(url_for("auth.login"))

    
    user = User.query.get(session["user_id"])

    # Get last 5 paid orders
    recent_orders = (
        Order.query
        .filter_by(user_id=user.userid, order_status="Paid")
        .order_by(Order.created_at.desc())
        .limit(5)
        .all()
    )

    # Example: assume user has `wallet_balance` field
    wallet_balance = user.wallet_balance if hasattr(user, "wallet_balance") else 0

    return render_template(
        "dashboard.html",
        user=user,
        recent_orders=recent_orders,
        wallet_balance=wallet_balance
    )


# ======================
# Logout
# ======================
@user_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect(url_for("auth.login"))
