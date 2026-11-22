from concurrent import futures
from hmac import compare_digest
import os
from threading import Lock
import time
from uuid import UUID, uuid4
import grpc
import telematica_pb2
import telematica_pb2_grpc

class CoordinatorServicer(telematica_pb2_grpc.CoordinatorServiceServicer):
    def __init__(self):
        self.asignaciones = Lock()


    def ReportMetrics(self, request, context):
        # Lógica para recibir métricas del agente
        print(f"[MÉTRICAS] Recibidas del nodo: {request.node_id}")
        print(f" -> CPU: {request.cpu_usage}% | Memoria: {request.memory_usage}% | Estado: {request.status}")

        # Responder confirmación al agente
        return telematica_pb2.MetricsReportResponse(
            acknowledged=True,
            message="Métricas procesadas correctamente por el coordinador."
        )

    def RequestAllocation(self, request, context):
        from taller2.saga.ejecutar import asignar_cpu

        token = os.environ.get("TALLER_TOKEN", "")
        auth = dict(context.invocation_metadata()).get("authorization", "")
        if not token:
            context.abort(grpc.StatusCode.FAILED_PRECONDITION, "Falta configurar TALLER_TOKEN.")
        if not compare_digest(auth.encode(), f"Bearer {token}".encode()):
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Token inválido.")
        if (not request.node_id.strip() or request.resource_type.upper() != "CPU"
                or request.requested_amount < 1 or request.lamport_timestamp < 0):
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Se requiere un nodo y una cantidad de CPU positiva.")
        try:
            saga_id = str(UUID(request.request_id)) if request.request_id else str(uuid4())
        except ValueError:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "request_id debe ser un UUID.")

        with self.asignaciones:
            if not context.is_active():
                context.abort(grpc.StatusCode.DEADLINE_EXCEEDED, "La solicitud expiró antes de asignar.")
            try:
                estado, recurso = asignar_cpu(
                    saga_id, destinatario=request.node_id,
                    cantidad=request.requested_amount, marca_solicitud=request.lamport_timestamp,
                )
            except ValueError as error:
                context.abort(grpc.StatusCode.FAILED_PRECONDITION, str(error))
            except Exception as error:
                print(f"[ASIGNACIÓN] Saga {saga_id}: {type(error).__name__}", flush=True)
                return telematica_pb2.AllocationResponse(
                    success=False, allocation_id=saga_id,
                    reason="Asignación sin confirmar. Reintenta con el mismo request_id.",
                )

        return telematica_pb2.AllocationResponse(
            success=estado == "completada", allocation_id=saga_id,
            assigned_node=recurso.replace("node", "nodo", 1) if estado == "completada" else "",
            reason=f"Saga {estado}.",
        )


def serve():
    # Inicia el servidor gRPC escuchando en todas las interfaces en el puerto 50051
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    telematica_pb2_grpc.add_CoordinatorServiceServicer_to_server(CoordinatorServicer(), server)

    server.add_insecure_port('[::]:50051')
    server.start()
    print("Servidor Coordinador gRPC iniciado en el puerto 50051...")

    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()
