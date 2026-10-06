#!/usr/bin/env python3
"""
Barplot apilado de composicion a nivel de genero, promediado por especie.

Promedia las abundancias relativas POR MUESTRA y luego hace la media dentro
de cada especie. 

inputs:
  tsv/feature-table-ms4.tsv
  tsv/taxonomy-ms4.tsv
  metadata/sample-metadata.tsv

outputs:
  plots/genus_barplot_by_species.png
  tsv/genus_mean_by_species.tsv    
"""

import csv
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from genus_table import (genus_matrix, load_metadata_column,  # noqa: E402
                         mean_by_group, top_genera, NORES)

# -------------------[ configuracion ]---------------------------------------#

TABLE_FILE = Path("tsv/feature-table-ms4.tsv")
TAXONOMY_FILE = Path("tsv/taxonomy-ms4.tsv")
METADATA_FILE = Path("metadata/sample-metadata.tsv")
SPECIES_COL = "host_species"

OUT_PNG = Path("plots/genus_barplot_by_species.png")
OUT_TSV = Path("tsv/genus_mean_by_species.tsv")

TOP_N = 20 # numero de generos con color; el resto se agrupa en "Other_genera"      
OTHER = "Other_genera"

# -------------------[ main ]---------------------------------------#

def main():
    for p in (TABLE_FILE, TAXONOMY_FILE, METADATA_FILE):
        if not p.exists():
            sys.exit(f"ERROR: no existe {p}")

    sp_map = load_metadata_column(METADATA_FILE, SPECIES_COL)
    samples, rel = genus_matrix(TABLE_FILE, TAXONOMY_FILE,
                                keep_samples=set(sp_map))

    # meida por especie (todas pesan lo mismo)
    species, mean = mean_by_group(rel, samples, sp_map)
    n_by_sp = [sum(1 for s in samples if sp_map[s] == sp) for sp in species]

    top = top_genera(mean, n=TOP_N)
    rest = [g for g in mean if g != NORES and g not in top]

    rows = [(g, mean[g]) for g in top]
    if rest:
        rows.append((OTHER, sum(mean[g] for g in rest)))
    rows.append((NORES, mean.get(NORES, np.zeros(len(species)))))

    # guardamos la tabla de abundancias relativas promedio por especie
    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_TSV.open("w", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["taxon"] + species)
        for name, vals in rows:
            w.writerow([name] + [f"{v:.6f}" for v in vals])

    # colores: descartamos los grises de tab20 y tab20b, que son muy parecidos
    def is_grey(c):
        return max(c[:3]) - min(c[:3]) < 0.06

    palette = [c for c in (list(plt.get_cmap("tab20").colors)
                           + list(plt.get_cmap("tab20b").colors))
               if not is_grey(c)]
    colors, k = [], 0
    for name, _ in rows:
        if name == OTHER:
            colors.append("#cccccc")
        elif name == NORES:
            colors.append("#4d4d4d")
        else:
            colors.append(palette[k % len(palette)])
            k += 1

    # barplot apilado
    fig, ax = plt.subplots(figsize=(max(9, 0.75 * len(species)), 7))
    bottom = np.zeros(len(species))
    x = np.arange(len(species))
    for (name, vals), c in zip(rows, colors):
        ax.bar(x, vals * 100, bottom=bottom * 100, color=c,
               edgecolor="white", linewidth=0.3, label=name)
        bottom += vals

    ax.set_xticks(x)
    ax.set_xticklabels([f"{sp}\n(n={k})" for sp, k in zip(species, n_by_sp)],
                       rotation=45, ha="right", fontsize=8, style="italic")
    ax.set_ylabel("Abundancia relativa media (%)")
    ax.set_ylim(0, 100)
    ax.set_title(f"Composicion a nivel de genero por especie "
                 f"(top {TOP_N} generos)")
    ax.legend(bbox_to_anchor=(1.01, 1), loc="upper left",
              fontsize=7, frameon=False)
    fig.tight_layout()
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PNG, dpi=300)

    print(f"Muestras: {len(samples)}   Especies: {len(species)}")
    print(f"Generos informativos: {len(rel) - (NORES in rel)}  "
          f"(top {len(top)} con color, {len(rest)} en {OTHER})")
    nr = mean.get(NORES, np.zeros(1))
    print(f"{NORES}: media {100*nr.mean():.1f}%  "
          f"(min {100*nr.min():.1f}%, max {100*nr.max():.1f}%)")
    print(f"\n{OUT_PNG}\n{OUT_TSV}")


if __name__ == "__main__":
    main()