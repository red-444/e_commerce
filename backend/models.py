# -----------------------
# Imports
# -----------------------
from backend.extensions import db
from datetime import datetime, timedelta

class Admin(db.Model):
    __tablename__ = "admin"
    admin_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.userid"), nullable=False, unique=True)
    role = db.Column(db.String(50), default="superadmin")  # e.g. "superadmin", "manager"
    permissions = db.Column(db.Text, nullable=True)  # JSON/text to store permission data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # relationship back to User
    user = db.relationship("User", backref=db.backref("admin_profile", uselist=False))
# -----------------------
# User
# -----------------------
class User(db.Model):
    __tablename__ = "user"
    userid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    fullname = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)  # ✅ admin flag
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # relationships
    carts = db.relationship("Cart", back_populates="user", cascade="all, delete-orphan", lazy=True)
    orders = db.relationship("Order", back_populates="user", lazy=True)
    otp_entries = db.relationship("OTPVerification", back_populates="user", cascade="all, delete-orphan", lazy=True)
    admin_action_logs = db.relationship("AdminActionLog", back_populates="admin", lazy=True)


# -----------------------
# Admin Action Log
# -----------------------
class AdminActionLog(db.Model):
    __tablename__ = "admin_action_log"
    id = db.Column(db.Integer, primary_key=True)
    admin_user_id = db.Column(db.Integer, db.ForeignKey("user.userid"), nullable=False)
    action_type = db.Column(db.String(50), nullable=False)  # e.g., "add_product"
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    admin = db.relationship("User", back_populates="admin_action_logs")


# -----------------------
# Product
# -----------------------
class Product(db.Model):
    __tablename__ = "product"
    product_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    stock_qty = db.Column(db.Integer, nullable=False, default=0)
    description = db.Column(db.Text, nullable=True)
    image = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(), default=datetime.utcnow)

    # relationships
    cart_items = db.relationship("CartItem", back_populates="product", cascade="all, delete-orphan", lazy=True)
    order_items = db.relationship("OrderItem", back_populates="product", cascade="all, delete-orphan", lazy=True)
    
    inventory = db.relationship("Inventory", back_populates="product", uselist=False)  
    logs = db.relationship("InventoryLog", back_populates="product", cascade="all, delete-orphan", lazy=True)

# -----------------------
# Cart
# -----------------------
class Cart(db.Model):
    __tablename__ = "cart"
    cart_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.userid"), nullable=False)
    status = db.Column(db.String(20), default="active")
    created_at = db.Column(db.DateTime(), default=datetime.utcnow)

    user = db.relationship("User", back_populates="carts")
    items = db.relationship("CartItem", back_populates="cart", cascade="all, delete-orphan", lazy=True)
    orders = db.relationship("Order", back_populates="cart", lazy=True)


# -----------------------
# CartItem
# -----------------------
class CartItem(db.Model):
    __tablename__ = "cart_item"
    item_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cart_id = db.Column(db.Integer, db.ForeignKey("cart.cart_id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.product_id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    cart = db.relationship("Cart", back_populates="items")
    product = db.relationship("Product", back_populates="cart_items")


# -----------------------
# Order
# -----------------------
class Order(db.Model):
    __tablename__ = "orders"
    order_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.userid"), nullable=False)
    cart_id = db.Column(db.Integer, db.ForeignKey("cart.cart_id"), nullable=True)
    total_amt = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    payment_method = db.Column(db.String(50), nullable=True)
    order_status = db.Column(db.String(30), default="pending")
    shipping_address = db.Column(db.Text, nullable=True)
    razorpay_order_id = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime(), default=datetime.utcnow)

    user = db.relationship("User", back_populates="orders")
    cart = db.relationship("Cart", back_populates="orders")
    items = db.relationship("OrderItem", back_populates="order", cascade="all, delete-orphan", lazy=True)
    otp_verification = db.relationship("OTPVerification", back_populates="order", lazy=True)


# -----------------------
# OrderItem
# -----------------------
class OrderItem(db.Model):
    __tablename__ = "order_item"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.order_id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.product_id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    order = db.relationship("Order", back_populates="items")
    product = db.relationship("Product", back_populates="order_items")


# -----------------------
# OTPVerification
# -----------------------
class OTPVerification(db.Model):
    __tablename__ = "otp_verification"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.userid"), nullable=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.order_id"), nullable=True)
    otp_code = db.Column(db.String(6), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(), default=datetime.utcnow)
    expires_at = db.Column(db.DateTime(), nullable=False, default=lambda: datetime.utcnow() + timedelta(minutes=5))

    user = db.relationship("User", back_populates="otp_entries")
    order = db.relationship("Order", back_populates="otp_verification")


# -----------------------
# Inventory
# -----------------------
class Inventory(db.Model):
    __tablename__ = "inventory"
    inventory_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.product_id"), nullable=False)
    stock_quantity = db.Column(db.Integer, nullable=False, default=0)
    reorder_level = db.Column(db.Integer, nullable=False, default=0)
    reserved_stock = db.Column(db.Integer, nullable=False, default=0)
    last_restock_date = db.Column(db.Date)
    supplier_name = db.Column(db.String(50))

    product = db.relationship("Product", back_populates="inventory")




class InventoryLog(db.Model):
    __tablename__ = "inventory_log"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.product_id"), nullable=False)
    change_type = db.Column(db.String(50), nullable=False)  # e.g. "Restock", "Sale", "Correction"
    before = db.Column(db.Integer, nullable=False)
    after = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=db.func.now())

    product = db.relationship("Product", back_populates="logs")
