from contextlib import closing
import json
import sqlite3
from uuid import UUID


def registrar_evento(ruta, evento):
    """Guarda el evento y devuelve True si es la primera entrega."""
    mensaje_id = str(UUID(evento["message_id"]))
    cuerpo = json.dumps(evento, ensure_ascii=False, sort_keys=True)

    with closing(sqlite3.connect(ruta)) as db, db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS eventos_procesados (
                message_id TEXT PRIMARY KEY,
                cuerpo TEXT NOT NULL
            )
        """)
        resultado = db.execute("""
            INSERT INTO eventos_procesados (message_id, cuerpo)
            VALUES (?, ?)
            ON CONFLICT (message_id) DO NOTHING
        """, (mensaje_id, cuerpo))
        return resultado.rowcount == 1
