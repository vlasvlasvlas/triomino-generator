import numpy as np
import matplotlib.pyplot as plt
import random
from matplotlib.patches import Polygon
import matplotlib.patheffects as pe
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
        x0 = j * side + (i % 2) * (side / 2)
        y0 = i * h
        # Triángulo "up" (apunta hacia arriba)
        coords_map[(i, j, 'up')] = np.array([
            (x0 + side/2, y0),
            (x0, y0 + h),
            (x0 + side, y0 + h)
        ])
        # Triángulo "down" (apunta hacia abajo)
        coords_map[(i, j, 'down')] = np.array([
            (x0, y0 + h),
            (x0 + side/2, y0 + 2 * h),
            (x0 + side, y0 + h)
        ])
cell_ids = list(coords_map.keys())
print(f"Total de triángulos en la grilla: {len(cell_ids)}")

# A. Pool de fichas disponibles
# Triples:
triples = [(0,0,0), (1,1,1), (2,2,2), (3,3,3), (4,4,4), (5,5,5)]
# Cuasitrís:
cuasitris = [(0,0,1), (0,0,2), (0,0,3), (0,0,4), (0,0,5),
             (1,1,2), (1,1,3), (1,1,4), (1,1,5),
             (2,2,3), (2,2,4), (2,2,5),
             (3,3,4), (3,3,5),
             (4,4,5)]
# Triferentes:
triferentes = [(0,1,2), (0,1,3), (0,1,4), (0,1,5),
               (0,2,3), (0,2,4), (0,2,5), (0,3,4), (0,3,5), (0,4,5),
               (1,2,3), (1,2,4), (1,2,5), (1,3,4), (1,3,5), (1,4,5),
               (2,3,4), (2,3,5), (2,4,5), (3,4,5)]
# Según la lista: 6 + 15 + 20 = 41 piezas. Para llegar a 56, agregamos 15 fichas adicionales del grupo triferentes.
extra = random.sample(triferentes, 15)
original_piece_pool = triples + cuasitris + triferentes + extra
print(f"Pool de piezas disponible (total {len(original_piece_pool)}): {original_piece_pool}")

# B. (Opcional) values_map para mostrar valores base.
values_map = {}
for cid in cell_ids:
    values_map[cid] = (random.randint(1,5), random.randint(1,5), random.randint(1,5))

# Función para obtener las aristas de un triángulo (redondeando para evitar precisión)
def get_edges(poly):
    pts = [(round(pt[0],5), round(pt[1],5)) for pt in poly]
    edges = []
    for k in range(3):
        edge = frozenset([pts[k], pts[(k+1)%3]])
        edges.append(edge)
    return set(edges)

# Crear mapa de aristas
edges_map = {}
for cid in cell_ids:
    edges_map[cid] = get_edges(coords_map[cid])
print("Mapa de aristas creado.")

# 3) Construir grafo de adyacencia (dos triángulos son vecinos si comparten una arista completa)
adj = {cid: [] for cid in cell_ids}
for i, cid1 in enumerate(cell_ids):
    for cid2 in cell_ids[i+1:]:
        if edges_map[cid1] & edges_map[cid2]:
            adj[cid1].append(cid2)
            adj[cid2].append(cid1)
