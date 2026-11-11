# E5 · Partición de red, conflicto y convergencia

Este entregable documenta el comportamiento del inventario antes, durante y después de aislar nodo3 del grupo formado por nodo1 y nodo2. Las capturas muestran estados locales distintos durante la partición y la convergencia del inventario después de restablecer la comunicación.

## Evidencia por nodo

| Directorio | Archivos destacados |
|---|---|
| [`nodo1/`](./nodo1/) | Capturas `E5_antes`, `E5_durante_grupo` y `E5_despues` en JSON/CSV; `inventario_inicial`; `eventos_inventario.jsonl` y `nodo1_inventario.log`. |
| [`nodo2/`](./nodo2/) | Captura `inventario_inicial` en JSON/CSV y `eventos_inventario.jsonl`. |
| [`nodo3/`](./nodo3/) | Capturas `inventario_inicial`, `E5_durante_aislado` y `cierre` en JSON/CSV; `eventos_inventario.jsonl`. |

Cada captura JSON incluye la hora UTC, los estados que respondieron, el líder observado, la vista de inventario y sus hashes. El CSV resume los datos por nodo y recurso; los archivos `.jsonl` y `.log` conservan eventos del proceso.

## Comparación de las capturas

| Fase | Captura UTC | Nodos observados y líder | Operaciones | Conflictos detectados/resueltos | CPU disponible en `node1` | Hash de inventario |
|---|---|---|---:|---:|---:|---|
| Antes de la partición | 04:32:56 | Nodos 1, 2 y 3; líder 3 | 4 | 0 / 0 | 2 | `e5ecd6ec…` |
| Grupo conectado | 04:43:00 | Nodos 1 y 2; líder 2 | 5 | 0 / 0 | 0 | `ae0ee7df…` |
| Nodo aislado | 04:41:37 | Nodo 3; aún se considera líder | 5 | 0 / 0 | 1 | `10548c61…` |
| Después de reconectar | 04:46:49 | Nodos 1, 2 y 3; líder 2 | 6 | 1 / 1 | 0 | `ae919189…` |

Los hashes se muestran abreviados para facilitar la lectura; los valores completos están en los JSON. Las horas corresponden a las capturas y no implican un orden absoluto entre los eventos locales.

## Comportamiento durante la partición

El grupo conectado (nodos 1 y 2) y nodo3 aislado conservaron vistas distintas del recurso `node1`: 0 CPU disponible en la captura del grupo y 1 CPU en la captura local de nodo3. Ambos lados registraban cinco operaciones y todavía no mostraban conflictos detectados en esas capturas. Nodo3 mantenía localmente el rol de líder durante su aislamiento; el grupo conectado registraba a nodo2 como líder.

La bitácora de nodo3 contiene un evento `write_accepted` a las 04:41:15 UTC, consistente con la captura del lado aislado. La bitácora de nodo2 también contiene un `write_accepted`, pero está fechado a las 02:24:20 UTC, fuera del intervalo de las capturas de estado de esta secuencia. Por ese desfase, no se presenta como una operación ocurrida en un instante determinado de la partición.

## Resolución y convergencia

Tras la reconexión, la captura [`E5_despues_20261110T044649_486978.json`](./nodo1/E5_despues_20261110T044649_486978.json) muestra los mismos resultados en los tres nodos:

- **Líder:** nodo2, época 8.
- **Operaciones:** 6.
- **Conflictos:** 1 detectado y 1 resuelto.
- **Hash del inventario:** `ae91918921eb22555418af91bd9bceb8a06aca39bfd6872493ac2d5fb9ca30bc`.
- **Hash del diario:** `945a785254103baaf4177aae452949e7ae4ded4649d65bef4e162f1d3bbb9e7f`.

El evento de nodo1 identifica un conflicto sobre `node1`. Se aplicó la regla `max_lamport_then_min_node_id`: gana la operación con el Lamport mayor y, en caso de empate, la originada por el nodo con el ID menor. La coincidencia de hashes y contadores de conflicto en la captura final respalda la convergencia del estado documentado.

## Interpretación de los tiempos

Las capturas de estado usan marcas UTC. Los eventos se escriben en cada nodo y la hora de un registro aislado puede no coincidir con la secuencia de capturas; se documentan las diferencias conocidas en vez de asumir una cronología global. Para el contexto de los demás entregables, vuelve al [índice de evidencias](../README.md).
