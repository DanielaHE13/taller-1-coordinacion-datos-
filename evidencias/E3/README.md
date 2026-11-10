# Conexión entre nodos y configuración de SSH

Este documento reúne la evidencia del entregable **E3: verificación inicial de conectividad**. Las capturas muestran pruebas de ping entre los nodos, acceso SSH mediante clave pública a través de Tailscale y la configuración de SSH en los tres nodos.

## 1. Verificación de conectividad mediante ping

### Ping de nodo 2 a nodo 1 y nodo 3

![Ping de nodo 2 a nodo 1 y nodo 3](Imagen1.jpeg)

### Ping de nodo 3 a nodo 1

![Ping de nodo 3 a nodo 1](Imagen2.jpeg)

## 2. Verificación de conectividad mediante SSH

### Conexión de nodo 2 a nodo 1

![Conexión SSH de nodo 2 a nodo 1](Imagen3.jpeg)

### Conexión de nodo 2 a nodo 3

![Conexión SSH de nodo 2 a nodo 3](Imagen4.jpeg)

### Conexión de nodo 3 a nodo 1

![Conexión SSH de nodo 3 a nodo 1](Imagen5.jpeg)

### Conexión de nodo 3 a nodo 2

![Conexión SSH de nodo 3 a nodo 2](Imagen6.jpeg)

### Conexión de nodo 1 a nodo 3

![Conexión SSH de nodo 1 a nodo 3](Imagen7.jpeg)

### Conexión de nodo 2 a nodo 3

![Conexión SSH de nodo 2 a nodo 3](Imagen8.jpeg)

## 3. Configuración de autenticación SSH

Las siguientes capturas documentan la configuración de SSH para deshabilitar la autenticación por contraseña (`PasswordAuthentication no`).

### Nodo 2

![Desactivación de autenticación por contraseña en nodo 2](Imagen9.jpeg)

### Nodo 3

![Desactivación de autenticación por contraseña en nodo 3](Imagen10.jpeg)

### Nodo 1

![Desactivación de autenticación por contraseña en nodo 1](Imagen11.jpeg)