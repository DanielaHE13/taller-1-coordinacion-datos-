"""Captura datos reales de Redis a través del servicio y escribe JSON y CSV."""
import argparse
import csv
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from urllib.request import Request, build_opener, ProxyHandler

ROOT = Path(__file__).resolve().parents[1]


def verificar_convergencia(result, total_nodos, conflictos_minimos=0):
    """Compara la evidencia leída de los Redis reales y del coordinador."""
    try:
        rows = result["nodos"]
        samples = list(rows.values())
        leaders = {s["estado"]["lider"] for s in samples}
        if len(samples) != total_nodos or len(leaders) != 1 or None in leaders:
            return False
        leader = next(iter(leaders))
        masters = [int(key) for key, s in rows.items()
                   if s["inventario"]["backend"]["role"] == "master"]
        replicas = [s for s in samples if s["inventario"]["backend"]["role"] == "slave"]
        return (
            masters == [leader] and len(replicas) == total_nodos - 1
            and all(s["inventario"]["source"] == "local_redis" for s in samples)
            and all(s["estado"]["rol"] == ("líder" if int(key) == leader else "seguidor")
                    for key, s in rows.items())
            and len({s["estado"]["epoca"] for s in samples}) == 1
            and all(s["inventario"]["backend"].get("master_link_status") == "up"
                    for s in replicas)
            and len({s["inventario"]["inventory_hash"] for s in samples}) == 1
            and len({s["estado"]["journal_hash"] for s in samples}) == 1
            and len({s["estado"]["conflictos_detectados"] for s in samples}) == 1
            and all(s["estado"]["conflictos_detectados"] >= conflictos_minimos
                    and s["estado"]["conflictos_detectados"] == s["estado"]["conflictos_resueltos"]
                    for s in samples)
        )
    except (KeyError, TypeError, ValueError):
        return False


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--fase", required=True)
    p.add_argument("--nodo", type=int, help="Capturar solo este nodo")
    p.add_argument("--local", action="store_true", help="Usar con --nodo en el aislado")
    p.add_argument("--verificar", action="store_true", help="Exigir convergencia de los tres nodos")
    p.add_argument("--conflictos-minimos", type=int, default=0,
                   help="Con --verificar, exigir al menos este número de conflictos")
    args = p.parse_args()
    if args.conflictos_minimos < 0:
        p.error("--conflictos-minimos no puede ser negativo")
    if args.local and args.nodo is None:
        p.error("--local requiere --nodo")
    nodos = json.loads((ROOT/"coordinador/nodos.json").read_text(encoding="utf-8-sig"))
    opener = build_opener(ProxyHandler({}))
    result = {"fase": args.fase, "hora_utc": datetime.now(timezone.utc).isoformat(), "nodos": {}}
    for key, peer in nodos.items():
        if args.nodo is not None and key != str(args.nodo):
            continue
        sample = {}
        for route in ("estado", "inventario", "conflictos"):
            host = "127.0.0.1" if args.local else peer["host"]
            req = Request(f"http://{host}:{peer['puerto']}/{route}",
                          headers={"Authorization": "Bearer " + os.environ.get("TALLER_TOKEN", "")})
            try:
                with opener.open(req, timeout=4) as response:
                    sample[route] = json.load(response)
            except Exception as exc:
                sample[route] = {"error": str(exc)}
        result["nodos"][key] = sample
    folder = ROOT/"evidencias"
    folder.mkdir(exist_ok=True)
    safe_phase = "".join(c for c in args.fase if c.isalnum() or c in "_-") or "captura"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%f")
    name = folder/(safe_phase+"_"+stamp)
    name.with_suffix(".json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    fields = ["fase", "nodo", "rol", "lider", "epoca", "recurso", "cpu", "memory_mb", "bandwidth_mbps",
              "vector", "inventory_hash", "journal_hash", "conflictos_detectados", "conflictos_resueltos"]
    with name.with_suffix(".csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for key, sample in result["nodos"].items():
            state, inventory = sample["estado"], sample["inventario"]
            for resource, view in inventory.get("inventory", {"inaccesible": {}}).items():
                writer.writerow({"fase": args.fase, "nodo": key, "rol": state.get("rol", "sin respuesta"),
                    "lider": state.get("lider"), "epoca": state.get("epoca"), "recurso": resource,
                    **{k: view.get("available", {}).get(k) for k in ("cpu", "memory_mb", "bandwidth_mbps")},
                    "vector": json.dumps(view.get("context", {}), sort_keys=True),
                    "inventory_hash": inventory.get("inventory_hash"), "journal_hash": state.get("journal_hash"),
                    "conflictos_detectados": state.get("conflictos_detectados"),
                    "conflictos_resueltos": state.get("conflictos_resueltos")})
    print(str(name.with_suffix(".json")))
    print(str(name.with_suffix(".csv")))
    if args.verificar:
        good = verificar_convergencia(result, len(nodos), args.conflictos_minimos)
        print("CONVERGENCIA VERIFICADA" if good else "TODAVIA NO CONVERGE: revisar captura y repetir")
        raise SystemExit(0 if good else 1)


if __name__ == "__main__":
    main()
