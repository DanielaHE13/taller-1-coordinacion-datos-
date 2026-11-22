from datetime import datetime, timezone
from getpass import getpass
import json
from time import sleep
from uuid import uuid4

import pika


def registrar(texto):
    hora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    print(f"{hora} | {texto}", flush=True)


clave = getpass("Contraseña de RabbitMQ para el usuario taller: ")
parametros = pika.ConnectionParameters(
    host="100.125.242.122",
    port=5672,
    virtual_host="/",
    credentials=pika.PlainCredentials("taller", clave),
    connection_attempts=1,
    socket_timeout=3,
    stack_timeout=5,
)

mensaje_id = str(uuid4())
cuerpo = json.dumps({
    "message_id": mensaje_id,
    "node_id": "nodo2",
    "tipo": "prueba_reconexion",
}).encode()

for intento in range(1, 9):
    registrar(f"Intento {intento} | ID: {mensaje_id}")
    try:
        with pika.BlockingConnection(parametros) as conexion:
            canal = conexion.channel()
            canal.queue_declare(queue="taller2.prueba", durable=True)
            canal.confirm_delivery()
            canal.basic_publish(
                exchange="",
                routing_key="taller2.prueba",
                body=cuerpo,
                properties=pika.BasicProperties(
                    delivery_mode=2, message_id=mensaje_id
                ),
                mandatory=True,
            )
            registrar(f"Publicación confirmada | ID: {mensaje_id}")
            break
    except pika.exceptions.AMQPError as error:
        if intento == 8:
            raise SystemExit(f"Se agotaron los intentos: {error}") from error
        espera = min(2 ** intento, 8)
        registrar(f"Fallo: {type(error).__name__} | Reintento en {espera}s")
        sleep(espera)
