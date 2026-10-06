#!/usr/bin/env python3

"""
Crea un archivo de etiquetas para iTOL a partir de un TSV de taxonomía.

input: 
    tsv/taxonomy_unique.tsv
output: 
    exported-tree/tree_v2/itol_labels.txt

"""

import csv
from pathlib import Path

# -------------------[ configuracion ]---------------------------------#

tsv_file = Path("tsv/taxonomy_unique.tsv")
output_file = Path("exported-tree/tree_v2/itol_labels.txt")

# -------------------[ main ]---------------------------------#

def main():
    with open(tsv_file, newline='') as f, open(output_file, "w") as out:
        reader = csv.reader(f, delimiter='\t')
        header = next(reader)  # saltamos cabecera

        out.write("LABELS\n")
        out.write("SEPARATOR TAB\n")
        out.write("DATA\n")

        count = 0
        for row in reader:
            if not row:
                continue
            feature_id = row[0].strip()
            taxon_full = row[1].strip() if len(row) > 1 else ""

            # separar por ";" y quedarnos con el último nivel taxonómico no vacío
            levels = [lvl.strip() for lvl in taxon_full.split(";") if lvl.strip() and "__" in lvl]
            short_name = levels[-1] if levels else taxon_full

            # limpiar caracteres problemáticos para iTOL
            short_name = short_name.replace(" ", "_").replace("(", "").replace(")", "")

            out.write(f"{feature_id}\t{short_name}\n")
            count += 1

    print(f"Archivo {output_file} generado con {count} entradas")

if __name__ == "__main__":
    main()
