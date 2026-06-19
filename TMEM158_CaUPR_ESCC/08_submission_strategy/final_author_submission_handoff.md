# Final Author Submission Handoff

Generated: 2026-06-20 01:46:34

## Status

- Machine-side final clearance: `pass`
- Final upload clearance: `not_yet`
- Local Scientific Reports bundle: `pass`
- Repository release package: `pass`

Interpretation: the machine-prepared manuscript package is ready for journal-system upload. The manuscript is not yet final-submission complete because the publisher-generated upload preview and a final claim-boundary read must still be completed by the human author. Public GitHub repository deposition is complete at https://github.com/afa-cloud/TMEM158_CaUPR_ESCC.

## Copy-Ready Submission Fields

### article_type

Status: `ready`

Article

Source: `target journal strategy`

### title

Status: `ready`

A TMEM158-associated Ca2/UPR-CAF stress ecology state defines proteostasis-linked adaptation in esophageal squamous cell carcinoma

Source: `07_manuscript/manuscript_scientific_reports.md`

### running_title

Status: `ready`

TMEM158-associated TAC_high stress ecology in ESCC

Source: `derived from title`

### abstract

Status: `ready`

Calcium homeostasis, unfolded protein response (UPR) branch activity and stromal remodelling are incompletely integrated in esophageal squamous cell carcinoma (ESCC). We performed an axis-first public-data analysis to identify upstream candidates associated with Ca2/UPR stress ecology. TMEM158 emerged as a lead computational entry point, but not as a standalone prognostic biomarker. We defined TAC_high as the co-occurrence of high TMEM158-Ca2/PERK core score and high cancer-associated fibroblast (CAF) score. TAC_high was reproducible across four bulk ESCC cohorts and associated with proteostasis and survival-transcriptional readouts, while overall-survival analyses remained negative. Whole-transcriptome meta-analysis showed a dominant extracellular-matrix/CAF programme and CAF-adjusted residual MYC, oxidative phosphorylation, KEAP1/NFE2L2, chemical-stress and translation signatures. GSE53625 externally calibrated the expression state in 179 paired samples without validating prognosis. Independent single-cell analyses localized TAC_high meta-signatures to fibroblast/CAF pseudo-bulk profiles and nominated expression-feasible POSTN/FN1/collagen-integrin and MIF-CXCR4 candidate CAF-to-epithelial bridges. Public spatial source data supported a fibroblast-rich progression context. These results define a TMEM158-associated Ca2/UPR-CAF stress ecology state in ESCC as a public-data biological discovery candidate, while preserving an explicit boundary between association and causality.

Source: `07_manuscript/manuscript_scientific_reports.md`

### keywords

Status: `ready`

Esophageal squamous cell carcinoma; TMEM158; calcium homeostasis; unfolded protein response; cancer-associated fibroblasts; public-data bioinformatics

Source: `07_manuscript/manuscript_scientific_reports.md`

### editor_significance_statement

Status: `ready_optional`

This public-data study defines a reproducible TMEM158-associated TAC_high Ca2/UPR-CAF stress-ecology state in ESCC, with CAF/fibroblast localization, CAF-adjusted residual stress transcription and explicit negative boundaries for prognosis, causality, immune suppression and treatment resistance.

Source: `derived from manuscript and reviewer-risk pack`

### plain_language_summary

Status: `ready_optional`

The study uses existing public cancer datasets to describe a stress-related tumour ecology pattern in esophageal squamous cell carcinoma. The findings suggest a testable biology state linked to fibroblast-rich tumour context, but they do not prove a treatment target or clinical biomarker.

Source: `derived from manuscript abstract and limitations`

### cover_letter_core_pitch

Status: `ready_author_confirmed`

This manuscript reports a reproducible public-data computational biology study of esophageal squamous cell carcinoma (ESCC). Starting from an axis-first Ca2/UPR regulator screen, we identify TMEM158 as a lead computational entry point and define a rule-based TAC_high state combining TMEM158-Ca2/PERK-core activity with a cancer-associated fibroblast score. Across public bulk cohorts, TAC_high is reproducible and is linked to proteostasis and stress-state transcriptional readouts. Whole-transcriptome and CAF-adjusted analyses distinguish a dominant ECM/CAF programme from residual MYC, oxidative phosphorylation, KEAP1/NFE2L2, chemical-stress and translation signatures. Independent single-cell pseudo-bulk analyses localize TAC_high meta-signatures to fibroblast/CAF profiles and nominate expression-feasible ECM-integrin and MIF-CXCR4 candidate bridges, while GSE53625 provides external expression-state calibration in 179 paired clinical samples.

