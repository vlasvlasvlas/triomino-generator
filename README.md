# triomino-generator

Generador y visualizador iterativo de triominos sobre una grilla triangular.
El proyecto dibuja la grilla, arma candidatos de “triomino” (conjuntos de 3 triángulos adyacentes) y coloca piezas rotadas mientras anima el proceso.

Estado actual: visualiza y anima correctamente la colocación de piezas. La validación numérica entre lados aún es un placeholder y siempre acepta la rotación 0.

⸻

👀 ¿Qué es un “triomino” acá?

Trabajamos con una grilla de triángulos equiláteros (cada celda es un triángulo up o down).
Un triomino es un conjunto de tres celdas triangulares que están conectadas entre sí compartiendo lados completos (no alcanza con tocar vértices).

El script:
	1.	Construye la grilla (por defecto 15 x 15) y su grafo de adyacencia.
	2.	Encuentra todos los triominos candidatos (tripletas de celdas con adyacencias válidas).
	3.	Coloca fichas (con números) sobre triominos, animando el proceso generación por generación.

⸻

🎴 Set de piezas (56)

Se usa un “pool” de fichas con números del 0 al 5:
	•	Triples (6): (0,0,0) … (5,5,5)
	•	Cuasitrís (15): dos números iguales + uno distinto (p. ej. (0,0,1))
	•	Triferentes (20): tres números todos distintos (p. ej. (0,1,2))
	•	Extra (15): se muestran aleatoriamente del grupo “triferentes” para completar 56

Nota: el orden de la terna representa los valores sobre los tres lados del triángulo. La función rotate_piece aplica rotaciones cíclicas de 120°.

⸻

✨ Características
	•	Grilla triangular con offsets por fila (tipo “panal” de triángulos).
	•	Cálculo de aristas por celda y grafo de adyacencia (vecinos = comparten lado).
	•	Búsqueda de triominos candidatos de forma estructurada.
	•	Animación interactiva con Matplotlib (modo plt.ion()).
	•	Render de valores de cada ficha centrados en las aristas.

⸻

🛠️ Requisitos
	•	Python 3.9+ (recomendado 3.10/3.11)
	•	Paquetes:
	•	numpy
	•	matplotlib

Opcional: ffmpeg si querés exportar la animación a video (ver Tips más abajo).

⸻

🚀 Instalación

git clone https://github.com/<tu-usuario>/triomino-generator.git
cd triomino-generator

# (opcional) crear venv
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt

Si no vas a usar requirements.txt, instalá directo:

pip install numpy matplotlib



⸻

▶️ Uso

Ejecutá el script principal:

python triomino_generator.py

Se abrirá una ventana con la grilla y la animación de colocación por generaciones.
Al final, se mantiene la ventana para inspección (plt.show()).

⸻

⚙️ Parámetros principales (editar en el script)
	•	Grilla
	•	rows, cols = 15, 15  → tamaño de la grilla
	•	side = 1              → lado del triángulo
	•	h = np.sqrt(3)/2 * side  → altura (derivada, no tocar salvo que cambies side)
	•	Animación / simulación
	•	max_fichas = 56        → tope de fichas a colocar por generación
	•	num_generaciones = 5   → cuántas “corridas” independientes animar
	•	original_piece_pool    → define el set de piezas; hoy incorpora 15 extra aleatorias
	•	Visual
	•	Colores y estilos de matplotlib.patches.Polygon
	•	Etiquetado con dibujar_valores (texto blanco con contorno para contraste)

⸻

🧩 Flujo del algoritmo (alto nivel)
	1.	Generación de grilla: se calculan coordenadas para cada celda (i, j, 'up'|'down').
	2.	Cálculo de aristas: para cada triángulo, se obtienen sus 3 aristas (pares de puntos).
	3.	Adyacencia: dos celdas son vecinas si comparten una arista completa.
	4.	Enumeración de triominos: recorrer celdas y sus vecinas para formar tripletas válidas.
	5.	Ejecución por generación:
	•	Copia del original_piece_pool.
	•	Semilla inicial: toma un triomino que contenga la celda más “central”.
	•	Bucle de colocación:
	•	filtra triominos no ocupados y adyacentes al frente ya ocupado,
	•	para cada triomino, prueba fichas disponibles y valida (hoy siempre rotación 0),
	•	elige un candidato al azar, asigna y dibuja acumulando estado.
	6.	Animación: dibuja grilla de fondo y luego pinta triomino por triomino (con valores).

⸻

📁 Estructura sugerida del repo

