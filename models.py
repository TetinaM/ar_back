from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json


db = SQLAlchemy()


# MODEL 1: Users
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with favorites
    favorites = db.relationship(
        'UserFavorite',
        back_populates='user',
        cascade='all, delete-orphan'
    )
    
    def set_password(self, password):
        """Hashes the password before saving"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Checks whether the entered password matches the stored one"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'full_name': self.full_name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# MODEL 2: Products (furniture)
class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(80))
    
    # Path to 3D model
    model_path = db.Column(db.String(255))
    
    # Product image
    image_url = db.Column(db.String(255))
    
    # Furniture parameters
    material = db.Column(db.String(120))
    color = db.Column(db.String(80))
    
    # Dimensions (stored as JSON for flexibility)
    dimensions = db.Column(db.JSON, default={})
    
    in_stock = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with favorites
    favorited_by = db.relationship(
        'UserFavorite',
        back_populates='product',
        cascade='all, delete-orphan'
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'category': self.category,
            'model_path': self.model_path,
            'image_url': self.image_url,
            'material': self.material,
            'color': self.color,
            'dimensions': self.dimensions if self.dimensions else {},
            'in_stock': self.in_stock,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# LINK TABLE: User favorite products
class UserFavorite(db.Model):
    __tablename__ = 'user_favorites'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='favorites')
    product = db.relationship('Product', back_populates='favorited_by')
    
    # Constraint: each product can be favorited only once per user
    __table_args__ = (db.UniqueConstraint('user_id', 'product_id', name='unique_user_product'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'product_id': self.product_id,
            'product': self.product.to_dict() if self.product else None,
            'added_at': self.added_at.isoformat() if self.added_at else None
        }