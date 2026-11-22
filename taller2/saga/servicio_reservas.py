from hmac import compare_digest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
from uuid import UUID

from .reservas import liberar_reserva, registrar_reserva


def servir(host, puerto, token, ruta, capacidad):
    class Manejador(BaseHTTPRequestHandler):
        def responder(self, codigo, datos):
            cuerpo = json.dumps(datos).encode()
            self.send_response(codigo)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(cuerpo)))
            self.end_headers()
            self.wfile.write(cuerpo)

        def do_POST(self):
            recibido = self.headers.get("Authorization", "").encode()
            if not compare_digest(recibido, f"Bearer {token}".encode()):
                return self.responder(401, {"error": "Token inválido"})

            if self.path not in {"/reservar", "/liberar"}:
                return self.responder(404, {"error": "Ruta inexistente"})

            try:
                longitud = int(self.headers.get("Content-Length", "0"))
                if not 0 < longitud <= 4096:
                    raise ValueError("Tamaño de solicitud inválido")
                datos = json.loads(self.rfile.read(longitud))
                saga_id = str(UUID(datos["saga_id"]))
                cantidad = datos.get("cantidad")
                if self.path == "/reservar" and (
                    type(cantidad) is not int or cantidad <= 0
                ):
                    raise ValueError("La cantidad debe ser un entero positivo")
            except (ValueError, KeyError, TypeError, AttributeError):
                return self.responder(400, {"error": "Solicitud inválida"})

            try:
                if self.path == "/reservar":
                    registrar_reserva(ruta, saga_id, cantidad, capacidad)
                    estado = "reservada"
                else:
                    liberar_reserva(ruta, saga_id)
                    estado = "liberada"
            except ValueError as error:
                return self.responder(409, {"error": str(error)})

            self.responder(200, {"saga_id": saga_id, "estado": estado})

    with ThreadingHTTPServer((host, puerto), Manejador) as servidor:
        print(f"Servicio de reservas escuchando en {host}:{puerto}", flush=True)
        servidor.serve_forever()


if __name__ == "__main__":
    base = Path(os.environ.get("RESERVAS_DB", "datos/reservas_taller2.sqlite3"))
    base.parent.mkdir(parents=True, exist_ok=True)
    servir(
        os.environ["RESERVAS_HOST"],
        int(os.environ.get("RESERVAS_PORT", "50052")),
        os.environ["TALLER_TOKEN"],
        base,
        int(os.environ["RESERVAS_CAPACIDAD_CPU"]),
    )
