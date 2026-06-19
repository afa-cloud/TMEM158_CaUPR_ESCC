# Reviewer Pre-emptive Response Pack

Generated: 2026-06-20 01:03:53

## Purpose

This document converts the current TMEM158/TAC_high public-data evidence into reviewer-facing response points. It is not a rebuttal to actual reviews and does not add new biological claims.

## Overall Positioning

The manuscript should be defended as a pure public-data, hypothesis-generating discovery of a TMEM158-associated TAC_high Ca2/UPR-CAF stress ecology state in ESCC. It should not be defended as a validated TMEM158 causal mechanism, prognostic model, immune-suppression mechanism, spatially validated programme or drug-resistance paper.

## Machine QC

- Reviewer-risk rows: 16
- High-severity rows: 8
- Rows with missing evidence files: 0

## Fast Editorial Answer

This study is suitable as a public-data biological discovery manuscript because it combines axis-first candidate selection, multi-cohort rule-defined state reproducibility, whole-transcriptome validation, CAF-adjusted stress testing, targeted clinical calibration, independent single-cell localization, candidate CAF-to-epithelial bridge analysis, public spatial source-data context, formal literature gating, claim-boundary auditing and a machine-clear submission bundle. The manuscript also keeps negative survival, immune, drug-resistance, spatial and causality boundaries visible.

## High-Risk Reviewer Questions

### R01_novelty_duplication

**Likely objection:** TMEM158/ESCC or Ca2-UPR-CAF signatures may already be reported.

**Defensible position:** Novelty is framed as an ESCC-specific, rule-defined TAC_high Ca2/UPR-CAF ecology, not generic TMEM158 biomarker biology.

**Short response:** We performed a VM-routed title/abstract, PMC full-text, local full-text and supplementary/context gate; no direct TMEM158-ESCC TAC_high/Ca2/UPR/CAF duplicate remains unresolved.

**Evidence files:** `04_results/qc/tmem158_literature_readiness_status.csv;01_literature/tmem158_fulltext_supplement_review_summary.csv;08_submission_strategy/reviewer_risk_checklist.md`

**Claim to avoid:** No claim that TMEM158 is globally novel in cancer or that no related TMEM158 literature exists.

### R02_public_data_only

**Likely objection:** The study lacks wet-lab validation.

**Defensible position:** The manuscript is submitted as a public-data biological discovery and hypothesis-generating study.

**Short response:** We explicitly state that only public datasets were used and that all findings are associations requiring experimental validation.

**Evidence files:** `07_manuscript/manuscript_scientific_reports.md;08_submission_strategy/claim_boundary_text_audit.md;04_results/qc/claim_boundary_text_audit_summary.csv`

**Claim to avoid:** No wet-lab validation, treatment recommendation, clinical implementation or causal mechanism claim.

### R03_tmem158_causality

**Likely objection:** The analysis does not prove TMEM158 causally drives Ca2/UPR signalling.

**Defensible position:** TMEM158 is a lead computational entry point into a broader state, not a validated driver.

**Short response:** The wording deliberately uses entry point, association and state-marker language, and multi-omics data argue against a simple genomic driver explanation.

**Evidence files:** `04_results/qc/claim_boundary_text_audit_summary.csv;04_results/mutation_cnv_methylation/tmem158_cbioportal_regulatory_correlations.csv;07_manuscript/manuscript_scientific_reports.md`

**Claim to avoid:** Do not write that TMEM158 drives, regulates or causes Ca2/UPR-CAF ecology.

### R04_prognosis_negative

**Likely objection:** Survival analysis is negative, so the paper is not a prognostic biomarker study.

**Defensible position:** The manuscript is a stress-ecology discovery study; OS-negative results are retained as boundaries.

**Short response:** Both TCGA and GSE53625 OS analyses are reported as negative; they calibrate the claim away from prognosis and toward biology-state discovery.

**Evidence files:** `04_results/survival/tmem158_ecology_state_survival.csv;04_results/survival/tmem158_gse53625_survival_cox.csv;04_results/qc/tmem158_submission_readiness_gate.csv`

