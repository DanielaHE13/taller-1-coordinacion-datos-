"""Cliente RESP2 mínimo. Cada comando usa una conexión autenticada.

No implementa Redis: habla con Redis Server real en las VM.
MemoryBackend existe exclusivamente para las pruebas locales.
"""
import json
import socket
from .versiones import canonical


class RedisError(RuntimeError):
    pass


class RedisBackend:
    def __init__(self, password, port=6379, timeout=2):
        self.password, self.port, self.timeout = password, port, timeout

    @staticmethod
    def _send(stream, *args):
        parts = [str(x).encode() for x in args]
        stream.write(b"*%d\r\n" % len(parts) + b"".join(
            b"$%d\r\n" % len(p) + p + b"\r\n" for p in parts))
        stream.flush()

    @classmethod
    def _read(cls, stream):
        line = stream.readline()
        if not line.endswith(b"\r\n"):
            raise RedisError("Respuesta Redis incompleta")
        kind, data = line[:1], line[1:-2]
        if kind == b"-":
            raise RedisError(data.decode())
        if kind == b"+":
            return data.decode()
        if kind == b":":
            return int(data)
        if kind == b"$":
            n = int(data)
            if n < 0:
                return None
            value = stream.read(n)
            if len(value) != n or stream.read(2) != b"\r\n":
                raise RedisError("Trama Redis truncada")
            return value.decode()
        if kind == b"*":
            return [cls._read(stream) for _ in range(int(data))]
        raise RedisError("Tipo RESP no soportado")

    def command(self, *args):
        with socket.create_connection(("127.0.0.1", self.port), self.timeout) as sock:
            with sock.makefile("rwb") as stream:
                self._send(stream, "AUTH", self.password)
                self._read(stream)
                self._send(stream, *args)
                return self._read(stream)

    def promote(self):
        if self.info().get("role") != "master":
            self.command("REPLICAOF", "NO", "ONE")

    def follow(self, host, port):
        info = self.info()
        if (info.get("role") != "slave" or info.get("master_host") != host
                or info.get("master_port") != str(port)):
            self.command("REPLICAOF", host, port)

    def info(self):
        return dict(line.split(":", 1) for line in
                    self.command("INFO", "replication").splitlines()
                    if ":" in line and not line.startswith("#"))

    def write(self, views):
        # Un único SET publica todo el pequeño inventario de forma atómica.
        # 1 confirmación local del maestro; 0 confirmaciones de réplicas.
        self.command("SET", "taller:inventory", canonical(views))

    def read(self):
        raw = self.command("GET", "taller:inventory")
        return json.loads(raw) if raw else {}


class MemoryBackend:
    """Pruebas de aplicación; no valida la replicación de Redis."""
    is_memory = True

    def __init__(self):
        self.views, self.role = {}, "master"

    def promote(self):
        self.role = "master"

    def follow(self, host, port):
        self.role = "slave"

    def info(self):
        return {"role": self.role, "test_backend": True}

    def write(self, views):
        self.views = json.loads(canonical(views))

    def read(self):
        return json.loads(canonical(self.views))

