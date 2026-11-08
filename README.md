# taller-1-coordinacion-datos-
Taller 1 de Sistemas Distribuidos: coordinador, inventario y partición.
# Taller 1: Coordinación y datos del sistema

Proyecto de la asignatura **Sistemas Distribuidos Modernos**.

## Descripción

En este taller construiremos y probaremos un sistema distribuido de gestión de recursos de borde. El sistema estará formado por varios nodos que se comunican entre sí para elegir un coordinador, mantener un inventario de recursos y recuperarse cuando falla un nodo o se interrumpe la comunicación.

El inventario registrará recursos como CPU, memoria y ancho de banda de cada nodo. También implementaremos un mecanismo para detectar y resolver cambios concurrentes cuando dos partes del sistema modifican el mismo recurso durante una partición de red.

El proyecto se ejecutará en máquinas virtuales del grupo. Documentaremos las decisiones de diseño y guardaremos evidencia de las pruebas realizadas.

## Integrantes

- Daniela Huertas
- Oscar Castillo
- Sebastian Zaldarriaga
- Andres Valencia
- Lorena Rubio

## Objetivos

- Elegir un coordinador entre los nodos y reemplazarlo cuando falle.
- Mantener un inventario de recursos replicado entre los nodos.
- Detectar escrituras concurrentes mediante versiones.
- Resolver los conflictos con una regla definida por el grupo.
- Provocar una partición de red, registrar el comportamiento del sistema y comprobar su convergencia al reconectar.

## Decisiones técnicas

Completar esta sección cuando el grupo tome las decisiones:

- **Algoritmo de elección:** pendiente de elegir entre algoritmo del matón o elección en anillo.
- **Base de datos:** pendiente de elegir entre MongoDB con replica set o Redis con replicación.
- **Mecanismo de versión:** pendiente de definir.
- **Regla de resolución de conflictos:** pendiente de definir.
- **Lecturas y confirmación de escrituras:** pendiente de documentar.

## Estructura del repositorio

- `coordinador/`: código para elegir y mantener el coordinador.
- `agentes/`: código de los procesos que ejecuta cada nodo.
- `scripts/`: scripts de ejecución y pruebas, incluida la partición de red.
- `logs/`: registros de las ejecuciones.
- `evidencias/`: pruebas iniciales de conectividad y resultados.
- `informe/`: informe técnico y material de apoyo.

## Requisitos del entorno

El taller requiere al menos tres máquinas virtuales Debian 13 o Ubuntu Server 26.04.1, acceso SSH por clave pública y conectividad entre los nodos mediante Tailscale.

Antes de iniciar el desarrollo, se debe comprobar y guardar evidencia de que los nodos pueden comunicarse por ping y SSH.

## Ejecución

Instrucciones pendientes. Se completarán cuando el grupo haya implementado y probado el sistema.

## Entregables

- **E1:** repositorio Git con código, scripts y README.
- **E2:** informe técnico en PDF de 6 a 8 páginas.
- **E3:** evidencia de la verificación inicial de conectividad.
- **E4:** logs de elección del líder y recuperación tras su caída.
- **E5:** logs y resultados del experimento de partición de red.

## Seguridad

No subir claves privadas, contraseñas ni credenciales al repositorio. El archivo `.gitignore` excluye archivos `.pem`, `.key` y la carpeta `.ssh/`.
