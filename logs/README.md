
# Registros de ejecución

El directorio `logs/` recibe la salida de consola del servicio al iniciarlo con `scripts/iniciar_inventario.sh`. Se crea un archivo por nodo, con el patrón `nodo<ID>_inventario.log`.

Estos archivos son registros de operación locales y pueden crecer durante la ejecución; los datos generados en `logs/` no forman parte del control de versiones. Para compartir una prueba como evidencia, conserva los registros seleccionados en el subdirectorio del entregable correspondiente bajo [`evidencias/`](../evidencias/README.md).

## Qué consultar

- Mensajes de inicio y actividad del nodo.
- Elecciones y cambios de líder.
- Aceptación o rechazo de operaciones.
- Errores de comunicación y sincronización.
- Resolución de conflictos, cuando aplica.

Cada nodo escribe su propio registro y puede tener una hora local distinta. Para verificar estados del inventario y comparar hashes de forma estructurada, consulta las capturas JSON y CSV descritas en [E5](../evidencias/E5/README.md).
