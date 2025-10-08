# backend/routes.py
from flask import current_app as app, request, jsonify
from .extensions import db
from .models import User, Product, Cart, CartItem, Orders, OrderItem, OTPVerification, InventoryLog
from .utils import hash_password, verify_password, generate_otp, otp_expiry
from sqlalchemy import func

# health
@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

# ---------- AUTH ----------
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json or {}
    for f in ('user_id','name','email','password'):
        if not data.get(f):
            return jsonify({'error': f'{f} required'}), 400
    if User.query.filter((User.user_id==data['user_id']) | (User.email==data['email'])).first():
        return jsonify({'error':'user exists'}), 400
    user = User(
        user_id=data['user_id'],
        name=data['name'],
        email=data['email'],
        password=hash_password(data['password']),
        phone=data.get('phone')
    )
    db.session.add(user); db.session.commit()
    return jsonify({'message':'registered','user_id':user.user_id})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json or {}
    user = User.query.filter((User.user_id==data.get('user')) | (User.email==data.get('user'))).first()
    if not user or not verify_password(user.password, data.get('password','')):
        return jsonify({'error':'invalid creds'}), 401
    # simple token = user_id (for demo). Use JWT for production.
    return jsonify({'token': user.user_id})

def get_current_user():
    token = request.headers.get('Authorization')
    if not token:
        return None
    return User.query.get(token)

# ---------- PRODUCTS ----------
@app.route('/api/products', methods=['GET'])
def get_products():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    q = Product.query.order_by(Product.product_id.asc())
    pag = q.paginate(page=page, per_page=per_page, error_out=False)
    items = [{
        'product_id': p.product_id,
        'name': str(p.name),
        'category': p.category,
        'price': float(p.price),
        'stock_qty': p.stock_qty,
        'description': p.description,
        'image': p.image
    } for p in pag.items]
    return jsonify({'total': pag.total, 'page': pag.page, 'per_page': pag.per_page, 'items': items})

@app.route('/api/products/<int:pid>', methods=['GET'])
def get_product(pid):
    p = Product.query.get_or_404(pid)
    return jsonify({'product_id': p.product_id, 'name': p.name, 'price': float(p.price), 'stock_qty': p.stock_qty})

# Admin create/edit product
@app.route('/api/products', methods=['POST'])
def create_product():
    user = get_current_user()
    if not user:
        return jsonify({'error':'auth required'}), 401
    # in real app require admin check
    data = request.json or {}
    p = Product(
        name=data.get('name','Untitled'),
        category=data.get('category','General'),
        price=data.get('price',0.0),
        stock_qty=data.get('stock_qty',0),
        description=data.get('description'),
        image=data.get('image')
    )
    db.session.add(p); db.session.commit()
    return jsonify({'message':'created','product_id': p.product_id}), 201

# ---------- CART ----------
@app.route('/api/cart', methods=['POST'])
def add_to_cart():
    user = get_current_user()
    if not user:
        return jsonify({'error':'auth required'}), 401
    data = request.json or {}
    pid = data.get('product_id'); qty = int(data.get('quantity',1))
    if not pid:
        return jsonify({'error':'product_id required'}), 400
    # create or get active cart
    cart = Cart.query.filter_by(user_id=user.user_id, status='active').first()
    if not cart:
        cart = Cart(user_id=user.user_id)
        db.session.add(cart); db.session.commit()
    # add/update cart item
    item = CartItem.query.filter_by(cart_id=cart.cart_id, product_id=pid).first()
    if item:
        item.quantity += qty
    else:
        item = CartItem(cart_id=cart.cart_id, product_id=pid, quantity=qty)
        db.session.add(item)
    db.session.commit()
    return jsonify({'message':'added'})

@app.route('/api/cart', methods=['GET'])
def view_cart():
    user = get_current_user()
    if not user:
        return jsonify({'error':'auth required'}), 401
    cart = Cart.query.filter_by(user_id=user.user_id, status='active').first()
    if not cart:
        return jsonify({'items': []})
    items = []
    for it in cart.items:
        prod = it.product
        items.append({'product_id': prod.product_id, 'name': prod.name, 'quantity': it.quantity, 'unit_price': float(prod.price)})
    return jsonify({'cart_id': cart.cart_id, 'items': items})

# ---------- ORDER ----------
@app.route('/api/orders', methods=['POST'])
def place_order():
    user = get_current_user()
    if not user:
        return jsonify({'error':'auth required'}), 401
    cart = Cart.query.filter_by(user_id=user.user_id, status='active').first()
    if not cart or not cart.items:
        return jsonify({'error':'cart empty'}), 400
    total = 0
    for it in cart.items:
        if it.product.stock_qty < it.quantity:
            return jsonify({'error': f'product {it.product_id} out of stock'}), 400
        total += float(it.product.price) * it.quantity
    order = Orders(user_id=user.user_id, cart_id=cart.cart_id, total_amt=total, payment_method='COD', order_status='pending')
    db.session.add(order)
    db.session.flush()  # get order id
    # create order items and reduce stock + inventory logs
    for it in cart.items:
        oi = OrderItem(order_id=order.order_id, product_id=it.product_id, quantity=it.quantity, unit_price=it.product.price)
        db.session.add(oi)
        # inventory
        before = it.product.stock_qty
        it.product.stock_qty -= it.quantity
        log = InventoryLog(product_id=it.product_id, change_type='sale', stock_before=before, stock_after=it.product.stock_qty, reason='order')
        db.session.add(log)
    cart.status = 'ordered'
    db.session.commit()
    # create an OTP entry for order verification
    code = generate_otp()
    otp = OTPVerification(order_id=order.order_id, otp_code=code, is_verified=False, expires_at=otp_expiry())
    db.session.add(otp); db.session.commit()
    # In real app send OTP via SMS/Email. Here return code for testing.
    return jsonify({'message':'order placed','order_id': order.order_id, 'otp': code})

@app.route('/api/orders/<int:order_id>/verify', methods=['POST'])
def verify_order(order_id):
    data = request.json or {}
    code = data.get('otp')
    otp = OTPVerification.query.filter_by(order_id=order_id, otp_code=code, is_verified=False).first()
    if not otp:
        return jsonify({'error':'invalid otp'}), 400
    if otp.expires_at < __import__('datetime').datetime.utcnow():
        return jsonify({'error':'otp expired'}), 400
    otp.is_verified = True
    # update order status
    order = Orders.query.get(order_id)
    order.order_status = 'paid'  # or verified
    db.session.commit()
    return jsonify({'message':'verified'})

# ---------- Inventory ----------
@app.route('/api/products/<int:pid>/stock', methods=['POST'])
def update_stock(pid):
    # admin-only in real app
    data = request.json or {}
    change = int(data.get('change', 0))
    reason = data.get('reason','manual')
    p = Product.query.get_or_404(pid)
    before = p.stock_qty
    p.stock_qty += change
    log = InventoryLog(product_id=pid, change_type='restock' if change>0 else 'deduct', stock_before=before, stock_after=p.stock_qty, reason=reason)
    db.session.add(log); db.session.commit()
    return jsonify({'product_id': pid, 'stock_after': p.stock_qty})
