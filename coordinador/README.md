
# Servicio de coordinación e inventario

Este paquete contiene la implementación del nodo distribuido: elección del líder, latidos, sincronización de operaciones, materialización del inventario y API HTTP. Cada instancia se inicia con un ID de nodo y usa las direcciones definidas en `nodos.json`.

## Componentes

| Archivo | Responsabilidad |
|---|---|
| `motor.py` | Servicio de inventario, API HTTP, elección Bully con épocas, comprobantes de elección, coordinación y sincronización. |
| `nodo.py` | Coordinador original y punto de entrada compatible para ejecutar la ampliación del inventario. |
| `bitacora.py` | Persistencia SQLite de operaciones, metadatos y conflictos. |
| `versiones.py` | Vectores por recurso, causalidad, reloj de Lamport, materialización determinista y regla de desempate. |
| `redis_inventario.py` | Cliente RESP2 de Redis y backend en memoria para pruebas locales. |
| `nodos.json` | Direcciones y puertos HTTP de los nodos desplegados. |

## Ejecución

La preparación, las credenciales y el inicio de Redis y del servicio se describen en la sección [Preparación y ejecución](../README.md#preparación-y-ejecución) del README principal. Desde la raíz del repositorio, el proceso de inventario se inicia así:

```bash
bash scripts/iniciar_inventario.sh ID
```

El script carga `.env` y ejecuta `coordinador/nodo.py ID --inventario`. También es posible consultar la ayuda del punto de entrada directamente:

```bash
python3 coordinador/nodo.py ID --inventario --help
```

## API

Las rutas para el cliente incluyen:

| Método | Ruta | Uso |
|---|---|---|
| `GET` | `/estado` | Consulta del rol, líder, época, operaciones y conflictos. |
| `GET` | `/inventario` | Lectura de la vista local de Redis y su hash. |
| `GET` | `/conflictos` | Consulta de los conflictos registrados. |
| `POST` | `/inicializar` | Inicialización de un recurso. |
| `POST` | `/asignar` | Asignación de recursos disponible únicamente en el líder. |

Las peticiones internas entre nodos usan autenticación compartida e identidad de nodo. El estado `/estado` también se expone para la consulta de salud del cliente sin autenticación; las demás rutas requieren el token configurado.

## Persistencia y consistencia

El diario SQLite se conserva en `datos/nodo<ID>/` y permite recuperar operaciones y época tras reiniciar el proceso. Redis guarda la vista materializada; los seguidores leen su réplica local, mientras el líder publica las escrituras. La API confirma la publicación en el maestro, no la replicación síncrona.

Durante una partición, las ramas pueden aceptar cambios independientes en sus respectivos líderes. Al reconectar, el diario se sincroniza y las versiones concurrentes se resuelven mediante Lamport mayor y, en caso de empate, ID de nodo menor. Este diseño no ofrece consenso por quórum ni tolerancia bizantina.
