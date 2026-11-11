# E4 · Elección y recuperación del coordinador

Este entregable documenta la elección del líder, su cambio cuando deja de responder y la reincorporación posterior del nodo de mayor ID.

## Archivos

| Archivo | Registro |
|---|---|
| [`nodo1_e4_coordinada.log`](./nodo1_e4_coordinada.log) | Cambios de líder observados por nodo1 durante la prueba. |
| [`nodo2_e4_coordinada.log`](./nodo2_e4_coordinada.log) | Elecciones y cambios de líder observados por nodo2. |
| [`nodo3_e4_coordinada.log`](./nodo3_e4_coordinada.log) | Elección y anuncios de liderazgo observados por nodo3. |

## Resultado documentado

En la secuencia registrada, nodo3 asume inicialmente el liderazgo. Cuando deja de participar, los registros muestran la elección de nodo2; al reincorporarse nodo3, vuelve a ser reconocido como líder por los nodos que registran ese cambio.

Los logs se generan localmente en cada máquina y sus relojes pueden diferir. Por ello, deben interpretarse como registros por nodo de las transiciones observadas, no como una fuente única de tiempo global. Consulta el [índice de evidencias](../README.md) para el contexto de los demás entregables.

