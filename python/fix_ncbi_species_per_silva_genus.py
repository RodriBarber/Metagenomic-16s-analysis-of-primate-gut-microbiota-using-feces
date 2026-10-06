#!/usr/bin/env python3

"""
Corrige los datos de especies ambiguas en un archivo TSV.

input: 
    contaminaion/ncbi_species_per_silva_genus.tsv
output: 
    contaminaion/ncbi_species_per_silva_genus_resolved.tsv

"""

import csv
from pathlib import Path
from Bio import Entrez

from count_ncbi_species_per_silva_genus import (
    ncbi_read,
    count_species,
)

# -------------------[ configuracion ]---------------------------------#

input = Path("contaminacion/ncbi_species_per_silva_genus.tsv")
output = Path("contaminacion/ncbi_species_per_silva_genus_resolved.tsv")

# Correspondencias revisadas manualmente.
corrections = {
    "Morganella": "581",
    "Schwartzia": "55506",
}

# -------------------[ main ]---------------------------------#

# Comprueba integridad básica de la tabla de entrada y que no se sobrescriba la salida.
if output.exists():
    raise SystemExit(f"Ya existe {output}. No se sobrescribe.")

with input.open(encoding="utf-8-sig", newline="") as handle:
    reader = csv.DictReader(handle, delimiter="\t")
    fields = reader.fieldnames
    rows = list(reader)

if any(None in r or any(v is None for v in r.values()) for r in rows):
    raise RuntimeError("La tabla contiene filas incompletas.")

errors = [r["silva_genus"] for r in rows if r["status"] == "error"]
if errors:
    raise RuntimeError(
        "Hay consultas fallidas que deben resolverse antes: "
        + ", ".join(errors)
    )

# Revisar tanto las correcciones como los géneros inicialmente aceptados.
selected = [
    row for row in rows
    if row["status"] == "complete"
    or row["silva_genus"] in corrections
]

taxids = sorted({
    corrections.get(row["silva_genus"], row["ncbi_genus_taxid"])
    for row in selected
})

# Recupera registros de NCBI y comprueba que son géneros procariotas.
records_by_id = {}

for start in range(0, len(taxids), 100):
    records = ncbi_read(
        Entrez.efetch,
        db="taxonomy",
        id=",".join(taxids[start:start + 100]),
        retmode="xml",
    )

    for record in records:
        records_by_id[str(record["TaxId"])] = record

for row in selected:
    genus = row["silva_genus"]
    taxid = corrections.get(genus, row["ncbi_genus_taxid"])

    if taxid not in records_by_id:
        raise RuntimeError(
            f"No se recuperó el TaxID esperado {taxid} para {genus}."
        )

    record = records_by_id[taxid]
    ancestors = {
        str(item["TaxId"])
        for item in record.get("LineageEx", [])
    }

    is_prokaryotic = bool(ancestors & {"2", "2157"})

    row["ncbi_genus_name"] = str(record["ScientificName"])
    row["ncbi_genus_taxid"] = taxid

    if record["Rank"] != "genus" or not is_prokaryotic:
        row["status"] = "non_prokaryotic_or_wrong_rank"
        row["number_of_ncbi_species"] = ""
        row["message"] = (
            f"Rank={record['Rank']}; "
            f"Lineage={record.get('Lineage', '')}"
        )
        print(f"Excluido del inventario procariótico: {genus}")
        continue

    if genus in corrections:
        if str(record["ScientificName"]).casefold() != genus.casefold():
            raise RuntimeError(
                f"La corrección de {genus} devuelve otro nombre."
            )

        row["number_of_ncbi_species"] = str(count_species(taxid))
        row["status"] = "complete"
        row["message"] = (
            "Bacterial genus selected after manual homonym review"
        )

        print(
            f"Corregido: {genus}; TaxID={taxid}; "
            f"especies={row['number_of_ncbi_species']}"
        )

# Guarda la tabla resultante, conservando las filas no resueltas
with output.open("x", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=fields,
        delimiter="\t",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)

print(f"\nTabla revisada creada: {output}")
