# 🎮 Triominó - War Games Edition

Simulador automático de partidas de Triominó donde 2 computadoras juegan entre sí con reglas 100% oficiales y visualización animada estilo "War Games".

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

---

## 📋 Características

- ✅ **56 fichas oficiales** - Sistema completo de fichas con números 0-5
- ✅ **Reglas 100% reales** - Matching de bordes, bonos, penalidades
- ✅ **4 estrategias de IA** - Greedy, Balanced, Defensive, Random
- ✅ **Visualización animada** - Tema oscuro estilo "War Games"
- ✅ **Simulación de N partidas** - Con estadísticas detalladas

---

## 🚀 Instalación

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/triomino-generator.git
cd triomino-generator
```

### 2. Crear entorno virtual
```bash
# Crear venv
python3 -m venv .venv

# Activar venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

---

## ▶️ Ejecución

### Modo visualizado (recomendado)
```bash
python3 main.py
```
Muestra las partidas con animación en tiempo real.

### Opciones de línea de comandos

| Opción | Descripción | Ejemplo |
|--------|-------------|---------|
| `-m, --matches` | Número de partidas | `--matches 10` |
| `-f, --fast` | Sin visualización | `--fast` |
| `-s, --seed` | Seed para reproducibilidad | `--seed 42` |
| `-d, --delay` | Delay de animación (seg) | `--delay 0.1` |

### Ejemplos
```bash
# 10 partidas con visualización
python3 main.py --matches 10

# Modo rápido sin gráficos (solo estadísticas)
python3 main.py --fast --matches 20

# Resultado reproducible
python3 main.py --seed 42

# Animación más rápida
python3 main.py --delay 0.1

# Ver ayuda
python3 main.py --help
```

---

## 📊 Sistema de Puntuación

| Evento | Puntos |
|--------|--------|
| Colocar ficha | Suma de los 3 valores |
| Abrir con triple | +10 bonus |
| Abrir con 0-0-0 | +40 bonus |
| Completar hexágono | +50 bonus |
| Formar puente | +40 bonus |
| Robar del pozo | -5 por ficha (máx 3) |
| No jugar tras 3 robos | -25 adicional |
| Pasar (pozo vacío) | -10 |
| Ganar ronda | +25 + suma fichas oponentes |

**Victoria:** Primer jugador en llegar a 400 puntos activa la ronda final. Gana quien tenga más puntos al terminar esa ronda.

---

## 🗂️ Estructura del Proyecto

```
triomino-generator/
├── src/
│   ├── models/          # Modelos: ficha, jugador, tablero
│   ├── engine/          # Motor: reglas, turnos, simulación
│   ├── ai/              # Estrategias de IA
│   └── visualization/   # Renderizado matplotlib
├── main.py              # Punto de entrada
├── RULES.md             # Reglas oficiales en español
└── requirements.txt     # Dependencias
```

---

## 📖 Reglas Oficiales

Ver [RULES.md](RULES.md) para el reglamento completo del juego.

Fuente: [Wikipedia - Triominoes](https://en.wikipedia.org/wiki/Triominoes)

---

## 🤝 Contribuir

1. Fork el proyecto
2. Crear rama feature (`git checkout -b feature/nueva-feature`)
3. Commit cambios (`git commit -m 'Add nueva feature'`)
4. Push a la rama (`git push origin feature/nueva-feature`)
5. Abrir Pull Request

---

## 📄 Licencia

MIT License - ver [LICENSE](LICENSE) para más detalles.