"""Vectores POR RECURSO y registro multiversión determinista.

Las operaciones originales son inmutables. La vista une sus contextos, pero
no sustituye el vector original del ganador por un vector sintético: eso
evita perder concurrencia cuando los mensajes llegan en distinto orden.
"""
from collections import defaultdict
from hashlib import sha256
import json


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def dominates(a, b):
    keys = a.keys() | b.keys()
    return all(a.get(k, 0) >= b.get(k, 0) for k in keys) and any(
        a.get(k, 0) > b.get(k, 0) for k in keys)


def concurrent(a, b):
    unequal = any(a.get(k, 0) != b.get(k, 0) for k in a.keys() | b.keys())
    return unequal and not dominates(a, b) and not dominates(b, a)


def join(vectors):
    result = {}
    for vector in vectors:
        for node, counter in vector.items():
            result[node] = max(result.get(node, 0), counter)
    return result


def winner_key(op):
    # Mayor Lamport; en empate menor ID numérico. UUID es desempate defensivo.
    return (op["lamport"], -int(op["origin"]), op["id"])


def materialize(operations):
    groups = defaultdict(list)
    for op in operations:
        groups[op["resource"]].append(op)
    views, conflicts = {}, {}
    for resource, ops in sorted(groups.items()):
        frontier = [a for a in ops if not any(
            dominates(b["vv"], a["vv"]) for b in ops)]
        chosen = max(frontier, key=winner_key)
        views[resource] = {
            "available": chosen["value"],
            "context": join(a["vv"] for a in frontier),
            "winner_operation": chosen["id"],
            "winner_lamport": chosen["lamport"],
            "winner_node": chosen["origin"],
            "frontier": sorted(a["id"] for a in frontier),
        }
        for i, a in enumerate(ops):
            for b in ops[i + 1:]:
                if concurrent(a["vv"], b["vv"]):
                    pair = sorted([a["id"], b["id"]])
                    cid = sha256(canonical(pair).encode()).hexdigest()
                    conflicts[cid] = {
                        "id": cid, "resource": resource, "operations": pair,
                        "winner": max([a, b], key=winner_key)["id"],
                        "rule": "max_lamport_then_min_node_id", "resolved": True,
                    }
    return views, conflicts

