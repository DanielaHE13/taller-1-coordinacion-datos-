#!/usr/bin/env bash
# Genera SOLO archivos locales del proyecto. No cambia SSH, Tailscale ni nodos.json.
set -euo pipefail
umask 077
cd "$(dirname "$0")/.."
[[ "$#" == 1 && "$1" =~ ^[1-3]$ ]] || { echo "Uso: bash scripts/preparar_inventario.sh ID"; exit 2; }
export NODO_ID="$1"
if [[ -f .env ]]; then
  source .env
else
  read -rsp "Token compartido de la API: " TALLER_TOKEN; echo
  read -rsp "Clave compartida de Redis (hexadecimal): " REDIS_PASSWORD; echo
  export TALLER_TOKEN REDIS_PASSWORD
fi
python3 - <<'PY'
import ipaddress, json, os, re, shlex
from pathlib import Path
root = Path.cwd()
node = os.environ["NODO_ID"]
config = json.loads((root/"coordinador/nodos.json").read_text(encoding="utf-8-sig"))
ip = config[node]["host"]
ipaddress.IPv4Address(ip)
token = os.environ.get("TALLER_TOKEN", "")
password = os.environ.get("REDIS_PASSWORD", "")
if len(token) < 16:
    raise SystemExit("Token demasiado corto: generar un token compartido de 64 caracteres hexadecimales")
if not re.fullmatch(r"[0-9a-fA-F]{32,}", password):
    raise SystemExit("La clave Redis debe ser hexadecimal y tener al menos 32 caracteres")
env = root/".env"
if not env.exists():
    env.write_text("export TALLER_TOKEN="+shlex.quote(token)+"\nexport REDIS_PASSWORD="+shlex.quote(password)+"\n",
                   encoding="utf-8")
env.chmod(0o600)
folder = root/"datos/redis"
folder.mkdir(parents=True, exist_ok=True)
(root/"logs").mkdir(exist_ok=True)
(root/"evidencias").mkdir(exist_ok=True)
port = int(config[node].get("redis_puerto", 6379))
text = f"""bind 127.0.0.1 {ip}
protected-mode yes
port {port}
daemonize yes
pidfile {json.dumps(str(folder/"redis.pid"))}
logfile {json.dumps(str(folder/"redis.log"))}
dir {json.dumps(str(folder))}
appendonly yes
appendfsync everysec
requirepass {password}
masterauth {password}
replica-read-only yes
replica-serve-stale-data yes
repl-diskless-sync-delay 0
min-replicas-to-write 0
"""
target = root/"config/redis.local.conf"
if target.exists():
    print("Se conserva config/redis.local.conf; revisar que corresponda a este nodo.")
else:
    target.write_text(text, encoding="utf-8")
    target.chmod(0o600)
print(f"Nodo {node}: archivos locales preparados. Se conservaron las IP y el puerto HTTP.")
PY
