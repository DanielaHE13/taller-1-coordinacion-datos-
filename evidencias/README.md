# Evidencias del taller

Esta carpeta reúne las evidencias de los entregables E3, E4 y E5. Cada subcarpeta contiene un README con la descripción de sus archivos y resultados.

## Estructura

- `E3/`: verificación inicial de conectividad entre los nodos mediante ping y SSH, y configuración de autenticación SSH.
- `E4/`: registros de la elección del líder y su recuperación tras la caída o desconexión de un nodo.
- `E5/`: archivos de inventario y registros de eventos de la prueba de partición de red, resolución de conflictos y convergencia.

## Organización de E5

La evidencia de E5 está separada por nodo:

- `E5/nodo1/`
- `E5/nodo2/`
- `E5/nodo3/`

Los archivos CSV y JSON guardan estados del inventario en diferentes fases. Los archivos `.jsonl` y los logs registran eventos de ejecución. La comparación final de convergencia está documentada en `E5/README.md`.

## Revisión

Consulta el README dentro de cada entregable para conocer el escenario probado, los archivos incluidos y los resultados observados.
