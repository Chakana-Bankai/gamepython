# Arcade Shooter (Pygame)

Juego 2D estilo arcade en un solo archivo (`shooter_arcade.py`).

## Ejecutar rápido

```bash
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
python shooter_arcade.py
```

## Si te aparece este error

> `ERROR: Failed to build 'pygame' when getting requirements to build wheel`

Ese error suele ocurrir cuando `pip` intenta compilar `pygame` desde código fuente y faltan dependencias del sistema.

### Solución recomendada en este proyecto

Este repositorio usa `pygame-ce` (compatible con `import pygame`) para evitar compilaciones locales en la mayoría de entornos:

```bash
python -m pip install -r requirements.txt
```

### Alternativa (si quieres `pygame` clásico)

Instala paquetes del sistema y luego vuelve a instalar:

```bash
sudo apt-get update
sudo apt-get install -y python3-dev python3-pip libSDL2-dev libSDL2-image-dev libSDL2-mixer-dev libSDL2-ttf-dev libportmidi-dev
python -m pip install --upgrade pip setuptools wheel
python -m pip install pygame
```

## Controles

- Mover: `WASD` o flechas
- Disparar: `Espacio`
- Menú/Inicio: `Enter` o `Espacio`
- Reiniciar en Game Over: `R` o `Enter`

