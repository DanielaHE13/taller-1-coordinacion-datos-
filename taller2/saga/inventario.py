import json
from time import monotonic, sleep
from urllib.request import Request, urlopen


def consultar_api(base_url, ruta, token, datos=None):
    solicitud = Request(
        base_url.rstrip("/") + ruta,
        data=None if datos is None else json.dumps(datos).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    with urlopen(solicitud, timeout=3) as respuesta:
        return json.load(respuesta)


def replicar_cpu(saga_id, *, lider_url, replica_url, token, recurso, cantidad):
    resultado = consultar_api(lider_url, "/asignar", token, {
        "request_id": saga_id,
        "request": {
            "resource": recurso,
            "amounts": {
                "cpu": cantidad,
                "memory_mb": 0,
                "bandwidth_mbps": 0,
            },
        },
    })

    if not resultado.get("accepted") or resultado["operation"]["id"] != saga_id:
        raise RuntimeError("El maestro no confirmó la operación esperada.")

    limite = monotonic() + 10
    while monotonic() < limite:
        copia = consultar_api(replica_url, "/inventario", token)
        recurso_replicado = copia["inventory"].get(recurso, {})
        if recurso_replicado.get("winner_operation") == saga_id:
            return recurso_replicado
        sleep(0.5)

    raise TimeoutError(f"La réplica todavía no confirma la Saga {saga_id}.")
