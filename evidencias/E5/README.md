# E5: Partición de red y resolución de conflictos

Esta carpeta reúne los registros del experimento de partición de red. La evidencia está organizada por nodo y contiene capturas del inventario antes, durante y después del aislamiento, además de los eventos de ejecución.

## Estructura de la evidencia

- `nodo1/`: estados del inventario y registro `nodo1_inventario.log`.
- `nodo2/`: inventario inicial y eventos registrados por nodo2.
- `nodo3/`: inventario inicial, estado durante el aislamiento, cierre y eventos registrados por nodo3.

Los archivos CSV facilitan la lectura tabular de cada captura. Los JSON conservan el estado detallado de los nodos y los hashes. Los archivos `eventos_inventario.jsonl` registran eventos locales.

## Resultados antes, durante y después

| Fase | Nodos que responden / líder observado | Operaciones y conflicto | CPU disponible en `node1` | Hash del inventario |
|---|---|---|---:|---|
| Antes de la partición (`E5_antes`, 04:32:56 UTC) | Nodos 1, 2 y 3; líder 3 | 4 operaciones; 0 conflictos | 2 | `e5ecd6ec…` |
| Durante: grupo conectado (`E5_durante_grupo`, 04:43:00 UTC) | Nodos 1 y 2 responden; nodo 3 no es alcanzable; líder 2 | 5 operaciones; 0 conflictos en esta captura. El log de nodo2 contiene `write_accepted` | 0 | `ae0ee7df…` |
| Durante: nodo aislado (`E5_durante_aislado`, 04:41:37 UTC) | Nodo 3 consulta su estado local y todavía se considera líder | 5 operaciones; 0 conflictos en esta captura; nodo3 registra `write_accepted` a las 04:41:15 UTC | 1 | `10548c61…` |
| Después de reconectar (`E5_despues`, 04:46:49 UTC) | Nodos 1, 2 y 3 responden; líder 2 | 6 operaciones; 1 conflicto detectado y resuelto | 0 | `ae919189…` |

Durante el aislamiento, las capturas muestran estados diferentes en los dos lados: el grupo conectado registra el inventario de nodo1 con 0 CPU disponible, mientras nodo3, aislado, registra 1 CPU disponible y continúa considerándose líder. Cada lado registra 5 operaciones, frente a 4 en la captura previa. El evento `write_accepted` de nodo3 coincide con la captura aislada; el registro de nodo2 también contiene `write_accepted`, pero su hora (02:24 UTC) no coincide con la serie de capturas (aproximadamente 04:32–04:56 UTC), así que no se le asigna aquí un instante preciso dentro de la partición. Después de reconectar, los tres nodos vuelven a compartir el mismo estado.

## Resolución del conflicto y convergencia

El log de nodo1 registra un conflicto resuelto para el recurso `node1`. Se aplicó la regla `max_lamport_then_min_node_id`: gana la operación con mayor valor de Lamport y, en caso de empate, la del nodo con el ID menor.

En `nodo1/E5_despues_20261110T044649_486978.json`, los tres nodos reportan:

- **Hash del inventario:** `ae91918921eb22555418af91bd9bceb8a06aca39bfd6872493ac2d5fb9ca30bc`
- **Hash del diario:** `945a785254103baaf4177aae452949e7ae4ded4649d65bef4e162f1d3bbb9e7f`
- **Líder:** nodo 2, época 8.
- **Operaciones:** 6.
- **Conflictos detectados y resueltos:** 1 y 1.

Por tanto, la captura posterior a la reconexión confirma que los tres nodos convergieron al mismo inventario y diario.

## Nota sobre los tiempos

Las capturas de estado incluyen hora UTC. Los registros locales de los nodos pueden mostrar horas distintas; para reconstruir la prueba se consideran la fase y el contenido de cada archivo junto con sus eventos.
