import os
import yaml
import secrets
from flask import Flask

# Import the blueprint
from app.routes.auth import auth_bp
from app.routes.users import users_bp
from app.routes.infra import infra_bp
from app.routes.support import support_bp

app = Flask(__name__, template_folder='../templates')

# ==========================================
# SYSTEM CONFIGURATION & SECRETS
# ==========================================
app.config['ADMIN_PASSWORD'] = os.environ.get('ADMIN_PASSWORD') or secrets.token_hex(16)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

CACHE_DIR = '/app/cache'
CONFIG_FILE = os.path.join(CACHE_DIR, 'profile.yml')

# ==========================================
# INITIALIZATION SEQUENCE
# ==========================================
print("[SYSTEM] Commencing startup initialization...")
print("[SYSTEM] Secrets initialized. (Admin Auth active)")

if os.path.exists(CONFIG_FILE):
    try:
        print("[SYSTEM] Loading cached legacy profile configuration...")
        with open(CONFIG_FILE, 'r') as f:
            yaml.load(f, Loader=yaml.Loader)
    except Exception as e:
        print(f"[SYSTEM] Profile load warning: {e}")

# ==========================================
# BLUEPRINT REGISTRATION
# ==========================================
app.register_blueprint(auth_bp)
app.register_blueprint(users_bp)
app.register_blueprint(infra_bp)
app.register_blueprint(support_bp)

# We will register the others as we build them:
# app.register_blueprint(users_bp)
# app.register_blueprint(infra_bp)
# app.register_blueprint(support_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)