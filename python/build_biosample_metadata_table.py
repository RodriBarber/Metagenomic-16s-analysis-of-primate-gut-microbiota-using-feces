#!/usr/bin/env python3

""""
Construye una tabla con los metadatos de todos los BioSamples de todas las especies.

input:
    ncbi_species_inventory_all_genera.tsv
    ncbi_biosample_counts_per_species.tsv
    biosample_metadata_by_species/
output:
    ncbi_biosample_metadata_all_species.tsv.gz
"""

import csv
import gzip
import json
import xml.etree.ElementTree as ET
from pathlib import Path

# -------------------[ configuracion ]---------------------------------#

INVENTORY = Path("contaminacion/ncbi_species_inventory_all_genera.tsv")
COUNTS = Path("contaminacion/ncbi_biosample_counts_per_species.tsv")
DOWNLOADS = Path("contaminacion/biosample_metadata_by_species")

OUTPUT = Path("contaminacion/ncbi_biosample_metadata_all_species.tsv.gz")
TEMPORARY = OUTPUT.with_name(OUTPUT.name + ".part")

FIELDS = [
    "biosample_accession",
    "biosample_id",
    "silva_genus",
    "ncbi_genus_name",
    "ncbi_genus_taxid",
    "ncbi_species_name",
    "ncbi_species_taxid",
    "organism",
    "organism_taxid",
    "isolation_source",
]

# -------------------[ funciones ]---------------------------------#

def read_tsv(path, required):
    """Lee un TSV y comprueba que tiene las columnas requeridas."""
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")

        missing = required - set(reader.fieldnames or [])
        if missing:
            raise RuntimeError(
                f"Faltan columnas en {path}: {sorted(missing)}"
            )

        rows = list(reader)

    for row in rows:
        if None in row or any(value is None for value in row.values()):
            raise RuntimeError(f"Fila incompleta en {path}")

    return rows

def extract_isolation_source(sample):
    """
    Conserva los valores originales.
    Un solo atributo: texto original.
    Varios atributos: lista JSON con todos los valores originales.
    Sin atributo: celda vacía.
    """
    values = []

    for attribute in sample.findall("./Attributes/Attribute"):
        names = [
            attribute.get("harmonized_name", ""),
            attribute.get("attribute_name", ""),
            attribute.get("display_name", ""),
        ]

        normalized_names = {
            name.strip().casefold().replace(" ", "_")
            for name in names
        }

        if "isolation_source" in normalized_names:
            values.append("".join(attribute.itertext()))

    if not values:
        return ""

    if len(values) == 1:
        return values[0]

    return json.dumps(values, ensure_ascii=False)

# -------------------[ main ]---------------------------------#

