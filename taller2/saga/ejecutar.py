import argparse
from getpass import getpass
import json
import os
from pathlib import Path
from uuid import UUID, uuid4, uuid5

import pika

from .inventario import consultar_api, replicar_cpu
from .orquestador import FalloSinEscritura, ejecutar_saga


def publicar_confirmacion(saga_id, marca, *, destinatario, recurso, cantidad, clave):
    parametros = pika.ConnectionParameters(
        host=os.environ.get("RABBITMQ_HOST", "100.125.242.122"),
        port=5672,
        virtual_host="/",
        credentials=pika.PlainCredentials("taller", clave),
        socket_timeout=5,
    )
    evento = {
        "message_id": str(uuid5(UUID(saga_id), "asignacion_confirmada")),
        "saga_id": saga_id,
        "node_id": os.environ.get("NODE_ID", "nodo2"),
        "lamport_time": marca,
        "tipo": "asignacion_confirmada",
        "destinatario": destinatario,
        "recurso": recurso,
        "cpu_asignada": cantidad,
    }

    with pika.BlockingConnection(parametros) as conexion:
        canal = conexion.channel()
        canal.queue_declare(queue="allocations", durable=True)
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


def asignar_cpu(
    saga_id, *, destinatario, cantidad, marca_solicitud=0, simular_fallo=False,
    clave_broker=None,
):
    token = os.environ["TALLER_TOKEN"]
    origen = os.environ.get("SAGA_RESERVAS_URL", "http://100.98.74.61:50052")
    recurso = os.environ.get("SAGA_RECURSO", "node3")
    base = Path(os.environ.get("SAGA_DB", "datos/sagas_taller2.sqlite3"))
    base.parent.mkdir(parents=True, exist_ok=True)
    clave_broker = clave_broker or os.environ.get("RABBITMQ_PASSWORD")
    if not clave_broker and not simular_fallo:
        raise RuntimeError("Falta la configuración de RabbitMQ.")
    marca_replicada = marca_solicitud

    def reservar(identificador):
        respuesta = consultar_api(origen, "/reservar", token, {
            "saga_id": identificador, "cantidad": cantidad,
        })
        if respuesta != {"saga_id": identificador, "estado": "reservada"}:
            raise RuntimeError("El nodo 3 no confirmó la reserva esperada.")
        print(f"Paso 1: reserva confirmada para {recurso}.", flush=True)

    def replicar(identificador):
        nonlocal marca_replicada
        if simular_fallo:
            print("Paso 2: fallo simulado antes de enviar la asignación.", flush=True)
            raise FalloSinEscritura("Fallo de prueba antes de escribir.")
        vista = replicar_cpu(
            identificador,
            lider_url=os.environ.get("SAGA_LIDER_URL", "http://100.92.63.103:5000"),
            replica_url=os.environ.get("SAGA_REPLICA_URL", "http://100.98.74.61:5000"),
            token=token,
            recurso=recurso,
            cantidad=cantidad,
        )
        marca_replicada = max(marca_solicitud, vista["winner_lamport"])
        print("Paso 2: asignación verificada en la réplica.", flush=True)

    def notificar(identificador):
        publicar_confirmacion(
            identificador, marca_replicada + 1, destinatario=destinatario,
            recurso=recurso, cantidad=cantidad, clave=clave_broker,
        )
        print("Paso 3: RabbitMQ confirmó la publicación en allocations.", flush=True)

    def liberar(identificador):
        respuesta = consultar_api(
            origen, "/liberar", token, {"saga_id": identificador}
        )
        if respuesta != {"saga_id": identificador, "estado": "liberada"}:
            raise RuntimeError("El nodo 3 no confirmó la liberación.")
        print(f"Compensación: reserva liberada para {recurso}.", flush=True)

    print(f"Saga: {saga_id}", flush=True)
    estado = ejecutar_saga(
        base, saga_id, reservar=reservar, replicar=replicar,
        notificar=notificar, liberar=liberar,
        solicitud={"destinatario": destinatario, "recurso": recurso, "cantidad": cantidad},
    )
    print(f"Estado persistido: {estado}", flush=True)
    return estado, recurso


def main():
    argumentos = argparse.ArgumentParser()
    argumentos.add_argument("--simular-fallo-paso-2", action="store_true")
    opciones = argumentos.parse_args()
    clave = None
    if not opciones.simular_fallo_paso_2:
        clave = os.environ.get("RABBITMQ_PASSWORD") or getpass(
            "Contraseña de RabbitMQ para el usuario taller: "
        )
    asignar_cpu(
        str(uuid4()), destinatario="nodo5", cantidad=1,
        simular_fallo=opciones.simular_fallo_paso_2, clave_broker=clave,
    )


if __name__ == "__main__":
    main()
