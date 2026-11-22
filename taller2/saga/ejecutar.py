import argparse
from getpass import getpass
import json
import os
from pathlib import Path
from uuid import UUID, uuid4, uuid5

import pika

from .inventario import consultar_api, replicar_cpu
from .orquestador import FalloSinEscritura, ejecutar_saga


def publicar_confirmacion(saga_id, marca):
    clave = os.environ.get("RABBITMQ_PASSWORD") or getpass(
        "Contraseña de RabbitMQ para el usuario taller: "
    )
    parametros = pika.ConnectionParameters(
        host="100.125.242.122",
        port=5672,
        virtual_host="/",
        credentials=pika.PlainCredentials("taller", clave),
        socket_timeout=5,
    )
    evento = {
        "message_id": str(uuid5(UUID(saga_id), "asignacion_confirmada")),
        "saga_id": saga_id,
        "node_id": "nodo2",
        "lamport_time": marca,
        "tipo": "asignacion_confirmada",
        "destinatario": "nodo5",
        "recurso": "node3",
        "cpu_asignada": 1,
    }

    with pika.BlockingConnection(parametros) as conexion:
        canal = conexion.channel()
        canal.confirm_delivery()
        canal.basic_publish(
            exchange="",
            routing_key="allocations",
            body=json.dumps(evento).encode(),
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=2,
                message_id=evento["message_id"],
            ),
            mandatory=True,
        )


def main():
    argumentos = argparse.ArgumentParser()
    argumentos.add_argument("--simular-fallo-paso-2", action="store_true")
    opciones = argumentos.parse_args()

    saga_id = str(uuid4())
    token = os.environ["TALLER_TOKEN"]
    origen = "http://100.98.74.61:50052"
    base = Path("datos/sagas_taller2.sqlite3")
    base.parent.mkdir(parents=True, exist_ok=True)
    marca_replicada = 0

    def reservar(identificador):
        respuesta = consultar_api(origen, "/reservar", token, {
            "saga_id": identificador, "cantidad": 1,
        })
        if respuesta != {"saga_id": identificador, "estado": "reservada"}:
            raise RuntimeError("El nodo 3 no confirmó la reserva esperada.")
        print("Paso 1: reserva confirmada en nodo3.", flush=True)

    def replicar(identificador):
        nonlocal marca_replicada
        if opciones.simular_fallo_paso_2:
            print("Paso 2: fallo simulado antes de enviar la asignación.", flush=True)
            raise FalloSinEscritura("Fallo de prueba antes de escribir.")
        vista = replicar_cpu(
            identificador,
            lider_url="http://100.92.63.103:5000",
            replica_url="http://100.98.74.61:5000",
            token=token,
            recurso="node3",
            cantidad=1,
        )
        marca_replicada = vista["winner_lamport"]
        print("Paso 2: asignación verificada en la réplica.", flush=True)

    def notificar(identificador):
        publicar_confirmacion(identificador, marca_replicada + 1)
        print("Paso 3: RabbitMQ confirmó la publicación en allocations.", flush=True)

    def liberar(identificador):
        respuesta = consultar_api(
            origen, "/liberar", token, {"saga_id": identificador}
        )
        if respuesta != {"saga_id": identificador, "estado": "liberada"}:
            raise RuntimeError("El nodo 3 no confirmó la liberación.")
        print("Compensación: reserva liberada en nodo3.", flush=True)

    print(f"Saga: {saga_id}", flush=True)
    estado = ejecutar_saga(
        base, saga_id, reservar=reservar, replicar=replicar,
        notificar=notificar, liberar=liberar,
    )
    print(f"Estado persistido: {estado}", flush=True)


if __name__ == "__main__":
    main()
