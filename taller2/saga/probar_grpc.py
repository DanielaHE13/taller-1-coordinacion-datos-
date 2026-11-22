"""Prueba de asignación real en un proyecto Compose de laboratorio."""
import os
from uuid import NAMESPACE_URL, uuid5

import grpc
from telematica_pb2 import AllocationRequest
from telematica_pb2_grpc import CoordinatorServiceStub

from .inventario import consultar_api


def main():
    token = os.environ["TALLER_TOKEN"]
    lider = os.environ["SAGA_LIDER_URL"]
    replica = os.environ["SAGA_REPLICA_URL"]
    recurso = os.environ.get("SAGA_RECURSO", "node3")
    estado = consultar_api(lider, "/estado", token)
    if estado["nodo"] != estado["lider"]:
        raise SystemExit(f"El nodo configurado aún no es líder: {estado['lider']}")

    inicio = str(uuid5(NAMESPACE_URL, "taller2-aula/inicializar/" + recurso))
    consultar_api(lider, "/inicializar", token, {
        "request_id": inicio,
        "request": {"resource": recurso},
    })

    saga_id = str(uuid5(NAMESPACE_URL, "taller2-aula/request-allocation/" + recurso))
    peticion = AllocationRequest(
        node_id="agente-compose", resource_type="CPU", requested_amount=1,
        lamport_timestamp=1, request_id=saga_id,
    )

    with grpc.insecure_channel("127.0.0.1:50051") as canal:
        cliente = CoordinatorServiceStub(canal)
        for numero in (1, 2):
            confirmacion = cliente.RequestAllocation(
                peticion, timeout=25, metadata=(("authorization", f"Bearer {token}"),),
            )
            if not confirmacion.success or confirmacion.allocation_id != saga_id:
                raise SystemExit(f"La solicitud no se confirmó: {confirmacion}")
            print(f"Solicitud {numero} confirmada por gRPC | ID: {confirmacion.allocation_id}")

    copia = consultar_api(replica, "/inventario", token)["inventory"][recurso]
    if copia["winner_operation"] != saga_id or copia["available"]["cpu"] != 1:
        raise SystemExit(f"La réplica no tiene el saldo esperado: {copia}")
    print(f"Réplica verificada | Recurso: {recurso} | CPU libre: 1")


if __name__ == "__main__":
    main()