Source: `08_submission_strategy/scientific_reports_cover_letter_draft.md`

### data_availability

Status: `ready_public_repository`

All data analysed in this study were obtained from public resources, including TCGA/GDC or cBioPortal, GEO, DepMap-derived public resources, UniProt, QuickGO, the Human Protein Atlas and the AlphaFold Protein Structure Database [1,9,17,18,22-25]. No new patient-level dataset was generated in this study. Processed intermediate tables and analysis outputs are available in the public GitHub repository at https://github.com/afa-cloud/TMEM158_CaUPR_ESCC.

Source: `07_manuscript/manuscript_scientific_reports.md`

### code_availability

Status: `ready_public_repository`

The reproducible workflow was implemented in TMEM158_CaUPR_ESCC/03_scripts/R/run_all.R, with helper scripts under TMEM158_CaUPR_ESCC/03_scripts/R/ and TMEM158_CaUPR_ESCC/03_scripts/Python/. The code is publicly available in the GitHub repository at https://github.com/afa-cloud/TMEM158_CaUPR_ESCC.

Source: `07_manuscript/manuscript_scientific_reports.md`

### ethics_statement

Status: `ready`

All datasets used in this study were public and de-identified. No new human specimens, animal experiments or wet-lab experiments were performed, and no new ethics approval or informed consent was required for this secondary analysis.

Source: `07_manuscript/manuscript_scientific_reports.md`

### public_data_boundary

Status: `ready`

This study used only publicly available datasets and did not involve newly collected human specimens, animal experiments or wet-lab experiments.

Source: `Methods / ethics statement`

### claims_not_made

Status: `ready`

The manuscript does not claim that TMEM158 is a validated causal driver, a clinical prognostic biomarker, a cisplatin-resistance mechanism, a direct immune-suppression mechanism, a directly spatially validated programme or an experimentally validated ESCC protein/ER-localization finding.

Source: `claim-boundary audit and reviewer-risk pack`

### limitations_summary

Status: `ready`

This study used retrospective public datasets and is subject to database heterogeneity, batch effects, platform differences and incomplete clinical annotation. Some GEO cohorts are small, and TCGA-ESCA contains histological-mixing risk even when used as ESCC-compatible context. Survival analyses were underpowered for some state contrasts and did not support a clinical OS claim. GSE53625 provides a larger paired clinical cohort, but it required targeted probe-sequence reannotation and did not support OS prognostic claims; it should therefore be treated as external calibration, not clinical validation. CAF-adjusted transcriptome models reduce but cannot eliminate stromal-composition confounding, because expression matrices do not directly identify the cellular origin of each residual gene programme. Single-cell analyses used pseudo-bulk and compartment-level signature summaries and therefore cannot prove cell-cell causality, cellular origin of ligand-receptor signalling or tumour-cell-autonomous regulation. The compartment-expression audit confirms ligand and receptor detectability for prioritized candidates, ...

Source: `07_manuscript/manuscript_scientific_reports.md`

## Upload File Map

