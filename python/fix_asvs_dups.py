#!/usr/bin/env python3
"""
Agrupa las ASVs por genero, deja u ID representativo y agrupa el resto de las ASVs del mismo genero. 

input: 
    tsv/taxonomy-ms4.tsv 
output: 
    tsv/taxonomy_unique.tsv (una fila por genero, con todas sus ASVs)

"""

import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from silva_tax import extract_rank  # noqa: E402

# -------------------[ configuracion ]---------------------------------#

TAXONOMY_FILE = Path("tsv/taxonomy-ms4.tsv")
OUT_GENUS = Path("tsv/taxonomy_unique.tsv")

# -------------------[ main ]---------------------------------#

def main():
    if not TAXONOMY_FILE.exists():
        sys.exit(f"ERROR: no existe {TAXONOMY_FILE}")

    tax = pd.read_csv(TAXONOMY_FILE, sep="\t")

    # compruebo que la tabla tiene las columnas esperadas
    id_col = next((c for c in ("Feature ID", "id", "#OTU ID")
                   if c in tax.columns), None)
    if id_col is None or "Taxon" not in tax.columns:
        sys.exit(f"ERROR: columnas inesperadas: {list(tax.columns)}")

    tax["genus"] = tax["Taxon"].fillna("").apply(
        lambda s: extract_rank(s, "g__"))

    con_genero = tax[tax["genus"].notna()]
    sin_genero = tax[tax["genus"].isna()]

    # una fila por genero, con todas sus ASVs
    grouped = (con_genero
               .groupby("genus")[id_col]
               .agg(all_asv_ids=lambda s: ";".join(s),
                    n_asvs="size",
                    representative="first")
               .reset_index()
               .sort_values(["n_asvs", "genus"], ascending=[False, True]))

    OUT_GENUS.parent.mkdir(parents=True, exist_ok=True)
    grouped = grouped.rename(columns={"representative": "id"})
    grouped[["id", "genus", "all_asv_ids", "n_asvs"]].to_csv(
        OUT_GENUS, sep="\t", index=False)

    print(f"ASVs totales:            {len(tax):,}")
    print(f"ASVs con genero:         {len(con_genero):,} "
          f"({100 * len(con_genero) / len(tax):.1f}%)")
    print(f"ASVs sin genero:         {len(sin_genero):,}")

if __name__ == "__main__":
    main()