# Compara el inventario de especies con los recuentos de BioSamples 
def main():
    if OUTPUT.exists():
        raise SystemExit(
            f"Ya existe {OUTPUT}. No se sobrescribe."
        )

    inventory_rows = read_tsv(
        INVENTORY,
        {
            "silva_genus",
            "ncbi_genus_name",
            "ncbi_genus_taxid",
            "ncbi_species_name",
            "ncbi_species_taxid",
        },
    )

    # Construye un diccionario de inventario para acceder a los metadatos de cada especie por su TaxID.
    inventory = {}

    for row in inventory_rows:
        taxid = row["ncbi_species_taxid"]

        if not taxid or taxid in inventory:
            raise RuntimeError(
                f"TaxID vacío o duplicado en el inventario: {taxid!r}"
            )

        inventory[taxid] = row

    count_rows = read_tsv(
        COUNTS,
        {"ncbi_species_taxid", "number_of_biosamples", "status"},
    )

    expected = []
    count_ids = set()

    for row in count_rows:
        taxid = row["ncbi_species_taxid"]

        if taxid in count_ids:
            raise RuntimeError(f"TaxID duplicado en recuentos: {taxid}")

        count_ids.add(taxid)

        if row["status"] != "complete":
            raise RuntimeError(f"Recuento sin completar: {taxid}")

        count = int(row["number_of_biosamples"])
        if count < 0:
            raise RuntimeError(f"Recuento negativo: {taxid}")

        if count > 0:
            expected.append(taxid)

    if count_ids != set(inventory):
        raise RuntimeError(
            "Los TaxID del inventario y de los recuentos no coinciden."
        )

    # Comprobar que todas las descargas esperadas están completadas.
    for taxid in expected:
        folder = DOWNLOADS / f"taxid_{taxid}"

        for filename in ("manifest.json", "complete.json"):
            if not (folder / filename).is_file():
                raise RuntimeError(
                    f"Falta {filename} para el TaxID {taxid}"
                )

    total = 0
    missing_sources = 0
    seen_accessions = set()
    seen_ids = set()

    with gzip.open(
        TEMPORARY, "wt", encoding="utf-8", newline=""
    ) as out:
        writer = csv.DictWriter(
            out,
            fieldnames=FIELDS,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()

        for index, taxid in enumerate(expected, start=1):
            folder = DOWNLOADS / f"taxid_{taxid}"
            taxonomy = inventory[taxid]

            manifest = json.loads(
                (folder / "manifest.json").read_text(encoding="utf-8")
            )
            complete = json.loads(
                (folder / "complete.json").read_text(encoding="utf-8")
            )

            ids = [str(value) for value in manifest["biosample_ids"]]
            batch_size = int(manifest["batch_size"])

            if (
                manifest["species"]["ncbi_species_taxid"] != taxid
                or len(ids) != int(manifest["count"])
                or len(ids) != len(set(ids))
                or batch_size <= 0
                or not ids
            ):
                raise RuntimeError(f"Manifiesto incoherente: {taxid}")

            if (
                str(complete["ncbi_species_taxid"]) != taxid
                or int(complete["downloaded_biosamples"]) != len(ids)
            ):
                raise RuntimeError(
                    f"Registro de finalización incoherente: {taxid}"
                )

            for start in range(0, len(ids), batch_size):
                file = folder / f"batch_{start:09d}.xml.gz"
                expected_ids = ids[start:start + batch_size]

                with gzip.open(file, "rb") as handle:
                    root = ET.parse(handle).getroot()

                samples = list(root.iter("BioSample"))
                actual_ids = [s.get("id", "") for s in samples]

                if (
                    len(actual_ids) != len(expected_ids)
                    or set(actual_ids) != set(expected_ids)
                ):
                    raise RuntimeError(
                        f"Lote incompleto o incorrecto: {file}"
                    )

                for sample in samples:
                    accession = sample.get("accession", "")
                    sample_id = sample.get("id", "")

                    if not accession or not sample_id:
                        raise RuntimeError(
                            f"BioSample sin identificador: {file}"
                        )

                    if (
                        accession in seen_accessions
                        or sample_id in seen_ids
                    ):
                        raise RuntimeError(
                            f"BioSample repetido: {accession}. "
                            "Revisar sus asociaciones antes de deduplicar."
                        )

                    seen_accessions.add(accession)
                    seen_ids.add(sample_id)

                    organism = sample.find("./Description/Organism")
                    source = extract_isolation_source(sample)

                    row = {
                        field: taxonomy[field]
                        for field in (
                            "silva_genus",
                            "ncbi_genus_name",
                            "ncbi_genus_taxid",
                            "ncbi_species_name",
                            "ncbi_species_taxid",
                        )
                    }

                    row.update({
                        "biosample_accession": accession,
                        "biosample_id": sample_id,
                        "organism": (
                            organism.get("taxonomy_name", "")
                            if organism is not None else ""
                        ),
                        "organism_taxid": (
                            organism.get("taxonomy_id", "")
                            if organism is not None else ""
                        ),
                        "isolation_source": source,
                    })

                    writer.writerow(row)
                    total += 1

                    if source == "":
                        missing_sources += 1

            if index % 100 == 0 or index == len(expected):
                print(
                    f"Taxones: {index}/{len(expected)}; "
                    f"BioSamples: {total:,}",
                    flush=True,
                )

    # Solo crea la tabla final si todas las comprobaciones pasan.
    TEMPORARY.replace(OUTPUT)

    print("\nTABLA COMPLETADA", flush=True)
    print(f"Taxones procesados: {len(expected):,}", flush=True)
    print(f"BioSamples únicos: {total:,}", flush=True)
    print(
        f"BioSamples sin isolation_source o con valor vacío: "
        f"{missing_sources:,}",
        flush=True,
    )
    print(f"Salida: {OUTPUT}", flush=True)


if __name__ == "__main__":
    main()
