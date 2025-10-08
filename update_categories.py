import random
from backend.app import app, db
from backend.models import Product  # Make sure this points to your Product model

# List of categories you want to assign
categories = [
    "Electronics",
    "Clothing",
    "Books",
    "Home & Kitchen",
    "Toys & Games"
]

def update_product_categories():
    with app.app_context():
        # Fetch all products from DB
        products = Product.query.all()
        print(f"Found {len(products)} products in the database.")

        for product in products:
            old_category = product.category
            new_category = random.choice(categories)
            product.category = new_category
            print(f"Updated '{product.title}': {old_category} -> {new_category}")

        # Commit changes
        db.session.commit()
        print(f"✅ Updated {len(products)} products with random categories.")

if __name__ == "__main__":
    update_product_categories()
