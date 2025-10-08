# backend/routes/product_routes.py
from flask import Blueprint, render_template, request, jsonify, session
from backend.models import Product, Cart, User, db
import razorpay

# ------------------ PRODUCT ROUTES ------------------
product_bp = Blueprint("product", __name__, url_prefix="/products")

@product_bp.route("/", methods=["GET"])
def products():
    search_query = request.args.get("q", "").strip()
    selected_category = request.args.get("category", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 8  # products per page

    query = Product.query

    # Search filter
    if search_query:
        query = query.filter(Product.title.ilike(f"%{search_query}%"))

    # Category filter
    if selected_category:
        query = query.filter(Product.category == selected_category)

    # ✅ Pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    products = pagination.items

    # Fetch all categories for dropdown
    categories = [c[0] for c in db.session.query(Product.category).distinct().all()]

    return render_template(
        "products.html",
        products=products,
        pagination=pagination,
        categories=categories,
        selected_category=selected_category,
        search_query=search_query,
    )

@product_bp.route("/<int:product_id>")
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)

    # ✅ Related products (exclude the same product)
    related_products = Product.query.filter(
        Product.category == product.category,
        Product.product_id != product.product_id
    ).limit(4).all()

    return render_template(
        "product_detail.html",
        product=product,
        related_products=related_products
    )



