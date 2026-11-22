import argparse
from getpass import getpass
import json
import os
from pathlib import Path

import pika

from .eventos_procesados import registrar_evento


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cola", required=True)
    parser.add_argument("--cantidad", type=int, default=1)
    parser.add_argument("--orden-lamport", action="store_true")
    parser.add_argument("--base", type=Path, default=Path("datos/eventos.sqlite3"))
    opciones = parser.parse_args()
    if opciones.cantidad < 1:
        parser.error("--cantidad debe ser mayor que cero")

    opciones.base.parent.mkdir(parents=True, exist_ok=True)
    clave = os.environ.get("RABBITMQ_PASSWORD") or getpass(
        "Contraseña de RabbitMQ para el usuario taller: "
    )
    parametros = pika.ConnectionParameters(
        host=os.environ.get("RABBITMQ_HOST", "100.125.242.122"),
        virtual_host="/",
        credentials=pika.PlainCredentials("taller", clave),
        socket_timeout=5,
    )

    with pika.BlockingConnection(parametros) as conexion:
        canal = conexion.channel()
        def recibir():
            entrega, _, cuerpo = canal.basic_get(
                queue=opciones.cola, auto_ack=False
            )
            if entrega is None:
                raise SystemExit(f"No hay suficientes mensajes en {opciones.cola}.")
            return entrega, json.loads(cuerpo)

        eventos = (recibir() for _ in range(opciones.cantidad))
        if opciones.orden_lamport:
            eventos = sorted(
                eventos,
                key=lambda item: (item[1]["lamport_time"], item[1]["node_id"]),
            )

        for entrega, evento in eventos:
            nuevo = registrar_evento(opciones.base, evento)
            canal.basic_ack(delivery_tag=entrega.delivery_tag)
            estado = "Evento guardado" if nuevo else "Duplicado omitido"
            print(f"{estado} | ID: {evento['message_id']} | ACK enviado", flush=True)


if __name__ == "__main__":
    main()
