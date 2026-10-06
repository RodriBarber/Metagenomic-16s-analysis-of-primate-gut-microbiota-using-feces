#!/usr/bin/env python3

"""
Plotea dos histogramas: uno de la prevalencia (número de muestras donde aparece cada ASV) 
y otro de la frecuencia total (número total de reads por ASV).

input: 
        tsv/feature-table-ms2.tsv (tabla de abundancias de ASVs por muestra, exportada desde QIIME2)
output: 
        plots/prevalence_frequency_histograms.png (histogramas)
        tsv/asv_frequency_prevalence.tsv (tabla con frecuencia y prevalencia por ASV)
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# -------------------[ configuracion ]---------------------------------------#

input= Path("tsv/feature-table-ms2.tsv")

# -------------------[ main ]------------------------------------------------#

# Cargamos la tabla exportada (saltando la línea de comentario del biom convert)
df = pd.read_csv(input, sep="\t", skiprows=1, index_col=0) 

# Prevalencia por ASV 
frequency = df.sum(axis=1)
prevalence = (df  > 0).sum(axis=1)

# Guardado de los resultados en un archivo tsv
summary = pd.DataFrame({"frequency": frequency, "prevalence": prevalence})
summary.to_csv("tsv/asv_frequency_prevalence.tsv", sep="\t")
 
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
 
# Histograma 1: Prevalencia 
axes[0].hist(summary["prevalence"], bins=range(1, summary["prevalence"].max() + 2), 
             color="steelblue", edgecolor="black")
axes[0].set_xlabel("Prevalencia (nº de muestras)")
axes[0].set_ylabel("Número de ASVs")
axes[0].set_title("Distribución de prevalencia por ASV")
 
# Histograma 2: Frecuencia total 
axes[1].hist(summary["frequency"], bins=50, color="darkorange", edgecolor="black")
axes[1].set_xscale("log")
axes[1].set_xlabel("Frecuencia total (nº de reads, escala log)")
axes[1].set_ylabel("Número de ASVs")
axes[1].set_title("Distribución de frecuencia por ASV")

# Salvamos la figura
plt.tight_layout()
plt.savefig("plots/prevalence_frequency_histograms.png", dpi=300)
print("Gráfico guardado como prevalence_frequency_histograms.png")
print(summary.describe())

