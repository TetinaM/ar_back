from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Product, User, UserFavorite
from sqlalchemy import desc


products_bp = Blueprint('products', __name__, url_prefix='/api/products')


# ✅ ROUTE 1: GET ALL PRODUCTS
@products_bp.route('/', methods=['GET'])
def get_products():
    """
    GET /api/products
    Returns a list of all products with optional filtering.
    Query parameters:
    - category: filter by category
    - in_stock: only products in stock (true/false)
    """
    try:
        query = Product.query
        
        # Filter by category, if provided
        category = request.args.get('category')
        if category:
            query = query.filter_by(category=category)
        
        # Filter by stock status
        in_stock = request.args.get('in_stock')
        if in_stock:
            in_stock = in_stock.lower() == 'true'
            query = query.filter_by(in_stock=in_stock)
        
        products = query.all()
        
        return jsonify({
            'success': True,
            'count': len(products),
            'products': [product.to_dict() for product in products]
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error while fetching products: {str(e)}'
        }), 500



# ✅ ROUTE 2: GET SINGLE PRODUCT BY ID
@products_bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """
    GET /api/products/<product_id>
    Returns detailed information about a product.
    """
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({
                'success': False,
                'message': 'Product not found'
            }), 404
        
        return jsonify({
            'success': True,
            'product': product.to_dict()
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500



# ✅ ROUTE 3: GET ALL CATEGORIES
@products_bp.route('/categories', methods=['GET'])
def get_categories():
    """GET /api/products/categories"""
    try:
        categories = db.session.query(Product.category).distinct().filter(
            Product.category != None
        ).all()
        category_list = sorted([cat[0] for cat in categories])
        
        return jsonify({
            'success': True,
            'categories': category_list
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500



# ✅ ROUTE 4: ADD PRODUCT TO FAVORITES
@products_bp.route('/<int:product_id>/favorite', methods=['POST'])
@jwt_required()
def add_to_favorite(product_id):
    """
    POST /api/products/<int:product_id>/favorite
    Adds a product to the current user's favorites.
    """
    try:
        # ✅ ИСПРАВЛЕННО: преобразуй в число
        user_id = int(get_jwt_identity())
        
        # Check if user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Check if product exists
        product = Product.query.get(product_id)
        if not product:
            return jsonify({
                'success': False,
                'message': 'Product not found'
            }), 404
        
        # Check if already in favorites
        existing = UserFavorite.query.filter_by(
            user_id=user_id,
            product_id=product_id
        ).first()
        
        if existing:
            return jsonify({
                'success': False,
                'message': 'Product already in favorites'
            }), 409
        
        # Add to favorites
        new_favorite = UserFavorite(user_id=user_id, product_id=product_id)
        db.session.add(new_favorite)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Product added to favorites',
            'favorite': new_favorite.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500



# ✅ ROUTE 5: REMOVE FROM FAVORITES
@products_bp.route('/<int:product_id>/favorite', methods=['DELETE'])
@jwt_required()
def remove_from_favorite(product_id):
    """
    DELETE /api/products/<product_id>/favorite
    Removes a product from the current user's favorites.
    """
    try:
        # ✅ ИСПРАВЛЕННО: преобразуй в число
        user_id = int(get_jwt_identity())
        
        # Find and delete favorite
        favorite = UserFavorite.query.filter_by(
            user_id=user_id,
            product_id=product_id
        ).first()
        
        if not favorite:
            return jsonify({
                'success': False,
                'message': 'Product is not in favorites'
            }), 404
        
        db.session.delete(favorite)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Product removed from favorites'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500



# ✅ ROUTE 6: CHECK IF PRODUCT IS FAVORITE
@products_bp.route('/<int:product_id>/favorite', methods=['GET'])
@jwt_required()
def is_favorite(product_id):
    """
    GET /api/products/<product_id>/favorite
    Checks if a product is in the current user's favorites.
    """
    try:
        # ✅ ИСПРАВЛЕННО: преобразуй в число
        user_id = int(get_jwt_identity())
        
        favorite = UserFavorite.query.filter_by(
            user_id=user_id,
            product_id=product_id
        ).first()
        
        return jsonify({
            'success': True,
            'is_favorite': favorite is not None
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500



# ✅ ROUTE 7: GET ALL FAVORITE PRODUCTS OF CURRENT USER
@products_bp.route('/my/favorites', methods=['GET'])
@jwt_required()
def get_my_favorites():
    """
    GET /api/products/my/favorites?page=1&sort_by=name&per_page=12
    Gets all favorite products of the current user.
    """
    try:
        # ✅ ИСПРАВЛЕННО: преобразуй в число
        user_id = int(get_jwt_identity())
        
        # Parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 12, type=int)
        sort_by = request.args.get('sort_by', 'name')  # name, price_asc, price_desc, newest
        
        # ✅ ВАЛИДАЦИЯ параметров:
        if page < 1:
            page = 1
        if per_page < 1:
            per_page = 12
        if per_page > 100:  # Максимум 100 товаров за раз
            per_page = 100
        
        # Base query
        query = UserFavorite.query.filter_by(user_id=user_id)
        
        # Sorting
        if sort_by == 'price_asc':
            query = query.join(Product).order_by(Product.price.asc())
        elif sort_by == 'price_desc':
            query = query.join(Product).order_by(Product.price.desc())
        elif sort_by == 'newest':
            query = query.order_by(desc(UserFavorite.added_at))
        else:  # name
            query = query.join(Product).order_by(Product.name.asc())
        
        # Pagination
        total = query.count()
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        favorites_data = [fav.product.to_dict() for fav in paginated.items]
        
        return jsonify({
            'success': True,
            'count': total,
            'page': page,
            'per_page': per_page,
            'total_pages': paginated.pages,
            'favorites': favorites_data
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500



# ✅ ROUTE 8: CLEAR ALL FAVORITES
@products_bp.route('/my/favorites/clear', methods=['DELETE'])
@jwt_required()
def clear_all_favorites():
    """
    DELETE /api/products/my/favorites/clear
    Deletes ALL favorite products of the current user.
    """
    try:
        # ✅ ИСПРАВЛЕННО: преобразуй в число
        user_id = int(get_jwt_identity())
        
        # Count how many will be deleted
        count = UserFavorite.query.filter_by(user_id=user_id).count()
        
        # Delete all
        UserFavorite.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Deleted {count} products from favorites',
            'deleted_count': count
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500