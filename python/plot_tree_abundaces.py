#!/usr/bin/env python3
"""
Genera un archivo para visualizar la abundancia de ASVs en diferentes especies.

input: 
    taxonomy_unique.tsv
    feature-table-ms4.tsv
    sample-metadata.tsv
output:
    itol_species_presence.txt (archivo para subir en iTOL con presencia/ausencia de ASVs por especie)

"""

import csv
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from genus_table import load_metadata_column  # noqa: E402

# -------------------[ configuracion ]---------------------------------------#

TABLE_FILE = Path("tsv/feature-table-ms4.tsv")
TAXONOMY_UNIQUE_FILE = Path("tsv/taxonomy_unique.tsv")
METADATA_FILE = Path("metadata/sample-metadata.tsv")
OUTPUT_FILE = Path("exported-tree/tree_v2/itol_species_abundance.txt")

MAX_SIZE = 1.0          # tamaño del circulo mayor
TRANSFORM = "linear"    # tipo de transformación: "sqrt" | "linear" | "log"

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

# -------------------[ funciones ]---------------------------------------#

def load_table(path):
    """Carga la tabla de abundancia de ASVs por muestra."""
    with path.open() as f:
        lines = [l.rstrip("\n") for l in f if l.strip()]
    start = 1 if lines[0].startswith("# Constructed") else 0
    samples = lines[start].split("\t")[1:]
    counts = {}
    for line in lines[start + 1:]:
        p = line.split("\t")
        counts[p[0]] = [float(x) for x in p[1:]]
    return samples, counts


def scale(value, vmax):
    """Normaliza a [0, MAX_SIZE] aplicando la transformacion elegida."""
    if vmax <= 0 or value <= 0:
        return 0.0
    r = value / vmax
    if TRANSFORM == "sqrt":
        r = r ** 0.5
    elif TRANSFORM == "log":
        from math import log10
        r = log10(1 + 9 * r)
    return MAX_SIZE * r

# -------------------[ main ]---------------------------------------#

def main():
    for p in (TABLE_FILE, TAXONOMY_UNIQUE_FILE, METADATA_FILE):
        if not p.exists():
            sys.exit(f"ERROR: no existe {p}")

    # cargamos tabla de abundancia y metadatos
    samples, abundance = load_table(TABLE_FILE)
    sp_map = load_metadata_column(METADATA_FILE, "host_species")

    # filtramos muestras sin metadatos
    keep = [i for i, s in enumerate(samples) if s in sp_map]
    if len(keep) < len(samples):
        print(f"AVISO: {len(samples) - len(keep)} muestras sin metadatos, "
              f"se excluyen")
        
    # filtramos las columnas correspondientes
    samples = [samples[i] for i in keep]
    abundance = {a: [v[i] for i in keep] for a, v in abundance.items()}
    totals = [sum(v[i] for v in abundance.values()) for i in range(len(samples))]

    # cargar los ASVs representantes y sus géneros
    representatives = []
    with TAXONOMY_UNIQUE_FILE.open(newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        id_col = next((c for c in ("id")
                       if c in (reader.fieldnames or [])), None)
        if id_col is None:
            sys.exit(f"ERROR: no hay columna de ID en {TAXONOMY_UNIQUE_FILE}; "
                     f"columnas: {reader.fieldnames}")
        for row in reader:
            representatives.append((row[id_col].strip(), row["genus"].strip(),
                                    [x.strip() for x in
                                     row["all_asv_ids"].split(";") if x.strip()]))

    # especies en orden alfabetico (el mismo orden que la leyenda)
    species_list = sorted({sp_map[s] for s in samples})
    idx_by_sp = {sp: [i for i, s in enumerate(samples) if sp_map[s] == sp]
                 for sp in species_list}

    # abundancia relativa promedio de cada genero por especie
    values = {}
    for rep_id, genus, all_ids in representatives:
        rel = [0.0] * len(samples)
        for asv in all_ids:
            if asv not in abundance:
                continue
            for i, v in enumerate(abundance[asv]):
                rel[i] += v / totals[i] if totals[i] else 0.0
        values[rep_id] = [sum(rel[i] for i in idx_by_sp[sp]) / len(idx_by_sp[sp])
                          for sp in species_list]

    vmax = max((max(v) for v in values.values()), default=0.0)
    if vmax <= 0:
        sys.exit("ERROR: todas las abundancias son cero")

    colors = [PALETTE.get(sp, FALLBACK_COLOR) for sp in species_list]
    sin_color = [sp for sp in species_list if sp not in PALETTE]
    if sin_color:
        print(f"AVISO: especies sin color en PALETTE: {sin_color}")

    # escribimos el archivo de salida para iTOL
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w") as out:
        out.write("DATASET_EXTERNALSHAPE\n")
        out.write("SEPARATOR TAB\n")
        out.write("DATASET_LABEL\tAbundancia relativa por especie\n")
        out.write("COLOR\t#000000\n")
        out.write(f"FIELD_LABELS\t" + "\t".join(species_list) + "\n")
        out.write(f"FIELD_COLORS\t" + "\t".join(colors) + "\n")
        # 2 = circulo
        out.write("FIELD_SHAPES\t" + "\t".join(["2"] * len(species_list)) + "\n")

        out.write("LEGEND_TITLE\tEspecie de primate\n")
        out.write("LEGEND_SHAPES\t" + "\t".join(["2"] * len(species_list)) + "\n")
        out.write("LEGEND_COLORS\t" + "\t".join(colors) + "\n")
        out.write("LEGEND_LABELS\t" + "\t".join(species_list) + "\n")

        out.write("HORIZONTAL_GRID\t1\n")
        out.write("VERTICAL_GRID\t0\n")
        out.write("SHAPE_SPACING\t2\n")
        out.write("MARGIN\t5\n")
        out.write("BORDER_WIDTH\t0.5\n")
        out.write("BORDER_COLOR\t#999999\n")

        out.write("DATA\n")
        for rep_id, genus, _ in representatives:
            row = [f"{scale(v, vmax):.4f}" for v in values[rep_id]]
            out.write(rep_id + "\t" + "\t".join(row) + "\n")

    print(f"Archivo generado: {OUTPUT_FILE}")
    print(f"Transformacion del tamaño: {TRANSFORM}")


if __name__ == "__main__":
    main()