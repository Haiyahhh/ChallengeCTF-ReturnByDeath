import datetime
import jwt
from flask import Blueprint, request, jsonify, make_response, current_app

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')

    # 1. Admin Service Account Intercept
    if username == 'admin' and password == current_app.config.get('ADMIN_PASSWORD'):
        role = "admin"
    else:
        # 2. Standard User Database Verification
        try:
            conn = get_connection()
            result = conn.run("SELECT role FROM users WHERE username = :u AND password = :p", u=username, p=password)
            conn.close()
            
            if not result:
                return jsonify({"error": "Invalid credentials"}), 401
                
            role = result[0][0]
        except Exception:
            return jsonify({"error": "Database error"}), 500

    # 3. Mint JWT (Logic remains the same)
    payload = {
        "username": username,
        "role": role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    token = jwt.encode(payload, current_app.config.get('SECRET_KEY'), algorithm="HS256")
    
    response = make_response(jsonify({"message": f"Welcome, {username}."}))
    response.set_cookie('session_token', token, httponly=True, path='/')
    return response

@auth_bp.route('/register', methods=['POST'])
def register():
    """RABBIT HOLE: Makes the app feel like a real SaaS platform."""
    return jsonify({
        "error": "Not Implemented", 
        "message": "Public registration has been disabled by the system administrator."
    }), 501

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Clears the session token."""
    response = make_response(jsonify({"message": "Logged out successfully."}))
    response.set_cookie('session_token', '', expires=0, path='/')
    return response