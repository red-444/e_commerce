# scripts/add_mock_products.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.database import db
from backend.models.product import Product
from flask import Flask
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

categories = ['Electronics', 'Clothing', 'Books', 'Home & Kitchen', 'Toys & Games']

with app.app_context():
    db.create_all()  # ensure tables exist
    product_id = 1

    for category in categories:
        for i in range(1, 101):
            name = f"{category} Product {i}"
            price = round(random.uniform(100, 1100), 2)
            image_url = 'https://via.placeholder.com/300x200'

            product = Product(
                name=name,
                category=category,
                price=price,
                image_url=image_url
            )
            db.session.add(product)

    db.session.commit()
    print("✅ 500 products added to database.")
