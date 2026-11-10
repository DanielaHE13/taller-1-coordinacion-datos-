"""Cliente del inventario; usa coordinador/nodos.json y el puerto existente."""
import argparse
import json
import os
import uuid
from urllib.error import HTTPError
from urllib.request import Request, build_opener, ProxyHandler
from coordinador.motor import configuracion_compatible


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--nodo", type=int, required=True)
    p.add_argument("--local", action="store_true", help="Usar localhost en el nodo aislado")
    p.add_argument("accion", choices=["estado", "inventario", "conflictos", "inicializar", "asignar"])
    p.add_argument("--recurso")
    p.add_argument("--cpu", type=int, default=0)
    p.add_argument("--memoria", type=int, default=0)
    p.add_argument("--ancho-banda", type=int, default=0)
    p.add_argument("--request-id")
    args = p.parse_args()
    config = configuracion_compatible(args.nodo)
    peer = config["nodes"][str(args.nodo)]
    host = "127.0.0.1" if args.local else peer["host"]
    token = os.environ.get("TALLER_TOKEN", "")
    if args.accion != "estado" and len(token) < 16:
        p.error("Cargar primero: source .env")
    opener = build_opener(ProxyHandler({}))

    def call(route, payload=None):
        req = Request(f"http://{host}:{peer['port']}/{route}",
                      data=None if payload is None else json.dumps(payload).encode(),
                      headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
        try:
            with opener.open(req, timeout=10) as response:
                result = json.load(response)
        except HTTPError as exc:
            print(exc.code, exc.read().decode(), flush=True)
            raise SystemExit(1)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return result

    if args.accion == "inicializar":
        recursos = [args.recurso] if args.recurso else ["node" + k for k in config["nodes"]]
        for recurso in recursos:
            call("inicializar", {"request_id": str(uuid.uuid4()), "request": {"resource": recurso}})
    elif args.accion == "asignar":
        request_id = args.request_id or str(uuid.uuid4())
        print("request_id=" + request_id, flush=True)
        call("asignar", {"request_id": request_id, "request": {
            "resource": args.recurso or "node1",
            "amounts": {"cpu": args.cpu, "memory_mb": args.memoria,
                        "bandwidth_mbps": args.ancho_banda}}})
    else:
        call(args.accion)


if __name__ == "__main__":
    main()
