import os
import subprocess
from flask import Blueprint, request, jsonify, current_app

support_bp = Blueprint('support', __name__)

@support_bp.route('/api/v1/telemetry/event', methods=['POST'])
def telemetry():
    """
    THE BENIGN ENDPOINT: The template's fallback analytics tracker hits this.
    It returns 200 OK so the player's browser console doesn't show any 404 errors.
    """
    return jsonify({"status": "recorded", "message": "Telemetry event logged."}), 200

@support_bp.route('/api/v1/support/ticket', methods=['POST'])
def create_ticket():
    """
    THE BOT TRIGGER: Disguised as a support ticket submission.
    """
    data = request.json or {}
    url = data.get('url')
    
    # We allow the bot to visit the new profile view URL
    if not url or not url.startswith('http://localhost:8080/u/'):
        return jsonify({"error": "Invalid URL. Please provide a local profile link."}), 400
    
    # Grab the dynamic password from the Flask app context
    admin_pass = current_app.config.get('ADMIN_PASSWORD')
    
    # Copy environment and inject the password so the bot can log in
    bot_env = os.environ.copy()
    bot_env['ADMIN_PASSWORD'] = admin_pass
    
    # Fire and forget the headless Chrome process
    subprocess.Popen(["python3", "app/utils/bot.py", url], env=bot_env)
    
    return jsonify({
        "message": "Ticket created successfully. An administrator will review your link shortly."
    }), 200