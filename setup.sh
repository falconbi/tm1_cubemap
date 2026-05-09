#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────────────────
#  TM1 CubeMap — One-command setup
# ──────────────────────────────────────────────────────────

CYAN='\033[0;36m'
GREEN='\033[0;32m'
BOLD='\033[1m'
NC='\033[0m'

info()  { echo -e "${CYAN}◆${NC} $1"; }
ok()    { echo -e "${GREEN}✓${NC} $1"; }
header(){ echo -e "\n${BOLD}$1${NC}\n"; }

# ── Prerequisites ──────────────────────────────────────────

header "TM1 CubeMap Setup"

if ! command -v docker &>/dev/null; then
  echo "Docker is required but not found."
  echo "Install it first: https://docs.docker.com/engine/install/"
  exit 1
fi

# ── Config directory ───────────────────────────────────────

info "This will create servers.json with your TM1 credentials."
info "Files will be stored in: $(pwd)"
echo

# ── servers.json ───────────────────────────────────────────

build_servers_json() {
  local servers=()
  local add_more=true

  while $add_more; do
    echo "─── TM1 Server ───"
    read -rp "  Name (e.g. V11 Production): "  name
    read -rp "  Address (e.g. 192.168.1.179): " addr
    read -rp "  Auth type (v11 / v12): " auth
    read -rp "  Username: " user
    read -rsp "  Password: " pass
    echo

    local dbs=()
    local add_db=true
    while $add_db; do
      echo "  ─── Database ───"
      read -rp "    Database name (e.g. SData): " db_name
      read -rp "    Port (e.g. 8010): " db_port
      dbs+=("{\"name\":\"$db_name\",\"port\":$db_port}")
      read -rp "  Add another database? (y/n): " yn
      [[ "$yn" != "y" ]] && add_db=false
    done

    local db_json=$(IFS=,; echo "${dbs[*]}")
    servers+=("{\"name\":\"$name\",\"address\":\"$addr\",\"auth\":\"$auth\",\"user\":\"$user\",\"password\":\"$pass\",\"databases\":[$db_json]}")
    read -rp "Add another TM1 server? (y/n): " yn
    [[ "$yn" != "y" ]] && add_more=false
  done

  local server_json=$(IFS=,; echo "${servers[*]}")
  echo "[$server_json]" > servers.json
  ok "servers.json created"
}

if [ -f servers.json ]; then
  if [[ "$(wc -c < servers.json)" -gt 10 ]]; then
    read -rp "servers.json already exists. Overwrite? (y/n): " yn
    [[ "$yn" == "y" ]] && build_servers_json
  else
    build_servers_json
  fi
else
  build_servers_json
fi

# ── .env ────────────────────────────────────────────────────

if [ ! -f .env ]; then
  cat > .env <<'EOF'
PORT=8083  # container port; host maps via docker-compose ports

  ok ".env created (PORT=8083)"
else
  info ".env already exists — keeping as-is"
fi

# ── docker-compose.yml ──────────────────────────────────────

if [ ! -f docker-compose.yml ]; then
  info "Downloading docker-compose.yml from GitHub..."
  curl -sSLO https://raw.githubusercontent.com/falconbi/tm1_cubemap/main/docker-compose.yml
  ok "docker-compose.yml downloaded"
else
  info "docker-compose.yml already exists — keeping as-is"
fi

# ── Launch ──────────────────────────────────────────────────

echo
header "Starting TM1 CubeMap..."

docker compose pull
docker compose up -d

echo
ok "CubeMap is running at http://localhost:8084"
info "Open it in your browser and click Refresh from TM1"
echo
