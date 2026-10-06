#!/usr/bin/env python3

""""
Descarga los metadatos para cada una de las especies del NCBI para los géneros dados

input: 
    contaminacion/ncbi_species_per_silva_genus_resolved.tsv
output: 
    contaminacion/ncbi_species_by_genus/genus_<taxid>.tsv
"""

from Bio import Entrez
import csv
import time
from pathlib import Path

# -------------------[ configuracion ]---------------------------------#

Entrez.email = "" # email de contacto para NCBI Entrez
Entrez.tool = "silva_genus_species_inventory"

INPUT = Path("contaminacion/ncbi_species_per_silva_genus_resolved.tsv")
OUTDIR = Path("contaminacion/ncbi_species_by_genus")
OUTDIR.mkdir(exist_ok=True)

FIELDS = [
    "silva_genus",
    "ncbi_genus_name",
    "ncbi_genus_taxid",
    "ncbi_species_name",
    "ncbi_species_taxid",
    "ncbi_rank",
]

# -------------------[ funciones ]---------------------------------#

def request(function, **kwargs):
    """Realiza una consulta a Entrez con reintentos y control de errores."""
    for attempt in range(5):
        try:
            with function(**kwargs) as handle:
                result = Entrez.read(handle)

            if isinstance(result, dict):
                if result.get("ErrorList") or result.get("WarningList"):
                    raise RuntimeError(str(result))

            return result

        except Exception as error:
            if attempt == 4:
                raise

            print(f"Reintentando: {error}", flush=True)
            time.sleep(2 ** attempt)

        finally:
            time.sleep(0.4)

# -------------------[ main ]---------------------------------#

# Lee la tabla de géneros y filtra los que están completos
with INPUT.open(encoding="utf-8-sig", newline="") as handle:
    genera = [
        row
        for row in csv.DictReader(handle, delimiter="\t")
        if row["status"] == "complete"
    ]

# Descarga los metadatos para cada uno de los géneros seleccionados
failed = []

for index, genus in enumerate(genera, 1):
    name = genus["silva_genus"]
    taxid = genus["ncbi_genus_taxid"]

    output = OUTDIR / f"genus_{taxid}.tsv"
    temporary = OUTDIR / f"genus_{taxid}.tsv.part"

    if output.exists():
        print(
            f"[{index}/{len(genera)}] {name}: ya descargado",
            flush=True,
        )
        continue

    print(
        f"[{index}/{len(genera)}] Consultando {name}",
        flush=True,
    )

    try:
        term = f"txid{taxid}[Subtree] AND species[Rank]"

        search = request(
            Entrez.esearch,
            db="taxonomy",
            term=term,
            retmax=0,
        )

        expected = int(search["Count"])
        seen = set()

        with temporary.open(
            "w", encoding="utf-8", newline=""
        ) as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=FIELDS,
                delimiter="\t",
                lineterminator="\n",
            )
            writer.writeheader()

            for start in range(0, expected, 500):
                batch_size = min(500, expected - start)

                page = request(
                    Entrez.esearch,
                    db="taxonomy",
                    term=term,
                    retstart=start,
                    retmax=batch_size,
                )

                if int(page["Count"]) != expected:
                    raise RuntimeError(
                        "El recuento cambió durante la consulta"
                    )

                ids = page["IdList"]

                if len(ids) != batch_size:
                    raise RuntimeError(
                        "Página de TaxID incompleta"
                    )

                records = request(
                    Entrez.efetch,
                    db="taxonomy",
                    id=",".join(ids),
                    retmode="xml",
                )

                recovered_ids = {
                    str(record["TaxId"])
                    for record in records
                }

                if recovered_ids != set(ids):
                    raise RuntimeError(
                        "Los TaxID recuperados no coinciden"
                    )

                for record in records:
                    species_taxid = str(record["TaxId"])

                    ancestors = {
                        str(item["TaxId"])
                        for item in record.get("LineageEx", [])
                    }

                    if (
                        record["Rank"] != "species"
                        or taxid not in ancestors
                    ):
                        raise RuntimeError(
                            "Rango o linaje inesperado: "
                            f"{species_taxid}"
                        )

                    if species_taxid in seen:
                        raise RuntimeError(
                            f"TaxID duplicado: {species_taxid}"
                        )

                    seen.add(species_taxid)

                    writer.writerow({
                        "silva_genus": name,
                        "ncbi_genus_name": genus["ncbi_genus_name"],
                        "ncbi_genus_taxid": taxid,
                        "ncbi_species_name": record["ScientificName"],
                        "ncbi_species_taxid": species_taxid,
                        "ncbi_rank": record["Rank"],
                    })

                print(
                    f"  {name}: {len(seen)}/{expected} especies",
                    flush=True,
                )

        if len(seen) != expected:
            raise RuntimeError(
                f"Esperadas {expected}; recuperadas {len(seen)}"
            )

        temporary.replace(output)

        print(
            f"  Completado: {len(seen)} especies",
            flush=True,
        )

    except Exception as error:
        failed.append(name)
        print(f"  ERROR en {name}: {error}", flush=True)

print("\nInventario terminado.", flush=True)
print("Carpeta:", OUTDIR, flush=True)
print("Géneros con error:", len(failed), flush=True)

for name in failed:
    print("  ", name, flush=True)

if failed:
    raise SystemExit(1)
