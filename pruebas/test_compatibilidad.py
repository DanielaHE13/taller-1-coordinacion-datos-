import json
from pathlib import Path
import subprocess
import sys
import threading
import unittest
from urllib.request import urlopen
import uuid
from coordinador import nodo as original
from coordinador.motor import Node, Rejected, configuracion_compatible
from coordinador.redis_inventario import MemoryBackend
from pruebas.apoyo import directorio_prueba


def prueba_comprobante(winner, epoch):
    return {"id": str(uuid.uuid4()), "epoch": epoch, "winner": winner,
            "members": list(range(1, winner+1)),
            "higher_probes": {str(i): "unreachable" for i in range(winner+1, 4)}}


class CompatibilidadTests(unittest.TestCase):
    def test_ruta_estado_del_coordinador_original(self):
        previous = original.NODOS
        original.NODOS = {1: {"host": "127.0.0.1", "puerto": 0},
                          2: {"host": "127.0.0.1", "puerto": 0},
                          3: {"host": "127.0.0.1", "puerto": 0}}
        server = None
        try:
            node = original.Nodo(1)
            self.assertTrue(node.aceptar_lider(3))
            self.assertFalse(node.aceptar_lider(0))
            server = original.crear_servidor(node)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            with urlopen(f"http://127.0.0.1:{server.server_port}/estado") as response:
                estado = json.load(response)
            self.assertEqual(estado, {"nodo": 1, "rol": "seguidor", "lider": 3})
        finally:
            if server:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)
            original.NODOS = previous

    def test_adaptador_utiliza_host_y_puerto_existentes(self):
        with directorio_prueba() as directory:
            p = Path(directory)/"nodos.json"
            p.write_text(json.dumps({"1": {"host": "127.0.0.1", "puerto": 5123},
                                     "2": {"host": "127.0.0.2", "puerto": 5456},
                                     "3": {"host": "127.0.0.3", "puerto": 5789}}), encoding="utf-8")
            config = configuracion_compatible(2, p)
            self.assertEqual(config["nodes"]["2"]["port"], 5456)
            self.assertEqual(config["nodes"]["3"]["host"], "127.0.0.3")

    def test_comando_ampliado_reconoce_la_opcion_sin_arrancar_servicios(self):
        root = Path(__file__).resolve().parents[1]
        process = subprocess.run([sys.executable, "coordinador/nodo.py", "1", "--inventario", "--help"],
                                 cwd=root, capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("--inventario", process.stdout)

    def test_nuevo_nodo_mayor_compite_pero_recuperado_acepta_nueva_epoca(self):
        with directorio_prueba() as directory:
            config = {"node_id": 3, "data_dir": directory,
                      "capacity": {"cpu": 2, "memory_mb": 1024, "bandwidth_mbps": 100},
                      "nodes": {str(i): {"host": "127.0.0.1", "port": 5000} for i in (1, 2, 3)}}
            lower = prueba_comprobante(2, 4)
            node = Node(config, "token-para-pruebas-locales", MemoryBackend())
            node.rpc = lambda *args: lower
            with self.assertRaises(Rejected):
                node.adopt(lower, source=2)
            old = prueba_comprobante(3, 2)
            node.issued[old["id"]] = old
            node.verified[old["id"]] = old
            node.adopt(old, source=3)
            node.journal.db.close()
            recovered = Node(config, "token-para-pruebas-locales", MemoryBackend())
            recovered.rpc = lambda *args: lower
            recovered.adopt(lower, source=2)
            self.assertEqual((recovered.role, recovered.leader), ("follower", 2))
            recovered.journal.db.close()
