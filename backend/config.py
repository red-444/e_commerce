import os

class Config:
      SQLALCHEMY_DATABASE_URI = os.getenv(
'postgresql://postgres:12345@localhost:5432/e_com',
"sqlite:///ecommerce.db" # easy for local; swap for Postgres if needed
)
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = os.getenv("SECRET_KEY", "change_me")