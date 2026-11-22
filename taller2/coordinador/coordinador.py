from concurrent import futures
import time
import grpc
import telematica_pb2
import telematica_pb2_grpc

class CoordinatorServicer(telematica_pb2_grpc.CoordinatorServiceServicer):
    
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
        # Lógica para procesar la solicitud de asignación (incluyendo el reloj de Lamport)
        print(f"[ASIGNACIÓN] Solicitud de {request.requested_amount} de '{request.resource_type}' desde el nodo {request.node_id}")
        print(f" -> Lamport Timestamp recibido: {request.lamport_timestamp}")
        
        # Simular una respuesta exitosa de asignación
        return telematica_pb2.AllocationResponse(
            success=True,
            allocation_id="ALLOC-2026-001",
            assigned_node=request.node_id,
            reason="Recurso asignado exitosamente."
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
