#!/usr/bin/env python3

"""Abundancia relativa de un taxon a lo largo de las muestras."""

import csv
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

# -------------------[ configuracion ]---------------------------------#

INPUT = Path("./tsv/rel_abundance_asv.tsv")
OUTPUT = Path("./plots/macellibacteroides_abundance.png")

TAXON = "Macellibacteroides"

# -------------------[ funciones ]-------------------------------------#

def genus_of(lineage):
    """Ultimo rango del linaje, sin el prefijo de rango."""
    last = lineage.strip().split(";")[-1].strip()
    return last.split("__", 1)[-1] if "__" in last else last

# -------------------[ main ]-------------------------------------#

with open(INPUT, encoding="utf-8-sig", newline="") as f:
    reader = csv.reader(f, delimiter="\t")
    samples = next(reader)[1:]

    # se suman todas las filas del taxon: un genero puede tener varias ASVs
    values = [0.0] * len(samples)
    n_rows = 0
    for row in reader:
        if genus_of(row[1]) != TAXON:
            continue
        n_rows += 1
        for i, x in enumerate(row[2:]):
            values[i] += float(x)


if n_rows == 0:
    sys.exit(f"ERROR: '{TAXON}' no aparece en la columna {1} de {INPUT}")

print(f"{TAXON}: {n_rows} fila(s) sumadas, {len(samples)} muestras")
print(f"  presente en {sum(v > 0 for v in values)} muestras | max {max(values):.4g}")

# Figura de barras: abundancia relativa por muestra
fig, ax = plt.subplots(figsize=(max(6, 0.3 * len(samples)), 4))
ax.bar(range(len(samples)), values, color="steelblue", edgecolor="black", lw=0.3)

ax.set_xticks(range(len(samples)))
ax.set_xticklabels(samples, rotation=90, fontsize=6)
ax.set_xlabel("Muestra")
ax.set_ylabel("Abundancia relativa")
ax.set_title(f"{TAXON} por muestra")

fig.tight_layout()
fig.savefig(OUTPUT, dpi=300)
print(f"Figura guardada: {OUTPUT}")