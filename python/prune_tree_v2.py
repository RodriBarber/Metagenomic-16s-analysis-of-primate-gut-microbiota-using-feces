#!/usr/bin/env python3

""""
Poda un árbol filogenético en formato newick, eliminando las hojas que no están en una lista de IDs de ASVs.

inputs:
    tree.nwk: 
    mis_asv_ids.txt
outputs:
    pruned_tree.nwk
"""
from Bio import Phylo
import time
from pathlib import Path

# -------------------[ configuracion ]---------------------------------#

input = Path("./exported-tree/tree_v2/tree.nwk") 
asv_ids = Path("./exported-tree/tree_v2/mis_asv_ids.txt")
output = Path("./exported-tree/tree_v2/pruned_tree.nwk")

# -------------------[ main ]---------------------------------#

# cargamos el árbol filogenético en formato newick
print("Cargando árbol...")
t0 = time.time()
tree = Phylo.read(input, "newick")
print(f"Árbol cargado en {time.time()-t0:.1f}s")

# ASVs a mantener
with open(asv_ids, "r") as f:
    keep_ids = set(line.strip() for line in f)

# elimianmos las hojas que no están en la lista de IDs
terminals = tree.get_terminals()
print(f"Total de hojas en el árbol: {len(terminals)}")
print(f"IDs a mantener (tus ASVs): {len(keep_ids)}")

to_remove = [t for t in terminals if t.name not in keep_ids]
print(f"Hojas a eliminar: {len(to_remove)}")

print("Podando ...")
t0 = time.time()
for i, t in enumerate(to_remove):
    tree.prune(t)
    if i % 1000 == 0:
        print(f"  Podadas {i}/{len(to_remove)}...")

# guardamos el árbol podado en formato newick
print(f"Poda completa en {time.time()-t0:.1f}s")
for clade in tree.get_nonterminals():
    clade.name = None

Phylo.write([tree], output, "newick")
print(f"Guardado como {output}")

