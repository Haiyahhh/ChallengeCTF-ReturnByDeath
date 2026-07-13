# CTF Challenge Proposal: Re:Zero (Return by Death)

## 1. Theme

**Concept:** "Return by Death" (Inspired by Re:Zero)

**Core Lesson:** Exploiting DOM Clobbering to hijack headless browsers, winning a TOCTOU race condition against a file-promotion pipeline, understanding Kubernetes Pod lifecycles (specifically container restarts vs. volume persistence), and building a custom PyYAML POP-chain gadget to bypass K8s NetworkPolicies and exfiltrate database secrets.

**Anti-Slop Design:** Punishes standard automated vulnerability scanners and LLM reliance in two distinct ways. First, automated tools will waste time on fake infrastructure rabbit holes (`/api/v1/infra/metrics`, `/nodes/status`, `/logs/system`, `/maintenance/cache/flush`) attempting standard SSRF or command injection. Second, and more importantly, a naive attacker who simply uploads a malicious `profile.yml` will fail outright: the backup-restore pipeline validates every staged file with `yaml.safe_load` before promoting it, which rejects the `!!python/object/apply` tag the exploit needs. Players must recognize that the promotion step re-reads the file from disk instead of reusing the already-validated content — a classic check-then-act gap — and win a race to swap in the malicious payload after validation passes but before promotion runs. Only then does the Pod-restart/deserialization stage even become reachable.

## 2. Exploitation (The Kill Chain)

The player must execute a strict four-step sequence to capture the flag:

- **Step 1: The Setup (Payload Staging):** The player registers a standard user account and uses the "Legacy Profile Migration" tool (`POST /api/v1/users/me/backup/restore`) to upload a `.yml` file. Because the container has a `readOnlyRootFilesystem`, the upload can't be written anywhere durable except `/app/cache`, which is backed by a Kubernetes `emptyDir` volume — but the endpoint only ever writes to a *staging* path (`profile.staging.yml`), never directly to the file the app actually trusts.

- **Step 2: The Race (Validation Bypass):** The player discovers that `GET /api/v1/infra/health` — the Kubernetes readiness probe — is also responsible for promoting a staged backup: it reads `profile.staging.yml`, runs it through `yaml.safe_load` to confirm it's well-formed (which a raw PyYAML gadget payload is not — `safe_load` rejects the `!!python/object/apply` tag), and only if validation passes does it `shutil.copyfile()` the staging path over the live `profile.yml`. Critically, that final copy re-reads the file from disk rather than reusing the content that was actually validated. The player stages a harmless placeholder, then fires a burst of racing requests — holding a `/health` request and a malicious re-upload request each one byte short of complete, then releasing both within microseconds of each other — aiming to land the malicious overwrite inside the gap between validation and promotion. Enough attempts eventually promote the malicious payload without it ever having been validated.

- **Step 3: The Death (Admin Hijack & Suicide):** With the malicious payload now sitting in the trusted `profile.yml` — which is only loaded at process boot via unsafe `yaml.Loader`, not on demand — the player needs the app to reboot. They craft a DOM Clobbering payload (a `<form id="STEWARD_STATUS_CONFIG" action="..." method="POST">`) in their profile bio, which survives the client-side sanitizer because `FORM` is on its tag allow-list. They submit their profile URL to the Support Ticketing system. The Admin Bot (Selenium) visits the page, the clobbered form hijacks the profile's own status-sync `fetch()` call, and the Admin's authenticated browser is forced to send a POST request to the restricted `/api/v1/infra/maintenance/restart` endpoint. The Web Pod commits suicide via `os._exit(1)`.

- **Step 4: The Return (Network Bypass & Exfiltration):** Kubernetes detects the crashed Web container and restarts it. Crucially, the Pod sandbox remains alive, meaning the `/app/cache` volume — and the malicious `profile.yml` promoted in Step 2 — survives the death. During the new container's boot sequence, it blindly deserializes `profile.yml` with `yaml.Loader`. The PyYAML payload instantiates the `DatabaseExporter` Python gadget, executing a raw SQL query over the internal cluster network to bypass the strict Kubernetes NetworkPolicy, dumping the flag from the isolated PostgreSQL Pod to an external webhook.

## 3. Architecture

The challenge is designed as a White/Gray Box, providing the source code and deployment manifests to emphasize logical exploitation over guesswork.

- **Infrastructure:** A Two-Tier Kubernetes cluster (Web Pod + DB Pod) deployable via `Kind` for 100% portability.

- **Container Defenses:** The K8s deployment explicitly uses `securityContext: readOnlyRootFilesystem: true` to prevent standard web shells. Furthermore, a strict `NetworkPolicy` isolates the Database Pod, dropping all traffic that does not originate from the Web Pod to prevent direct port-forwarding bypasses.

- **File Promotion Pipeline:** Uploaded backups never land directly on the file the app trusts. They're staged (`profile.staging.yml`), validated with `yaml.safe_load` on the readiness probe, and only then promoted (`shutil.copyfile`) to the live `profile.yml`. The validate step and the promote step operate on the same path but not the same read, which is what makes the race in Step 2 possible.

- **State Persistence:** The challenge heavily relies on the unique behavior of Kubernetes `emptyDir` volumes, which outlive individual container crashes but are destroyed if the Pod is deleted.

- **Flag Location:** The flag exists entirely outside the Web Pod. It is natively seeded into the `system_secrets` table of the PostgreSQL database, forcing a true network-level exploit.

## 4. Tech Stack

- **Web Framework:** Python with Flask (keeps the codebase lightweight and highly readable).

- **Database:** PostgreSQL (`pg8000` pure-Python driver)

- **Vulnerable Component:** PyYAML (configured to use the unsafe `yaml.Loader` at boot time; the staging path uses `yaml.safe_load` for validation only, which the race condition in Step 2 is designed to bypass).

- **Bot Simulation:** Selenium WebDriver with Headless Chromium.

- **Containerization:** Docker (Split into `web` and `db` images).

- **Orchestration:** Kubernetes manifests (`k8s/db-deployment.yaml`, `k8s/web-deployment.yaml`) wrapped in an automated `build-challenge.sh` script.
