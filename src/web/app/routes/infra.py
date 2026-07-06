import os
from flask import Blueprint, jsonify
from app.utils.security import admin_required

infra_bp = Blueprint('infra', __name__, url_prefix='/api/v1/infra')

@infra_bp.route('/health', methods=['GET'])
def health_check():
    """Standard Kubernetes readiness probe endpoint."""
    return jsonify({"status": "healthy", "uptime": "ok"}), 200

@infra_bp.route('/metrics', methods=['GET'])
def get_metrics():
    """
    RABBIT HOLE: Fake Prometheus metrics. 
    Players might waste time trying to exploit SSRF or command injection here.
    """
    return """
    # HELP process_virtual_memory_bytes Virtual memory size in bytes.
    # TYPE process_virtual_memory_bytes gauge
    process_virtual_memory_bytes 3.48315648e+08
    # HELP process_cpu_seconds_total Total user and system CPU time spent in seconds.
    # TYPE process_cpu_seconds_total counter
    process_cpu_seconds_total 12.34
    """, 200, {'Content-Type': 'text/plain; version=0.0.4'}

@infra_bp.route('/maintenance/restart', methods=['POST'])
@admin_required
def trigger_restart():
    """
    THE DEATH TRIGGER: Forces the Pod to commit suicide.
    Only the Admin Bot (hijacked via CSRF) can hit this.
    """
    print("[SYSTEM] CRITICAL: Administrator initiated maintenance cycle. Terminating Pod...")
    os._exit(1)