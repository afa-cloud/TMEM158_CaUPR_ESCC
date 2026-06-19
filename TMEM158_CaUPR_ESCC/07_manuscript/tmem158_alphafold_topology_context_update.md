# TMEM158 AlphaFold topology context

## Purpose

This module adds predicted structural/topology context for TMEM158 using the official AlphaFold Protein Structure Database and UniProt feature annotation. It is a protein-background layer, not physical-interaction evidence.

## Main findings

- AlphaFold entry: AF-Q8WZ71-F1 (AlphaFold Monomer v2.0 pipeline).
- Canonical model coverage: 1-300.
- Global pLDDT: 56.66; low/very-low pLDDT fraction: 0.684.
- UniProt transmembrane segments: 2.
- UniProt_Transmembrane_1: 231-251 (Helical), mean pLDDT 76.13, mean hydropathy 1.835, call=confident.
- UniProt_Transmembrane_2: 273-293 (Helical), mean pLDDT 43.96, mean hydropathy 1.255, call=very_low.

## Interpretation

AlphaFold/UniProt support a membrane-topology rationale for TMEM158, especially the first C-terminal transmembrane segment. The second UniProt transmembrane segment has lower AlphaFold confidence and should be treated as an annotated but structurally lower-confidence segment. This layer can strengthen the biological plausibility that TMEM158 is a membrane protein suitable for Ca2/UPR-axis follow-up, but it does not prove ER localization, binding to Ca2/UPR proteins, interaction with ECM components, or ESCC-specific protein expression. Its practical role is to prioritize localization, membrane-fraction, proximity-labelling, co-immunoprecipitation or future defined-partner co-modelling experiments.

## Output files

- `04_results/structure/tmem158_alphafold_model_summary.csv`
- `04_results/structure/tmem158_alphafold_topology_segments.csv`
- `04_results/structure/tmem158_alphafold_residue_confidence.csv`
- `04_results/qc/tmem158_alphafold_topology_context_status.csv`
- `05_figures/figure25_tmem158_alphafold_topology_context.png/.pdf/.svg`
