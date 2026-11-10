import itertools
from pruebas.apoyo import directorio_prueba
import unittest
import uuid
from coordinador.bitacora import Journal
from coordinador.versiones import concurrent, dominates, materialize

def op(origin, vv, lamport, cpu):
    return {"id": str(uuid.uuid4()), "origin": origin, "resource": "node1",
            "vv": vv, "lamport": lamport,
            "value": {"cpu": cpu, "memory_mb": 1024, "bandwidth_mbps": 100}}

class VersionTests(unittest.TestCase):
    def test_causality_and_concurrency(self):
        self.assertTrue(dominates({"1": 2, "2": 1}, {"1": 1, "2": 1}))
        self.assertTrue(concurrent({"1": 1, "2": 0}, {"1": 0, "2": 1}))
        self.assertFalse(concurrent({"1": 1}, {"1": 1}))
        self.assertFalse(concurrent({"1": 0}, {}))

    def test_tie_uses_smaller_node_id(self):
        a = op(3, {"1": 0, "2": 0, "3": 2}, 11, 3)
        b = op(2, {"1": 0, "2": 1, "3": 1}, 11, 2)
        views, conflicts = materialize([a, b])
        self.assertEqual(views["node1"]["winner_node"], 2)
        self.assertEqual(views["node1"]["context"], {"1": 0, "2": 1, "3": 2})
        self.assertEqual(len(conflicts), 1)

    def test_all_message_orders_converge_and_keep_original_vectors(self):
        a = op(1, {"1": 1, "2": 0, "3": 0}, 1, 3)
        b = op(2, {"1": 0, "2": 1, "3": 0}, 2, 2)
        c = op(3, {"1": 1, "2": 0, "3": 1}, 3, 1)
        expected = materialize([a, b, c])
        for order in itertools.permutations([a, b, c]):
            self.assertEqual(materialize(order), expected)
        self.assertEqual(a["vv"], {"1": 1, "2": 0, "3": 0})

    def test_write_after_resolution_dominates_both_branches(self):
        a = op(3, {"1": 0, "2": 0, "3": 2}, 11, 3)
        b = op(2, {"1": 0, "2": 1, "3": 1}, 11, 2)
        c = op(2, {"1": 0, "2": 2, "3": 2}, 12, 1)
        views, conflicts = materialize([a, b, c])
        self.assertEqual(views["node1"]["frontier"], [c["id"]])
        self.assertEqual(len(conflicts), 1)

    def test_journal_survives_restart_and_deduplicates_conflicts(self):
        a = op(1, {"1": 1, "2": 0, "3": 0}, 1, 3)
        b = op(2, {"1": 0, "2": 1, "3": 0}, 2, 2)
        with directorio_prueba() as directory:
            j = Journal(directory)
            j.add([a, b, a])
            self.assertEqual(j.add([b, a]), ([], []))
            j.db.close()
            recovered = Journal(directory)
            self.assertEqual(len(recovered.ops), 2)
            self.assertEqual(len(recovered.conflicts), 1)
            recovered.db.close()

if __name__ == "__main__":
    unittest.main()
