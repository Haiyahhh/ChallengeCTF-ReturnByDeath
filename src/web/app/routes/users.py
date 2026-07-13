import os
from flask import Blueprint, request, jsonify, render_template
from app.utils.security import login_required, ui_login_required, get_decoded_token
from app.utils.db import get_connection

users_bp = Blueprint('users', __name__, template_folder='../templates')

CACHE_DIR = '/app/cache'
CONFIG_FILE = os.path.join(CACHE_DIR, 'profile.yml')
STAGING_FILE = os.path.join(CACHE_DIR, 'profile.staging.yml')
DEFAULT_BIO = 'This steward has not yet written a bio.'

@users_bp.route('/dashboard', methods=['GET'])
@ui_login_required
def dashboard_page():
    return render_template('dashboard.html')

@users_bp.route('/directory', methods=['GET'])
@ui_login_required
def directory_page():
    return render_template('directory.html')

@users_bp.route('/profile/<username>', methods=['GET'])
def view_profile_html(username):
    try:
        conn = get_connection()
        result = conn.run("SELECT bio FROM users WHERE username = :u", u=username)
        conn.close()
        db_bio = result[0][0] if result and result[0][0] else DEFAULT_BIO
    except Exception:
        db_bio = DEFAULT_BIO

    preview_bio = request.args.get('bio')
    bio = preview_bio if preview_bio is not None else db_bio

    return render_template('profile.html', username=username, bio=bio)

@users_bp.route('/api/v1/users', methods=['GET'])
@login_required
def list_users():
    try:
        conn = get_connection()
        result = conn.run("SELECT username, role FROM users ORDER BY username")
        conn.close()
        staff = [{"username": row[0], "role": row[1]} for row in result]
        return jsonify({"staff": staff}), 200
    except Exception:
        return jsonify({"error": "Directory unavailable."}), 500

@users_bp.route('/api/v1/users/me/bio', methods=['GET'])
@login_required
def get_own_bio():
    decoded, err = get_decoded_token()
    try:
        conn = get_connection()
        result = conn.run("SELECT bio FROM users WHERE username = :u", u=decoded['username'])
        conn.close()
        bio = result[0][0] if result and result[0][0] else ''
        return jsonify({"bio": bio}), 200
    except Exception:
        return jsonify({"bio": ''}), 200

@users_bp.route('/api/v1/users/me/bio', methods=['POST'])
@login_required
def update_bio():
    decoded, err = get_decoded_token()
    data = request.json or {}
    bio = data.get('bio', '')

    try:
        conn = get_connection()
        conn.run("UPDATE users SET bio = :b WHERE username = :u", b=bio, u=decoded['username'])
        conn.close()
        return jsonify({"message": "Profile updated."}), 200
    except Exception:
        return jsonify({"error": "Database error."}), 500

@users_bp.route('/api/v1/users/me/backup/restore', methods=['POST'])
@login_required
def restore_profile_backup():
    if 'file' not in request.files:
        return jsonify({"error": "No backup file provided."}), 400

    file = request.files['file']
    file.save(STAGING_FILE)

    return jsonify({"message": "Backup staged. It will be validated and applied automatically at the next health check cycle."}), 200

@users_bp.route('/api/v1/users/<username>/export', methods=['GET'])
@login_required
def export_profile(username):
    try:
        conn = get_connection()
        result = conn.run(
            "SELECT username, role, bio, internal_notes FROM users WHERE username = :u",
            u=username
        )
        conn.close()
        if not result:
            return jsonify({"error": "User not found."}), 404
        row = result[0]
        return jsonify({
            "username": row[0],
            "role": row[1],
            "bio": row[2],
            "internal_notes": row[3]
        }), 200
    except Exception:
        return jsonify({"error": "Export failed."}), 500
