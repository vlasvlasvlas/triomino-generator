# 🎮 Triominó Professional Edition

> **State-of-the-Art implementation of the Triominó board game, featuring a premium Pygame interface, robust Reinforcement Learning agents, and fully customizable aesthetics.**

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-yellow.svg)
![Status](https://img.shields.io/badge/status-stable-green.svg)
![AI](https://img.shields.io/badge/AI-Reinforcement%20Learning-red)

---

## ✨ Características Principales

### 🖥️ Interfaz Gráfica SOTA (Pygame)
*   **Visualización Nativa:** Adiós a la terminal. Juego renderizado a 60 FPS con animaciones fluidas y gráficos vectoriales.
*   **Drag & Drop Feeling:** Sistema intuitivo "Click & Place". Selecciona tu ficha y las **"Sombras Guía" (Ghosts)** te mostrarán exactamente dónde puedes jugarla.
*   **Personalización Total:**
    *   **6 Temas de Fichas:** *Classic, Ocean, Sunset, Nature, Cyber, Pastel*.
    *   **5 Fondos de Alto Contraste:** *Midnight, Deep Ocean, Forest, Void, Slate* (Optimizados para largas sesiones).

### 🤖 Inteligencia Artificial y RL
*   **Agentes Inteligentes:** Desde estrategias *Greedy* (codiciosas) hasta modelos entrenados con **Proximal Policy Optimization (PPO)**.
*   **Pipeline de Entrenamiento Completo:** Entorno compatible con `Gymnasium` y `Stable-Baselines3` para entrenar tus propios agentes desde cero.
*   **Modo Simulación:** Observa a dos IAs luchar entre sí a velocidad sobrehumana (o lenta para análisis).

### 👥 Modos de Juego
1.  **Human vs AI:** Desafía a la máquina.
2.  **Human vs Human (Hotseat):** Modo local para dos jugadores con sistema **Anti-Cheat (Cortina)** que oculta la mano del oponente entre turnos.
3.  **Bot vs Bot:** Relájate y mira cómo juegan las estrategias.

---

## 🚀 Inicio Rápido (Quick Start)

Hemos simplificado todo con el script maestro `run.sh`.

### 1. Instalación
```bash
# Crear entorno virtual (recomendado)
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Jugar (GUI)
Lanza la interfaz gráfica profesional:
```bash
./run.sh
```
*Desde el menú principal podrás elegir Modo, Dificultad, Nombres y Colores.*

### 3. Otros Comandos
```bash
# Entrenar un nuevo agente de RL (Training Loop)
./run.sh train

# Jugar en modo Legacy (Terminal/ASCII)
./run.sh cli
```

---

## 🎮 Guía de Interfaz

### Controles
*   **Mouse Izquierdo:**
    *   **Click en Mano:** Seleccionar ficha (se ilumina en dorado).
    *   **Click en Tablero:** Colocar ficha seleccionada sobre una **"Sombra Guía" (Ghost tile)**.
    *   **Botones:** Usar los botones [DRAW] y [PASS] en pantalla.
*   **Navegación:** Todo el menú es controlable con el mouse.

### Modos de Visualización
En el **Menú Principal**, usa los selectores circulares para cambiar la estética del juego *antes* de empezar. Tus preferencias se aplican instantáneamente al tablero.

---

## 🧠 Arquitectura Técnica

### Estructura del Proyecto
```
.
├── models/             # Checkpoints de modelos entrenados (RL)
├── src/
│   ├── ai/             # Estrategias (Greedy, Random, HumanWrapper)
│   ├── engine/         # Motor lógico del juego (Reglas, Validaciones, Puntajes)
│   ├── gui/            # NUEVO: Motor Gráfico Pygame (SOTA)
│   │   ├── main.py     # Entrypoint de la aplicación gráfica y loop principal
│   │   ├── assets.py   # Gestión de recursos, fuentes y paletas de colores
│   │   └── pygame_board.py # Renderizado geométrico de triángulos
│   ├── models/         # Clases de datos (Triomino, Board, Player)
│   └── rl/             # Pipeline de Reinforcement Learning (Env, Train)
├── run.sh              # Script maestro de ejecución
└── requirements.txt    # Dependencias del proyecto
```

### Reinforcement Learning (RL) Details
El proyecto implementa un entorno personalizado de Gymnasium (`TriominoEnv`) que expone el estado del juego como un vector de observaciones y utiliza **Action Masking** para garantizar movimientos válidos.
*   **Algoritmo:** MaskablePPO (`sb3-contrib`).
*   **Rewards:** Scoring denso basado en reglas del juego + rewards por victorias.

---

## 🛠️ Troubleshooting

**Problema:** `box2d-py` error durante instalación.
**Solución:** Este proyecto NO requiere box2d. Asegúrate de usar el `requirements.txt` provisto que está limpio de dependencias innecesarias.

**Problema:** La ventana se cierra inmediatamente.
**Solución:** Ejecuta desde la terminal `./run.sh` para ver el log de errores. Asegúrate de estar en el entorno virtual.

---
*Desarrollado con ❤️ y Python.*
