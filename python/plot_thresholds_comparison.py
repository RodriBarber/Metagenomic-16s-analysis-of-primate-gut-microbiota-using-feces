#!/usr/bin/env python3

"""""
Plotea histogramas de la distribución de frecuencias de ASVs para diferentes umbrales de corte.
Ayuda a elegir el umbral de corte más adecuado para filtrar ASVs poco frecuentes.

input: 
    tabla de frecuencias de ASVs (feature-table-ms2.tsv)
output: 
    plots/threshold_comparison_histograms.png

"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# -------------------[ configuracion ]---------------------------------------#

input = Path("tsv/feature-table-ms2.tsv")
thresholds_pct= [0.005, 0.01, 0.05, 0.1] # umbrales a probar, en porcentaje (%)

# -------------------[ main ]------------------------------------------------#
    
# Cargamos la tabla exportada (saltando la línea de comentario del biom convert)
df = pd.read_csv(input, sep="\t", skiprows=1, index_col=0)

# Frecuencia total por ASV 
frequency = df.sum(axis=1)
total_dataset = frequency.sum()

print(f"Total de reads en el dataset: {total_dataset:,.0f}")
print(f"Total de ASVs antes de filtrar: {len(frequency)}\n")

# Cálculo de las ASVs que sobreviven y las que se eliminan para cada umbral
results = {}
for pct in thresholds_pct:
    min_reads = total_dataset * (pct / 100)
    n_survive = (frequency >= min_reads).sum()
    n_removed = (frequency < min_reads).sum()
    results[pct] = {
        "min_reads": min_reads,
        "n_survive": n_survive,
        "n_removed": n_removed
    }
    print(f"Umbral {pct}%  ->  {min_reads:.2f} reads mínimas  ->  "
          f"ASVs que sobreviven: {n_survive}  |  ASVs eliminadas: {n_removed}")

# Ploteamos el histograma de frecuencias con los umbrales
fig, axes = plt.subplots(2, 2, figsize=(13, 10))
axes = axes.flatten()

# Usamos log10(frecuencia+1) para que el histograma sea legible
log_freq = np.log10(frequency + 1)

for i, pct in enumerate(thresholds_pct):
    ax = axes[i]
    min_reads = results[pct]["min_reads"]
    log_threshold = np.log10(min_reads + 1)

    ax.hist(log_freq, bins=50, color="steelblue", edgecolor="black", alpha=0.8)
    ax.axvline(log_threshold, color="red", linestyle="--", linewidth=2,
               label=f"Umbral: {min_reads:.1f} reads")
    ax.set_title(f"Corte al {pct}%  ->  {results[pct]['n_survive']} ASVs sobreviven "
                 f"/ {results[pct]['n_removed']} eliminadas")
    ax.set_xlabel("log10(Frecuencia total + 1)")
    ax.set_ylabel("Número de ASVs")
    ax.legend()

# Guardadamos la figura
plt.tight_layout()
plt.savefig("plots/threshold_comparison_histograms.png", dpi=300)
print("\nGráfico guardado como threshold_comparison_histograms.png")
