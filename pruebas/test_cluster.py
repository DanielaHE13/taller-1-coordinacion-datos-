"""HTTP real entre 3 procesos lógicos; backend en memoria, sin VM/Redis."""
import contextlib
import io
import json
from pathlib import Path
import socket
from pruebas.apoyo import directorio_prueba
import threading
import time
import unittest
import uuid
from coordinador.redis_inventario import MemoryBackend
from coordinador.motor import Node, Rejected

def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]

def wait_for(predicate, timeout=18):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        try:
            if predicate():
                return
        except Exception:
            pass
        time.sleep(.08)
    raise AssertionError("No se cumplió la condición dentro del tiempo límite")

class ClusterTests(unittest.TestCase):
    def test_election_partition_conflicts_rejoin_and_rejections(self):
        with directorio_prueba() as directory:
            peers = {str(i): {"host": "127.0.0.1", "port": free_port(), "redis_port": 6379}
                     for i in (1, 2, 3)}
            configs = [{"node_id": i, "bind": "127.0.0.1", "data_dir": str(Path(directory)/str(i)),
                        "nodes": peers, "capacity": {"cpu": 4, "memory_mb": 1024, "bandwidth_mbps": 100},
                        "heartbeat_interval": .12, "failure_timeout": 1.2,
                        "election_wait": .5, "rpc_timeout": .3} for i in (1, 2, 3)]
            nodes = [Node(cfg, "test-token-at-least-16", MemoryBackend()) for cfg in configs]
            threads = [threading.Thread(target=n.serve, daemon=True) for n in nodes]
            try:
                for thread in threads:
                    thread.start()
                wait_for(lambda: all(n.leader == 3 and n.role in ("leader", "follower") for n in nodes))
                n1, n2, n3 = nodes
                first_proof = n3.proof
                n3.write({"resource": "node1"}, str(uuid.uuid4()), seed=True)
                wait_for(lambda: all(len(n.journal.ops) == 1 for n in nodes))
                with self.assertRaises(Rejected) as rejected:
                    n1.write({"resource": "node1", "amounts": {"cpu": 1, "memory_mb": 0, "bandwidth_mbps": 0}}, str(uuid.uuid4()))
                self.assertEqual(rejected.exception.status, 409)
                fake = {"id": str(uuid.uuid4()), "epoch": n3.epoch + 100,
                        "winner": 1, "members": [1], "higher_probes": {"2": "unreachable", "3": "unreachable"}}
                with self.assertRaises(Rejected):
                    n2.handle("POST", "/heartbeat", {"proof": fake}, sender=1)
                self.assertEqual(n2.leader, 3)
                altered = dict(first_proof, epoch=first_proof["epoch"] + 100)
                with self.assertRaises(Rejected):
                    n2.handle("POST", "/heartbeat", {"proof": altered}, sender=3)
                # Simula bloqueo bidireccional; el cliente local sigue funcionando.
                n3.blocked = {1, 2}
                n1.blocked = n2.blocked = {3}
                wait_for(lambda: n2.role == "leader" and n1.leader == 2)
                self.assertEqual(n3.role, "leader")
                self.assertGreater(n2.proof["epoch"], first_proof["epoch"])
                a = n3.write({"resource": "node1", "amounts": {"cpu": 1, "memory_mb": 0, "bandwidth_mbps": 0}}, str(uuid.uuid4()))
                request_id = str(uuid.uuid4())
                request = {"resource": "node1", "amounts": {"cpu": 2, "memory_mb": 0, "bandwidth_mbps": 0}}
                b = n2.write(request, request_id)
                self.assertTrue(n2.write(request, request_id)["duplicate"])
                self.assertNotEqual(a["operation"]["vv"], b["operation"]["vv"])
                n1.blocked, n2.blocked, n3.blocked = set(), set(), set()
                wait_for(lambda: all(n.leader == 2 for n in nodes))
                wait_for(lambda: all(len(n.journal.ops) == 3 for n in nodes))
                wait_for(lambda: len({n.inventory()["inventory_hash"] for n in nodes}) == 1)
                self.assertEqual(n3.role, "follower")
                self.assertTrue(all(n.status()["conflicts_detected"] == 1 for n in nodes))
                self.assertTrue(all(n.status()["conflicts_resolved"] == 1 for n in nodes))
                with self.assertRaises(Rejected):
                    n3.write(request, str(uuid.uuid4()))
                with self.assertRaises(Rejected):
                    n2.handle("POST", "/heartbeat", {"proof": first_proof}, sender=3)
                # Caída completa del proceso líder: el mayor ID restante es 3.
                n2.stop.set()
                n2.server.shutdown()
                wait_for(lambda: n3.role == "leader" and n1.leader == 3)
                self.assertGreater(n3.proof["epoch"], first_proof["epoch"])
            finally:
                for n in nodes:
                    n.stop.set()
                for n in nodes:
                    if n.server:
                        n.server.shutdown()
                for thread in threads:
                    thread.join(timeout=5)
                time.sleep(.7)
                for n in nodes:
                    n.journal.db.close()

if __name__ == "__main__":
    unittest.main()
