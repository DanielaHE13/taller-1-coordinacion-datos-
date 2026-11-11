
# Cliente de línea de comandos

El módulo `agentes.cliente` permite consultar el servicio distribuido y enviar solicitudes de inicialización o asignación al nodo indicado. Las peticiones se dirigen a la dirección y al puerto configurados para ese nodo en [`../coordinador/nodos.json`](../coordinador/nodos.json).

## Requisitos

- Python 3 disponible en el entorno.
- El servicio de inventario activo en el nodo consultado.
- `TALLER_TOKEN` cargado en el entorno para todas las acciones, excepto `estado`.

En un nodo preparado, carga las credenciales locales antes de las consultas autenticadas:

```bash
source .env
```

## Uso

```bash
python3 -m agentes.cliente --nodo ID ACCIÓN [opciones]
```

| Acción | Ejemplo | Resultado |
|---|---|---|
| `estado` | `python3 -m agentes.cliente --nodo 1 estado` | Estado del nodo, su rol y el líder conocido. |
| `inventario` | `python3 -m agentes.cliente --nodo 1 inventario` | Vista del inventario en el Redis local del nodo. |
| `conflictos` | `python3 -m agentes.cliente --nodo 1 conflictos` | Conflictos detectados y resultado de su resolución. |
| `inicializar` | `python3 -m agentes.cliente --nodo 1 inicializar` | Inicializa todos los recursos; `--recurso node1` limita la operación a uno. |
| `asignar` | `python3 -m agentes.cliente --nodo 1 asignar --recurso node1 --cpu 1` | Solicita una asignación de recursos al líder. |

Las opciones de asignación son `--cpu`, `--memoria` y `--ancho-banda`; deben ser enteros no negativos y al menos una debe ser positiva. El servidor rechaza solicitudes que exceden la capacidad disponible o que se envían a un nodo que no es el líder.

El cliente genera un UUID para cada solicitud de inicialización o asignación. Para reintentar una asignación de forma idempotente, reutiliza el mismo identificador:

```bash
python3 -m agentes.cliente --nodo 1 asignar --recurso node1 --cpu 1 --request-id UUID
```

En el nodo aislado se puede apuntar a `localhost` con `--local`. Para consultar las opciones completas:

```bash
python3 -m agentes.cliente --help
```