**Claim to avoid:** No prognostic biomarker, clinical subtype or survival predictor framing.

### R05_caf_composition

**Likely objection:** TAC_high may simply reflect CAF abundance or stromal contamination.

**Defensible position:** The CAF component is part of the ecological state, and CAF-adjusted models separate stromal localization from residual stress transcription.

**Short response:** We added continuous CAF-adjusted score and transcriptome models; they retain residual MYC/OXPHOS/NFE2L2/translation programmes while preventing overclaiming of CAF-independent score effects.

**Evidence files:** `04_results/validation/tmem158_stromal_adjusted_score_meta.csv;04_results/transcriptome/tmem158_stromal_adjusted_meta_differential_genes.csv;04_results/transcriptome/tmem158_stromal_adjusted_geneset_enrichment.csv;05_figures/main_figure3_tac_high_transcriptome.png`

**Claim to avoid:** No tumour-cell-intrinsic proof or CAF-independent proteostasis/efflux proof.

### R08_single_cell_causality

**Likely objection:** Single-cell localization and ligand-receptor scoring do not prove cell-cell signalling.

**Defensible position:** Single-cell data support fibroblast/CAF localization and expression-feasible candidate bridges only.

**Short response:** The text calls POSTN/FN1-integrin and MIF-CXCR4 expression-feasible candidate bridges and explicitly avoids ligand-receptor causality, receptor activation and physical communication claims.

**Evidence files:** `04_results/scrna_signature/tmem158_tac_high_scrna_signature_compartment_tests.csv;04_results/ligand_receptor/tmem158_tac_high_caf_epi_lr_pair_tests.csv;04_results/ligand_receptor/tmem158_tac_high_caf_epi_lr_axis_tests.csv;08_submission_strategy/tmem158_lr_compartment_expression_audit.csv;04_results/qc/tmem158_lr_compartment_expression_audit_qc.csv;05_figures/main_figure5_scrna_caf_bridge.png`

**Claim to avoid:** No CellChat-level proof, spatial adjacency, receptor activation, physical communication or causal signalling claim.

### R10_spatial_context_boundary

**Likely objection:** Public spatial source data do not directly validate TAC_high spatial activation.

**Defensible position:** Spatial source data provide fibroblast-rich tissue-context calibration only.

**Short response:** The public source workbook lacks complete WTA expression; therefore we use DSP fibroblast and alpha-SMA trends only as tissue-context evidence.

**Evidence files:** `04_results/spatial_progression/tmem158_spatial_progression_context_status.csv;04_results/spatial_progression/tmem158_spatial_progression_stage_tests.csv;05_figures/main_figure6_independent_context_and_boundaries.png`

**Claim to avoid:** No direct spatial validation of TMEM158, TAC_high, Ca2/UPR or ligand-receptor proximity.

### R12_drug_resistance_boundary

**Likely objection:** Drug-efflux or proteostasis signals may be overread as cisplatin resistance.

**Defensible position:** Transport/proteostasis signals are transcriptional readouts and hypothesis-generating.

**Short response:** The text restricts drug-efflux to a bounded transcriptional readout and explicitly states that public data do not establish therapy resistance.

**Evidence files:** `04_results/validation/tmem158_tac_high_permutation_summary.csv;04_results/validation/tmem158_gse53625_tac_state_contrasts.csv;08_submission_strategy/claim_boundary_text_audit.md`

**Claim to avoid:** No cisplatin resistance, therapy response or treatment recommendation claim.

## Full Risk Matrix

- **R01_novelty_duplication** (high; ready): We performed a VM-routed title/abstract, PMC full-text, local full-text and supplementary/context gate; no direct TMEM158-ESCC TAC_high/Ca2/UPR/CAF duplicate remains unresolved. Avoid: No claim that TMEM158 is globally novel in cancer or that no related TMEM158 literature exists.

- **R02_public_data_only** (high; ready): We explicitly state that only public datasets were used and that all findings are associations requiring experimental validation. Avoid: No wet-lab validation, treatment recommendation, clinical implementation or causal mechanism claim.

