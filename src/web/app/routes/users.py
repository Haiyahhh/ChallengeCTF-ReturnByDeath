import os
from flask import Blueprint, request, jsonify, render_template
from app.utils.security import login_required, ui_login_required

users_bp = Blueprint('users', __name__, template_folder='../templates')

CACHE_DIR = '/app/cache'
CONFIG_FILE = os.path.join(CACHE_DIR, 'profile.yml')

# ==========================================
# FRONTEND ROUTES
# ==========================================
@users_bp.route('/dashboard', methods=['GET'])
@ui_login_required
def dashboard_page():
    return render_template('dashboard.html')

@users_bp.route('/profile/<username>', methods=['GET'])
def view_profile_html(username):
    bio = request.args.get('bio', 'Default enterprise bio...')
    return render_template('profile.html', username=username, bio=bio)

# ==========================================
# API ROUTES
# ==========================================
@users_bp.route('/api/v1/users/<username>', methods=['GET'])
def get_user(username):
    return jsonify({"username": username, "status": "active"})

@users_bp.route('/api/v1/users/me/import-legacy', methods=['POST'])
@login_required
def import_legacy_profile():
    if 'file' not in request.files:
        return jsonify({"error": "No legacy migration file provided."}), 400
        
    file = request.files['file']
    file.save(CONFIG_FILE)
    
    return jsonify({"message": "Legacy profile queued for migration! Changes will apply upon the next system maintenance cycle."}), 200