| Step | Upload item | Path | Required | Status | Notes |
|---|---|---|---|---|---|
| 1 | Main manuscript DOCX | `07_manuscript/manuscript_scientific_reports.docx` | yes | pass | Editable Scientific Reports manuscript. Local render QA passed, but publisher preview remains human-gated. |
| 2 | Cover letter | `08_submission_strategy/scientific_reports_cover_letter_draft.md` | yes | pass | Add corresponding-author header, signature and any required editor salutation before upload. |
| 3 | Supplementary Information | `07_manuscript/supplementary_information_scientific_reports.md` | yes | pass | Markdown supplementary draft; convert to DOCX/PDF only if journal system requests a specific format. |
| 4 | Repository release ZIP | `08_submission_strategy/TMEM158_TAC_high_repository_release.zip` | optional | pass | Author currently chose not to deposit code before initial submission. Keep this clean repository package for later Zenodo/OSF/GitHub deposition if requested. |
| 5 | Local submission dry-run ZIP | `08_submission_strategy/TMEM158_TAC_high_ScientificReports_submission_bundle.zip` | no | pass | Use for local organization only unless a coauthor asks for one archive. Not the public repository deposit package. |
| 6 | Reporting Summary working draft | `08_submission_strategy/nature_portfolio_reporting_summary_working_draft.md` | if_requested | pass | Use as a working draft if the submission workflow requests a formal Nature Portfolio Reporting Summary form. |
| F1.png | Main Figure 1 PNG | `05_figures/main_figure1_tmem158_axis_discovery.png` | yes | pass | Upload the format requested by the journal; retain all three local formats for QA and conversion. |
| F1.pdf | Main Figure 1 PDF | `05_figures/main_figure1_tmem158_axis_discovery.pdf` | yes | pass | Upload the format requested by the journal; retain all three local formats for QA and conversion. |
| F1.svg | Main Figure 1 SVG | `05_figures/main_figure1_tmem158_axis_discovery.svg` | yes | pass | Upload the format requested by the journal; retain all three local formats for QA and conversion. |
| F2.png | Main Figure 2 PNG | `05_figures/main_figure2_tac_high_bulk_state.png` | yes | pass | Upload the format requested by the journal; retain all three local formats for QA and conversion. |
| F2.pdf | Main Figure 2 PDF | `05_figures/main_figure2_tac_high_bulk_state.pdf` | yes | pass | Upload the format requested by the journal; retain all three local formats for QA and conversion. |
| F2.svg | Main Figure 2 SVG | `05_figures/main_figure2_tac_high_bulk_state.svg` | yes | pass | Upload the format requested by the journal; retain all three local formats for QA and conversion. |
| F3.png | Main Figure 3 PNG | `05_figures/main_figure3_tac_high_transcriptome.png` | yes | pass | Upload the format requested by the journal; retain all three local formats for QA and conversion. |
| F3.pdf | Main Figure 3 PDF | `05_figures/main_figure3_tac_high_transcriptome.pdf` | yes | pass | Upload the format requested by the journal; retain all three local formats for QA and conversion. |
| F3.svg | Main Figure 3 SVG | `05_figures/main_figure3_tac_high_transcriptome.svg` | yes | pass | Upload the format requested by the journal; retain all three local formats for QA and conversion. |
| F4.png | Main Figure 4 PNG | `05_figures/main_figure4_gse53625_clinical_calibration.png` | yes | pass | Upload the format requested by the journal; retain all three local formats for QA and conversion. |
| F4.pdf | Main Figure 4 PDF | `05_figures/main_figure4_gse53625_clinical_calibration.pdf` | yes | pass | Upload the format requested by the journal; retain all three local formats for QA and conversion. |
| F4.svg | Main Figure 4 SVG | `05_figures/main_figure4_gse53625_clinical_calibration.svg` | yes | pass | Upload the format requested by the journal; retain all three local formats for QA and conversion. |
| F5.png | Main Figure 5 PNG | `05_figures/main_figure5_scrna_caf_bridge.png` | yes | pass | Upload the format requested by the journal; retain all three local formats for QA and conversion. |
| F5.pdf | Main Figure 5 PDF | `05_figures/main_figure5_scrna_caf_bridge.pdf` | yes | pass | Upload the format requested by the journal; retain all three local formats for QA and conversion. |
| F5.svg | Main Figure 5 SVG | `05_figures/main_figure5_scrna_caf_bridge.svg` | yes | pass | Upload the format requested by the journal; retain all three local formats for QA and conversion. |
| F6.png | Main Figure 6 PNG | `05_figures/main_figure6_independent_context_and_boundaries.png` | yes | pass | Upload the format requested by the journal; retain all three local formats for QA and conversion. |
| F6.pdf | Main Figure 6 PDF | `05_figures/main_figure6_independent_context_and_boundaries.pdf` | yes | pass | Upload the format requested by the journal; retain all three local formats for QA and conversion. |
| F6.svg | Main Figure 6 SVG | `05_figures/main_figure6_independent_context_and_boundaries.svg` | yes | pass | Upload the format requested by the journal; retain all three local formats for QA and conversion. |

