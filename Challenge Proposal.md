# CTF Challenge Proposal: Re:Zero (Return by Death)

## 1. Theme

**Concept:** "Return by Death" (Inspired by Re:Zero)

**Core Lesson:** Exploiting DOM Clobbering to hijack headless browsers, understanding Kubernetes Pod lifecycles (specifically container restarts vs. volume persistence), and building custom POP chains via PyYAML insecure deserialization to bypass K8s NetworkPolicies and exfiltrate database secrets.

**Anti-Slop Design:** Punishes standard automated vulnerability scanners and LLM reliance. Automated tools will attempt standard SSRF or Command Injection on the fake infrastructure rabbit holes. Players must understand that a Kubernetes Pod restart does not destroy `emptyDir` mounted volumes, and they must chain client-side and server-side vulnerabilities to win.

## 2. Exploitation (The Kill Chain)

The player must execute a strict three-step sequence to capture the flag:

- **Step 1: The Setup (Payload Staging):** The player registers a standard user account and uses the "Legacy Profile Migration" tool. They upload a `.yml` file containing a malicious PyYAML payload. Because the container has a `readOnlyRootFilesystem`, the file is saved to `/app/cache`, which is backed by a Kubernetes `emptyDir` volume.
    
- **Step 2: The Death (Admin Hijack & Suicide):** The player realizes the actual vulnerability requires the application to reboot to load the legacy profile. They craft a DOM Clobbering payload in their profile bio and submit their profile URL to the Support Ticketing system. The Admin Bot (Selenium) visits the page, the DOM is clobbered, and the Admin's browser is forced to send a POST request to the restricted `/api/v1/infra/maintenance/restart` endpoint. The Web Pod commits suicide via `os._exit(1)`.
    
- **Step 3: The Return (Network Bypass & Exfiltration):** Kubernetes detects the crashed Web container and restarts it. Crucially, the Pod sandbox remains alive, meaning the `/app/cache` volume survives the death. During the new container's boot sequence, it blindly deserializes the player's saved `profile.yml`. The PyYAML payload instantiates the `DatabaseExporter` Python gadget, executing a raw SQL query over the internal cluster network to bypass the strict Kubernetes NetworkPolicy, dumping the flag from the isolated PostgreSQL Pod to an external webhook.
    

## 3. Architecture

The challenge is designed as a White/Gray Box, providing the source code and deployment manifests to emphasize logical exploitation over guesswork.

- **Infrastructure:** A Two-Tier Kubernetes cluster (Web Pod + DB Pod) deployable via `Kind` for 100% portability.
    
- **Container Defenses:** The K8s deployment explicitly uses `securityContext: readOnlyRootFilesystem: true` to prevent standard web shells. Furthermore, a strict `NetworkPolicy` isolates the Database Pod, dropping all traffic that does not originate from the Web Pod to prevent direct port-forwarding bypasses.
    
- **State Persistence:** The challenge heavily relies on the unique behavior of Kubernetes `emptyDir` volumes, which outlive individual container crashes but are destroyed if the Pod is deleted.
    
- **Flag Location:** The flag exists entirely outside the Web Pod. It is natively seeded into the `system_secrets` table of the PostgreSQL database, forcing a true network-level exploit.
    

## 4. Tech Stack

- **Web Framework:** Python with Flask (keeps the codebase lightweight and highly readable).
    
- **Database:** PostgreSQL (`pg8000` pure-Python driver)
    
- **Vulnerable Component:** PyYAML (configured to use the unsafe `yaml.Loader`).
    
- **Bot Simulation:** Selenium WebDriver with Headless Chromium.
    
- **Containerization:** Docker (Split into `web` and `db` images).
    
- **Orchestration:** Kubernetes manifests (`deployment.yaml`, `service.yaml`, `networkpolicy.yaml`) wrapped in an automated `build-challenge.sh` script.