"""Bitácora durable para sobrevivir a REPLICAOF y deduplicar mensajes."""
import json
from pathlib import Path
import sqlite3
from .versiones import canonical, materialize


class Journal:
    # El propietario Node serializa todas las llamadas con su RLock.
    def __init__(self, directory):
        Path(directory).mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(Path(directory) / "journal.sqlite"),
                                  check_same_thread=False)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS metadata(k TEXT PRIMARY KEY, v TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS operations(id TEXT PRIMARY KEY, body TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS conflicts(id TEXT PRIMARY KEY, body TEXT NOT NULL);
        """)
        self.db.commit()
        self.ops = {key: json.loads(body) for key, body in
                    self.db.execute("SELECT id,body FROM operations")}
        self.views, self.conflicts = materialize(list(self.ops.values()))

    def get(self, key, default=None):
        row = self.db.execute("SELECT v FROM metadata WHERE k=?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def set(self, key, value):
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO metadata VALUES(?,?)",
                            (key, canonical(value)))

    def add(self, operations):
        new = []
        batch = {}
        for op in operations:
            if op["id"] in batch and batch[op["id"]] != op:
                raise ValueError("UUID duplicado con contenidos diferentes en el lote")
            batch[op["id"]] = op
        for op in batch.values():
            existing = self.ops.get(op["id"])
            if existing is not None and existing != op:
                raise ValueError("UUID reutilizado con otra operación")
            if existing is None:
                new.append(op)
        if not new:
            return [], []
        combined = dict(self.ops)
        combined.update({op["id"]: op for op in new})
        views, conflicts = materialize(list(combined.values()))
        discovered = [c for cid, c in conflicts.items() if cid not in self.conflicts]
        with self.db:
            self.db.executemany("INSERT INTO operations VALUES(?,?)",
                                [(op["id"], canonical(op)) for op in new])
            self.db.executemany("INSERT OR IGNORE INTO conflicts VALUES(?,?)",
                                [(c["id"], canonical(c)) for c in discovered])
        self.ops, self.views, self.conflicts = combined, views, conflicts
        return new, discovered