- **R03_tmem158_causality** (high; ready): The wording deliberately uses entry point, association and state-marker language, and multi-omics data argue against a simple genomic driver explanation. Avoid: Do not write that TMEM158 drives, regulates or causes Ca2/UPR-CAF ecology.

- **R04_prognosis_negative** (high; ready): Both TCGA and GSE53625 OS analyses are reported as negative; they calibrate the claim away from prognosis and toward biology-state discovery. Avoid: No prognostic biomarker, clinical subtype or survival predictor framing.

- **R05_caf_composition** (high; ready): We added continuous CAF-adjusted score and transcriptome models; they retain residual MYC/OXPHOS/NFE2L2/translation programmes while preventing overclaiming of CAF-independent score effects. Avoid: No tumour-cell-intrinsic proof or CAF-independent proteostasis/efflux proof.

- **R06_score_defined_state** (medium; ready): The state appears in all four bulk cohorts and random-label permutation supports specificity for the strongest transport/efflux readout. Avoid: No claim that TAC_high is a clinically validated molecular subtype.

- **R07_gse53625_targeted_reannotation** (medium; ready): We recovered 64/67 requested genes and report missing ORAI1/PDPN/TALDO1 coverage; the cohort is used only for clinical calibration. Avoid: No full-transcriptome validation or prognostic validation claim.

- **R08_single_cell_causality** (high; ready): The text calls POSTN/FN1-integrin and MIF-CXCR4 expression-feasible candidate bridges and explicitly avoids ligand-receptor causality, receptor activation and physical communication claims. Avoid: No CellChat-level proof, spatial adjacency, receptor activation, physical communication or causal signalling claim.

- **R09_gse221561_partial_recovery** (medium; ready): We report 7/11 raw library recovery, 124/124 target-gene coverage and six matched tumour libraries as a bounded independent context layer. Avoid: No definitive therapy-response or bridge-causality conclusion from GSE221561.

- **R10_spatial_context_boundary** (high; ready): The public source workbook lacks complete WTA expression; therefore we use DSP fibroblast and alpha-SMA trends only as tissue-context evidence. Avoid: No direct spatial validation of TMEM158, TAC_high, Ca2/UPR or ligand-receptor proximity.

- **R11_immune_suppression_boundary** (medium; ready): GSE160269 immune pseudo-bulk tests are retained as negative boundaries and the manuscript avoids immune-suppression claims. Avoid: No CD8 exhaustion, Treg or suppressive myeloid mechanism claim.

- **R12_drug_resistance_boundary** (high; ready): The text restricts drug-efflux to a bounded transcriptional readout and explicitly states that public data do not establish therapy resistance. Avoid: No cisplatin resistance, therapy response or treatment recommendation claim.

- **R13_batch_and_platform** (medium; ready): The manuscript emphasizes cohort-specific scoring, signed meta-analysis and heterogeneous Ca2-direction boundaries. Avoid: No claim of uniform direction across every platform.

- **R14_data_code_availability** (medium; ready): The project includes run_all.R, source-data inventory, repository manifest/checksums and a machine-clear submission bundle; DOI remains human-gated. Avoid: Do not say final DOI is available before repository deposition.

- **R15_final_upload_preview** (medium; ready): The readiness gate intentionally remains not-yet-final because publisher upload preview and final claim-boundary read require human confirmation; public code deposition is deferred by author decision before initial submission. Avoid: No claim of final journal upload clearance until publisher preview and final claim-boundary read are complete.

- **R16_alphafold_topology_boundary** (medium; ready): We report the predicted model as structural plausibility for follow-up localization and interaction experiments, and explicitly state that it does not demonstrate localization, binding, signalling or ESCC protein validation. Avoid: No ER localization, physical interaction with Ca2/UPR nodes, ECM binding or ESCC protein validation claim.

## Remaining Human-Gated Items

- Author names and affiliations.
- Corresponding author contact information.
- Author contributions.
- Funding, acknowledgements and competing interests.
- Repository DOI or permanent URL.
- Final manuscript and figure preview inside the journal upload system.
