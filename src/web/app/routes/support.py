import os
import subprocess
from flask import Blueprint, request, jsonify, current_app, render_template
from app.utils.security import ui_login_required

support_bp = Blueprint('support', __name__)

@support_bp.route('/support', methods=['GET'])
@ui_login_required
def support_page():
    return render_template('support.html')

@support_bp.route('/api/v1/support/telemetry/event', methods=['POST'])
def telemetry():
    return jsonify({"status": "recorded", "message": "Telemetry event logged."}), 200

@support_bp.route('/api/v1/support/ticket', methods=['POST'])
def create_ticket():
    data = request.json or {}
    url = data.get('url')
    
    if not url or not url.startswith('http://localhost:8080/profile/'):
        return jsonify({"error": "Invalid URL. Please provide a local profile link."}), 400
    
    admin_pass = current_app.config.get('ADMIN_PASSWORD')
    bot_env = os.environ.copy()
    bot_env['ADMIN_PASSWORD'] = admin_pass
    
    subprocess.Popen(["python3", "app/utils/bot.py", url], env=bot_env)
    
    return jsonify({"message": "Ticket created successfully. An administrator will review your link shortly."}), 200