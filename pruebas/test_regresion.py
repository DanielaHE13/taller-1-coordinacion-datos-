"""Regresión del modo existente y promoción progresiva del mayor ID."""
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import socket
import threading
import unittest

from coordinador import nodo as legado
from coordinador.motor import Node
from coordinador.redis_inventario import MemoryBackend
from pruebas.apoyo import directorio_prueba
from pruebas.test_cluster import free_port, wait_for
from scripts.capturar_estado import verificar_convergencia


class RegresionTests(unittest.TestCase):
    def test_eleccion_original_caida_y_regreso_del_mayor(self):
        previous = legado.NODOS
        legado.NODOS = {i: {"host": "127.0.0.1", "puerto": 5000} for i in (1, 2, 3)}
        try:
            nodes = {i: legado.Nodo(i) for i in (1, 2, 3)}
            active = {1, 2, 3}

            def enviar(destino, ruta, datos=None):
                if destino not in active:
                    raise ConnectionError("Nodo detenido en la prueba")
                if ruta in ("coordinador", "latido"):
                    return {"aceptado": nodes[destino].aceptar_lider(datos["lider"])}
                return {"recibido": True}

            for node in nodes.values():
                node.enviar = enviar
            nodes[3].bloqueo_eleccion.acquire()
            nodes[3].elegir()
            self.assertEqual([n.lider for n in nodes.values()], [3, 3, 3])
            active.remove(3)
            nodes[2].bloqueo_eleccion.acquire()
            nodes[2].elegir()
            self.assertEqual((nodes[1].lider, nodes[2].lider), (2, 2))
            active.add(3)
            nodes[3].bloqueo_eleccion.acquire()
            nodes[3].elegir()
            self.assertEqual([n.lider for n in nodes.values()], [3, 3, 3])
        finally:
            legado.NODOS = previous

    def test_nodos_nuevos_de_mayor_id_se_incorporan_en_orden(self):
        with directorio_prueba() as directory:
            peers = {str(i): {"host": "127.0.0.1", "port": free_port(), "redis_port": 6379}
                     for i in (1, 2, 3)}
            nodes, threads = [], []
            try:
                for i in (1, 2, 3):
                    config = {"node_id": i, "bind": "127.0.0.1",
                              "data_dir": str(Path(directory)/str(i)),
                              "nodes": peers,
                              "capacity": {"cpu": 2, "memory_mb": 1024, "bandwidth_mbps": 100},
                              "heartbeat_interval": .1, "failure_timeout": .8,
                              "election_wait": .3, "rpc_timeout": .2}
                    node = Node(config, "token-local-mas-de-16", MemoryBackend())
                    nodes.append(node)
                    thread = threading.Thread(target=node.serve, daemon=True)
                    threads.append(thread)
                    thread.start()
                    wait_for(lambda: all(n.leader == i for n in nodes))
                self.assertEqual([n.leader for n in nodes], [3, 3, 3])
            finally:
                for node in nodes:
                    node.stop.set()
                for node in nodes:
                    if node.server:
                        node.server.shutdown()
                for thread in threads:
                    thread.join(timeout=5)
                for node in nodes:
                    if node.worker:
                        node.worker.join(timeout=5)
                    node.journal.db.close()

    def test_verificar_convergencia_no_oculta_falta_de_conflicto_o_redis(self):
        result = {"nodos": {}}
        for i in (1, 2, 3):
            result["nodos"][str(i)] = {
                "estado": {"lider": 2, "rol": "líder" if i == 2 else "seguidor",
                           "epoca": 8, "journal_hash": "historia",
                           "conflictos_detectados": 1, "conflictos_resueltos": 1},
                "inventario": {"source": "local_redis", "inventory_hash": "inventario",
                               "backend": {"role": "master" if i == 2 else "slave",
                                           "master_link_status": "up"}}
            }
        self.assertTrue(verificar_convergencia(result, 3, 1))
        missing = deepcopy(result)
        missing["nodos"].pop("3")
        self.assertFalse(verificar_convergencia(missing, 3, 1))
        different = deepcopy(result)
        different["nodos"]["3"]["inventario"]["inventory_hash"] = "otra-rama"
        self.assertFalse(verificar_convergencia(different, 3, 1))
        no_conflict = deepcopy(result)
        for sample in no_conflict["nodos"].values():
            sample["estado"]["conflictos_detectados"] = 0
            sample["estado"]["conflictos_resueltos"] = 0
        self.assertTrue(verificar_convergencia(no_conflict, 3))
        self.assertFalse(verificar_convergencia(no_conflict, 3, 1))
        fake = deepcopy(result)
        fake["nodos"]["1"]["inventario"]["source"] = "memory_test_only"
        self.assertFalse(verificar_convergencia(fake, 3, 1))

    def test_logica_original_se_conserva(self):
        source = Path(legado.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        expected = {'Nodo': '6a89b955b29c8f7010839c621df6b089656b613a645d48dc79b2c77a8079f911', 'crear_servidor': '7ed48f4d9f19379b7b2430ea1541b86456d5328d468b257a260371bf2a174f68', 'main': '8fc96808e98470a591725f91b1bccd10e3bc2ca562ff4301c076cacb0dc3b85f'}
        for name in ("Nodo", "crear_servidor", "main"):
            item = next(n for n in tree.body if getattr(n, "name", None) == name)
            if name == "main":
                self.assertIsInstance(item.body[0], ast.If)
                self.assertIn("--inventario", ast.dump(item.body[0]))
                item.body = item.body[1:]
            digest = hashlib.sha256(ast.dump(item, include_attributes=False).encode()).hexdigest()
            self.assertEqual(digest, expected[name], name)


if __name__ == "__main__":
    unittest.main()
