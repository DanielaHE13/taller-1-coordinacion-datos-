"""Bully con épocas persistentes, latidos y reconciliación de bitácoras.

Modelo de fallas: procesos confiables que pueden caer o quedar aislados.
Los comprobantes verificables por RPC impiden un anuncio sin elección
registrada. No constituyen consenso por quórum ni tolerancia bizantina.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import threading
import time
from urllib.error import HTTPError
from urllib.request import Request, build_opener, ProxyHandler
import uuid

from .redis_inventario import RedisBackend
from .bitacora import Journal
from .versiones import canonical


class Rejected(Exception):
    def __init__(self, status, reason):
        self.status, self.reason = status, reason
        super().__init__(reason)


class Node:
    def __init__(self, config, token, backend):
        if len(token) < 16:
            raise ValueError("TALLER_TOKEN debe tener al menos 16 caracteres")
        self.config, self.token, self.backend = config, token, backend
        self.id = int(config["node_id"])
        self.nodes = {int(k): v for k, v in config["nodes"].items()}
        if self.id not in self.nodes or len(self.nodes) < 3:
            raise ValueError("Configurar al menos tres nodos con IDs únicos")
        self.lock, self.election_lock = threading.RLock(), threading.Lock()
        self.journal = Journal(config["data_dir"])
        self.epoch = self.journal.get("epoch", 0)
        self.lamport = max(self.journal.get("lamport", 0),
                           max((o["lamport"] for o in self.journal.ops.values()), default=0))
        self.proof = self.journal.get("accepted_proof")
        self.primera_ejecucion = self.proof is None
        self.issued = self.journal.get("issued_proofs", {})
        self.verified = dict(self.issued)
        self.role, self.leader = "follower", None
        self.last_heartbeat = time.monotonic()
        self.stop = threading.Event()
        self.blocked = set()  # Inyección de fallas usada SOLO por tests.
        self.opener = build_opener(ProxyHandler({}))
        self.logfile = Path(config["data_dir"]) / "events.jsonl"
        self.server = None
        self.worker = None
        self.event("started", recovered_operations=len(self.journal.ops))

    def event(self, event, **fields):
        record = {"time": datetime.now(timezone.utc).isoformat(),
                  "node": self.id, "event": event, **fields}
        line = canonical(record)
        with self.lock:
            with self.logfile.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
        print(line, flush=True)

    def rpc(self, node, path, body=None):
        if node in self.blocked:
            raise OSError("Partición simulada")
        peer = self.nodes[node]
        request = Request(f"http://{peer['host']}:{peer['port']}{path}",
                          data=None if body is None else canonical(body).encode(),
                          headers={"Authorization": "Bearer " + self.token,
                                   "Content-Type": "application/json",
                                   "X-Node-ID": str(self.id)})
        with self.opener.open(request, timeout=self.config.get("rpc_timeout", 0.7)) as r:
            return json.load(r)

    @staticmethod
    def rank(proof):
        return (proof["epoch"], proof["winner"]) if proof else (0, 0)

    def observe_epoch(self, epoch):
        if type(epoch) is not int or epoch < 0:
            raise Rejected(400, "Época inválida")
        with self.lock:
            if epoch > self.epoch:
                self.epoch = epoch
                self.journal.set("epoch", epoch)

    def validate_proof(self, proof):
        if not isinstance(proof, dict):
            raise Rejected(403, "Anuncio sin comprobante de elección")
        try:
            winner, members, higher = proof["winner"], proof["members"], proof["higher_probes"]
            valid = (type(winner) is int and winner in self.nodes and
                     type(proof["epoch"]) is int and proof["epoch"] > 0 and
                     isinstance(members, list) and winner in members and
                     all(type(x) is int and x in self.nodes for x in members) and
                     max(members) == winner and
                     higher == {str(x): "unreachable" for x in self.nodes if x > winner})
            uuid.UUID(proof["id"])
            if not valid:
                raise ValueError()
        except (KeyError, TypeError, ValueError):
            raise Rejected(403, "Comprobante inválido o ganador distinto del mayor ID")
        with self.lock:
            if proof["id"] in self.verified:
                if self.verified[proof["id"]] != proof:
                    raise Rejected(403, "Comprobante registrado modificado")
                return
        # Un anuncio no crea esta evidencia. Solo el algoritmo de elección
        # registra y publica el comprobante en el nodo ganador.
        try:
            registered = self.rpc(winner, "/proof/" + proof["id"])
        except Exception:
            raise Rejected(403, "El ganador no pudo acreditar su elección")
        if registered != proof:
            raise Rejected(403, "El ganador no reconoce el comprobante")
        with self.lock:
            self.verified[proof["id"]] = dict(proof)

    def adopt(self, proof, source=None):
        self.validate_proof(proof)
        changed = False
        with self.lock:
            if self.primera_ejecucion and proof["winner"] < self.id:
                self.observe_epoch(proof["epoch"])
                raise Rejected(409, "Un nodo nuevo de mayor ID debe participar en la elección")
            if self.rank(proof) < self.rank(self.proof):
                raise Rejected(409, "Anuncio de una elección anterior")
            if self.rank(proof) == self.rank(self.proof) and self.proof != proof:
                raise Rejected(409, "Comprobantes incompatibles para la misma época")
            if self.proof != proof or self.leader is None:
                previous = self.leader
                self.proof, self.leader = proof, proof["winner"]
                self.primera_ejecucion = False
                self.role = "leader" if self.leader == self.id else "follower"
                self.journal.set("accepted_proof", proof)
                self.last_heartbeat = time.monotonic()
                changed = True
            self.observe_epoch(proof["epoch"])
            if source == self.leader:
                self.last_heartbeat = time.monotonic()
        if changed:
            self.event("leader_adopted", previous=previous, leader=self.leader,
                       epoch=proof["epoch"], role=self.role)

    def start_election(self):
        if not self.election_lock.acquire(blocking=False):
            return
        threading.Thread(target=self._election, daemon=True).start()

    def _election(self):
        try:
            with self.lock:
                self.role, self.leader = "candidate", None
                self.observe_epoch(self.epoch + 1)
                term = self.epoch
                self.last_heartbeat = time.monotonic()
            self.event("election_started", epoch=term)
            answered = []
            for peer in sorted(x for x in self.nodes if x > self.id):
                try:
                    response = self.rpc(peer, "/election", {"candidate": self.id, "epoch": term})
                    self.observe_epoch(response["epoch"])
                    answered.append(peer)
                except Exception:
                    pass
            if answered:
                self.event("higher_nodes_answered", nodes=answered)
                self.stop.wait(self.config.get("election_wait", 3))
                return
            members = [self.id]
            for peer in sorted(x for x in self.nodes if x < self.id):
                try:
                    state = self.rpc(peer, "/state")
                    self.observe_epoch(state["epoch"])
                    self.merge(state["operations"])
                    members.append(peer)
                except Exception:
                    pass
            with self.lock:
                # Si se adoptó un líder mientras se consultaban los pares,
                # no publicar una candidatura que ya quedó cancelada.
                if self.role != "candidate":
                    return
                self.observe_epoch(self.epoch + 1)
                proof = {"id": str(uuid.uuid4()), "epoch": self.epoch,
                         "winner": self.id, "members": sorted(members),
                         "higher_probes": {str(x): "unreachable" for x in self.nodes if x > self.id}}
                self.issued[proof["id"]] = proof
                self.verified[proof["id"]] = dict(proof)
                self.journal.set("issued_proofs", self.issued)
            self.adopt(proof, self.id)
            self.configure_backend()
            self.event("election_won", proof=proof)
            self.broadcast_heartbeat()
        except Exception as exc:
            self.event("election_error", reason=str(exc))
        finally:
            self.election_lock.release()

    def check_operation(self, op):
        try:
            uuid.UUID(op["id"])
            origin = op["origin"]
            if type(origin) is not int or origin not in self.nodes:
                raise ValueError()
            if op["resource"] not in {"node" + str(x) for x in self.nodes}:
                raise ValueError()
            if type(op["lamport"]) is not int or op["lamport"] < 1:
                raise ValueError()
            if (not isinstance(op["vv"], dict) or
                    set(op["vv"]) != {str(x) for x in self.nodes} or
                    any(type(v) is not int or v < 0 for v in op["vv"].values()) or
                    op["vv"][str(origin)] < 1):
                raise ValueError()
            if set(op["value"]) != set(self.config["capacity"]):
                raise ValueError()
            for key, value in op["value"].items():
                if type(value) is not int or not 0 <= value <= self.config["capacity"][key]:
                    raise ValueError()
        except (KeyError, TypeError, ValueError, AttributeError):
            raise Rejected(400, "Operación inválida")

    def merge(self, operations):
        if not isinstance(operations, list) or len(operations) > 10000:
            raise Rejected(400, "Lote inválido o demasiado grande")
        for op in operations:
            self.check_operation(op)
        with self.lock:
            new, conflicts = self.journal.add(operations)
            if new:
                self.lamport = max(self.lamport, max(o["lamport"] for o in new)) + 1
                self.journal.set("lamport", self.lamport)
            # En Redis real SOLO escribe el líder; los seguidores leen su réplica.
            if new and (self.role == "leader" or getattr(self.backend, "is_memory", False)):
                self.backend.write(self.journal.views)
        for conflict in conflicts:
            self.event("conflict_resolved", conflict=conflict)
        return len(new)

    def configure_backend(self):
        with self.lock:
            role, leader = self.role, self.leader
            if role == "leader":
                self.backend.promote()
                self.backend.write(self.journal.views)
                return
            operations = list(self.journal.ops.values())
        if leader is not None:
            # Primero entregar la historia. REPLICAOF puede borrar la rama local.
            self.rpc(leader, "/sync", {"operations": operations})
            peer = self.nodes[leader]
            with self.lock:
                if self.role == "follower" and self.leader == leader:
                    self.backend.follow(peer["host"], peer.get("redis_port", 6379))

    def broadcast_heartbeat(self):
        with self.lock:
            proof = self.proof if self.role == "leader" else None
        if not proof:
            return
        for peer in self.nodes:
            if peer != self.id:
                try:
                    self.rpc(peer, "/heartbeat", {"proof": proof})
                except Exception:
                    pass

    def poll_peer(self, peer):
        try:
            state = self.rpc(peer, "/state")
            self.observe_epoch(state["epoch"])
            if state.get("proof") and state.get("role") == "leader":
                try:
                    self.adopt(state["proof"], source=peer)
                except Rejected:
                    pass
            self.merge(state["operations"])
        except Exception as exc:
            # No confundir un error de datos/backend con un peer alcanzable.
            if not isinstance(exc, (OSError, HTTPError, TimeoutError)):
                self.event("peer_sync_error", peer=peer, reason=str(exc))

    def run(self):
        with ThreadPoolExecutor(max_workers=max(2, len(self.nodes) - 1)) as pool:
            while not self.stop.is_set():
                futures = [pool.submit(self.poll_peer, peer) for peer in self.nodes if peer != self.id]
                for future in futures:
                    future.result()
                try:
                    self.configure_backend()
                except Exception as exc:
                    self.event("backend_or_handoff_error", reason=str(exc))
                self.broadcast_heartbeat()
                with self.lock:
                    expired = (self.role != "leader" and time.monotonic() - self.last_heartbeat
                               > self.config.get("failure_timeout", 5))
                if expired:
                    self.start_election()
                self.stop.wait(self.config.get("heartbeat_interval", 1))

    def status(self, include_operations=False):
        with self.lock:
            result = {"node": self.id, "role": self.role, "leader": self.leader,
                      "epoch": self.epoch, "proof": self.proof,
                      "heartbeat_age_s": round(time.monotonic() - self.last_heartbeat, 3),
                      "operation_count": len(self.journal.ops),
                      "conflicts_detected": len(self.journal.conflicts),
                      "conflicts_resolved": sum(c["resolved"] for c in self.journal.conflicts.values()),
                      "journal_hash": hashlib.sha256(canonical(sorted(self.journal.ops.values(), key=lambda op: op["id"])).encode()).hexdigest()}
            if include_operations:
                result["operations"] = list(self.journal.ops.values())
            return result

    def inventory(self):
        with self.lock:
            views = self.backend.read()
            return {"node": self.id, "source": "local_redis" if not getattr(self.backend, "is_memory", False)
                    else "memory_test_only", "backend": self.backend.info(), "inventory": views,
                    "inventory_hash": hashlib.sha256(canonical(views).encode()).hexdigest()}

    def write(self, request, op_id, seed=False):
        try:
            uuid.UUID(op_id)
        except (ValueError, TypeError, AttributeError):
            raise Rejected(400, "request_id debe ser un UUID")
        with self.lock:
            if self.role != "leader" or self.leader != self.id:
                self.event("write_rejected", role=self.role, leader=self.leader)
                raise Rejected(409, "Solo escribe el coordinador elegido; consultar /status")
            resource = request.get("resource")
            if resource not in {"node" + str(x) for x in self.nodes}:
                raise Rejected(400, "Recurso desconocido")
            existing = self.journal.ops.get(op_id)
            request_record = {"seed": seed, **request}
            if existing:
                if existing.get("request") != request_record:
                    raise Rejected(409, "request_id ya corresponde a otra solicitud")
                self.backend.write(self.journal.views)
                return {"accepted": True, "duplicate": True, "operation": existing}
            view = self.journal.views.get(resource)
            if seed:
                if view is not None:
                    raise Rejected(409, "El recurso ya fue inicializado")
                value = dict(self.config["capacity"])
            else:
                if view is None:
                    raise Rejected(409, "Inicializar el inventario primero")
                amounts = request.get("amounts", {})
                if (not isinstance(amounts, dict) or set(amounts) != set(self.config["capacity"]) or
                        any(type(x) is not int or x < 0 for x in amounts.values()) or
                        not any(amounts.values())):
                    raise Rejected(400, "Usar cantidades enteras no negativas y al menos una positiva")
                value = {key: view["available"][key] - amounts[key] for key in amounts}
                if any(x < 0 for x in value.values()):
                    raise Rejected(409, "Capacidad insuficiente")
            # Asegurar que Redis está disponible y es maestro ANTES del journal.
            self.backend.promote()
            context = dict(view["context"]) if view else {str(x): 0 for x in self.nodes}
            context[str(self.id)] += 1
            self.lamport += 1
            self.journal.set("lamport", self.lamport)
            op = {"id": op_id, "resource": resource, "origin": self.id,
                  "lamport": self.lamport, "vv": context, "value": value,
                  "request": request_record, "election": self.proof["id"]}
            self.journal.add([op])
            try:
                self.backend.write(self.journal.views)
            except Exception as exc:
                self.event("write_uncertain", operation=op_id, reason=str(exc))
                raise Rejected(503, "Operación registrada pero publicación incierta; reintentar el MISMO request_id")
            self.event("write_accepted", operation=op)
            return {"accepted": True, "duplicate": False, "operation": op,
                    "acknowledgments": {"master": 1, "replicas_required": 0},
                    "allocation_is_provisional_during_partition": True}

    def handle(self, method, path, body, sender=None):
        if method == "GET" and path == "/estado":
            estado = self.status()
            return {
                "nodo": self.id,
                "rol": {"leader": "líder", "candidate": "candidato", "follower": "seguidor"}[estado["role"]],
                "lider": estado["leader"],
                "epoca": estado["proof"]["epoch"] if estado["proof"] else 0,
                "inventario_habilitado": True,
                "operaciones": estado["operation_count"],
                "journal_hash": estado["journal_hash"],
                "conflictos_detectados": estado["conflicts_detected"],
                "conflictos_resueltos": estado["conflicts_resolved"],
            }
        path = {"/inventario": "/inventory", "/conflictos": "/conflicts",
                "/asignar": "/assign", "/inicializar": "/seed",
                "/eleccion": "/election", "/coordinador": "/heartbeat",
                "/latido": "/heartbeat"}.get(path, path)
        if method == "GET":
            if path == "/status":
                return self.status()
            if path == "/state":
                return self.status(include_operations=True)
            if path == "/inventory":
                return self.inventory()
            if path == "/conflicts":
                with self.lock:
                    return {"conflicts": list(self.journal.conflicts.values())}
            if path.startswith("/proof/"):
                with self.lock:
                    proof = self.issued.get(path[len("/proof/"):])
                if proof is None:
                    raise Rejected(404, "No existe esa elección registrada")
                return proof
        if method == "POST":
            if path in {"/heartbeat", "/election", "/sync"} and sender not in self.nodes:
                raise Rejected(403, "Falta identidad de nodo")
            if path == "/heartbeat":
                proof = body.get("proof")
                if not isinstance(proof, dict) or sender != proof.get("winner"):
                    raise Rejected(403, "Latido sin elección o remitente distinto del ganador")
                try:
                    self.adopt(proof, source=sender)
                except Rejected as exc:
                    self.event("leader_claim_rejected", sender=sender, reason=exc.reason)
                    raise
                return {"accepted": True}
            if path == "/election":
                if body.get("candidate") != sender or sender >= self.id:
                    raise Rejected(400, "ELECTION debe dirigirse a un ID mayor")
                self.observe_epoch(body["epoch"])
                self.start_election()
                return {"ok": True, "epoch": self.epoch}
            if path == "/sync":
                return {"new_operations": self.merge(body["operations"]), **self.status()}
            if path in {"/assign", "/seed"}:
                return self.write(body["request"], body["request_id"], seed=path == "/seed")
        raise Rejected(404, "Ruta inexistente")

    def serve(self):
        node = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.dispatch("GET")

            def do_POST(self):
                self.dispatch("POST")

            def dispatch(self, method):
                status = 200
                try:
                    auth = self.headers.get("Authorization", "")
                    if not (method == "GET" and self.path == "/estado") and not hmac.compare_digest(auth, "Bearer " + node.token):
                        raise Rejected(401, "Credencial inválida")
                    sender = int(self.headers.get("X-Node-ID", "0"))
                    if sender in node.blocked:
                        raise Rejected(503, "Partición simulada")
                    length = int(self.headers.get("Content-Length", "0"))
                    if not 0 <= length <= 8_000_000:
                        raise Rejected(413, "Mensaje demasiado grande")
                    body = json.loads(self.rfile.read(length)) if length else {}
                    result = node.handle(method, self.path, body, sender)
                except Rejected as exc:
                    status, result = exc.status, {"error": exc.reason}
                except (KeyError, ValueError, TypeError) as exc:
                    status, result = 400, {"error": "Solicitud inválida: " + str(exc)}
                except Exception as exc:
                    status, result = 503, {"error": str(exc)}
                raw = canonical(result).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                try:
                    self.wfile.write(raw)
                except (BrokenPipeError, ConnectionResetError):
                    pass

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer((self.config.get("bind", "0.0.0.0"),
                                            self.nodes[self.id]["port"]), Handler)
        self.server.daemon_threads = True
        worker = threading.Thread(target=self.run, daemon=True)
        self.worker = worker
        worker.start()
        try:
            self.server.serve_forever(poll_interval=0.2)
        finally:
            self.stop.set()
            self.server.server_close()
            worker.join(timeout=5)


def configuracion_compatible(identificador, archivo=None):
    """Lee las IP y los puertos existentes sin modificar nodos.json."""
    archivo = Path(archivo) if archivo else Path(__file__).with_name("nodos.json")
    nodos = json.loads(archivo.read_text(encoding="utf-8-sig"))
    if str(identificador) not in nodos:
        raise ValueError("El ID debe existir en nodos.json")
    raiz = Path(__file__).resolve().parents[1]
    opciones_path = raiz / "config" / "inventario.local.json"
    if not opciones_path.exists():
        opciones_path = raiz / "config" / "inventario.example.json"
    opciones = json.loads(opciones_path.read_text(encoding="utf-8-sig"))
    return {
        "node_id": identificador,
        "bind": "0.0.0.0",
        "data_dir": str(raiz / "datos" / f"nodo{identificador}"),
        "heartbeat_interval": opciones.get("heartbeat_interval", 1.0),
        "failure_timeout": opciones.get("failure_timeout", 5.0),
        "election_wait": opciones.get("election_wait", 3.0),
        "rpc_timeout": opciones.get("rpc_timeout", 0.7),
        "capacity": opciones["capacity"],
        "nodes": {
            clave: {"host": nodo["host"], "port": nodo["puerto"],
                    "redis_port": nodo.get("redis_puerto", 6379)}
            for clave, nodo in nodos.items()
        },
    }


def main_compatible():
    parser = argparse.ArgumentParser(description="Ampliación opcional del coordinador existente")
    parser.add_argument("identificador", type=int)
    parser.add_argument("--inventario", action="store_true", required=True)
    args = parser.parse_args()
    token = os.environ.get("TALLER_TOKEN", "")
    password = os.environ.get("REDIS_PASSWORD", "")
    if not password or len(token) < 16:
        parser.error("Cargar .env con TALLER_TOKEN y REDIS_PASSWORD")
    config = configuracion_compatible(args.identificador)
    node = Node(config, token, RedisBackend(
        password, config["nodes"][str(args.identificador)]["redis_port"]))
    try:
        node.serve()
    except KeyboardInterrupt:
        node.stop.set()


if __name__ == "__main__":
    main_compatible()
