import datetime
import jwt
from flask import Blueprint, request, jsonify, make_response, current_app, render_template, redirect
from app.utils.db import get_connection
from app.utils.security import get_decoded_token

auth_bp = Blueprint('auth', __name__, template_folder='../templates')

# ==========================================
# FRONTEND ROUTES
# ==========================================
@auth_bp.route('/login', methods=['GET'])
def login_page():
    """Renders login. Redirects to dashboard if already authenticated."""
    decoded, err = get_decoded_token()
    if not err:
        return redirect('/dashboard')
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET'])
def register_page():
    return render_template('register.html')

# ==========================================
# API ROUTES
# ==========================================
@auth_bp.route('/api/v1/auth/register', methods=['POST'])
def register():
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"error": "Username and password required."}), 400
        
    try:
        conn = get_connection()
        conn.run("INSERT INTO users (username, password) VALUES (:u, :p)", u=username, p=password)
        conn.close()
        return jsonify({"message": "Registration successful. You may now log in."}), 201
    except Exception:
        return jsonify({"error": "Username already exists or database error."}), 400

@auth_bp.route('/api/v1/auth/login', methods=['POST'])
def login():
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')

    if username == 'admin' and password == current_app.config.get('ADMIN_PASSWORD'):
        role = "admin"
    else:
        try:
            conn = get_connection()
            result = conn.run("SELECT role FROM users WHERE username = :u AND password = :p", u=username, p=password)
            conn.close()
            
            if not result:
                return jsonify({"error": "Invalid credentials"}), 401
            role = result[0][0]
        except Exception:
            return jsonify({"error": "Database error"}), 500

    payload = {
        "username": username,
        "role": role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    token = jwt.encode(payload, current_app.config.get('SECRET_KEY'), algorithm="HS256")
    
    response = make_response(jsonify({"message": f"Welcome, {username}."}))
    response.set_cookie('session_token', token, httponly=True, path='/')
    return response

@auth_bp.route('/api/v1/auth/logout', methods=['POST'])
def logout():
    response = make_response(jsonify({"message": "Logged out successfully."}))
    response.set_cookie('session_token', '', expires=0, path='/')
    return response