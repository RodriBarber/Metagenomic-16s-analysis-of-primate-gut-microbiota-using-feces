#!/usr/bin/env python3
"""
Genera un archivo txt con la lista de generos unicos en la taxonomia de un TSV de biom convert.

input:
    tsv/taxonomy-ms4.tsv
output:
    tsv/genera_unique.txt
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from silva_tax import extract_rank

# -------------------[ configuracion ]-------------------------------------#

TAXONOMY_FILE = Path("tsv/taxonomy-ms4.tsv")
OUT_LIST = Path("tsv/genera_unique.txt")

# -------------------[ main ]---------------------------------------------#

def main():
    if not TAXONOMY_FILE.exists():
        raise SystemExit(f"ERROR: no existe {TAXONOMY_FILE}")

    genera = set()

    with TAXONOMY_FILE.open(newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        next(reader)  # cabecera

        for row in reader:
            if not row:
                continue

            taxon = row[1].strip() if len(row) > 1 else ""
            genus = extract_rank(taxon, "g__")

            if genus:
                genera.add(genus)

    OUT_LIST.parent.mkdir(parents=True, exist_ok=True)

    with OUT_LIST.open("w") as f:
        for genus in sorted(genera):
            f.write(genus + "\n")

    print(f"Géneros únicos: {len(genera):,}")


if __name__ == "__main__":
    main()