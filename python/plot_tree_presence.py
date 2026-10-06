#!/usr/bin/env python3
"""
Genera un archivo para visualizar la presencia/ausenciade ASVs en diferentes especies.

input: 
    taxonomy_unique.tsv
    feature-table-ms4.tsv
    sample-metadata.tsv
output:
    itol_species_presence.txt (archivo para subir en iTOL con presencia/ausencia de ASVs por especie)

"""

import csv
from pathlib import Path

# -------------------[ configuracion ]---------------------------------#

TABLE_FILE = Path("tsv/feature-table-ms4.tsv")
TAXONOMY_UNIQUE_FILE = Path ("tsv/taxonomy_unique.tsv")   
METADATA_FILE = Path("metadata/sample-metadata.tsv")
OUTPUT_FILE = Path("exported-tree/tree_v2/itol_species_presence.txt")

# paleta de colores
PALETTE = {
    "Alouatta caraya":        "#2476b3",
    "Alouatta palliata":      "#adc6e7",
    "Alouatta seniculus":     "#ff7e10",
    "Ateles belzebuth":       "#ffba77",
    "Cercopithecus ascanius": "#319e30",
    "Colobus guereza":        "#97de89",
    "Eulemur rubriventer":    "#d52c2b",
    "Gorilla gorilla":        "#ff9794",
    "Lemur catta":            "#9267bc",
    "Pan troglodytes":        "#c4afd4",
    "Papio anubis":           "#8b574c",
    "Papio hamadryas":        "#c39b93",
    "Piliocolobus badius":    "#e277c1",
    "Propithecus verreauxi":  "#f7b5d1",
    "Theropithecus gelada":   "#7e7e7e",
}
FALLBACK_COLOR = "#000000"

# -------------------[ main ]---------------------------------#

with open(TABLE_FILE) as f:
    lines = f.readlines()

header = lines[1].strip().split("\t")
sample_ids = header[1:]

abundance = {}  
for line in lines[2:]:
    parts = line.strip().split("\t")
    fid = parts[0]
    abundance[fid] = [float(x) for x in parts[1:]]

# cargamos metadata y asignamos una id de especie a cada muestra
representatives = []
with open(TAXONOMY_UNIQUE_FILE, newline='') as f:
    reader = csv.DictReader(f, delimiter='\t')
    for row in reader:
        rep_id = row["id"].strip()
        genus = row["genus"].strip()
        all_ids = [x.strip() for x in row["all_asv_ids"].split(";") if x.strip()]
        representatives.append((rep_id, genus, all_ids))

# lista de especies únicas en orden de aparición
sample_to_species = {}
with open(METADATA_FILE, newline='') as f:
    reader = csv.reader(f, delimiter='\t')
    header_meta = next(reader)
    id_idx = header_meta.index("sample-id")
    sp_idx = header_meta.index("host_species")
    for row in reader:
        if not row or row[0].startswith("#q2:types"):
            continue
        sample_to_species[row[id_idx].strip()] = row[sp_idx].strip()

species_list = sorted({sample_to_species.get(sid, "Unknown") for sid in sample_ids})
for sid in sample_ids:
    sp = sample_to_species.get(sid, "Unknown")
    if sp not in species_list:
        species_list.append(sp)

species_colors = {sp: PALETTE.get(sp, FALLBACK_COLOR) for sp in species_list}

# calculamos presencia/ausencia de ASVs por especie
presence = {}
for rep_id, genus, all_ids in representatives:
    presence[rep_id] = {sp: False for sp in species_list}
    for asv_id in all_ids:
        if asv_id not in abundance:
            continue  # por si algún id no está en la tabla 
        for j, sid in enumerate(sample_ids):
            if abundance[asv_id][j] > 0:
                sp = sample_to_species.get(sid, "Unknown")
                presence[rep_id][sp] = True

# guardamos el archivo de presencia/ausencia para iTOL
with open(OUTPUT_FILE, "w") as out:
    out.write("DATASET_BINARY\n")
    out.write("SEPARATOR TAB\n")
    out.write("DATASET_LABEL\tPresencia por especie (agregado por genero)\n")
    out.write("COLOR\t#000000\n")

    field_shapes = "\t".join(["2"] * len(species_list))
    field_labels = "\t".join(species_list)
    field_colors = "\t".join([species_colors[sp] for sp in species_list])

    out.write(f"FIELD_SHAPES\t{field_shapes}\n")
    out.write(f"FIELD_LABELS\t{field_labels}\n")
    out.write(f"FIELD_COLORS\t{field_colors}\n")

    out.write("LEGEND_TITLE\tEspecie de primate\n")
    out.write(f"LEGEND_SHAPES\t{field_shapes}\n")
    out.write(f"LEGEND_COLORS\t{field_colors}\n")
    out.write(f"LEGEND_LABELS\t{field_labels}\n")

    out.write("MARGIN\t5\n")
    out.write("HEIGHT_FACTOR\t1\n")
    out.write("SYMBOL_SPACING\t10\n")

    out.write("DATA\n")
    for rep_id, genus, all_ids in representatives:
        row_values = ["1" if presence[rep_id][sp] else "-1" for sp in species_list]
        out.write(rep_id + "\t" + "\t".join(row_values) + "\n")

print(f"Archivo generado: {OUTPUT_FILE}")
print(f"Géneros/representantes procesados: {len(representatives)}")

