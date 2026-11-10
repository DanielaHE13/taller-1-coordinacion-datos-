# CONEXIÓN EXITOSA ENTRE NODOS Y CONFIGURACIÓN SSH

A continuación se evidencia el cumplimiento del Entregable E3 (Registro de la verificación de conectividad inicial). Se demuestra la conectividad básica, el acceso SSH por clave pública entre los nodos a través de las IP de Tailscale y la desactivación de la autenticación por contraseña.

## 1. Verificación de conectividad (Ping)

- **Ping de nodo 2 a nodo 1 y nodo 3:**
  ![Ping de nodo2 a nodo1 y nodo3](evidencias/Imagen1.jpeg)

- **Ping de nodo 3 a nodo 1:**
  ![Ping de nodo 3 a nodo1](evidencias/Imagen2.jpeg)

## 2. Verificación de conectividad mediante SSH

- **Conexión de nodo 2 a nodo 1:**
  ![ssh_nodo2_a_nodo1](evidencias/Imagen3.jpeg)

- **Conexión de nodo 2 a nodo 3:**
  ![ssh_nodo2_a_nodo3](evidencias/Imagen4.jpeg)

- **Conexión de nodo 3 a nodo 1:**
  ![ssh_nodo3_a_nodo1](evidencias/Imagen5.jpeg)

- **Conexión de nodo 3 a nodo 2:**
  ![ssh nodo 3 a nodo 2](evidencias/Imagen6.jpeg)

- **Conexión de nodo 1 a nodo 3:**
  ![ssh nodo 1 a nodo 3](evidencias/Imagen7.jpeg)

- **Conexión de nodo 2 a nodo 3:**
  ![ssh nodo 2 a nodo 3](evidencias/Imagen8.jpeg)

## 3. Configuración y desactivación de contraseñas SSH

Para cumplir con los requisitos del entorno, se deshabilitó el acceso por contraseña editando la configuración de SSH (`PasswordAuthentication no`).

- **Desactivación de contraseña en nodo 2:**
  ![desactivacion de contraseña nodo 2](evidencias/Imagen9.jpeg)

- **Desactivación de contraseña en nodo 3:**
  ![Desactivacion contraseña nodo 3](evidencias/Imagen10.jpeg)

- **Desactivación de contraseña en nodo 1:**
  ![Desactivacion constraseña nodo 1](evidencias/Imagen11.jpeg)
