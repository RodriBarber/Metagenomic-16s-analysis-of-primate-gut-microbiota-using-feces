#!/usr/bin/env python3
"""
Genera un Heatmap clusterizado de los TOP_N generos mas abundantes.

El clustering s ehace sobre el total de los géneros aunque luego se muestran solo el TOP_N

input
  tsv/feature-table-ms4.tsv
  tsv/taxonomy-ms4.tsv
  metadata/sample-metadata.tsv

output:
  plots/heatmap_clustered.png
  tsv/heatmap_top_genera.tsv    
"""

import csv
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402
from scipy.cluster.hierarchy import linkage  # noqa: E402
from scipy.spatial.distance import pdist  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from genus_table import (genus_matrix, load_metadata_column,  # noqa: E402
                         mean_by_group, top_genera, NORES)

# -------------------[ configuracion ]---------------------------------------#

TABLE_FILE = Path("tsv/feature-table-ms4.tsv")
TAXONOMY_FILE = Path("tsv/taxonomy-ms4.tsv")
METADATA_FILE = Path("metadata/sample-metadata.tsv")
SPECIES_COL = "host_species"

OUT_PNG = Path("plots/heatmap_clustered.png")
OUT_TSV = Path("tsv/heatmap_top_genera.tsv")

TOP_N = 50          
SHOW_SAMPLE_IDS = False   # True añade etiqueta a cada muestra

# -------------------[ main ]---------------------------------------#

def main():
    for p in (TABLE_FILE, TAXONOMY_FILE, METADATA_FILE):
        if not p.exists():
            sys.exit(f"ERROR: no existe {p}")

    sp_map = load_metadata_column(METADATA_FILE, SPECIES_COL)
    samples, rel = genus_matrix(TABLE_FILE, TAXONOMY_FILE,
                                keep_samples=set(sp_map))
    print(f"Muestras: {len(samples)}   "
          f"generos informativos: {len(rel) - (NORES in rel)}")

    # matriz completa de abundancia relativa
    full = pd.DataFrame({g: rel[g] for g in rel}, index=samples).T * 100

    _, mean_sp = mean_by_group(rel, samples, sp_map)
    top = top_genera(mean_sp, n=TOP_N)
    df = full.loc[top]

    # clustering: columnas (muestras) por Bray-Curtis, filas (generos) por correlacion
    col_link = linkage(pdist(full.T.values, metric="braycurtis"),
                       method="average")

    row_link = linkage(pdist(df.values, metric="correlation"),
                       method="average")

    # coloreado de muestras por especie
    species = sorted({sp_map[s] for s in samples})
    pal = sns.color_palette("tab20", len(species))
    cmap_sp = dict(zip(species, pal))
    col_colors = pd.Series([cmap_sp[sp_map[s]] for s in samples],
                           index=samples, name="Especie")

    labels = ([f"{sp_map[s]} ({s})" for s in samples] if SHOW_SAMPLE_IDS
              else [sp_map[s] for s in samples])
    df.columns = labels
    col_colors.index = labels

    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_TSV, sep="\t", float_format="%.6f")

    # figura
    g = sns.clustermap(
        df,
        row_linkage=row_link,
        col_linkage=col_link,
        cmap="YlOrRd",
        col_colors=col_colors,
        figsize=(max(12, len(samples) * 0.14), max(8, len(top) * 0.42)),
        xticklabels=True, yticklabels=True,
        cbar_kws={"label": "Abundancia relativa (%)"},
        cbar_pos=(0.02, 0.83, 0.02, 0.14),
        linewidths=0,
    )

    g.ax_heatmap.set_xlabel("Muestras (agrupadas por Bray-Curtis)")
    g.ax_heatmap.set_ylabel("")
    plt.setp(g.ax_heatmap.get_xticklabels(), rotation=90, fontsize=5,
             style="italic")
    plt.setp(g.ax_heatmap.get_yticklabels(), rotation=0, fontsize=8)

    # leyenda de especies
    handles = [plt.Rectangle((0, 0), 1, 1, color=cmap_sp[s]) for s in species]
    g.ax_heatmap.legend(handles, species, loc="upper center",
                        bbox_to_anchor=(0.5, -0.28), ncol=5, fontsize=7,
                        frameon=False, title="Especie de hospedador",
                        title_fontsize=8)

    g.fig.suptitle(f"Abundancia relativa de los {TOP_N} generos mas "
                   f"abundantes", y=1.01, fontsize=11)
    g.savefig(OUT_PNG, dpi=300, bbox_inches="tight")

    cov = df.sum(axis=0)
    print(f"Top {TOP_N} generos: cubren de media "
          f"{cov.mean():.1f}% de las lecturas "
          f"(min {cov.min():.1f}%, max {cov.max():.1f}%)")
    print(f"\n{OUT_PNG}\n{OUT_TSV}")


if __name__ == "__main__":
    main()