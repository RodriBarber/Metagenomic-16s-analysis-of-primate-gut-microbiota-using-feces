# 16S Metagenomic Analysis of Primate Gut Microbiota

Reanalysis of 16S rRNA amplicon data (V4 region, single-end) from
[Amato et al. 2019, *ISME J*](https://doi.org/10.1038/s41396-018-0175-0),
with two objectives: to characterize the taxonomic composition of the
fecal microbiota of 15 primate species and to assess the presence of
environmental contamination.

## Data

154 samples from the ENA project [ERP104379](https://www.ebi.ac.uk/ena/browser/view/ERP104379).
Not included in the repository: download them using `python/download_16S_data.sh`.
The analysis uses the 134 samples with available dietary data (15 species).

## Requirements

- QIIME 2 (`rachis-qiime2-2026.7` environment)
- Python 3 with pandas, matplotlib, seaborn, scipy, biopython

## Usage

The complete pipeline is documented in `metag_16s_v2.md`, which must
be run in order.

## Structure

| Folder | Contents |
|---|---|
| `python/` | Analysis scripts and figures |
| `metadata/` | Table of samples, species, and diet indices |
| `tsv/` | Intermediate and results tables |
| `plots/` | Figures |
| `contaminacion/` | Classification of genus origin via NCBI BioSample |
| `exported-tree/tree_v2` | Phylogenetic tree |


## Methodological Decisions

- Prevalence filter: ≥2 samples
- Abundance filter: 0.01% of total reads.
- Filtering out mitochondria and chloroplasts
- Taxonomic classifier: SILVA 144 V4-515f-806r.
- Identification of contaminating genera based on the mean and standard deviation of the percentage of species assigned to each biosample by genus
