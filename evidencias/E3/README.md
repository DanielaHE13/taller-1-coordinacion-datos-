# E3 · Conectividad entre nodos y SSH

Esta evidencia documenta la verificación inicial de comunicación entre las máquinas del clúster mediante ping y SSH sobre Tailscale, además de la configuración de autenticación por clave pública.

## Pruebas de conectividad

### Ping

**Nodo 2 hacia los nodos 1 y 3**

![Pruebas de ping de nodo 2 a nodos 1 y 3](Imagen1.jpeg)

**Nodo 3 hacia nodo 1**

![Prueba de ping de nodo 3 a nodo 1](Imagen2.jpeg)

### Acceso SSH

Las capturas muestran sesiones entre los nodos usando las direcciones de la red Tailscale.

| Origen | Destino | Evidencia |
|---|---|---|
| Nodo 2 | Nodo 1 | ![Conexión SSH de nodo 2 a nodo 1](Imagen3.jpeg) |
| Nodo 2 | Nodo 3 | ![Conexión SSH de nodo 2 a nodo 3](Imagen4.jpeg) |
| Nodo 3 | Nodo 1 | ![Conexión SSH de nodo 3 a nodo 1](Imagen5.jpeg) |
| Nodo 3 | Nodo 2 | ![Conexión SSH de nodo 3 a nodo 2](Imagen6.jpeg) |
| Nodo 1 | Nodo 3 | ![Conexión SSH de nodo 1 a nodo 3](Imagen7.jpeg) |
| Nodo 2 | Nodo 3 | ![Conexión SSH de nodo 2 a nodo 3](Imagen8.jpeg) |

## Autenticación SSH

Las capturas siguientes documentan la configuración de `PasswordAuthentication no`, para deshabilitar el acceso SSH por contraseña.

| Nodo | Evidencia |
|---|---|
| Nodo 2 | ![Configuración de autenticación SSH en nodo 2](Imagen9.jpeg) |
| Nodo 3 | ![Configuración de autenticación SSH en nodo 3](Imagen10.jpeg) |
| Nodo 1 | ![Configuración de autenticación SSH en nodo 1](Imagen11.jpeg) |

## Alcance

Estas capturas corresponden a la verificación inicial de conectividad y configuración de SSH; no sustituyen las pruebas de elección de líder ni las de partición de red descritas en [E4](../E4/README.md) y [E5](../E5/README.md).