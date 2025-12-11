from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from models import db, User, Product
from auth.auth_routes import auth_bp
from products.product_routes import products_bp
import os
import ssl

# Create Flask app
app = Flask(__name__)

# Load configuration
app.config.from_object(Config)

# Initialize database
db.init_app(app)

# Initialize JWT
jwt = JWTManager(app)

# Initialize CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(products_bp)

# Create tables on startup
with app.app_context():
    db.create_all()

# ✅ ROUTE: Health check
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'OK',
        'message': 'Backend is running!'
    }), 200

# ✅ ROUTE: Get all categories
@app.route('/api/categories', methods=['GET'])
def get_categories():
    try:
        categories = db.session.query(Product.category).distinct().filter(
            Product.category != None
        ).all()
        category_list = sorted([cat[0] for cat in categories if cat[0]])
        
        return jsonify({
            'success': True,
            'categories': category_list
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

# ✅ DYNAMIC SERVING OF 3D MODELS
@app.route('/models/<filename>')
def serve_model(filename):
    """Dynamically returns 3D models with CORS."""
    try:
        models_path = os.path.join(os.getcwd(), 'static', 'models')
        
        # Check that file exists
        if not os.path.exists(os.path.join(models_path, filename)):
            return jsonify({
                'success': False,
                'message': f'Model {filename} not found'
            }), 404
        
        response = send_from_directory(models_path, filename)
        # Add CORS headers
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error loading model: {str(e)}'
        }), 500

# ✅ DYNAMIC SERVING OF IMAGES
@app.route('/images/<filename>')
def serve_image(filename):
    """Dynamically returns product images with CORS."""
    try:
        images_path = os.path.join(os.getcwd(), 'static', 'images')
        
        # Check that file exists
        if not os.path.exists(os.path.join(images_path, filename)):
            return jsonify({
                'success': False,
                'message': f'Image {filename} not found'
            }), 404
        
        response = send_from_directory(images_path, filename)
        # Add CORS headers
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error loading image: {str(e)}'
        }), 500

# 404 error handler
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': 'Route not found'
    }), 404

# 500 error handler
@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'message': 'Internal server error'
    }), 500

if __name__ == '__main__':
    # For development use this:
    # app.run(host='0.0.0.0', port=5000, debug=True)
    
    # For production with SSL
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(
        './certs/192.168.137.1.pem',
        './certs/192.168.137.1-key.pem'
    )
    app.run(
        host='192.168.137.1',
        port=5000,
        ssl_context=ssl_context,
        debug=True
    )
