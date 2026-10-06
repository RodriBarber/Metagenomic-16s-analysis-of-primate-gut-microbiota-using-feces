#!/usr/bin/env python3

"""

Selecciona los generos ecologicamente homogeneos (SD entre especies por debajo
de un umbral) y los clasifica segun su origen dominante: gut, contaminacion, animal u
otros.

input: 
      contaminacion/ncbi_genus_species_percentages_mean_sd_excluding_unknown.tsv
output: 
      contaminacion/generos_clasificados.tsv
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd

# -------------------[ configuracion ]---------------------------------------#

input = Path("contaminacion/ncbi_genus_species_percentages_mean_sd_excluding_unknown.tsv")
output = Path("contaminacion/generos_clasificados.tsv")

SD_MAX = 20.0        # umbral de SD para considerar un genero ecologicamente homogeneo
MIN_SPECIES = 2      # numero minimo de especies para considerar un genero ecologicamente homogeneo
DOM_MIN = 50.0       # % minimo de la categoria dominante para asignar etiqueta
DOM_MARGIN = 20.0    # % minimo de ventaja sobre la segunda categoria

CATEGORIES = {
    "gut": "fecal_gut_samples",
    "animal": "animal_samples",
    "contaminacion": "contaminant_samples",
    "otros": "other_samples",
}

# -------------------[ main ]---------------------------------------#

# Abremos el archivo de entrada y comprobamos que tiene las columnas esperadas
df = pd.read_csv(input, sep="\t")
required = ["silva_genus", "n_species_used", "total_biosamples",
            "unknown_pct_of_total_biosamples"]
required += [f"{p}_{s}" for p in CATEGORIES.values() for s in ("mean_pct", "sd_pp")]
missing = [c for c in required if c not in df.columns]

if missing:
    sys.exit(f"ERROR: faltan columnas en {input}: {', '.join(missing)}\n"
             f"Columnas encontradas:\n  " + "\n  ".join(df.columns))

mean_cols = [f"{p}_mean_pct" for p in CATEGORIES.values()]
sd_cols = [f"{p}_sd_pp" for p in CATEGORIES.values()]
label_of = {f"{p}_mean_pct": k for k, p in CATEGORIES.items()}

# Clasificacion de generos: se descartan los que no cumplen los criterios de homogeneidad y numero de especies

n_total = len(df)

# Se exige SD <= umbral solo en la categoria dominante
idx = df[mean_cols].to_numpy().argmax(axis=1)              
sd_vals = df[sd_cols].to_numpy()[np.arange(len(df)), idx] 
homogeneous = sd_vals <= SD_MAX
enough_species = df["n_species_used"] >= MIN_SPECIES

sel = df[homogeneous & enough_species].copy()

print(f"Generos en el archivo:            {n_total}")
print(f"  descartados por n_species < {MIN_SPECIES}: "
      f"{int((~enough_species).sum())}")
print(f"  descartados por SD > {SD_MAX:.0f} pp:      "
      f"{int((enough_species & ~homogeneous).sum())}")
print(f"Generos seleccionados:            {len(sel)}\n")

# Clasificacion de generos: se asigna la categoria dominante y se calcula el margen respecto a la segunda 
# categoria

# categoria dominante y margen respecto a la segunda.
ordered = np.sort(sel[mean_cols].to_numpy(), axis=1)[:, ::-1]
sel["dominante"] = sel[mean_cols].idxmax(axis=1).map(label_of)
sel["pct_dominante"] = ordered[:, 0]
sel["margen_pp"] = ordered[:, 0] - ordered[:, 1]

# se etiqueta solo cuando la dominancia es clara; si no, "ambiguo"
clear = (sel["pct_dominante"] >= DOM_MIN) & (sel["margen_pp"] >= DOM_MARGIN)
sel["clasificacion"] = sel["dominante"].where(clear, "ambiguo")

# aviso separado: la clasificacion se apoya en pocos datos de origen
sel["aviso"] = ""
sel.loc[sel["unknown_pct_of_total_biosamples"] > 50, "aviso"] = "unknown>50%"
sel.loc[sel["total_biosamples"] < 10, "aviso"] += " pocas_biosamples"

# Salvamos la tabla de generos clasificados, con las columnas seleccionadas y ordenadas
cols = ["silva_genus", "ncbi_genus_taxid", "clasificacion", "pct_dominante",
        "margen_pp", "n_species_used", "total_biosamples",
        "unknown_pct_of_total_biosamples"] + mean_cols + sd_cols + ["aviso"]
cols = [c for c in cols if c in sel.columns]

out = sel[cols].sort_values(["clasificacion", "pct_dominante"],
                            ascending=[True, False])
out.to_csv(output, sep="\t", index=False, float_format="%.2f")

print(sel["clasificacion"].value_counts().to_string())
print(f"\nCon aviso de fiabilidad: {int((sel['aviso'].str.strip() != '').sum())}")
print(f"Tabla guardada: {output}")
