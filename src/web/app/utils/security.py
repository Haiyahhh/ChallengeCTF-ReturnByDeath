import jwt
from functools import wraps
from flask import request, jsonify, current_app, redirect

def get_decoded_token():
    """Helper to decode and validate the JWT from cookies."""
    token = request.cookies.get('session_token')
    if not token:
        return None, {"error": "Unauthorized. Please log in."}
        
    try:
        secret = current_app.config.get('SECRET_KEY')
        decoded = jwt.decode(token, secret, algorithms=["HS256"])
        return decoded, None
    except jwt.ExpiredSignatureError:
        return None, {"error": "Session expired."}
    except jwt.InvalidTokenError:
        return None, {"error": "Invalid session token."}

def login_required(f):
    """Requires ANY valid user session."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        decoded, err = get_decoded_token()
        if err:
            return jsonify(err), 401
        return f(*args, **kwargs)
    return decorated_function

def ui_login_required(f):
    """Requires a valid session for HTML pages. Redirects to login if invalid."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        decoded, err = get_decoded_token()
        if err:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Requires specifically the Admin session."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        decoded, err = get_decoded_token()
        if err:
            return jsonify(err), 401
            
        if decoded.get("role") != "admin":
            return jsonify({"error": "Forbidden. Admin privileges required."}), 403
            
        return f(*args, **kwargs)
    return decorated_function