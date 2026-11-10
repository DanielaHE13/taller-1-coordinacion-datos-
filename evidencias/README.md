# CONEXIÓN EXITOSA ENTRE NODOS Y CONFIGURACIÓN SSH

A continuación se evidencia el cumplimiento del Entregable E3 (Registro de la verificación de conectividad inicial). Se demuestra el acceso SSH por clave pública entre todos los nodos del grupo a través de las IP de Tailscale y la desactivación de la autenticación por contraseña.

## 1. Verificación de conectividad general

Aquí se evidencia la conexión del Nodo 2 con el Nodo 1 y con el Nodo 3:
![Conexión general Nodo 2](https://github.com/DanielaHE13/taller-1-coordinacion-datos-/raw/main/evidencias/Imagen1.jpeg)

Aquí se evidencia la conexión del Nodo 3 con el Nodo 2 y con el Nodo 1:
![Conexión general Nodo 3](https://github.com/DanielaHE13/taller-1-coordinacion-datos-/raw/main/evidencias/Imagen2.jpeg)

## 2. Verificación de conectividad bidireccional

**Conexiones desde el Nodo 2:**
- Hacia el Nodo 1:
  ![Conexión de Nodo 2 a Nodo 1](https://github.com/DanielaHE13/taller-1-coordinacion-datos-/raw/main/evidencias/Imagen%203.jpeg)
- Hacia el Nodo 3:
  ![Conexión de Nodo 2 a Nodo 3](https://github.com/DanielaHE13/taller-1-coordinacion-datos-/raw/main/evidencias/Imagen4.jpeg)

**Conexiones desde el Nodo 3:**
- Hacia el Nodo 1:
  ![Conexión de Nodo 3 a Nodo 1](https://github.com/DanielaHE13/taller-1-coordinacion-datos-/raw/main/evidencias/Imagen5.jpeg)
- Hacia el Nodo 2:
  ![Conexión de Nodo 3 a Nodo 2](https://github.com/DanielaHE13/taller-1-coordinacion-datos-/raw/main/evidencias/Imagen6.jpeg)

**Conexiones desde el Nodo 1:**
- Hacia el Nodo 3:
  ![Conexión de Nodo 1 a Nodo 3](https://github.com/DanielaHE13/taller-1-coordinacion-datos-/raw/main/evidencias/Imagen7.jpeg)
- Hacia el Nodo 2:
  ![Conexión de Nodo 1 a Nodo 2](https://github.com/DanielaHE13/taller-1-coordinacion-datos-/raw/main/evidencias/Imagen8.jpeg)

## 3. Desactivación de contraseñas SSH

Para cumplir con los requisitos del entorno, se deshabilitó el acceso por contraseña editando el archivo `/etc/ssh/sshd_config` y configurando `PasswordAuthentication no`.

- **Desactivación en Nodo 2:**
  ![Desactivación contraseña Nodo 2](https://github.com/DanielaHE13/taller-1-coordinacion-datos-/raw/main/evidencias/Imagen9.jpeg)

- **Desactivación en Nodo 3:**
  ![Desactivación contraseña Nodo 3](https://github.com/DanielaHE13/taller-1-coordinacion-datos-/raw/main/evidencias/Imagen10.jpeg)

- **Desactivación en Nodo 1:**
  ![Desactivación contraseña Nodo 1](https://github.com/DanielaHE13/taller-1-coordinacion-datos-/raw/main/evidencias/Imagen11.jpeg)
