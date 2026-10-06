#!/usr/bin/env python3
"""
Cuenta las especies que existen en NCBI para una lista de géneros dada

input: 
    tsv/genera_unique.txt
output: 
    contaminacion/ncbi_species_per_silva_genus.tsv

"""

import csv
import time
from pathlib import Path
from Bio import Entrez

# -------------------[ configuracion ]---------------------------------#

# Variables de entorno para NCBI Entrez. 
Entrez.email = "" # idicar correo electronico
Entrez.tool = "silva_genus_ncbi_species_count"


INPUT = Path("./tsv/genera_unique.txt")
OUTPUT = Path("./contaminacion/ncbi_species_per_silva_genus.tsv")

MAX_RETRIES = 6 # reintentos de consulta a NCBI antes de fallar
REQUEST_SLEEP = 2.0 # tiempo de espera entre consultas a NCBI (segundos)

FIELDS = [
    "silva_genus",
    "ncbi_query_name",
    "ncbi_genus_name",
    "ncbi_genus_taxid",
    "number_of_ncbi_species",
    "status",
    "message",
]

# -------------------[ funciones ]---------------------------------#

def ncbi_read(function, **kwargs):
    """Realiza una consulta con espera y reintentos."""
    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            time.sleep(REQUEST_SLEEP)

            with function(**kwargs) as handle:
                return Entrez.read(handle)

        except Exception as error:
            last_error = error

            if attempt == MAX_RETRIES - 1:
                break

            wait = min(60, 2 ** attempt)
            print(
                f"Error de NCBI: {error}. "
                f"Reintento en {wait} segundos.",
                flush=True,
            )
            time.sleep(wait)

    raise RuntimeError(
        f"NCBI falló tras {MAX_RETRIES} intentos: {last_error}"
    )


def find_ncbi_genus(query_name):
    """Busca el nombre científico exacto con rango genus."""
    term = f'"{query_name}"[Scientific Name] AND genus[Rank]'

    result = ncbi_read(
        Entrez.esearch,
        db="taxonomy",
        term=term,
        retmax=100,
    )

    taxids = result["IdList"]
    total = int(result["Count"])

    errors = result.get("ErrorList", {})
    if errors.get("FieldNotFound"):
        raise RuntimeError(f"Campo de búsqueda no reconocido: {errors}")

    if total == 0:
        return "", "", "taxonomy_not_found", (
            "Genus not found by the scientific-name query"
        )

    if total > 1:
        return "", "", "taxonomy_ambiguous", (
            f"Multiple genus TaxIDs returned ({total}): "
            + ",".join(taxids)
        )

    if len(taxids) != 1:
        raise RuntimeError("Respuesta incoherente de NCBI")

    taxid = str(taxids[0])

    records = ncbi_read(
        Entrez.efetch,
        db="taxonomy",
        id=taxid,
        retmode="xml",
    )

    if len(records) != 1:
        raise RuntimeError(f"Respuesta inesperada para TaxID {taxid}")

    record = records[0]
    name = str(record["ScientificName"])

    if record["Rank"] != "genus":
        return taxid, name, "wrong_taxonomic_rank", (
            f"NCBI rank: {record['Rank']}"
        )

    return taxid, name, "complete", ""


def count_species(genus_taxid):
    """Cuenta descendientes con rango species; no cuenta BioSamples."""
    result = ncbi_read(
        Entrez.esearch,
        db="taxonomy",
        term=f"txid{genus_taxid}[Subtree] AND species[Rank]",
        retmax=0,
    )

    if result.get("ErrorList"):
        raise RuntimeError(
            f"Error al contar especies: {result['ErrorList']}"
        )

    return int(result["Count"])

# -------------------[ main ]---------------------------------#

def main():
    if OUTPUT.exists():
        raise SystemExit(
            f"Ya existe {OUTPUT}. No se sobrescribe."
        )

    with INPUT.open(encoding="utf-8-sig") as handle:
        genera = sorted(
            {line.strip() for line in handle if line.strip()},
            key=str.casefold,
        )

    print(f"Géneros únicos de SILVA: {len(genera)}", flush=True)

    with OUTPUT.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=FIELDS,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()

        for index, genus in enumerate(genera, start=1):
            row = dict.fromkeys(FIELDS, "")
            row["silva_genus"] = genus
            row["ncbi_query_name"] = genus.replace("_", " ").strip()

            try:
                taxid, name, status, message = find_ncbi_genus(
                    row["ncbi_query_name"]
                )

                row.update({
                    "ncbi_genus_taxid": taxid,
                    "ncbi_genus_name": name,
                    "status": status,
                    "message": message,
                })

                if status == "complete":
                    row["number_of_ncbi_species"] = count_species(taxid)

            except Exception as error:
                row["status"] = "error"
                row["message"] = str(error)

            writer.writerow(row)
            handle.flush()

            print(
                f"[{index}/{len(genera)}] {genus}: "
                f"TaxID={row['ncbi_genus_taxid'] or 'NA'}, "
                f"especies={row['number_of_ncbi_species']}, "
                f"estado={row['status']}",
                flush=True,
            )

    print(f"\nTabla creada: {OUTPUT}", flush=True)


if __name__ == "__main__":
    main()
