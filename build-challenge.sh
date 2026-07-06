#!/bin/bash
set -e

CLUSTER_NAME="rbd-ctf"
WEB_IMAGE="return-by-death-web:latest"
DB_IMAGE="return-by-death-db:latest"

echo "[*] Initializing 'Return By Death' Environment..."

# 1. THE CACHE: Docker automatically leverages layer caching here.
echo "[+] 1/5 Building Docker images..."
docker build -t $DB_IMAGE ./src/db
docker build -t $WEB_IMAGE ./src/web

# 2. CLUSTER CHECK: Skips the heavy lifting if the environment is already up.
if ! kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
    echo "[+] 2/5 Creating isolated Kind cluster (First run only)..."
    kind create cluster --name $CLUSTER_NAME
else
    echo "[+] 2/5 Cluster already exists. Bypassing creation..."
fi

# 3. SIDELOAD: Pushes the newly built images directly into the K8s node's registry.
echo "[+] 3/5 Loading updated images into cluster..."
kind load docker-image $DB_IMAGE --name $CLUSTER_NAME
kind load docker-image $WEB_IMAGE --name $CLUSTER_NAME

# 4. THE RESTART BUTTON: Applies changes and forces K8s to cycle the pods.
echo "[+] 4/5 Applying K8s manifests..."
kubectl apply -f ./k8s/

echo "[+] Forcing deployment restarts to apply any codebase changes..."
kubectl rollout restart deployment postgres-db
kubectl rollout restart deployment return-by-death

echo "[+] Waiting for the new containers to spin up..."
# rollout status is smarter than 'wait'; it specifically waits for the new pod replacing the old one
kubectl rollout status deployment postgres-db --timeout=90s
kubectl rollout status deployment return-by-death --timeout=90s

# 5. THE LOG STREAM & ROUTING
echo ""
echo "[*] Environment is LIVE!"
echo "[*] Web application accessible at: http://localhost:8080"
echo "[*] Tailing live internal logs. Press [Ctrl+C] to stop and detach."
echo "------------------------------------------------------------------"

# Start port-forwarding in the background so we can use the foreground for logs
kubectl port-forward svc/rbd-service 8080:8080 > /dev/null 2>&1 &
PORT_FORWARD_PID=$!

# Trap Ctrl+C (SIGINT) to clean up the port-forwarding gracefully when the user exits the logs
trap "kill $PORT_FORWARD_PID 2>/dev/null; echo -e '\n[*] Detached from logs. Port-forward stopped.'; exit 0" SIGINT

# Follow the logs of the newly spun-up web container
LATEST_POD=$(kubectl get pods -l app=rbd-web --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.name}')

echo "[*] Attaching specifically to new pod: $LATEST_POD"

# Stream logs exclusively from the new pod
kubectl logs -f $LATEST_POD --all-containers=true