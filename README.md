# triomino-generator

Generador y visualizador **iterativo** de triominos sobre una grilla triangular.  
El proyecto dibuja la grilla, arma candidatos de “triomino” (conjuntos de 3 triángulos adyacentes) y coloca piezas rotadas mientras anima el proceso.

> Estado actual: **visualiza y anima correctamente** la colocación de piezas.  
> La validación numérica entre lados aún es un _placeholder_ y siempre acepta la rotación `0`.

---

## 👀 ¿Qué es un “triomino” acá?

Trabajamos con una grilla de triángulos equiláteros (cada celda es un triángulo `up` o `down`).  
Un **triomino** es un conjunto de **tres** celdas triangulares que están conectadas entre sí **compartiendo lados completos** (no alcanza con tocar vértices).

El script:
1. Construye la grilla (`15 x 15` por defecto) y su **grafo de adyacencia**.
2. Encuentra **todos los triominos candidatos**.
3. Coloca fichas (con números) sobre triominos, animando el proceso generación por generación.

---

## 🎴 Set de piezas (56)

Se usa un “pool” de fichas con números del **0 al 5**:

- **Triples** (6): `(0,0,0) … (5,5,5)`  
- **Cuasitrís** (15): dos números iguales + uno distinto (p. ej. `(0,0,1)`)  
- **Triferentes** (20): tres números distintos (p. ej. `(0,1,2)`)  
- **Extra** (15): se eligen **aleatoriamente** del grupo “triferentes” para llegar a 56

---

## ✨ Características

- Grilla triangular con offsets por fila (tipo panal).
- Cálculo de **aristas** y **grafo de adyacencia**.
- Búsqueda de **triominos candidatos**.
- **Animación interactiva** con Matplotlib.
- Render de valores de cada ficha **en los lados**.

---

## 🛠️ Requisitos

- Python **3.9+**
- Paquetes:
  - `numpy`
  - `matplotlib`

---

## 🚀 Instalación

```bash
git clone https://github.com/<tu-usuario>/triomino-generator.git
cd triomino-generator

# (opcional) crear venv
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt