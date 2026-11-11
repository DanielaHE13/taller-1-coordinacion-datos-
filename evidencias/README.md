# Evidencias del taller

Esta carpeta reúne los archivos seleccionados para documentar los entregables E3, E4 y E5. Cada entregable cuenta con una guía que describe el escenario, la organización de los archivos y los resultados observados.

## Índice

| Entregable | Evidencia | Guía |
|---|---|---|
| E3 | Capturas de conectividad por ping y SSH, y configuración de autenticación SSH. | [Conectividad y SSH](./E3/README.md) |
| E4 | Registros de elección del coordinador, cambio de líder y recuperación. | [Elección y recuperación](./E4/README.md) |
| E5 | Estados JSON/CSV, eventos y registros de la prueba de partición y reconciliación. | [Partición y convergencia](./E5/README.md) |

## Organización de E5

Los archivos de la prueba de inventario están separados por nodo:

```text
E5/
├── nodo1/
├── nodo2/
└── nodo3/
```

Los estados de cada fase se conservan en JSON y CSV; los archivos `.jsonl` contienen eventos locales del servicio y puede haber también registros de consola. Los CSV facilitan la comparación tabular; los JSON incluyen los datos completos de cada captura, incluidos roles, operaciones y hashes.

## Consulta

Empieza por la guía de cada entregable para interpretar la evidencia y sus limitaciones. Para conocer las decisiones de diseño y el alcance de las pruebas, consulta también el [README principal](../README.md).
