from . import db
from flask_login import UserMixin

from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model, UserMixin):
    __tablename__ = "accounts"
    id = db.Column(db.Integer(), primary_key=True, nullable=False)
    first_name = db.Column(db.String(length=30), nullable=False)
    last_name = db.Column(db.String(length=30), nullable=False)
    email = db.Column(db.String(length=50), nullable=False, unique=True)
    password = db.Column(db.String(length=60), nullable=False)
    created_on = db.Column(db.DateTime, server_default=db.func.now())
    # confirmed = db.Column(db.Boolean, nullable=False, default=False)
    # confirmed_on = db.Column(db.DateTime, nullable=True)
    # updated_on = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())
    # last_login = db.Column(
    #     db.DateTime,
    #     index=False,
    #     unique=False,
    #     nullable=True
    # )

    def check_password(self, password):
        """Check hashed password."""
        return check_password_hash(self.password, password)

    def __repr__(self):
        return "<User {}>".format(f"{self.first_name} {self.last_name}")

# products model
# class Item(db.Model):
#     __tablename__ = "products"
#     id = db.Column(db.Integer(), primary_key=True, nullable=False)
#     buyer = db.Column(db.Integer(), db.ForeignKey('accounts.id'), nullable=False)
#     name = db.Column(db.String(length=30), nullable=False, unique=True)
#     price = db.Column(db.Float(), nullable=False)
#     description = db.Column(db.String(length=1000), nullable=False, unique=True)


