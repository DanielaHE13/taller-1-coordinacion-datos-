from contextlib import closing
import json
import sqlite3


def iniciar_saga(ruta, saga_id, solicitud=None):
    with closing(sqlite3.connect(ruta)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        db.execute("""
            CREATE TABLE IF NOT EXISTS sagas (
                saga_id TEXT PRIMARY KEY,
                estado TEXT NOT NULL CHECK (
                    estado IN ('en_curso', 'completada', 'compensada')
                ),
                actualizado_utc TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        creada = db.execute(
            "INSERT OR IGNORE INTO sagas (saga_id, estado) VALUES (?, 'en_curso')",
            (saga_id,),
        ).rowcount == 1
        if solicitud is not None:
            db.execute("""
                CREATE TABLE IF NOT EXISTS solicitudes_saga (
                    saga_id TEXT PRIMARY KEY,
                    solicitud TEXT NOT NULL
                )
            """)
            descripcion = json.dumps(solicitud, sort_keys=True)
            if creada:
                db.execute(
                    "INSERT INTO solicitudes_saga VALUES (?, ?)",
                    (saga_id, descripcion),
                )
            else:
                anterior = db.execute(
                    "SELECT solicitud FROM solicitudes_saga WHERE saga_id = ?",
                    (saga_id,),
                ).fetchone()
                if anterior != (descripcion,):
                    raise ValueError("El ID de Saga pertenece a otra solicitud.")
        return db.execute(
            "SELECT estado FROM sagas WHERE saga_id = ?", (saga_id,)
        ).fetchone()[0]


def finalizar_saga(ruta, saga_id, estado):
    if estado not in {"completada", "compensada"}:
        raise ValueError("Estado final inválido")

    with closing(sqlite3.connect(ruta)) as db, db:
        db.execute("""
            UPDATE sagas
            SET estado = ?, actualizado_utc = CURRENT_TIMESTAMP
            WHERE saga_id = ? AND estado = 'en_curso'
        """, (estado, saga_id))
        registro = db.execute(
            "SELECT estado FROM sagas WHERE saga_id = ?", (saga_id,)
        ).fetchone()

        if registro is None:
            raise ValueError(f"La Saga {saga_id} no existe")
        if registro[0] != estado:
            raise ValueError(f"La Saga {saga_id} ya está {registro[0]}")
