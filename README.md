# 🎮 Triominó - War Games Edition

**Simulador automático de partidas de Triominó** donde dos computadoras juegan entre sí siguiendo las reglas oficiales del juego.

---

## 🎯 ¿Qué es esto?

Un programa que simula partidas completas de Triominó entre 2 jugadores controlados por IA. Incluye:

- ✅ Reglas 100% oficiales (tomadas de Wikipedia)
- ✅ 56 fichas triangulares con valores 0-5
- ✅ Sistema de puntuación completo con bonos y penalidades
- ✅ Visualización animada en tiempo real
- ✅ Estadísticas de múltiples partidas

---

## 🚀 Instalación Rápida

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/triomino-generator.git
cd triomino-generator

# 2. Crear entorno virtual
python3 -m venv venv

# 3. Activar entorno virtual
source venv/bin/activate   # macOS/Linux
# venv\Scripts\activate    # Windows

# 4. Instalar dependencias
pip install -r requirements.txt
```

---

## ▶️ Cómo Ejecutar

### Opción 1: Con visualización (recomendado)
```bash
python3 main.py
```
Verás el tablero animado con las fichas colocándose en tiempo real.

### Opción 2: Modo rápido (solo estadísticas)
```bash
python3 main.py --fast
```
Sin gráficos, muestra solo los resultados finales.

### Opciones adicionales

| Opción | Descripción | Ejemplo |
|--------|-------------|---------|
| `--matches N` | Cantidad de partidas | `--matches 10` |
| `--fast` | Sin visualización | `--fast` |
| `--seed N` | Resultado reproducible | `--seed 42` |
| `--delay N` | Velocidad de animación | `--delay 0.1` |

### Ejemplos

```bash
# 10 partidas con visualización
python3 main.py --matches 10

# 20 partidas rápidas
python3 main.py --fast --matches 20

# Partida reproducible
python3 main.py --seed 42

# Animación más rápida
python3 main.py --delay 0.1
```

---

## 📊 Reglas de Puntuación

| Acción | Puntos |
|--------|--------|
| Colocar ficha | Suma de los 3 valores |
| Abrir con triple (ej: 3-3-3) | +10 bonus |
| Abrir con 0-0-0 | +40 bonus |
| Completar hexágono | +50 bonus |
| Formar puente | +40 bonus |
| Robar del pozo | -5 por ficha |
| No poder jugar tras 3 robos | -25 adicional |
| Pasar (pozo vacío) | -10 |
| Ganar la ronda | +25 + suma de fichas del oponente |

**¿Cómo ganar?** El primero en llegar a 400 puntos activa la "ronda final". Al terminar esa ronda, gana quien tenga más puntos.

---

## 📁 Estructura del Proyecto

```
triomino-generator/
├── main.py              # ← Punto de entrada (ejecutar este)
├── src/
│   ├── models/          # Fichas, jugadores, tablero
│   ├── engine/          # Motor del juego y reglas
│   ├── ai/              # Estrategias de IA
│   └── visualization/   # Renderizado con matplotlib
├── RULES.md             # Reglas oficiales en español
├── requirements.txt     # Dependencias (numpy, matplotlib)
└── README.md            # Este archivo
```

---

## 📖 Reglas Oficiales

Ver [RULES.md](RULES.md) para el reglamento completo.

Fuente: [Wikipedia - Triominoes](https://en.wikipedia.org/wiki/Triominoes)

---

## 🛠️ Requisitos

- Python 3.9 o superior
- numpy
- matplotlib

---

## 📄 Licencia

MIT License