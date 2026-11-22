import argparse
import os
from time import sleep

from . import agente


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--intervalo", type=int, default=0,
        help="Segundos entre reportes. Usa 0 para enviar un solo reporte.",
    )
    opciones = parser.parse_args()
    if opciones.intervalo < 0:
        parser.error("--intervalo debe ser mayor o igual a cero")

    agente.COORDINATOR_IP = os.environ["COORDINADOR_HOST"]
    agente.NODE_ID = os.environ["NODE_ID"]

    while True:
        respuesta = agente.report_metrics_with_retry()
        if opciones.intervalo == 0:
            if respuesta is None or not respuesta.acknowledged:
                raise SystemExit("El coordinador no confirmó las métricas.")
            return
        sleep(opciones.intervalo)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Agente detenido.")