print("Grafo de adyacencia construido.")
central_example = cell_ids[len(cell_ids)//2]
print(f"Vecinos de {central_example}: {adj[central_example]}")

# 4) Buscar candidatos a "triomino": tres triángulos conectados por al menos 2 aristas.
triominos = set()
for i, a in enumerate(cell_ids):
    for b in adj[a]:
        if b <= a:
            continue
        union_neighbors = set(adj[a]).union(adj[b])
        for c in union_neighbors:
            if c <= b:
                continue
            if (c in adj[a]) or (c in adj[b]):
                triominos.add((a, b, c))
triominos = list(triominos)
print(f"Número total de triominos candidatos: {len(triominos)}")

# C. Función auxiliar: Rotar una ficha (rotación cíclica de 120°)
def rotate_piece(piece, rot):
    rot = rot % 3
    return piece[rot:] + piece[:rot]

# D. Función placeholder para validar candidato.
def valid_candidate(triomino, occupied, assigned, candidate_piece):
    # Aquí se debe implementar la validación real de coincidencia numérica.
    # Se debe considerar compatibilidad en 1, 2 o 3 lados.
    # De momento, aceptamos siempre la candidate con rotación 0.
    return 0

# E. Función para dibujar los valores numéricos en cada triángulo.
def dibujar_valores(ax, cid, piece_assigned, rot_assigned):
    rotated = rotate_piece(list(piece_assigned), rot_assigned)
    coords = coords_map[cid]
    for idx in range(3):
        pt1 = coords[idx]
        pt2 = coords[(idx+1)%3]
        midpoint = ((pt1[0]+pt2[0])/2, (pt1[1]+pt2[1])/2)
        txt = ax.text(midpoint[0], midpoint[1], str(rotated[idx]),
                      fontsize=8, color='white', ha='center', va='center')
        txt.set_path_effects([pe.withStroke(linewidth=1, foreground='black')])

# F. Función para dibujar la grilla (fondo)
def dibujar_grilla(ax):
    ax.cla()
    for cid, coords in coords_map.items():
        poly = Polygon(coords, facecolor='none', edgecolor='darkgray', zorder=1, linewidth=0.5)
        ax.add_patch(poly)
    ax.set_aspect('equal')
    ax.autoscale_view()
    ax.axis('off')
    plt.tight_layout()

# Parámetros para la animación de generaciones:
max_fichas = 56      # Se intenta colocar hasta 56 fichas
num_generaciones = 5 # Número de generaciones

# Preparamos la figura y eje una sola vez
plt.ion()
fig, ax = plt.subplots(figsize=(10, 10))

# G. Bucle principal por generación
for gen in range(num_generaciones):
    # Reiniciamos el pool para cada generación
    piece_pool = original_piece_pool.copy()
    print(f"\n===== Generación {gen+1} =====")
    placed = []      # Lista de triominos colocados en esta generación
    occupied = set() # Celdas ocupadas
    assigned = {}    # Diccionario: clave = celda, valor = (piece, rot)

    # Colocar la primera ficha en el centro
    center = min(cell_ids, key=lambda cid: abs(cid[0]-rows/2) + abs(cid[1]-cols/2))
    first_candidates = [t for t in triominos if center in t]
    if first_candidates:
        t_candidate = random.choice(first_candidates)
        piece_assigned = piece_pool.pop(0)  # Siempre hay fichas en el pool al inicio
        rot_assigned = 0
        for cell in t_candidate:
            assigned[cell] = (piece_assigned, rot_assigned)
        placed.append(t_candidate)
        occupied.update(t_candidate)
        print(f"Primera ficha colocada (centro {center}): {t_candidate} asignada {piece_assigned} con rot {rot_assigned}")
    else:
        print("No se encontró candidato para la ficha inicial.")
    
    loop_iter = 0
    # Mientras queden candidatos posibles y fichas en el pool
    while len(placed) < max_fichas and piece_pool:
        loop_iter += 1
        candidates = []
        for t in triominos:
            if any(cell in occupied for cell in t):
                continue
            if occupied and not any(cell in adj[occ] for occ in occupied for cell in t):
                continue
            for candidate_piece in piece_pool:
                rot = valid_candidate(t, occupied, assigned, candidate_piece)
                if rot is not None:
                    candidates.append((t, candidate_piece, rot))
                    break
        print(f"Iteración {loop_iter} - Candidatos disponibles: {len(candidates)}")
        if not candidates:
            print("No quedan candidatos disponibles en esta generación.")
            break
        t_sel, piece_sel, rot_sel = random.choice(candidates)
        placed.append(t_sel)
        occupied.update(t_sel)
        for cell in t_sel:
            assigned[cell] = (piece_sel, rot_sel)
        piece_pool.remove(piece_sel)
        print(f"Ficha colocada: {t_sel} asignada {piece_sel} con rot {rot_sel}")
    
    print(f"Fichas colocadas en generación {gen+1}: {len(placed)}")
    
    # Animación: dibujar grilla y sobre ella, ficha a ficha
    dibujar_grilla(ax)
    # Crear textos informativos de generación y conteo de piezas
    info_gen = ax.text(0.01, 0.99, f"Generación: {gen+1}", transform=ax.transAxes,
                       verticalalignment='top', horizontalalignment='left', fontsize=12, color='black')
    info_piezas = ax.text(0.99, 0.99, f"Piezas: 0 de {max_fichas}", transform=ax.transAxes,
                          verticalalignment='top', horizontalalignment='right', fontsize=12, color='black')
    fig.canvas.draw()
    fig.canvas.flush_events()
    plt.pause(0.0005)
    
    for i, triomino in enumerate(placed):
        info_piezas.set_text(f"Piezas: {i+1} de {max_fichas}")
        for cid in triomino:
            poly = Polygon(coords_map[cid], facecolor='tomato', edgecolor='black', zorder=2)
            ax.add_patch(poly)
            if cid in assigned:
                dibujar_valores(ax, cid, assigned[cid][0], assigned[cid][1])
        fig.canvas.draw()
        fig.canvas.flush_events()
        plt.pause(0.0005)
    plt.pause(0.0005)

plt.ioff()
plt.show()