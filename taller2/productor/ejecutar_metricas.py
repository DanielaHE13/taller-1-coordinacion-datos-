import os

from . import agente


if __name__ == "__main__":
    agente.COORDINATOR_IP = os.environ["COORDINADOR_HOST"]
    agente.NODE_ID = os.environ["NODE_ID"]
    respuesta = agente.report_metrics_with_retry()
    if respuesta is None or not respuesta.acknowledged:
        raise SystemExit("El coordinador no confirmó las métricas.")
