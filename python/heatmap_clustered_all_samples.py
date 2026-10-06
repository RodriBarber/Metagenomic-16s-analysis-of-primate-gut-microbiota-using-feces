#!/usr/bin/env python3
"""
Genera un Heatmap clusterizado de los TOP_N generos mas abundantes, con dos capas de
anotacion:

  - Muestras (barra superior): clusterizado por Bray-Curtis

  - Generos (etiquetas del eje Y): coloreadas segun su origen inferido a
    partir de los BioSamples de NCBI: VERDE = gut, ROJO = contaminacion,
    negro = sin clasificar.

input:
  tsv/feature-table-ms4.tsv
  tsv/taxonomy-ms4.tsv
  metadata/sample-metadata.tsv
  tsv/percent_mapped_by_sample.tsv
  contaminacion/generos_clasificados.tsv

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
MAPPED_FILE = Path("tsv/percent_mapped_by_sample.tsv")
GENUS_CLASS_FILE = Path("contaminacion/generos_clasificados.tsv")
SPECIES_COL = "host_species"        # columna a elegir del metadata para agrupar las muestras
GUILD_COL = "TrophicGuild"          # columna a elegir del metadata para colorear las muestras por guild trofica

OUT_PNG = Path("plots/heatmap_clustered_v2.png")
OUT_TSV = Path("tsv/heatmap_top_genera.tsv")

TOP_N = 50
SHOW_SAMPLE_IDS = False     # True añade el ERR a la etiqueta de columna
MIN_PCT_MAPPED = 50.0       # umbral de lecturas asignadas a genero

COLOR_LOW = "#d62728"       # muestra por debajo del umbral
COLOR_OK = "#d9d9d9"        # muestra por encima
COLOR_GUT = "#2ca02c"       # genero de origen intestinal
COLOR_CONT = "#d62728"      # genero de origen ambiental
COLOR_NA = "#000000"        # genero sin clasificar

# Paleta de la dieta trofica
GUILD_COLORS = {
    "Folivore":           "#1b7837",
    "Folivore-frugivore": "#a6dba0",
    "Frugivore":          "#f1a340",
    "Omnivore":           "#998ec3",
}

# -------------------[ funciones ]-----------------------------------------#

def load_mapped(path, col, id_col="sample-id"):
    """% de lecturas asignadas a genero por muestra."""
    out = {}
    with path.open(newline="") as f:
        r = csv.DictReader(f, delimiter="\t")
        if col not in (r.fieldnames or []):
            sys.exit(f"ERROR: no hay columna {col} en {path}")
        for row in r:
            out[row[id_col].strip()] = float(row[col])
    return out


def load_genus_class(path):
    """genero -> (clasificacion, aviso). Vacio si el fichero no existe."""
    if not path.exists():
        print(f"AVISO: no existe {path}; no se coloreran los generos")
        return {}
    out = {}
    with path.open(newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            out[row["silva_genus"].strip()] = (
                row["clasificacion"].strip().lower(),
                row.get("aviso", "").strip())
    return out

# -------------------[ main ]-----------------------------------------#

def main():
    for p in (TABLE_FILE, TAXONOMY_FILE, METADATA_FILE, MAPPED_FILE):
        if not p.exists():
            sys.exit(f"ERROR: no existe {p}")

    sp_map = load_metadata_column(METADATA_FILE, SPECIES_COL)
    guild_map = load_metadata_column(METADATA_FILE, GUILD_COL)
    mapped = load_mapped(MAPPED_FILE, "pct_Genero")
    gclass = load_genus_class(GENUS_CLASS_FILE)

    samples, rel = genus_matrix(TABLE_FILE, TAXONOMY_FILE,
                                keep_samples=set(sp_map))
    print(f"Muestras: {len(samples)}   "
          f"generos informativos: {len(rel) - (NORES in rel)}")

    sin_mapeo = [s for s in samples if s not in mapped]
    if sin_mapeo:
        print(f"AVISO: {len(sin_mapeo)} muestras sin dato de mapeo; "
              f"se tratan como por encima del umbral")

    # Matriz completa (generos x muestras) en porcentaje, base del cluterizado
    full = pd.DataFrame({g: rel[g] for g in rel}, index=samples).T * 100

    # TOP_N a  dibujar, por especie de hospedador
    _, mean_sp = mean_by_group(rel, samples, sp_map)
    top = top_genera(mean_sp, n=TOP_N)
    df = full.loc[top]

    # Clustering de columnas y filas
    col_link = linkage(pdist(full.T.values, metric="braycurtis"),
                       method="average")
    row_link = linkage(pdist(df.values, metric="correlation"),
                       method="average")

    # Anotacion de columnas
    species = sorted({sp_map[s] for s in samples})
    pal = sns.color_palette("tab20", len(species))
    cmap_sp = dict(zip(species, pal))

    guilds = [g for g in GUILD_COLORS if g in {guild_map[s] for s in samples}]
    sin_guild = {guild_map[s] for s in samples} - set(GUILD_COLORS)
    if sin_guild:
        print(f"AVISO: guilds sin color definido: {sorted(sin_guild)}")

    low = [s for s in samples if mapped.get(s, 100.0) < MIN_PCT_MAPPED]
    col_colors = pd.DataFrame({
        "Guild trofica": [GUILD_COLORS.get(guild_map[s], "#ffffff")
                          for s in samples],
        "Especie": [cmap_sp[sp_map[s]] for s in samples],
    }, index=samples)

    labels = ([f"{sp_map[s]} ({s})" for s in samples] if SHOW_SAMPLE_IDS
              else [sp_map[s] for s in samples])
    df.columns = labels
    col_colors.index = labels

    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_TSV, sep="\t", float_format="%.6f")

    # Figura clusterizada
    g = sns.clustermap(
        df,
        row_linkage=row_link,
        col_linkage=col_link,
        cmap="YlOrRd",
        col_colors=col_colors,
        figsize=(max(12, len(samples) * 0.14), max(8, len(top) * 0.30)),
        xticklabels=True, yticklabels=True,
        cbar_kws={"label": "Abundancia relativa (%)"},
        cbar_pos=(0.02, 0.83, 0.02, 0.14),
        linewidths=0,
    )

    g.ax_heatmap.set_xlabel("Muestras (agrupadas por Bray-Curtis)")
    g.ax_heatmap.set_ylabel("")
    plt.setp(g.ax_heatmap.get_xticklabels(), rotation=90, fontsize=5,
             style="italic")

    # Marcamos las muestras por debajo del umbral de mapeo con color y negrita
    low_labels = {lab for lab, s in zip(labels, samples) if s in low}
    for tick in g.ax_heatmap.get_xticklabels():
        if tick.get_text() in low_labels:
            tick.set_color(COLOR_LOW)
            tick.set_fontweight("bold")
    plt.setp(g.ax_heatmap.get_yticklabels(), rotation=0, fontsize=8)

    # Marcamos las etiquetas de genero segun su origen.
    n_gut = n_cont = n_na = 0
    for tick in g.ax_heatmap.get_yticklabels():
        name = tick.get_text()
        clas, aviso = gclass.get(name, ("", ""))
        if clas == "gut":
            tick.set_color(COLOR_GUT); n_gut += 1
        elif clas.startswith("contamin"):
            tick.set_color(COLOR_CONT); n_cont += 1

    # Leyendas
    h_gu = [plt.Rectangle((0, 0), 1, 1, color=GUILD_COLORS[g]) for g in guilds]
    leg0 = g.ax_heatmap.legend(h_gu, guilds, loc="upper center",
                               bbox_to_anchor=(0.5, -0.145), ncol=4, fontsize=7,
                               frameon=False, title="Dieta trofica",
                               title_fontsize=8)
    g.ax_heatmap.add_artist(leg0)

    h_sp = [plt.Rectangle((0, 0), 1, 1, color=cmap_sp[s]) for s in species]
    leg1 = g.ax_heatmap.legend(h_sp, species, loc="upper center",
                               bbox_to_anchor=(0.5, -0.195), ncol=8, fontsize=7,
                               frameon=False, title="Especie de hospedador",
                               title_fontsize=8)
    g.ax_heatmap.add_artist(leg1)

    h_an = [plt.Line2D([], [], color=COLOR_LOW, marker="s", ls="",
                       markersize=8),
            plt.Line2D([], [], color=COLOR_GUT, marker="s", ls="",
                       markersize=8),
            plt.Line2D([], [], color=COLOR_CONT, marker="s", ls="",
                       markersize=8),
            plt.Line2D([], [], color=COLOR_NA, marker="s", ls="",
                       markersize=8)]
    g.ax_heatmap.legend(
        h_an,
        [f"muestra con <{MIN_PCT_MAPPED}% de lecturas asignadas a genero",
         "genero: origen intestinal (gut)",
         "genero: origen ambiental (contaminacion)",
         "genero sin clasificar en gut/contaminacion"],
        loc="upper center", bbox_to_anchor=(0.5, -0.265), ncol=2, fontsize=7,
        frameon=False, title="Anotaciones (color del texto)", title_fontsize=8)

    g.fig.suptitle(f"Abundancia relativa de los {TOP_N} generos más "
                   f"abundantes", y=1.01, fontsize=11)

    # Guardamos la figura y mostramos resumen de cobertura y generos dibujados
    g.savefig(OUT_PNG, dpi=300, bbox_inches="tight")

    cov = df.sum(axis=0)
    print(f"Top {TOP_N} generos: cubren de media {cov.mean():.1f}% "
          f"de las lecturas (min {cov.min():.1f}%, max {cov.max():.1f}%)")
    print(f"Muestras por debajo de {MIN_PCT_MAPPED:.0f}% de mapeo: "
          f"{len(low)} de {len(samples)}")
    print(f"Generos dibujados: gut={n_gut}  contaminacion={n_cont}  "
          f"sin clasificar={n_na}")
    print(f"\n{OUT_PNG}\n{OUT_TSV}")


if __name__ == "__main__":
    main()