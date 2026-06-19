# Repository Release README

## Project

TMEM158-associated TAC_high Ca2/UPR-CAF stress ecology in oesophageal squamous cell carcinoma.

## Scope

This repository package supports a pure public-data, hypothesis-generating bioinformatics manuscript. It contains reproducible scripts, processed result tables, figure files, manuscript drafts, source-data indexes and submission-readiness QC outputs.

## Primary Reproducibility Command

```sh
Rscript TMEM158_CaUPR_ESCC/03_scripts/R/run_all.R
```

The script rebuilds the TMEM158/TAC_high result layers and refreshes the manuscript-facing figure/readiness archive. Some public raw downloads may need to be present locally or re-downloaded from the public sources documented in the data inventories and scripts.

## Key Files

- `07_manuscript/manuscript_scientific_reports.md`: Scientific Reports-targeted source manuscript.
- `07_manuscript/manuscript_scientific_reports.docx`: editable manuscript generated from Markdown.
- `07_manuscript/supplementary_information_scientific_reports.md`: supplementary information draft.
- `05_figures/main_figure1_tmem158_axis_discovery.*` to `main_figure6_independent_context_and_boundaries.*`: six submission-facing figures.
- `08_submission_strategy/source_data_and_supplementary_inventory.csv`: source-data map for figures and supplementary tables.
- `08_submission_strategy/repository_deposit_manifest.csv`: repository inclusion manifest.
- `08_submission_strategy/repository_file_checksums.sha256`: checksums for included files.
- `08_submission_strategy/TMEM158_TAC_high_repository_release.zip`: standalone repository-release archive for deposition.
- `08_submission_strategy/repository_release_package_manifest.csv`: copied-file manifest for the standalone release package.
- `08_submission_strategy/repository_release_package_qc.csv`: QC summary for the standalone release package.
- `08_submission_strategy/tmem158_structural_followup_prioritization.md`: bounded structural/assay follow-up ranking for TAC_high bridge candidates.
- `08_submission_strategy/tmem158_lr_compartment_expression_audit.md`: bounded compartment-expression feasibility audit for top TAC_high bridge candidates.

## Data Availability Draft

All datasets are public. This package redistributes processed result tables, code and manuscript-facing outputs rather than restricted or publisher-controlled raw full-text files. The code and processed outputs are deposited in the public GitHub repository at https://github.com/afa-cloud/TMEM158_CaUPR_ESCC, with an initial-submission release at https://github.com/afa-cloud/TMEM158_CaUPR_ESCC/releases/tag/v1.0-initial-submission. A DOI-minted release can be added later through Zenodo or another archival repository if required.

Raw public downloads, publisher/full-text gate files, local logs and local Scientific Reports upload dry-run bundles are deliberately excluded from the repository-release archive. These sources can be reobtained from the public repositories and literature sources documented in the scripts, inventories and manuscript.

## Code Availability Draft

The analysis code is under `03_scripts/`. The current full controller is `03_scripts/R/run_all.R`. Public repository URL: https://github.com/afa-cloud/TMEM158_CaUPR_ESCC. Initial-submission release: https://github.com/afa-cloud/TMEM158_CaUPR_ESCC/releases/tag/v1.0-initial-submission.

## Claim Boundary

The analysis identifies a TMEM158-associated TAC_high Ca2/UPR-CAF stress-ecology state. It does not demonstrate TMEM158 causality, clinical prognosis, direct immune suppression, spatial activation, ligand-receptor causality, physical interaction, receptor activation, protein-level communication or treatment recommendation.

Generated: 2026-06-20 01:51:33
