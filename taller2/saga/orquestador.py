from .estado import finalizar_saga, iniciar_saga


class FalloSinEscritura(Exception):
    """El paso 2 falló y se sabe que la asignación no fue registrada."""


def ejecutar_saga(
    ruta, saga_id, *, reservar, replicar, notificar, liberar, solicitud=None
):
    estado = iniciar_saga(ruta, saga_id, solicitud)
    if estado != "en_curso":
        return estado
    reservar(saga_id)

    try:
        replicar(saga_id)
    except FalloSinEscritura:
        liberar(saga_id)
        finalizar_saga(ruta, saga_id, "compensada")
        return "compensada"

    notificar(saga_id)
    finalizar_saga(ruta, saga_id, "completada")
    return "completada"
