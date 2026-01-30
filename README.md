# 🎮 Triominó

Un juego de Triominó con interfaz gráfica en Pygame y agentes de RL entrenables.

![Python](https://img.shields.io/badge/python-3.11+-yellow.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

---

## Modos de Juego

### Humano vs IA
Jugás contra una IA con dificultad seleccionable (Greedy, Random, o un modelo PPO entrenado).

### Humano vs Humano (Hotseat)
Dos jugadores en la misma computadora. Entre turnos aparece una "cortina" que oculta la mano del jugador anterior para evitar trampas.

### Bot vs Bot
Observá cómo dos IAs juegan entre sí. Útil para:
- Ver estrategias en acción
- Generar datos de entrenamiento
- Modo "infinito" que reinicia automáticamente al terminar cada partida

**Controles especiales en Bot vs Bot:**
- `↑/↓` - Aumentar/disminuir velocidad de juego
- `N` - Activar **Modo Noche**: fondo semi-transparente con grilla visible, ideal para ver mejor las fichas
- `G` - Activar **Ghost Trails**: muestra rastros de partidas anteriores como fichas fantasma
- `M` - Silenciar/activar sonido
- `←/→` - Cambiar preset de sonido (diferentes instrumentos/estilos)

---

## Características Visuales

### Temas de Colores
6 paletas para los jugadores: Classic, Ocean, Sunset, Nature, Cyber, Pastel

### Fondos
5 gradientes de fondo: Midnight, Deep Ocean, Forest, Void, Slate

### Sistema de Ghosts
Cuando seleccionás una ficha, aparecen "fantasmas" en todas las posiciones válidas donde podés colocarla. Click en un ghost para confirmar la jugada.

### Cámara Interactiva
- **Zoom**: Rueda del mouse
- **Pan**: Click derecho + arrastrar

---

## Audio

El modo Bot vs Bot incluye un motor de sonido procedural:
- Sonidos al colocar fichas
- Diferentes presets seleccionables con `←/→`
- Silenciable con `M`

---

## Entrenamiento RL

Podés entrenar tu propio agente usando Reinforcement Learning.

### Desde el menú
Click en "🧠 Train RL Agent" - abre una terminal y comienza el entrenamiento.

### Desde consola
```bash
./run.sh train
```

### Ver métricas
```bash
tensorboard --logdir logs/triomino_rl/
```

El entrenamiento muestra métricas explicadas cada 10 episodios:
- **Win Rate**: Porcentaje de victorias del agente
- **Loss**: Error del modelo (debería bajar)
- **Entropy**: Nivel de exploración (alto = explora, bajo = explota)

---

## Instalación

```bash
git clone https://github.com/tu-usuario/triomino-generator.git
cd triomino-generator
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Uso

```bash
./run.sh          # Interfaz gráfica
./run.sh train    # Entrenar agente
./run.sh cli      # Modo terminal (legacy)
```

---

## Controles

| Input | Acción |
|-------|--------|
| Click izquierdo (mano) | Seleccionar ficha |
| Click izquierdo (ghost) | Colocar ficha |
| Click derecho + arrastrar | Mover cámara |
| Rueda del mouse | Zoom |
| ESC | Volver al menú |

**Solo en Bot vs Bot:**
| Input | Acción |
|-------|--------|
| N | Modo noche (transparencia + grilla) |
| G | Ghost trails (rastros de partidas) |
| ↑/↓ | Velocidad de juego |
| ←/→ | Cambiar preset de sonido |
| M | Silenciar |

---

## Estructura

```
src/
├── engine/    # Lógica del juego (reglas, validación, puntaje)
├── gui/       # Interfaz Pygame
│   ├── main.py          # Loop principal
│   ├── pygame_board.py  # Renderizado del tablero
│   ├── assets.py        # Temas y colores
│   └── sound_engine.py  # Audio procedural
├── ai/        # Estrategias (Greedy, Random)
├── rl/        # Entrenamiento RL
│   ├── env.py     # Entorno Gymnasium
│   └── train.py   # Script de entrenamiento
└── cli/       # Interfaz de terminal
```

---

## Logs y Modelos

- `logs/gui/` - Logs de sesiones de juego
- `logs/triomino_rl/` - Métricas de entrenamiento (TensorBoard)
- `models/triomino_rl/` - Checkpoints de modelos entrenados

---

## Licencia

MIT
