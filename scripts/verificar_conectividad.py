"""E3 con los usuarios reales del grupo y sin modificar SSH ni Tailscale."""
from datetime import datetime, timezone
import ipaddress
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
USUARIOS = {"1": "taller", "2": "daniela", "3": "taller"}


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in USUARIOS:
        raise SystemExit("Uso: python3 scripts/verificar_conectividad.py ID_ORIGEN")
    origin = sys.argv[1]
    nodes = json.loads((ROOT/"coordinador/nodos.json").read_text(encoding="utf-8-sig"))
    lines = [f"E3 | origen=nodo{origin} | {datetime.now(timezone.utc).isoformat()}\n"]
    failed = False
    for key, peer in nodes.items():
        if key == origin:
            continue
        ipaddress.IPv4Address(peer["host"])
        for command in [
            ["ping", "-c", "4", "-W", "2", peer["host"]],
            ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
             "-o", "PasswordAuthentication=no", "-o", "KbdInteractiveAuthentication=no",
             "-o", "ConnectTimeout=5", USUARIOS[key]+"@"+peer["host"], "hostname; date -Is"],
        ]:
            lines.append("\n$ "+" ".join(command)+"\n")
            try:
                process = subprocess.run(command, capture_output=True, text=True, timeout=25)
                lines.append(process.stdout+process.stderr)
                failed = failed or process.returncode != 0
            except Exception as exc:
                failed = True
                lines.append(str(exc)+"\n")
    lines.append("\nRESULTADO: "+("REVISAR ERRORES" if failed else "CORRECTO")+"\n")
    path = ROOT/"evidencias"/("E3_nodo"+origin+"_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")+".log")
    path.parent.mkdir(exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")
    print("".join(lines))
    print(path)
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
