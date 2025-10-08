import csv
from backend.extensions import db
from backend.models import Product
from backend.app import app

with app.app_context():
    with open('product.csv', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            product = Product(
                title=row['title'],
                description=row['description'],
                price=float(row['price']),
                category=row['category'],
                image_url=row['image_url'],  # fixed here
                stock=int(row['stock'])
            )
            db.session.add(product)
        db.session.commit()

print("✅ Products imported successfully")
