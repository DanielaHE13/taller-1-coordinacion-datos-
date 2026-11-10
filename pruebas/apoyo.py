from contextlib import contextmanager
from pathlib import Path
import shutil
import uuid
import tempfile
import time


@contextmanager
def directorio_prueba():
    parent = Path(tempfile.gettempdir()).resolve()/"taller_coordinacion_pruebas"
    parent.mkdir(exist_ok=True)
    target = parent/("prueba_"+uuid.uuid4().hex)
    target.mkdir()
    try:
        yield str(target)
    finally:
        resolved = target.resolve()
        if resolved.parent != parent.resolve() or not resolved.name.startswith("prueba_"):
            raise RuntimeError("Destino de limpieza fuera del directorio de pruebas")
        for attempt in range(8):
            try:
                shutil.rmtree(resolved)
                break
            except PermissionError:
                if attempt == 7:
                    raise
                time.sleep(0.15 * (attempt + 1))
