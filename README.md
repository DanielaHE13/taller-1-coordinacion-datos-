# Coordinación distribuida e inventario de recursos

<p align="center">
  <strong>Taller 1 · Sistemas Distribuidos Modernos</strong><br>
  Elección de coordinador, inventario replicado y recuperación ante particiones de red
</p>

---

## Resumen

Este proyecto implementa un servicio distribuido de gestión de recursos para tres nodos. Los nodos eligen un coordinador, mantienen un inventario de CPU, memoria y ancho de banda, registran las operaciones en una bitácora durable y reconcilian cambios concurrentes cuando se restablece la comunicación.

El repositorio incluye el servicio de inventario, un cliente de línea de comandos, scripts de operación, pruebas automatizadas y evidencias de los entregables E3, E4 y E5.

## Contenido

- [Arquitectura](#arquitectura)
- [Comportamiento y decisiones de diseño](#comportamiento-y-decisiones-de-diseño)
- [Nodos](#nodos)
- [Requisitos](#requisitos)
- [Preparación y ejecución](#preparación-y-ejecución)
- [Cliente del inventario](#cliente-del-inventario)
- [Pruebas](#pruebas)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Entregables y evidencias](#entregables-y-evidencias)
- [Alcance y limitaciones](#alcance-y-limitaciones)
- [Equipo](#equipo)

## Arquitectura

```text
┌───────────────────────┐       HTTP + token       ┌────────────────────────┐
│ Cliente de terminal   │ ───────────────────────► │ Servicio en cada nodo  │
│ agentes/cliente.py    │                          │ coordinador/motor.py   │
└───────────────────────┘                          └───────────┬────────────┘
                                                               │
                           ┌───────────────────────────────────┼──────────────────────────────────┐
                           │                                   │                                  │
                    ┌──────▼──────┐                     ┌──────▼──────┐                    ┌──────▼──────┐
                    │    nodo1    │ ◄──── HTTP/RPC ───► │    nodo2    │ ◄── HTTP/RPC ───► │    nodo3    │
                    │ Redis +     │                     │ Redis +     │                    │ Redis +     │
                    │ SQLite      │                     │ SQLite      │                    │ SQLite      │
                    └─────────────┘                     └─────────────┘                    └─────────────┘
```

Cada nodo ejecuta el servicio HTTP del coordinador y mantiene su propio diario SQLite. Redis almacena la vista materializada del inventario: el coordinador elegido escribe en el maestro y los demás nodos consultan su réplica local. Los nodos intercambian estado y operaciones por HTTP para detectar cambios y sincronizar el diario.

## Comportamiento y decisiones de diseño

| Área | Decisión |
|---|---|
| Elección | Algoritmo Matón (*Bully*): compite el nodo de mayor ID que responde en esa elección. |
| Coordinación | Latidos, épocas persistentes y comprobantes de elección registrados por el nodo ganador. |
| Persistencia de operaciones | Diario SQLite local con modo WAL y sincronización durable. |
| Vista del inventario | Redis maestro-réplica; el líder actual configura la topología y publica la vista. |
| Versionado | Vector de versión por recurso y reloj de Lamport por operación. |
| Conflictos | Entre operaciones concurrentes gana el Lamport mayor; si empatan, el ID numérico de nodo menor. |
| Asignaciones | Solo escribe el líder. Se rechazan solicitudes inválidas o que excedan la capacidad disponible. |
| Confirmación | La escritura se confirma en el maestro Redis; no se exige confirmación de las réplicas. |
| Lecturas | Cada nodo consulta su Redis local; una réplica puede mostrar una vista atrasada durante una partición. |

Las operaciones conservan sus vectores originales. Al reunir la bitácora, los nodos vuelven a materializar el inventario con la misma regla de desempate, lo que permite converger sin depender del orden de llegada de los mensajes.

## Nodos

| Nodo | ID | Sistema operativo | Dirección Tailscale |
|---|---:|---|---|
| nodo1 | 1 | Debian 13 | `100.101.47.119` |
| nodo2 | 2 | Ubuntu Server 26.04.1 | `100.92.63.103` |
| nodo3 | 3 | Debian 13 | `100.98.74.61` |

La configuración de host y puerto HTTP se encuentra en [`coordinador/nodos.json`](./coordinador/nodos.json). El servicio escucha en el puerto definido allí; Redis utiliza el puerto indicado para cada nodo o, si no se especifica, el `6379` predeterminado.

## Requisitos

- Tres máquinas virtuales con Python 3 y Redis Server.
- Conectividad entre los nodos por Tailscale y acceso SSH mediante clave pública para las tareas de operación.
- El repositorio disponible en cada máquina.
- Un token compartido para la API de al menos 16 caracteres y una clave compartida de Redis hexadecimal de al menos 32 caracteres.
- Las mismas credenciales compartidas configuradas localmente en los tres nodos.

El proyecto usa la biblioteca estándar de Python; no incluye un archivo de dependencias de paquetes.

## Preparación y ejecución

Realiza estos pasos en cada máquina, desde la raíz del repositorio. Sustituye `ID` por el identificador de ese equipo: `1`, `2` o `3`.

1. Prepara la configuración local y las credenciales:

   ```bash
   bash scripts/preparar_inventario.sh ID
   ```

   El script solicita las credenciales si aún no existe `.env` y genera la configuración local de Redis. Los secretos se guardan en archivos ignorados por Git.

2. Inicia Redis con la configuración del nodo:

   ```bash
   redis-server config/redis.local.conf
   ```

3. Inicia el servicio de inventario:

   ```bash
   bash scripts/iniciar_inventario.sh ID
   ```

   El script carga `.env` y guarda la salida del proceso en `logs/nodo<ID>_inventario.log`. Mantén el proceso activo en cada equipo.

4. Comprueba el estado de un nodo desde la raíz del proyecto:

   ```bash
   python3 -m agentes.cliente --nodo 1 estado
   ```

La configuración de capacidades y temporizadores parte de [`config/inventario.example.json`](./config/inventario.example.json). La función de compatibilidad usa `config/inventario.local.json` si existe; de lo contrario, utiliza el archivo de ejemplo. No guardes credenciales en el archivo de ejemplo ni en el repositorio.

## Cliente del inventario

El cliente se ejecuta con `python3 -m agentes.cliente --nodo ID ACCIÓN`. Las acciones disponibles son:

| Acción | Ejemplo | Descripción |
|---|---|---|
| `estado` | `python3 -m agentes.cliente --nodo 1 estado` | Consulta el rol, el líder y el estado de coordinación. |
| `inventario` | `python3 -m agentes.cliente --nodo 1 inventario` | Consulta la vista local del inventario. |
| `conflictos` | `python3 -m agentes.cliente --nodo 1 conflictos` | Consulta los conflictos registrados. |
| `inicializar` | `python3 -m agentes.cliente --nodo 1 inicializar` | Inicializa los recursos configurados. |
| `asignar` | `python3 -m agentes.cliente --nodo 1 asignar --recurso node1 --cpu 1` | Solicita una asignación al líder. |

Las acciones distintas de `estado` requieren `TALLER_TOKEN` en el entorno. En los nodos, carga las variables con `source .env` antes de usar el cliente. Para asignar recursos, pueden indicarse `--cpu`, `--memoria` y `--ancho-banda`; los valores deben ser enteros no negativos y al menos uno debe ser mayor que cero. También se puede elegir un recurso con `--recurso` y proporcionar un `--request-id` UUID para repetir una solicitud de forma idempotente.

Durante una partición, una asignación aceptada puede ser provisional. Las escrituras de ramas aisladas se reconcilian al recuperar la conectividad.

## Pruebas

Ejecuta la suite desde la raíz del repositorio:

```bash
python3 -m unittest discover -s pruebas -v
```

Las pruebas cubren la elección y recuperación del líder, las particiones y la reconexión, los conflictos y su resolución, la convergencia, la compatibilidad con el coordinador existente y casos de rechazo. Para las pruebas de aplicación se utiliza un backend Redis en memoria; estas no sustituyen una validación con Redis real en las máquinas virtuales.

## Estructura del repositorio

| Ruta | Contenido |
|---|---|
| [`agentes/`](./agentes/README.md) | Cliente de línea de comandos para consultar y modificar el inventario. |
| [`coordinador/`](./coordinador/README.md) | Servicio, elección, sincronización, diario, versionado y acceso a Redis. |
| `config/` | Configuración de ejemplo y destino de configuraciones locales ignoradas por Git. |
| `scripts/` | Preparación e inicio del servicio, captura de estado, verificación de conectividad y simulación de particiones. |
| `pruebas/` | Pruebas automatizadas de aplicación, integración lógica y regresión. |
| [`evidencias/`](./evidencias/README.md) | Evidencias organizadas por entregable. |
| [`logs/`](./logs/README.md) | Registros de ejecuciones y pruebas. |
| [`informe/`](./informe/README.md) | Espacio previsto para el informe técnico PDF. |
| `datos/` | Datos locales de ejecución, ignorados por Git. |

## Entregables y evidencias

| Entregable | Descripción | Documentación |
|---|---|---|
| E1 | Repositorio, código, scripts y documentación. | Este README y los README de cada componente. |
| E2 | Informe técnico de 6 a 8 páginas en PDF. | [`informe/README.md`](./informe/README.md). |
| E3 | Verificación inicial de conectividad entre nodos y configuración de SSH. | [`evidencias/E3/README.md`](./evidencias/E3/README.md). |
| E4 | Elección del líder y recuperación ante caída o desconexión. | [`evidencias/E4/README.md`](./evidencias/E4/README.md). |
| E5 | Partición de red, escrituras concurrentes, resolución del conflicto y convergencia. | [`evidencias/E5/README.md`](./evidencias/E5/README.md). |

Consulta el [índice de evidencias](./evidencias/README.md) para acceder a las capturas, los registros y los archivos de estado JSON y CSV.

## Alcance y limitaciones

Este trabajo es una implementación académica de coordinación y reconciliación, no un sistema de consenso por quórum ni una solución con tolerancia bizantina. En una partición pueden existir líderes y vistas distintos en cada lado; el servicio acepta escrituras únicamente en el líder local de cada rama y las trata como provisionales hasta la reconciliación. La confirmación de escritura requiere una respuesta del Redis maestro, no de las réplicas.

La convergencia se verifica comparando la vista del inventario, el diario, los líderes y el estado de las réplicas. Los resultados de las pruebas locales en memoria no demuestran por sí solos el comportamiento de Redis real ni de la red de producción.

## Equipo

- Daniela Huertas
- Oscar Castillo
- Sebastian Saldarriaga
- Andres Valencia
- Lorena Rubio