## Human-Gated Actions

| Order | Field | Required | Current status | Action | Recommended handling |
|---|---|---|---|---|---|
| 1 | suggested_reviewers | optional | optional_human_required | OPTIONAL_HUMAN_REQUIRED: add only if the journal requests suggested reviewers. | Optional. Add only if the system requests reviewers and conflicts have been checked. |
| 2 | opposed_reviewers | optional | optional_human_required | OPTIONAL_HUMAN_REQUIRED: add only if necessary and journal allows exclusions. | Optional. Add only if necessary and allowed by the journal. |
| 3 | final_upload_preview | yes | human_required | Inspect final manuscript DOCX/PDF and figure previews in the journal upload system. | After upload, inspect the publisher-generated PDF/HTML previews for manuscript, figures and supplement. |
| 4 | final_claim_boundary_read | yes | human_required | Confirm no causal, prognostic, immune-suppression, spatial-validation or treatment-resistance claim was introduced during metadata editing. | After any metadata edits, re-read title, abstract, cover letter and generated preview for overclaim drift. |

## Recommended Repository Step

The code and processed outputs have been deposited in the public GitHub repository: https://github.com/afa-cloud/TMEM158_CaUPR_ESCC. Keep `08_submission_strategy/TMEM158_TAC_high_repository_release.zip` as the clean archival package for a later Zenodo/OSF DOI-minted release if the editor requests it. Do not deposit `TMEM158_TAC_high_ScientificReports_submission_bundle.zip`; that file is a local journal-upload dry run.

If a DOI is later required, use a DOI-capable repository such as Zenodo, OSF or an institutional repository, then update Data availability and Code availability with the DOI. Until then, the manuscript and submission fields should use the public GitHub URL above.

## Final Claim-Boundary Read

Before clicking submit, confirm that the title, abstract, cover letter, editor comments and upload-system generated PDF do not introduce any of the following claims:

- TMEM158 is a validated causal driver.
- TAC_high is a clinically validated prognostic subtype.
- The study demonstrates direct immune suppression or CD8 exhaustion.
- The study proves cisplatin or treatment resistance.
- The study proves direct spatial activation or ligand-receptor signalling causality.
- TMEM158 is experimentally validated as an ESCC protein or ER-localized mechanism.
- POSTN/FN1/collagen-integrin or MIF-CXCR4 candidates are proven receptor-activation or physical-communication mechanisms.

Safe wording: public-data association, computationally supported stress-ecology state, expression-feasible candidate bridge, follow-up prioritization, hypothesis-generating discovery candidate.

## Machine QC Snapshot

| Item | Value | Status | Notes |
|---|---|---|---|
| generated_at | 2026-06-20 01:46:34 | info | Local system timestamp |
| handoff_markdown | 08_submission_strategy/final_author_submission_handoff.md | pass | Author-facing final submission handoff |
| action_table | 08_submission_strategy/final_author_submission_action_table.csv | pass | Machine-readable upload and human action table |
| upload_rows | 24 | pass | Upload/file rows listed in handoff |
| missing_upload_rows | 0 | pass | Listed upload/source files that are absent |
| required_human_tasks | 2 | not_yet | Human-gated required tasks retained as explicit blockers |
| final_machine_clearance | pass | pass | From final SCI gap audit |
| bundle_clearance | pass | pass | From local Scientific Reports submission bundle QC |
| repository_release_clearance | pass | pass | From repository release package QC |
| claim_boundary_clearance | yes | pass | From public-facing claim-boundary text audit |
| numeric_consistency_clearance | pass | pass | From manuscript numeric consistency audit |
| citation_coverage_clearance | pass | pass | From Scientific Reports citation coverage audit |
| machine_handoff_clearance | pass | pass | Pass means no machine-side handoff artifact is missing |
| final_upload_clearance | not_yet | not_yet | Publisher upload preview and final claim-boundary read remain required; public GitHub repository is listed as https://github.com/afa-cloud/TMEM158_CaUPR_ESCC |

## Boundary

This handoff does not declare the manuscript submitted or accepted. It proves that the machine-prepared pure public-data package, author metadata and declarations are organized for journal-system upload; the remaining hard gates are publisher-system preview and a final claim-boundary read.
