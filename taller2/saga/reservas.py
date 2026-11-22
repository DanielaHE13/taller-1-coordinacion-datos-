from contextlib import closing
import sqlite3


def registrar_reserva(ruta, saga_id, cantidad, capacidad):
    if cantidad <= 0 or capacidad < 0:
        raise ValueError("Cantidad o capacidad inválida")

    with closing(sqlite3.connect(ruta)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        db.execute("""
            CREATE TABLE IF NOT EXISTS reservas_cpu (
                saga_id TEXT PRIMARY KEY,
                cantidad INTEGER NOT NULL,
                activa INTEGER NOT NULL
            )
        """)
        anterior = db.execute(
            "SELECT cantidad, activa FROM reservas_cpu WHERE saga_id = ?",
            (saga_id,),
        ).fetchone()
        if anterior is not None:
            if anterior == (cantidad, 1):
                return
            raise ValueError("La Saga ya tiene otro estado o cantidad de reserva")

        ocupada = db.execute(
            "SELECT COALESCE(SUM(cantidad), 0) FROM reservas_cpu WHERE activa = 1"
        ).fetchone()[0]
        if ocupada + cantidad > capacidad:
            raise ValueError("CPU insuficiente para reservar")

        db.execute(
            "INSERT INTO reservas_cpu VALUES (?, ?, 1)", (saga_id, cantidad)
        )


def liberar_reserva(ruta, saga_id):
    with closing(sqlite3.connect(ruta)) as db, db:
        db.execute(
            "UPDATE reservas_cpu SET activa = 0 WHERE saga_id = ?",
            (saga_id,),
        )
