#!/usr/bin/env python3
"""
Genera un grafico con el porcentaje de lecturas asignadas a genero, muestra a muestra.

input:
    tsv/percent_mapped_by_sample.tsv

output:
    plots/percent_mapped_by_sample.png
"""

import csv
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")          
import matplotlib.pyplot as plt  # noqa: E402

# -------------------[ configuracion ]------------------------------------#

INPUT = Path("tsv/percent_mapped_by_sample.tsv")
OUTPUT = Path("plots/percent_mapped_by_sample.png")
THRESHOLD = 50.0

# -------------------[ funciones ]---------------------------------------#

def load_species(path, col="host_species", id_col="sample-id"):
    if not path.exists():
        return {}
    out = {}
    with path.open(newline="") as f:
        r = csv.reader(f, delimiter="\t")
        hdr = next(r)
        i_id, i_sp = hdr.index(id_col), hdr.index(col)
        for row in r:
            if not row or row[0].startswith("#q2:types"):
                continue
            out[row[i_id].strip()] = row[i_sp].strip()
    return out

# -------------------[ main ]---------------------------------------#

def main():
    if not INPUT.exists():
        sys.exit(f"ERROR: no existe {INPUT}")

    with INPUT.open(newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        if "pct_Genero" not in reader.fieldnames:
            sys.exit(f"ERROR: no hay columna {"pct_Genero"}. "
                     f"Disponibles: {reader.fieldnames}")
        rows = [(r["sample-id"], float(r["pct_Genero"])) for r in reader]

    rows.sort(key=lambda x: x[1], reverse=True)
    sp = load_species("ct_Genero")

    # Etiqueta: especie + accession, para identificar la muestra concreta
    labels = [f"{sp[s]}  {s}" if s in sp else s for s, _ in rows]
    values = [v for _, v in rows]
    colors = ["#d62728" if v < THRESHOLD else "#4878a8" for v in values]

    # Figura
    fig, ax = plt.subplots(figsize=(8, max(6, 0.16 * len(rows))))
    y = range(len(rows))
    ax.barh(y, values, color=colors, height=0.75)

    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, fontsize=5)
    ax.invert_yaxis()                      
    ax.set_xlim(0, 100)
    ax.set_xlabel("Lecturas asignadas a genero (%)")
    ax.set_ylabel("")
    ax.set_title("Porcentaje de lecturas asignadas a genero por muestra",
                 fontsize=11)

    # Umbral de porcentaje de lecturas asignadas a genero
    ax.axvline(THRESHOLD, color="red", ls="--", lw=1.2,
               label=f"umbral {THRESHOLD:.0f}%")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.grid(axis="x", ls=":", lw=0.5, alpha=0.6)
    ax.set_axisbelow(True)

    fig.tight_layout()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT, dpi=300, bbox_inches="tight")

    n_low = sum(1 for v in values if v < THRESHOLD)
    print(f"Muestras: {len(values)}   por debajo de {THRESHOLD:.0f}%: {n_low}")
    print(f"min {min(values):.1f}%   mediana "
          f"{sorted(values)[len(values)//2]:.1f}%   max {max(values):.1f}%")
    print(f"\n{OUTPUT}")


if __name__ == "__main__":
    main()