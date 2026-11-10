# Taller 1: Coordinación y datos del sistema

Proyecto de la asignatura **Sistemas Distribuidos Modernos**.

## Descripción

En este taller construiremos y probaremos un sistema distribuido de gestión de recursos de borde. El sistema estará formado por varios nodos que se comunican entre sí para elegir un coordinador, mantener un inventario de recursos y recuperarse cuando falla un nodo o se interrumpe la comunicación.

El inventario registrará recursos como CPU, memoria y ancho de banda de cada nodo. También implementaremos un mecanismo para detectar y resolver cambios concurrentes cuando dos partes del sistema modifican el mismo recurso durante una partición de red.

El proyecto se ejecutará en máquinas virtuales del grupo. Documentaremos las decisiones de diseño y guardaremos evidencia de las pruebas realizadas.

## Integrantes

- Daniela Huertas
- Oscar Castillo
- Sebastian Saldarriaga
- Andres Valencia
- Lorena Rubio

## Objetivos

- Elegir un coordinador entre los nodos y reemplazarlo cuando falle.
- Mantener un inventario de recursos replicado entre los nodos.
- Detectar escrituras concurrentes mediante versiones.
- Resolver los conflictos con una regla definida por el grupo.
- Provocar una partición de red, registrar el comportamiento del sistema y comprobar su convergencia al reconectar.

## Decisiones técnicas

- **Algoritmo de elección:** Matón. Gana el nodo con el ID más alto entre los nodos que participan en esa elección.
- **Base de datos:** Redis con topología maestro-réplica. El líder coordina las escrituras y la topología de Redis se ajusta al líder actual.
- **Bitácora de operaciones:** cada nodo conserva localmente un diario SQLite para recuperar y sincronizar operaciones.
- **Mecanismo de versión:** vector de versión por recurso y reloj de Lamport por operación.
- **Regla de resolución de conflictos:** entre operaciones concurrentes gana el Lamport mayor; si empatan, gana el ID de nodo menor.
- **Lecturas:** cada nodo consulta la vista del inventario guardada en su Redis local. Durante una partición, la vista puede estar desactualizada hasta que se reconcilien las operaciones.
- **Escrituras:** solo el líder acepta asignaciones. Cada asignación descuenta recursos disponibles y se rechaza si supera la capacidad.
- **Confirmación de escrituras:** la API confirma la escritura en el Redis maestro; no espera confirmación de las réplicas. Las asignaciones realizadas durante una partición son provisionales y se reconcilian al reconectar.
- **Confirmación:** la API confirma la escritura en el maestro Redis; no espera confirmaciones de las réplicas. Durante una partición, las asignaciones se consideran provisionales y se reconcilian al reconectar.

 ## Nodos

| Nodo | ID | Sistema | Dirección Tailscale |
|---|---:|---|---|
| nodo1 | 1 | Debian 13 | `100.101.47.119` |
| nodo2 | 2 | Ubuntu Server 26.04.1 | `100.92.63.103` |
| nodo3 | 3 | Debian 13 | `100.98.74.61` |

## Estructura del repositorio

- `agentes/`: cliente de línea de comandos para consultar y modificar el inventario.
- `coordinador/`: elección, bitácora, versionado y conexión con Redis.
- `config/`: configuración de ejemplo. 
- `scripts/`: preparación e inicio de los nodos.
- `pruebas/`: pruebas automatizadas o auxiliares.
- `Validacion/`: material de validación del proyecto.
- `logs/`: registros de las ejecuciones.
- `evidencias/`: capturas, salidas y archivos seleccionados para los entregables.
- `informe/`: informe técnico.
- `datos/`: datos locales de ejecución; no deben confundirse con la evidencia seleccionada para entregar.


## Requisitos del entorno

- Tres máquinas virtuales Debian 13 o Ubuntu Server 26.04.1.
- Conectividad entre nodos mediante Tailscale.
- Acceso SSH mediante clave pública.
- Python 3 y Redis Server instalados en cada nodo.
- El mismo token de API y la misma clave de Redis configurados localmente en los tres nodos

## Entregables

- **E1:** repositorio Git con código, scripts y README.
- **E2:** informe técnico en PDF de 6 a 8 páginas.
- **E3:** evidencia de la verificación inicial de conectividad.
- **E4:** logs de elección del líder y recuperación tras su caída.
- **E5:** logs y resultados del experimento de partición de red.


