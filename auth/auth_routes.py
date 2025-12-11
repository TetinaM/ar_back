from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db, User
from werkzeug.security import generate_password_hash


# Blueprint - это способ организации маршрутов в Flask
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


# МАРШРУТ 1: РЕГИСТРАЦИЯ НОВЫХ ПОЛЬЗОВАТЕЛЕЙ
@auth_bp.route('/register', methods=['POST'])
def register():
    """
    POST /api/auth/register
    
    Получает данные пользователя и создает новый аккаунт
    
    Требует JSON:
    {
        "email": "user@example.com",
        "username": "john_doe",
        "password": "secure_password",
        "full_name": "John Doe"
    }
    """
    try:
        # Получаем данные из JSON запроса
        data = request.get_json()
        
        # Проверяем, что все необходимые поля есть
        if not all(k in data for k in ['email', 'username', 'password']):
            return jsonify({
                'success': False,
                'message': 'Заполните все обязательные поля'
            }), 400
        
        # Проверяем, не существует ли уже пользователь с таким email
        if User.query.filter_by(email=data['email']).first():
            return jsonify({
                'success': False,
                'message': 'Пользователь с таким email уже существует'
            }), 409
        
        # Проверяем username
        if User.query.filter_by(username=data['username']).first():
            return jsonify({
                'success': False,
                'message': 'Это имя пользователя уже занято'
            }), 409
        
        # Создаем нового пользователя
        new_user = User(
            email=data['email'],
            username=data['username'],
            full_name=data.get('full_name', '')
        )
        
        # Устанавливаем пароль (он автоматически шифруется)
        new_user.set_password(data['password'])
        
        # Добавляем в базу данных
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Аккаунт успешно создан',
            'user': new_user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Ошибка при регистрации: {str(e)}'
        }), 500



# МАРШРУТ 2: ВХОД ПОЛЬЗОВАТЕЛЯ
@auth_bp.route('/login', methods=['POST'])
def login():
    """
    POST /api/auth/login
    
    Проверяет учетные данные и возвращает JWT токен
    
    Требует JSON:
    {
        "email": "user@example.com",
        "password": "secure_password"
    }
    """
    try:
        data = request.get_json()
        
        # Проверяем наличие необходимых полей
        if not data.get('email') or not data.get('password'):
            return jsonify({
                'success': False,
                'message': 'Email и пароль обязательны'
            }), 400
        
        # Ищем пользователя по email
        user = User.query.filter_by(email=data['email']).first()
        
        # Если пользователя нет или пароль неправильный
        if not user or not user.check_password(data['password']):
            return jsonify({
                'success': False,
                'message': 'Неправильный email или пароль'
            }), 401
        
        # ✅ ИСПРАВЛЕННО: преобразуй user.id в строку
        access_token = create_access_token(identity=str(user.id))
        
        return jsonify({
            'success': True,
            'message': 'Вход успешен',
            'access_token': access_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при входе: {str(e)}'
        }), 500



# МАРШРУТ 3: ПОЛУЧЕНИЕ ПРОФИЛЯ ТЕКУЩЕГО ПОЛЬЗОВАТЕЛЯ
@auth_bp.route('/profile', methods=['GET'])
@jwt_required()  # Этот маршрут требует валидный токен
def get_profile():
    """
    GET /api/auth/profile
    
    Возвращает информацию о текущем пользователе
    Требует: Header "Authorization: Bearer <token>"
    """
    try:
        # ✅ ИСПРАВЛЕННО: преобразуй в число
        user_id = int(get_jwt_identity())
        
        # Ищем пользователя
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'Пользователь не найден'
            }), 404
        
        return jsonify({
            'success': True,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        }), 500