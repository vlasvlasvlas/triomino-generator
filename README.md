# 🎮 Triominó

Un juego de Triominó con interfaz gráfica en Pygame y agentes de RL entrenables.

![Python](https://img.shields.io/badge/python-3.11+-yellow.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

📖 **[Reglas del juego](RULES.md)** - Si no conocés el Triominó, empezá por acá.

---

## Modos de Juego

### Humano vs IA
Jugás contra una IA con dificultad seleccionable (Greedy, Balanced, Defensive, Random, o un modelo PPO entrenado).

### Humano vs Humano (Hotseat)
Dos jugadores en la misma computadora. Entre turnos aparece una "cortina" que oculta la mano del jugador anterior para evitar trampas.

### Bot vs Bot
Observá cómo dos IAs juegan entre sí. Útil para:
- Ver estrategias en acción
- Generar datos de entrenamiento
- Modo "infinito" que reinicia automáticamente al terminar cada partida

Incluye panel de control en pantalla con:
- Tempo actual (BPM y milisegundos)
- Timbre activo
- Fondo activo y estado de fondo dinámico
- Atajos visibles (también en pantalla pequeña)
- Marcador acumulado por sesión: partidas ganadas por bot + puntaje total acumulado

### 🎵 Sonic Mode
Modo instrumental infinito entre bots, orientado a experimentar con ritmo/sonido y visuales en vivo.

Comparte controles con Bot vs Bot y además permite recargar presets sin reiniciar partida.

**Controles especiales (Bot vs Bot + Sonic):**
- `W/S` o `↑/↓` - Subir/bajar tempo
- `A/D` o `←/→` - Cambiar timbre/preset
- `Q/E` - Cambiar fondo
- `B` - Activar/desactivar fondo dinámico
- `G` - Activar/desactivar ghost trails
- `N` - Activar/desactivar modo noche (transparencia + grilla)
- `M` - Silenciar/activar sonido
- `R` - Recargar configuración sónica (solo en Sonic)

---

## Características Visuales

### Temas de Colores
6 paletas para los jugadores: Classic, Ocean, Sunset, Nature, Cyber, Pastel

### Fondos
6 gradientes de fondo: Ocean, Midnight, Forest, Sunset, Night, Void.

En Bot vs Bot y Sonic se puede ciclar el fondo en vivo (`Q/E`) y activar animación dinámica (`B`).

### Sistema de Ghosts
Cuando seleccionás una ficha, aparecen "fantasmas" en todas las posiciones válidas donde podés colocarla. Click en un ghost para confirmar la jugada.

### Cámara Interactiva
- **Zoom**: Rueda del mouse
- **Pan**: Click derecho + arrastrar

### Modo Terminal Retro
Podés activar un look estilo terminal clásica (fondo negro + verde flúo) con `T`.

---

## Audio y Modo Sónico

Bot vs Bot y Sonic incluyen motor de sonido procedural:
- Sonidos al colocar fichas
- Tempo ajustable en vivo (`W/S` o `↑/↓`)
- Timbres/presets seleccionables (`A/D` o `←/→`)
- Silenciable con `M`
- Recarga de config en caliente con `R` (solo Sonic)

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
git clone https://github.com/vlasvlasvlas/triomino-generator.git
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
| T | Activar/desactivar modo terminal retro |
| Z | Fullscreen normal (UI visible) |
| X | Fullscreen limpio (solo juego) |

**Solo en Bot vs Bot y Sonic:**
| Input | Acción |
|-------|--------|
| W/S o ↑/↓ | Subir/bajar tempo |
| A/D o ←/→ | Cambiar timbre/preset |
| Q/E | Cambiar fondo |
| B | Fondo dinámico ON/OFF |
| N | Modo noche (transparencia + grilla) |
| G | Ghost trails (rastros de partidas) |
| M | Silenciar |
| R | Recargar config sónica (solo Sonic) |

Nota: en fullscreen normal (`Z`) se mantiene la UI. En fullscreen limpio (`X`) se ocultan HUD y shortcuts, pero se mantiene una barra mínima con puntajes (y pool) para seguir la partida. Con `ESC` salís de fullscreen. El modo terminal (`T`) funciona en menú y partida.

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
