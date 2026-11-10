import json
import sys
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen


CARPETA = Path(__file__).parent
CONFIG = json.loads((CARPETA / "nodos.json").read_text(encoding="utf-8"))
NODOS = {int(k): v for k, v in CONFIG.items()}


class Nodo:
    def __init__(self, identificador):
        if identificador not in NODOS:
            raise ValueError("El ID debe existir en nodos.json")

        self.id = identificador
        self.lock = threading.Lock()
        self.bloqueo_eleccion = threading.Lock()
        self.rol = "seguidor"
        self.lider = None
        self.ultimo_latido = time.monotonic() - 5

    def registrar(self, evento):
        hora = datetime.now().strftime("%H:%M:%S")
        print(f"[{hora}] nodo{self.id}: {evento}", flush=True)

    def enviar(self, destino, ruta, datos=None):
        nodo = NODOS[destino]
        contenido = None if datos is None else json.dumps(datos).encode("utf-8")
        solicitud = Request(
            f"http://{nodo['host']}:{nodo['puerto']}/{ruta}",
            data=contenido,
            headers={"Content-Type": "application/json"},
        )
        with urlopen(solicitud, timeout=1.5) as respuesta:
            return json.loads(respuesta.read().decode("utf-8"))

    def aceptar_lider(self, id_lider):
        if id_lider not in NODOS or id_lider < self.id:
            return False

        with self.lock:
            cambio = self.lider != id_lider
            self.lider = id_lider
            self.rol = "líder" if id_lider == self.id else "seguidor"
            self.ultimo_latido = time.monotonic()

        if cambio:
            self.registrar(f"reconoce a nodo{id_lider} como líder")
        return True

    def iniciar_eleccion(self):
        if self.bloqueo_eleccion.acquire(blocking=False):
            threading.Thread(target=self.elegir, daemon=True).start()

    def elegir(self):
        try:
            with self.lock:
                self.rol = "candidato"
                self.lider = None
                self.ultimo_latido = time.monotonic()

            self.registrar("inicia una elección")
            nodos_mayores = [n for n in NODOS if n > self.id]
            respondieron = []

            for otro in nodos_mayores:
                try:
                    self.enviar(otro, "eleccion", {"candidato": self.id})
                    respondieron.append(otro)
                except Exception:
                    pass

            if respondieron:
                self.registrar(
                    f"nodos con ID mayor respondieron: {respondieron}; espera su anuncio"
                )
                with self.lock:
                    self.rol = "seguidor"
                    self.ultimo_latido = time.monotonic()
                return

            self.aceptar_lider(self.id)
            self.registrar("gana la elección")
            for otro in NODOS:
                if otro != self.id:
                    try:
                        self.enviar(otro, "coordinador", {"lider": self.id})
                    except Exception:
                        pass
        finally:
            self.bloqueo_eleccion.release()

    def vigilar(self):
        while True:
            time.sleep(1)

            with self.lock:
                rol = self.rol
                lider = self.lider
                vencio = time.monotonic() - self.ultimo_latido > 5

            if rol == "líder":
                for otro in NODOS:
                    if otro != self.id:
                        try:
                            self.enviar(otro, "latido", {"lider": self.id})
                        except Exception:
                            pass
            elif vencio:
                self.registrar(f"no recibe latidos del líder {lider}")
                self.iniciar_eleccion()


def crear_servidor(nodo):
    class Manejador(BaseHTTPRequestHandler):
        def responder(self, codigo, contenido):
            respuesta = json.dumps(contenido).encode("utf-8")
            self.send_response(codigo)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(respuesta)))
            self.end_headers()
            self.wfile.write(respuesta)

        def do_GET(self):
            if self.path == "/estado":
                with nodo.lock:
                    estado = {
                        "nodo": nodo.id,
                        "rol": nodo.rol,
                        "lider": nodo.lider,
                    }
                self.responder(200, estado)
            else:
                self.responder(404, {"error": "ruta no encontrada"})

        def do_POST(self):
            largo = int(self.headers.get("Content-Length", "0"))
            datos = json.loads(self.rfile.read(largo)) if largo else {}
            if self.path == "/eleccion":
                candidato = datos.get("candidato")

                if (
                    type(candidato) is not int
                    or candidato not in NODOS
                    or candidato >= nodo.id
                ):
                    self.responder(400, {"error": "ID de candidato inválido"})
                    return

                with nodo.lock:
                    ya_es_lider = nodo.rol == "líder"

                nodo.registrar(f"recibe solicitud de elección de nodo{candidato}")

                if not ya_es_lider:
                    nodo.iniciar_eleccion()

                self.responder(
                    200,
                    {"recibido": True, "lider": nodo.id if ya_es_lider else None},
                )
           

            elif self.path == "/coordinador":
                aceptado = nodo.aceptar_lider(datos.get("lider"))
                self.responder(200 if aceptado else 409, {"aceptado": aceptado})

            elif self.path == "/latido":
                aceptado = nodo.aceptar_lider(datos.get("lider"))
                self.responder(200 if aceptado else 409, {"aceptado": aceptado})

            else:
                self.responder(404, {"error": "ruta no encontrada"})

        def log_message(self, formato, *argumentos):
            pass

    direccion = NODOS[nodo.id]
    servidor = ThreadingHTTPServer(
        ("0.0.0.0", direccion["puerto"]),
        Manejador,
    )
    return servidor


def main():
    if "--inventario" in sys.argv:
        sys.path.insert(0, str(CARPETA.parent))
        from coordinador.motor import main_compatible
        main_compatible()
        return

    if len(sys.argv) != 2:
        print("Uso: python3 nodo.py ID")
        print("Ejemplo: python3 nodo.py 2")
        raise SystemExit(1)

    nodo = Nodo(int(sys.argv[1]))
    servidor = crear_servidor(nodo)

    threading.Thread(target=nodo.vigilar, daemon=True).start()
    nodo.registrar(f"activo en el puerto {NODOS[nodo.id]['puerto']}")

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        nodo.registrar("se detuvo")
        servidor.server_close()


if __name__ == "__main__":
    main()
