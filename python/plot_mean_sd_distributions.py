#!/usr/bin/env python3
"""
Grafica la distribucion de la media y SD de cada genero, por categoria.

input:
    tsv/contaminacion/ncbi_genus_species_percentages_mean_sd_excluding_unknown.tsv
output:
    png/contaminacion/plots/clasificacion_media_vs_sd.png

"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# -------------------[ configuracion ]---------------------------------------#

INPUT = Path("contaminacion/ncbi_genus_species_percentages_mean_sd_excluding_unknown.tsv")
OUTPUT = Path("contaminacion/plots/clasificacion_media_vs_sd.png")


SD_MAX = 20.0        # umbral de SD para considerar un genero ecologicamente homogeneo
MIN_SPECIES = 2      # numero minimo de especies para considerar un genero ecologicamente homogeneo
DOM_MIN = 50.0       # % minimo de la categoria dominante para asignar etiqueta
DOM_MARGIN = 20.0    # % minimo de ventaja sobre la segunda categoria

CATEGORIES = {
    "gut": "fecal_gut_samples",
    "contaminacion": "contaminant_samples",
    "animal": "animal_samples",
    "otros": "other_samples",
}


COLORS = {"gut": "#4363d8", "contaminacion": "#e6194b",
          "animal": "#f58518",
          "otros": "#3cb44b", "ambiguo": "#999999",
          "descartado (SD alta)": "#d9d9d9"}

LABEL = {"fecal_gut_samples": "Heces / intestino",
         "contaminant_samples": "Contaminante",
         "animal_samples": "Animal",
         "other_samples": "Otro"}

# -------------------[ main ]---------------------------------------#

# Abre el archivo de entrada y verifica que contenga las columnas esperadas
infile, outfile = INPUT, OUTPUT
if not infile.exists():
    sys.exit(f"ERROR: no existe {infile}\n(directorio actual: {Path.cwd()})")
outfile.parent.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(infile, sep="\t")
mean_cols = [f"{p}_mean_pct" for p in CATEGORIES.values()]
sd_cols = [f"{p}_sd_pp" for p in CATEGORIES.values()]
label_of = {f"{p}_mean_pct": k for k, p in CATEGORIES.items()}

missing = [c for c in mean_cols + sd_cols + ["n_species_used"]
           if c not in df.columns]
if missing:
    sys.exit(f"ERROR: faltan columnas en {infile}: {', '.join(missing)}")

# Filtra los datos para incluir solo géneros con al menos un número mínimo de especies
df = df[df["n_species_used"] >= MIN_SPECIES].copy()

ordered = np.sort(df[mean_cols].to_numpy(), axis=1)[:, ::-1]
dominante = df[mean_cols].idxmax(axis=1).map(label_of)
pct_dom, margen = ordered[:, 0], ordered[:, 0] - ordered[:, 1]

# Se exige SD <= umbral solo en la categoria dominante
idx = df[mean_cols].to_numpy().argmax(axis=1)              
sd_vals = df[sd_cols].to_numpy()[np.arange(len(df)), idx] 
homogeneous = sd_vals <= SD_MAX
claro = (pct_dom >= DOM_MIN) & (margen >= DOM_MARGIN)

df["clase"] = np.where(~homogeneous, "descartado (SD alta)",
                       np.where(claro, dominante, "ambiguo"))

print(df["clase"].value_counts().to_string(), "\n")

# Figura: media frente a SD, por categoria
fig, axes = plt.subplots(1, len(CATEGORIES), figsize=(5.2 * len(CATEGORIES), 4.8),
                         sharex=True, sharey=True)

for ax, prefix in zip(np.atleast_1d(axes), CATEGORIES.values()):
    # region de decision: solo lo que cae aqui puede etiquetarse con esta clase
    ax.axhspan(0, SD_MAX, xmin=DOM_MIN / 100, color="gold", alpha=0.15, zorder=0)
    ax.axhline(SD_MAX, color="grey", ls="--", lw=1)
    ax.axvline(DOM_MIN, color="grey", ls="--", lw=1)

    # se dibuja primero lo descartado para que no tape a los candidatos
    for clase in ["descartado (SD alta)", "ambiguo", "otros", "gut", "contaminacion", "animal"]:
        sub = df[df["clase"] == clase]
        if sub.empty:
            continue
        ax.scatter(sub[f"{prefix}_mean_pct"], sub[f"{prefix}_sd_pp"],
                   s=8 + 2.5 * sub["n_species_used"], color=COLORS[clase],
                   edgecolor="black", linewidth=0.3, alpha=0.75,
                   label=f"{clase} (n={len(sub)})", zorder=2)

    ax.set_title(LABEL.get(prefix, prefix))
    ax.set_xlabel("Media entre especies (%)")
    ax.set_xlim(-3, 103)
    ax.set_ylim(-2, 62)

np.atleast_1d(axes)[0].set_ylabel("SD entre especies (pp)")


handles, labels = np.atleast_1d(axes)[0].get_legend_handles_labels()
fig.legend(handles, labels, fontsize=9, loc="upper left",
           bbox_to_anchor=(0.01, 0.99), framealpha=0.9, markerscale=0.6)

fig.suptitle(..., fontsize=12, y=0.98)
fig.tight_layout(rect=[0, 0, 1, 0.82])

fig.suptitle("Clasificacion de generos: media frente a SD por categoria\n"
             "(zona sombreada = media >= "
             f"{DOM_MIN:.0f}% y SD <= {SD_MAX:.0f} pp; tamaño = nº de especies)",
             fontsize=12)
fig.tight_layout(rect=[0, 0, 1, 0.9])
fig.savefig(outfile, dpi=300)
print(f"Figura guardada: {outfile}")