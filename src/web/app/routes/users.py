import os
from flask import Blueprint, request, jsonify, render_template
from app.utils.security import login_required

users_bp = Blueprint('users', __name__, template_folder='../templates')

CACHE_DIR = '/app/cache'
CONFIG_FILE = os.path.join(CACHE_DIR, 'profile.yml')

# ==========================================
# REST API ENDPOINTS
# ==========================================
@users_bp.route('/api/v1/users/<username>', methods=['GET'])
def get_user(username):
    """Public profile data fetch."""
    return jsonify({"username": username, "status": "active"})

@users_bp.route('/api/v1/users/me/update', methods=['PUT'])
@login_required
def update_profile():
    """Requires standard user authentication."""
    return jsonify({"message": "Profile updated successfully."}), 200

@users_bp.route('/api/v1/users/me/import-legacy', methods=['POST'])
@login_required
def import_legacy_profile():
    """
    THE SAVE POINT: Requires standard user authentication.
    The attacker must log in as 'guest' to access this tool.
    """
    if 'file' not in request.files:
        return jsonify({"error": "No legacy migration file provided."}), 400
        
    file = request.files['file']
    file.save(CONFIG_FILE)
    
    return jsonify({
        "message": "Legacy profile queued for migration! Changes will apply upon the next system maintenance cycle."
    }), 200

# ==========================================
# FRONTEND WEB ROUTE
# ==========================================
@users_bp.route('/u/<username>', methods=['GET'])
def view_profile_html(username):
    """Public profile rendering endpoint."""
    bio = request.args.get('bio', 'Default enterprise bio...')
    return render_template('profile.html', username=username, bio=bio)