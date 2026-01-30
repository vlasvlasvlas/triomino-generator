# 🎮 Triominó

Un juego de Triominó con interfaz gráfica en Pygame y agentes de RL entrenables.

![Python](https://img.shields.io/badge/python-3.11+-yellow.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

---

## Características

- **Interfaz gráfica** con Pygame (zoom, pan, temas de colores)
- **3 modos de juego**: Humano vs IA, Humano vs Humano, Bot vs Bot
- **Entrenamiento RL**: Entrená tu propio agente con MaskablePPO
- **Ghosts visuales**: Muestra dónde podés colocar fichas

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

### Jugar
```bash
./run.sh
```

### Entrenar agente RL
Desde el menú: click en "🧠 Train RL Agent"

O por consola:
```bash
./run.sh train
```

### Ver métricas de entrenamiento
```bash
tensorboard --logdir logs/triomino_rl/
```

---

## Controles

| Input | Acción |
|-------|--------|
| Click izquierdo (mano) | Seleccionar ficha |
| Click izquierdo (tablero) | Colocar ficha |
| Click derecho + arrastrar | Mover cámara |
| Rueda del mouse | Zoom |
| N | Modo noche (Bot vs Bot) |
| G | Rastros fantasma (Bot vs Bot) |
| ↑/↓ | Velocidad (Bot vs Bot) |
| M | Silenciar |
| ESC | Volver al menú |

---

## Estructura

```
src/
├── engine/    # Lógica del juego
├── gui/       # Interfaz Pygame
├── ai/        # Estrategias (Greedy, Random)
├── rl/        # Entrenamiento (MaskablePPO)
└── cli/       # Interfaz de terminal
```

---

## Logs

- `logs/gui/` - Sesiones de juego
- `logs/triomino_rl/` - Métricas de entrenamiento
- `models/` - Checkpoints de modelos

---

## Licencia

MIT
