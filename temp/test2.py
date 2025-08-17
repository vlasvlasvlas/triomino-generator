import numpy as np
import matplotlib.pyplot as plt
import random
from matplotlib.patches import Polygon
import time

# 1) Parámetros de la grilla
rows, cols = 15, 15
side = 1
h = np.sqrt(3)/2 * side

print("Generando grilla...")

# 2) Generar la grilla (la misma para todas las generaciones)
coords_map = {}
for i in range(rows):
    for j in range(cols):
        x0 = j*side + (i % 2)*(side/2)
        y0 = i * h
        # Triángulo "up" (apunta hacia arriba)
        coords_map[(i, j, 'up')] = np.array([
            (x0+side/2, y0),
            (x0, y0+h),
            (x0+side, y0+h)
        ])
        # Triángulo "down" (apunta hacia abajo)
        coords_map[(i, j, 'down')] = np.array([
            (x0, y0+h),
            (x0+side/2, y0+2*h),
            (x0+side, y0+h)
        ])
cell_ids = list(coords_map.keys())
print(f"Total de triángulos en la grilla: {len(cell_ids)}")


# Función para obtener las aristas de un triángulo (redondeando para evitar precisión)
def get_edges(poly):
    pts = [(round(pt[0], 5), round(pt[1], 5)) for pt in poly]
    edges = []
    for k in range(3):
        edge = frozenset([pts[k], pts[(k+1) % 3]])
        edges.append(edge)
    return set(edges)

# Crear mapa de aristas
edges_map = {}
for cid in cell_ids:
    edges_map[cid] = get_edges(coords_map[cid])
print("Mapa de aristas creado.")

# 3) Construir grafo de adyacencia (dos triángulos vecinas si comparten una arista completa)
adj = {cid: [] for cid in cell_ids}
for i, cid1 in enumerate(cell_ids):
    for cid2 in cell_ids[i+1:]:
        if edges_map[cid1] & edges_map[cid2]:
            adj[cid1].append(cid2)
            adj[cid2].append(cid1)
print("Grafo de adyacencia construido.")
central_example = cell_ids[len(cell_ids)//2]
print(f"Vecinos de {central_example}: {adj[central_example]}")

# 4) Buscar candidatos a "triomino": Tres triángulos conectados por al menos 2 aristas
triominos = set()
for i, a in enumerate(cell_ids):
    for b in adj[a]:
        if b <= a:
            continue
        union_neighbors = set(adj[a]).union(adj[b])
        for c in union_neighbors:
            if c <= b:
                continue
            # La conectividad se comprueba si c está en vecinos de a o de b
            if (c in adj[a]) or (c in adj[b]):
                triominos.add((a, b, c))
triominos = list(triominos)
print(f"Número total de triominos candidatos: {len(triominos)}")

# Función para verificar adyacencia (por lados) respecto al área ocupada
def is_adjacent_to_occupied(triomino, occupied):
    for cell in triomino:
        for occ in occupied:
            if cell in adj[occ]:
                return True
    return False

# Parámetros para la animación de generaciones:
max_fichas = 56      # Fichas por generación
num_generaciones = 5 # Número de iteraciones de llenado

# Preparamos la figura y eje una sola vez
plt.ion()  # Modo interactivo
fig, ax = plt.subplots(figsize=(10, 10))

# Función para dibujar la grilla (fondo) en el eje
def dibujar_grilla(ax):
    ax.cla()  # Limpiar el eje
    for cid, coords in coords_map.items():
        poly = Polygon(coords, facecolor='none', edgecolor='darkgray', zorder=1, linewidth=0.5)
        ax.add_patch(poly)
    ax.set_aspect('equal')
    ax.autoscale_view()
    ax.axis('off')
    plt.tight_layout()

# Generación de ideogramas (cada generación limpia y vuelve a llenar)
for gen in range(num_generaciones):
    print(f"\n===== Generación {gen+1} =====")
    placed = []
    occupied = set()
    # Seleccionar el centro y colocar la primera ficha que contenga dicha celda
    center = min(cell_ids, key=lambda cid: abs(cid[0]-rows/2) + abs(cid[1]-cols/2))
    first_candidates = [t for t in triominos if center in t]
    if first_candidates:
        piece = random.choice(first_candidates)
        placed.append(piece)
        occupied.update(piece)
        print(f"Primera ficha colocada (centro {center}): {piece}")
    else:
        print("No se encontró candidato para la ficha inicial.")
    
    loop_iter = 0
    while len(placed) < max_fichas:
        loop_iter += 1
        candidates = []
        for t in triominos:
            if any(cell in occupied for cell in t):
                continue
            if occupied and not is_adjacent_to_occupied(t, occupied):
                continue
            candidates.append(t)
        print(f"Iteración {loop_iter} - Candidatos disponibles: {len(candidates)}")
        if not candidates:
            print("No quedan candidatos disponibles en esta generación.")
            break
        piece = random.choice(candidates)
        placed.append(piece)
        occupied.update(piece)
        print(f"Ficha colocada: {piece}")
    
    print(f"Fichas colocadas en generación {gen+1}: {len(placed)}")
    
    # Animar la colocación de fichas en la figura:
    dibujar_grilla(ax)
    fig.canvas.draw()
    fig.canvas.flush_events()
    plt.pause(0.1)  # Pausa para visualizar la grilla vacía
    
    for triomino in placed:
        for cid in triomino:
            poly = Polygon(coords_map[cid], facecolor='tomato', edgecolor='black', zorder=2)
            ax.add_patch(poly)
        fig.canvas.draw()
        fig.canvas.flush_events()
        plt.pause(0.0010)  # Pausa breve entre cada ficha
    
    # Mantener la visualización por 1 segundo y luego limpiar para la siguiente generación
    plt.pause(1)
    
plt.ioff()
plt.show()