import os
import platform
from flask import Blueprint, jsonify
from app.utils.security import admin_required

infra_bp = Blueprint('infra', __name__, url_prefix='/api/v1/infra')

# ==========================================
# PUBLIC INFRASTRUCTURE ENDPOINTS
# ==========================================
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


# ==========================================
# RESTRICTED ADMINISTRATIVE ENDPOINTS
# ==========================================
@infra_bp.route('/nodes/status', methods=['GET'])
@admin_required
def node_status():
    """RABBIT HOLE: Returns fake Kubernetes cluster status."""
    return jsonify({
        "cluster_name": "rbd-production-eu-west",
        "nodes": [
            {"name": "worker-node-1", "status": "Ready", "roles": ["worker"]},
            {"name": "worker-node-2", "status": "Ready", "roles": ["worker"]},
            {"name": "control-plane-1", "status": "Ready", "roles": ["master"]}
        ],
        "k8s_version": "v1.27.3"
    }), 200

@infra_bp.route('/logs/system', methods=['GET'])
@admin_required
def system_logs():
    """RABBIT HOLE: Returns static mock logs. Players might try Log4j or LFI here."""
    logs = [
        "[INFO] System boot sequence initiated.",
        f"[INFO] Running on architecture: {platform.machine()}",
        "[WARN] High memory usage detected on worker-node-2.",
        "[INFO] Database connection established successfully.",
        "[DEBUG] Legacy profile sync complete."
    ]
    return jsonify({"logs": logs}), 200

@infra_bp.route('/maintenance/cache/flush', methods=['POST'])
@admin_required
def flush_cache():
    """RABBIT HOLE: A fake cache flush. Does absolutely nothing."""
    return jsonify({
        "status": "success",
        "message": "Redis and local filesystem caches have been marked for eviction."
    }), 200

@infra_bp.route('/maintenance/restart', methods=['POST'])
@admin_required
def trigger_restart():
    """
    THE DEATH TRIGGER: Forces the Pod to commit suicide.
    Only the Admin Bot (hijacked via DOM Clobbering) can hit this.
    """
    print("[SYSTEM] CRITICAL: Administrator initiated maintenance cycle. Terminating Pod...")
    os._exit(1)