# TMEM158 public protein and localization context

## Purpose

This module adds official public protein/context evidence for TMEM158 after the TAC_high state analysis. It is intended to support biological plausibility and assayability, not to create new ESCC protein validation.

## Data used

- UniProt REST query: `gene_exact:TMEM158 AND organism_id:9606`.
- QuickGO cellular-component annotations for the retrieved UniProt accession.
- Human Protein Atlas TMEM158 search and individual ENSG entry.

## Main findings

- UniProt reviewed accession: Q8WZ71 (Transmembrane protein 158).
- UniProt subcellular location/topology: Membrane; Multi-pass membrane protein.
- UniProt/QuickGO cellular-component terms: UniProt GO:0016020 membrane [IEA:UniProtKB-SubCell]; QuickGO GO:0016020  [IEA]
- HPA protein class: Predicted membrane proteins.
- HPA public antibody/IHC context: HPA074974.
- HPA protein tissue distribution: Not detected.
- HPA subcellular IF main location: not available.

## HPA single-cell RNA context

- Platelets: 227.9 nCPM
- Müller glia: 94 nCPM
- Other brain neurons: 59.1 nCPM
- Ependymal cells: 57.8 nCPM
- Endometrial stromal cells: 47.3 nCPM
- Brain inhibitory neurons: 45.6 nCPM
- Breast myoepithelial cells: 43.9 nCPM
- Fibroblasts: 34.2 nCPM

## Interpretation boundary

This layer supports TMEM158 as a public, reviewed transmembrane-protein candidate with HPA antibody/IHC context. It does not show ESCC-specific TMEM158 protein overexpression, direct ER localization, Ca2+ flux, UPR activation, CAF causality, immune suppression or treatment resistance. In the manuscript, it should be placed as a database-level protein plausibility and limitation layer.

## Output files

- `04_results/validation/tmem158_public_protein_knowledgebase_summary.csv`
- `04_results/validation/tmem158_uniprot_quickgo_localization.csv`
- `04_results/validation/tmem158_hpa_context_summary.csv`
- `04_results/validation/tmem158_public_protein_evidence_cards.csv`
- `04_results/qc/tmem158_public_protein_context_status.csv`
- `05_figures/figure11_tmem158_public_protein_context.png/.pdf/.svg`
