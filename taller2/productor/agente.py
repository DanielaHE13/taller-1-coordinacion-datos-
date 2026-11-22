import time
import grpc
import telematica_pb2
import telematica_pb2_grpc

COORDINATOR_IP = "100.74.54.112"
NODE_ID = "Agente-Node-02"
lamport_clock = 0

def tick_lamport():
    global lamport_clock
    lamport_clock += 1
    return lamport_clock

def report_metrics_with_retry():
    target = f"{COORDINATOR_IP}:50051"
    for attempt in range(1, 6):
        try:
            with grpc.insecure_channel(target) as channel:
                stub = telematica_pb2_grpc.CoordinatorServiceStub(channel)
                req = telematica_pb2.MetricsReportRequest(
                    node_id=NODE_ID,
                    timestamp=int(time.time()),
                    cpu_usage=45.5,
                    memory_usage=60.2,
                    status="OK"
                )
                resp = stub.ReportMetrics(req, timeout=3)
                print(f"[MÉTRICAS] ack={resp.acknowledged} | msg={resp.message}")
                return resp
        except grpc.RpcError as e:
            wait = 2 ** attempt
            print(f"[REINTENTO {attempt}] Fallo gRPC ({e.code()}). Esperando {wait}s...")
            time.sleep(wait)

def request_resource(resource_type="CPU", amount=2):
    target = f"{COORDINATOR_IP}:50051"
    lc = tick_lamport()
    with grpc.insecure_channel(target) as channel:
        stub = telematica_pb2_grpc.CoordinatorServiceStub(channel)
        req = telematica_pb2.AllocationRequest(
            node_id=NODE_ID,
            resource_type=resource_type,
            requested_amount=amount,
            lamport_timestamp=lc
        )
        print(f"[ASIGNACIÓN] Solicitando {amount} {resource_type} | Lamport={lc}...")
        resp = stub.RequestAllocation(req, timeout=3)
        print(f"[RESPUESTA ASIGNACIÓN] success={resp.success} | id={resp.allocation_id} | nodo={resp.assigned_node} | motivo={resp.reason}")
        return resp

if __name__ == '__main__':
    report_metrics_with_retry()
    request_resource("CPU", 2)
    request_resource("CPU", 4)
