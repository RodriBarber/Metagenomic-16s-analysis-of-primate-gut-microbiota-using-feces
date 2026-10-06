#!/usr/bin/env python3

"""
Cuenta el numero de BioSamples en NCBI para cada especie del inventario.

input: 
    ncbi_species_inventory_all_genera.tsv
output: 
    ncbi_biosample_counts_per_species.tsv

"""

import csv
import time
from datetime import datetime, timezone
from pathlib import Path
from Bio import Entrez

# -------------------[ configuracion ]---------------------------------#

Entrez.email = "" # email de contacto para NCBI Entrez
Entrez.tool = "primate_species_biosample_counts"

INPUT = Path("contaminacion/ncbi_species_inventory_all_genera.tsv")
OUTPUT = Path("contaminacion/ncbi_biosample_counts_per_species.tsv")

MAX_RETRIES = 5 # numero de reintentos para consultas a NCBI Entrez
REQUEST_DELAY = 1 # segundos de espera entre consultas

# -------------------[ funciones ]---------------------------------#

def interpret_result(result, taxid):
    """Aceptar resultados válidos y reconocer el caso sin BioSamples."""
    count = int(result["Count"])
    errors = result.get("ErrorList", {})
    warnings = result.get("WarningList", {})
    term = f"txid{taxid}[Organism:exp]"

    # Respuesta sin avisos ni errores.
    if not any(errors.values()) and not any(warnings.values()):
        return count

    # NCBI puede indicar PhraseNotFound cuando el TaxID consultado
    # no tiene registros indexados en BioSample.
    allowed_errors = {"FieldNotFound", "PhraseNotFound"}
    allowed_warnings = {
        "QuotedPhraseNotFound",
        "PhraseIgnored",
        "OutputMessage",
    }

    unexpected_errors = any(
        value
        for key, value in errors.items()
        if key not in allowed_errors
    )

    unexpected_warnings = any(
        value
        for key, value in warnings.items()
        if key not in allowed_warnings
    )

    missing_phrases = set(errors.get("PhraseNotFound", []))
    output_messages = set(warnings.get("OutputMessage", []))

    no_records = (
        count == 0
        and not result.get("IdList")
        and not errors.get("FieldNotFound")
        and missing_phrases.issubset({term})
        and not warnings.get("QuotedPhraseNotFound")
        and not warnings.get("PhraseIgnored")
        and output_messages.issubset({"No items found."})
        and not unexpected_errors
        and not unexpected_warnings
    )

    if no_records:
        return 0

    raise RuntimeError(f"Respuesta inesperada de NCBI: {result}")

def count_biosamples(taxid):
    """Reintentar la consulta completa, incluida la lectura de la respuesta."""
    for attempt in range(MAX_RETRIES):
        try:
            with Entrez.esearch(
                db="biosample",
                term=f"txid{taxid}[Organism:exp]",
                retmax=0,
            ) as handle:
                result = Entrez.read(handle)

            return interpret_result(result, taxid)

        except Exception as error:
            if attempt == MAX_RETRIES - 1:
                raise

            wait = 2 ** attempt
            print(
                f"  Reintento para TaxID {taxid} "
                f"en {wait} segundos: {error}",
                flush=True,
            )
            time.sleep(wait)

        finally:
            time.sleep(REQUEST_DELAY)

# -------------------[ main ]---------------------------------#

def main():
    if not INPUT.is_file():
        raise SystemExit(f"ERROR: no existe {INPUT}")

    with INPUT.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        input_fields = reader.fieldnames

        required = {"ncbi_species_taxid", "ncbi_species_name"}
        if not required.issubset(set(input_fields or [])):
            raise SystemExit("ERROR: cabecera inesperada en el inventario")

        species = list(reader)

    fields = input_fields + [
        "number_of_biosamples",
        "status",
        "message",
        "queried_at_utc",
    ]

    # Leer el último estado guardado para cada TaxID.
    previous = {}

    if OUTPUT.exists() and OUTPUT.stat().st_size > 0:
        with OUTPUT.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")

            if reader.fieldnames != fields:
                raise SystemExit(
                    "ERROR: cabecera inesperada en la salida existente"
                )

            for row in reader:
                taxid = row.get("ncbi_species_taxid")
                status = row.get("status")
                count = row.get("number_of_biosamples", "")

                if (
                    status == "complete"
                    and count is not None
                    and count.isdigit()
                ):
                    previous[taxid] = "complete"
                else:
                    previous[taxid] = "error"

    needs_header = not OUTPUT.exists() or OUTPUT.stat().st_size == 0
    completed = 0
    skipped = 0
    failed = 0

    print(f"Especies en el inventario: {len(species)}", flush=True)

    with OUTPUT.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            delimiter="\t",
            lineterminator="\n",
        )

        if needs_header:
            writer.writeheader()
            handle.flush()

        for index, record in enumerate(species, start=1):
            taxid = record["ncbi_species_taxid"]
            name = record["ncbi_species_name"]

            # Conservar los resultados correctos de ejecuciones previas.
            if previous.get(taxid) == "complete":
                skipped += 1
                continue

            row = dict(record)

            try:
                count = count_biosamples(taxid)

                row.update({
                    "number_of_biosamples": count,
                    "status": "complete",
                    "message": "",
                })
                completed += 1

                print(
                    f"[{index}/{len(species)}] "
                    f"{name}: {count} BioSamples",
                    flush=True,
                )

            except Exception as error:
                row.update({
                    "number_of_biosamples": "",
                    "status": "error",
                    "message": str(error),
                })
                failed += 1

                print(
                    f"[{index}/{len(species)}] "
                    f"ERROR {name}: {error}",
                    flush=True,
                )

            row["queried_at_utc"] = datetime.now(
                timezone.utc
            ).isoformat()

            writer.writerow(row)
            handle.flush()

    print("\nRECUENTO TERMINADO", flush=True)
    print("Completadas en esta ejecución:", completed, flush=True)
    print("Ya completadas anteriormente:", skipped, flush=True)
    print("Errores en esta ejecución:", failed, flush=True)
    print("Salida:", OUTPUT, flush=True)

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