triomino-generator/
├─ triomino_generator.py        # el script que pegaste (renombrado)
├─ README.md
├─ requirements.txt
├─ LICENSE                      # MIT (sugerida)
└─ media/
   ├─ screenshots/              # imágenes de ejemplo
   └─ videos/                   # exportaciones (mp4/gif) opcionales

Contenido de requirements.txt (mínimo):

numpy>=1.24
matplotlib>=3.7


⸻

🧪 Reproducibilidad

El script usa aleatoriedad en:
	•	Selección de las 15 piezas extra.
	•	Elección de candidatos durante la colocación.

Para resultados reproducibles, fijá la semilla al inicio:

import random
import numpy as np

random.seed(42)
np.random.seed(42)


⸻

🚧 TODO / Roadmap
	•	Validación real de coincidencia numérica de lados
Implementar en valid_candidate(triomino, occupied, assigned, candidate_piece):
	•	Calcular, para cada celda del triomino, qué lado toca con su vecino y verificar que los valores coinciden en ambas celdas.
	•	Probar todas las rotaciones (0, 1, 2) y aceptar la que cumpla (devolver esa rotación) o None si ninguna sirve.
	•	Considerar compatibilidad con el entorno ya colocado (no solo dentro del triomino).
	•	Heurísticas de colocación:
	•	Greedy por mayor número de coincidencias.
	•	Best-first por expansión compacta del frente.
	•	Penalizar “cuellos de botella”.
	•	Estrategias de búsqueda:
	•	Backtracking con límite de profundidad.
	•	Monte Carlo / Beam search para mejorar tasa de colocación.
	•	Persistencia / Export:
	•	Guardar estado final (JSON/CSV) y frames de la animación.
	•	Exportar a MP4/GIF.
	•	CLI / Config:
	•	argparse para parámetros (--rows, --cols, --generations, etc.).
	•	Tests básicos:
	•	Testear adyacencia y enumeración de triominos.
	•	Testear rotaciones y mapeo de aristas.

⸻

🧠 Pistas para implementar valid_candidate
	1.	Rotaciones: para cada rot in {0,1,2}, rotar candidate_piece y asignar tentativamente.
	2.	Aristas internas del triomino: identificar pares de celdas de la tripleta que comparten arista; para cada par:
	•	Determinar qué lado de cada celda toca esa arista (índice 0/1/2).
	•	Comparar los valores rotados en esos lados.
	3.	Aristas externas: si alguna celda del triomino es vecina de una celda ya asignada:
	•	Asegurar coincidencia también con esa celda externa (usando su pieza y rotación ya fijadas).
	4.	Si todas las comprobaciones pasan para cierta rot, devolver rot; si no, None.

Tip: para mapear “lado del triángulo ↔ arista geométrica” podés normalizar y comparar aristas como ya hacés en get_edges. Mantené una estructura edge -> (celda, lado_index).

⸻

🧩 Consejos de performance
	•	Reducí rows/cols para experimentar rápido.
	•	Cacheá mapeos de arista → lado_index por celda.
	•	Filtrá temprano candidatos que no sean adyacentes al frente ya ocupado.
	•	Si implementás backtracking, poné límites (tiempo/profundidad) y una heurística de orden.

⸻

🎥 Tips de animación / export
	•	El script usa modo interactivo (plt.ion()), ideal para explorar en vivo.
	•	Para exportar a video:
	•	Reemplazá el paso incremental por matplotlib.animation.FuncAnimation.
	•	Instalá ffmpeg y guardá:

anim.save('media/videos/simulacion.mp4', fps=30, dpi=150)


	•	Para guardar una imagen del estado final:

plt.savefig('media/screenshots/final.png', dpi=200, bbox_inches='tight')



⸻

🧯 Problemas comunes
	•	La ventana no aparece / se cierra rápido: ejecutá desde una terminal y asegurate de no quitar plt.show() al final.
	•	Muy lento: baja rows/cols, reduce num_generaciones, o desactiva textos de aristas mientras depurás.
	•	Resultados “raros” entre corridas: fijá la semilla (ver sección Reproducibilidad).

⸻

🤝 Contribuciones

¡Bienvenidas! Abrí un issue con ejemplos, ideas de validación o PRs con:
	•	Implementación de valid_candidate.
	•	Heurísticas de colocación y backtracking.
	•	CLI y exportaciones.

⸻

📄 Licencia

Sugerida: MIT.
Podés agregar un LICENSE si lo vas a publicar.

⸻

📚 Créditos
	•	Autor/a: Vladimiro Bellini (y colaboradores/as)
	•	Librerías: numpy, matplotlib

⸻

🧾 Changelog (breve)
	•	v0.1.0: Grilla, adyacencias, enumeración de triominos, animación básica, placeholder de validación.

