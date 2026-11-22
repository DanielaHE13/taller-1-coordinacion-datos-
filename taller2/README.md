# Taller 2 · Integración, mensajería y transacciones

## Despliegue con Docker Compose

Se requiere Docker con Compose v2. Desde la raíz del repositorio, en la rama
`taller2-integracion`, define las credenciales en la terminal:

```bash
read -rsp "Token de inventario (mínimo 16 caracteres): " TALLER_TOKEN; echo
read -rsp "Contraseña de Redis: " REDIS_PASSWORD; echo
read -rsp "Contraseña de RabbitMQ: " RABBITMQ_PASSWORD; echo
export TALLER_TOKEN REDIS_PASSWORD RABBITMQ_PASSWORD
```

Usa las mismas credenciales al volver a levantar el proyecto con sus volúmenes
existentes. Guarda las contraseñas fuera del repositorio.

Levanta el coordinador gRPC, RabbitMQ y los tres nodos de inventario.
Compose iniciará también los Redis de los que dependen:

```bash
docker compose -p taller2-aula -f taller2/docker-compose.yml \
  up --build --wait --wait-timeout 120 \
  coordinador rabbitmq inventario1 inventario2 inventario3

docker compose -p taller2-aula -f taller2/docker-compose.yml ps
```

## Verificar la comunicación gRPC

```bash
docker compose -p taller2-aula -f taller2/docker-compose.yml build agente
docker compose -p taller2-aula -f taller2/docker-compose.yml run --rm agente
```

El agente debe mostrar `ack=True`. Para comprobar la recepción:

```bash
docker compose -p taller2-aula -f taller2/docker-compose.yml logs coordinador
```

En los logs debe aparecer el reporte de `agente-compose`.

## Contratos y evidencias

- [Contrato gRPC](config/telematica.proto)
- [Esquema JSON de eventos](config/evento.schema.json)
- [Registros de desconexión y recuperación de RabbitMQ](evidencias/E5/)

Las pruebas de Saga E3 y E4 se ejecutaron entre las VMs del grupo por
Tailscale. El [ejecutor de la Saga](saga/ejecutar.py) usa las direcciones
de ese despliegue.
