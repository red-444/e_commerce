
# backend/routes/admin_routes.py
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from sqlalchemy import func
from backend.extensions import db
from backend.models import Product, Order, User, Inventory
from werkzeug.security import generate_password_hash, check_password_hash
# Blueprint
admin_bp = Blueprint("admin", __name__, url_prefix="/admin", template_folder="../templates")


# Utility: Count rows
def _count(model):
    return db.session.query(model).count()


@admin_bp.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        fullname = request.form["fullname"]
        username = request.form["username"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        # ✅ Password match check
        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for("admin.register"))

        # ✅ Check if email or username already exists
        existing_user = User.query.filter(
            (User.email == email) | (User.username == username)
        ).first()

        if existing_user:
            flash("Email or Username already exists!", "danger")
            return redirect(url_for("admin.register"))

        # ✅ Hash password
        hashed_password = generate_password_hash(password)

        # ✅ Create new admin
        new_admin = User(
            fullname=fullname,
            username=username,
            email=email,
            phone=phone,
            password=hashed_password,
            is_admin=True
        )
        db.session.add(new_admin)
        db.session.commit()

        # 🔹 Redirect to login after successful registration
        flash("Admin registered successfully! Please login.", "success")
        return redirect(url_for("admin.login"))

    return render_template("admin_register.html")


# ----------------------- Login -----------------------
@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        admin = User.query.filter_by(username=username, is_admin=True).first()

        if admin and check_password_hash(admin.password, password):
            session["admin_id"] = admin.userid
            session["is_admin"] = True
            flash("Login successful!", "success")
            return redirect(url_for("admin.dashboard"))
        else:
            flash("Invalid username or password", "danger")
    
    return render_template("admin_login.html")

# ---------- Dashboard ----------
@admin_bp.route("/dashboard")
def dashboard():
    stats = {
        "totalproducts": _count(Product),
        "totalorders": _count(Order),
        "totalusers": _count(User),
        "pendingorders": db.session.query(Order).filter_by(order_status="pending").count(),
    }

    low_stock = (
        db.session.query(func.count(Inventory.inventory_id))
        .filter((Inventory.stock_quantity - Inventory.reserved_stock) <= Inventory.reorder_level)
        .scalar()
    )

    return render_template("admin_dashboard.html", low_stock=low_stock, **stats)


# ---------- Product list ----------
@admin_bp.route("/products", methods=["GET", "POST"])
def products():
    if request.method == "POST":
        name = request.form.get("name")
        category = request.form.get("category")
        price = request.form.get("price")
        stock = request.form.get("stockquantity")
        image = request.form.get("imageurl")

        # Create new product
        new_product = Product(
            name=name,
            category=category,
            price=price,
            stock_qty=stock,
            image=image
        )
        db.session.add(new_product)
        db.session.commit()

        flash("✅ Product added successfully!", "success")
        return redirect(url_for("admin.products"))

    # Default: show product list
    products = Product.query.all()
    return render_template("products_admin.html", products=products)



# ---------- Orders ----------
@admin_bp.route("/orders")
def orders():
    from backend.models import Order, User
    orders = Order.query.all()  # fetch all orders
    return render_template("orders_admin.html", orders=orders)


# ---------- Inventory ----------
@admin_bp.route("/inventory")
def inventory():
    rows = (
        db.session.query(Product, Inventory)
        .outerjoin(Inventory, Inventory.product_id == Product.product_id)
        .order_by(Product.created_at.desc())
        .all()
    )

    inventory_rows = []
    for product, inventory in rows:
        inventory_rows.append({
            "id": product.product_id,
            "name": product.name,
            "category": product.category,
            "price": product.price,
            "stock": inventory.stock if inventory else 0,
            "reorder_level": inventory.reorder_level if inventory else "N/A"
        })

    return render_template("admin_inventory.html", rows=inventory_rows)



@admin_bp.route("/manageinventory")
def manageinventory():

    return render_template("manageinventory.html")


# ---------- Users ----------
@admin_bp.route("/users")
def users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin_user.html", users=users)

# ---------- Restock Product ----------
@admin_bp.route("/products/<int:productid>/restock", methods=["POST"])
def restock_product(productid):
    product = Product.query.get_or_404(productid)
    qty = request.form.get("quantity", type=int)

    if qty and qty > 0:
        before_qty = product.stock_qty
        product.stock_qty += qty

        # Add inventory log
        log = Inventory(
            product_id=product.product_id,
            changetype="restock",
            stockbefore=before_qty,
            stockafter=product.stock_qty,
            reason=f"Restocked {qty} units",
            createdat=datetime.utcnow()
        )
        db.session.add(log)

        db.session.commit()
        flash(f"{qty} units added to {product.name} ✅", "success")
    else:
        flash("Invalid quantity ❌", "danger")

    return redirect(url_for("admin.products"))



# ---------- Adjust Stock ----------
@admin_bp.route("/products/<int:productid>/adjust", methods=["POST"])
def adjust_stock(productid):
    product = Product.query.get_or_404(productid)
    new_qty = request.form.get("stockqty", type=int)

    if new_qty is not None and new_qty >= 0:
        before_qty = product.stock_qty
        product.stock_qty = new_qty

        # Add inventory log
        log = Inventory(
            product_id=product.product_id,
            changetype="adjust",
            stockbefore=before_qty,
            stockafter=new_qty,
            reason="Manual stock adjustment",
            createdat=datetime.utcnow()
        )
        db.session.add(log)

        db.session.commit()
        flash(f"Stock adjusted for {product.name} → {new_qty} ✅", "success")
    else:
        flash("Invalid stock quantity ❌", "danger")

    return redirect(url_for("admin.products"))



# Update order status
@admin_bp.route("/orders/<int:order_id>/update", methods=["POST"])
def update_order_status(order_id):
    from backend.models import Order, db

    order = Order.query.get_or_404(order_id)
    new_status = request.form.get("status")

    if new_status:
        order.order_status = new_status
        db.session.commit()
        flash(f"Order #{order_id} updated to {new_status}", "success")
    else:
        flash("No status provided", "danger")

    return redirect(url_for("admin.orders"))


@admin_bp.route("/users/delete/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("User deleted successfully!", "success")
    return redirect(url_for("admin.manage_users"))


