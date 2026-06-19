# Supplementary Information

## Title

TMEM158-associated Ca2/UPR-CAF stress ecology in oesophageal squamous cell carcinoma

## Public-data boundary statement

This study used only publicly available datasets and did not involve newly collected human specimens, animal experiments, or wet-lab experiments. All supplementary results should be interpreted as public-data associations and computational prioritization, not as causal or clinical validation.

## Supplementary Methods

### Public-data provenance and reproducibility

All analysis modules are controlled by `03_scripts/R/run_all.R`. The source-data and repository manifests generated here record the manuscript-facing result tables, figure files, scripts and quality-control outputs needed to reproduce or audit the current Scientific Reports package.

### TMEM158/TAC_high state definition

`TAC_high` was treated as a rule-defined ecology state combining TMEM158, Ca2/PERK branch-state and CAF context. It was used as a transparent public-data state, not as an unsupervised clinical subtype or validated prognostic classifier.

### Transcriptome and stromal-confounding analyses

Whole-transcriptome and CAF-adjusted analyses were used to distinguish the dominant ECM/CAF programme from residual MYC, OXPHOS, KEAP1/NFE2L2, translation and chemical-stress signals. These analyses do not prove tumour-cell-intrinsic causality.

### External clinical and single-cell calibration

GSE53625 targeted probe-sequence reannotation was used as an external clinical calibration layer. GSE160269 and GSE221561 pseudo-bulk single-cell analyses were used to localize TAC_high signatures and evaluate candidate CAF-to-epithelial bridges. These layers do not prove ligand-receptor causality, spatial adjacency or therapy response.

### Spatial source-data context

Public source data from an ESCC spatial progression study were used only for fibroblast/alpha-SMA-rich tissue-context calibration because the full WTA matrix was not available for direct TMEM158/TAC_high rescoring.

### AlphaFold topology context

The AlphaFold Protein Structure Database Q8WZ71 model and UniProt feature annotations were used to summarize predicted TMEM158 topology, per-residue pLDDT confidence, transmembrane-feature positions and sequence hydropathy. This predicted-structure layer supports membrane-topology plausibility only and does not demonstrate ER localization, physical interaction with Ca2/UPR nodes, ECM binding or ESCC-specific protein validation. It is used to prioritize follow-up localization and interaction experiments, not to infer a direct TMEM158-Ca2/UPR or TMEM158-ECM interface.

### Structural follow-up prioritization

The TAC_high CAF-to-epithelial ligand-receptor bridge and the TMEM158 protein-topology boundary audit were integrated to prioritize defined-partner modelling and orthogonal validation targets. This layer ranks candidates such as POSTN/FN1/collagen-integrin and MIF-CXCR4 for follow-up, but it does not prove ligand-receptor causality, receptor activation, TMEM158 binding or physical CAF-to-epithelial communication.

### Ligand-receptor compartment-expression audit

Prioritized ligand-receptor candidates were further checked against GSE160269 pseudo-bulk compartment-expression summaries. This audit asks whether nominated ligands are measurable in fibroblast/CAF profiles and whether nominated receptors are detectable in epithelial profiles. It is used only as an expression-feasibility sanity check and does not prove spatial contact, protein abundance, receptor activation or causal signalling.

### Literature and novelty gate

The literature gate combined VM-routed PubMed/PMC retrieval, local text/full-text scans and curated context adjudication. The current manifest has no unresolved manual items and no direct TMEM158-ESCC Ca2/UPR/CAF duplication signal, but novelty should still be written as ESCC-specific TAC_high ecology rather than generic TMEM158 biomarker discovery.

## Supplementary Figures

**Supplementary Figure S1. Main Figure 1 panel A source.** TMEM158 expression across public ESCC cohorts Source figure: `05_figures/figure1_tmem158_expression_public_cohorts.png`. Source data: `04_results/expression/tmem158_tumor_normal_tests.csv`. Boundary: TMEM158 is a lead computational entry point, not a validated driver or prognostic biomarker.

**Supplementary Figure S2. Main Figure 1 panel B source.** TMEM158 coupling with Ca2/UPR and CAF scores Source figure: `05_figures/figure2_tmem158_axis_correlation_heatmap.png`. Source data: `04_results/enrichment/tmem158_axis_correlations_by_dataset.csv`. Boundary: TMEM158 is a lead computational entry point, not a validated driver or prognostic biomarker.

**Supplementary Figure S3. Main Figure 1 panel C source.** Cross-layer evidence used to nominate TMEM158 Source figure: `05_figures/figure5_tmem158_cross_layer_evidence.png`. Source data: `04_results/validation/tmem158_cross_layer_evidence.csv;06_tables/tmem158_primary_evidence_status.csv`. Boundary: TMEM158 is a lead computational entry point, not a validated driver or prognostic biomarker.

**Supplementary Figure S4. Main Figure 2 panel A source.** Composite ecology-state validation Source figure: `05_figures/figure6_tmem158_ecology_state_validation.png`. Source data: `04_results/validation/tmem158_ecology_state_tests.csv;04_results/validation/tmem158_ecology_state_reproducibility.csv;06_tables/tmem158_ecology_state_key_results.csv`. Boundary: TAC_high is a rule-defined public-data state, not a clinical subtype.

**Supplementary Figure S5. Main Figure 2 panel B source.** Rule-defined TAC_high states across cohorts Source figure: `05_figures/figure7_rule_tmem158_ecology_subtypes.png`. Source data: `04_results/validation/tmem158_rule_ecology_subtype_counts.csv;04_results/validation/tmem158_rule_ecology_subtype_tests.csv;04_results/validation/tmem158_rule_ecology_subtype_reproducibility.csv`. Boundary: TAC_high is a rule-defined public-data state, not a clinical subtype.

**Supplementary Figure S6. Main Figure 2 panel C source.** Cohort-preserving random-label specificity testing Source figure: `05_figures/figure12_tac_high_state_specificity.png`. Source data: `04_results/validation/tmem158_tac_high_permutation_summary.csv;04_results/validation/tmem158_tac_high_component_specificity_meta.csv;04_results/validation/tmem158_tac_high_component_specificity_tests.csv`. Boundary: TAC_high is a rule-defined public-data state, not a clinical subtype.

**Supplementary Figure S7. Main Figure 3 panel A source.** TAC_high whole-transcriptome programme Source figure: `05_figures/figure13_tac_high_transcriptome_programs.png`. Source data: `04_results/transcriptome/tmem158_tac_high_meta_differential_genes.csv;04_results/transcriptome/tmem158_tac_high_geneset_enrichment.csv;04_results/transcriptome/tmem158_tac_high_top_meta_genes.csv`. Boundary: CAF-adjusted residual programmes do not prove tumour-cell-intrinsic causality.

**Supplementary Figure S8. Main Figure 3 panel B source.** Core-by-CAF pathway-level interaction context Source figure: `05_figures/figure14_tac_high_interaction_gene_heatmap.png`. Source data: `04_results/validation/tmem158_tac_high_interaction_models.csv`. Boundary: CAF-adjusted residual programmes do not prove tumour-cell-intrinsic causality.

**Supplementary Figure S9. Main Figure 3 panel C source.** CAF-adjusted score specificity stress test Source figure: `05_figures/figure22_stromal_adjusted_tac_score_specificity.png`. Source data: `04_results/validation/tmem158_stromal_adjusted_score_meta.csv;04_results/validation/tmem158_stromal_adjusted_score_model_meta.csv`. Boundary: CAF-adjusted residual programmes do not prove tumour-cell-intrinsic causality.

**Supplementary Figure S10. Main Figure 3 panel D source.** CAF-adjusted residual transcriptome programme Source figure: `05_figures/figure23_stromal_adjusted_tac_transcriptome.png`. Source data: `04_results/transcriptome/tmem158_stromal_adjusted_meta_differential_genes.csv;04_results/transcriptome/tmem158_stromal_adjusted_geneset_enrichment.csv;04_results/transcriptome/tmem158_stromal_adjusted_top_meta_genes.csv`. Boundary: CAF-adjusted residual programmes do not prove tumour-cell-intrinsic causality.

**Supplementary Figure S11. Main Figure 4 panel A source.** GSE53625 paired and tumour-only TAC calibration Source figure: `05_figures/figure24_gse53625_tmem158_tac_external_validation.png`. Source data: `04_results/validation/tmem158_gse53625_paired_tumor_normal_tests.csv;04_results/validation/tmem158_gse53625_tac_state_contrasts.csv;04_results/survival/tmem158_gse53625_survival_cox.csv;04_results/validation/tmem158_gse53625_signature_coverage.csv`. Boundary: GSE53625 provides expression-state calibration, not OS prognostic validation.

**Supplementary Figure S12. Main Figure 4 panel B source.** TCGA/cBioPortal regulatory boundary Source figure: `05_figures/figure9_tmem158_multiomics_regulation.png`. Source data: `04_results/mutation_cnv_methylation/tmem158_cbioportal_regulatory_correlations.csv;04_results/mutation_cnv_methylation/tmem158_cbioportal_cnv_counts.csv;04_results/mutation_cnv_methylation/tmem158_cbioportal_methylation_probe_correlations.csv;04_results/mutation_cnv_methylation/tmem158_cbioportal_mutation_summary.csv`. Boundary: GSE53625 provides expression-state calibration, not OS prognostic validation.

**Supplementary Figure S13. Main Figure 4 panel C source.** Public TMEM158 protein and antibody context Source figure: `05_figures/figure11_tmem158_public_protein_context.png`. Source data: `04_results/validation/tmem158_public_protein_knowledgebase_summary.csv;04_results/validation/tmem158_public_protein_evidence_cards.csv;04_results/validation/tmem158_uniprot_quickgo_localization.csv;04_results/validation/tmem158_hpa_context_summary.csv`. Boundary: GSE53625 provides expression-state calibration, not OS prognostic validation.

**Supplementary Figure S14. Main Figure 5 panel A source.** GSE160269 compartment localization of TAC signatures Source figure: `05_figures/figure15_tac_high_scrna_signature_compartments.png`. Source data: `04_results/scrna_signature/tmem158_tac_high_scrna_signature_compartment_tests.csv;04_results/scrna_signature/tmem158_tac_high_scrna_signature_compartment_scores.csv;04_results/scrna_signature/tmem158_tac_high_scrna_signature_coverage.csv`. Boundary: Ligand-receptor scores nominate candidate bridges, not causal cell-cell signalling.

**Supplementary Figure S15. Main Figure 5 panel B source.** Fibroblast TAC signature elevation in TAC_high tumours Source figure: `05_figures/figure16_tac_high_scrna_state_signature_mapping.png`. Source data: `04_results/scrna_signature/tmem158_tac_high_scrna_signature_state_tests.csv;04_results/scrna_signature/tmem158_tac_high_scrna_signature_cross_correlations.csv`. Boundary: Ligand-receptor scores nominate candidate bridges, not causal cell-cell signalling.

**Supplementary Figure S16. Main Figure 5 panel C source.** Candidate CAF-to-epithelial ligand-receptor pairs Source figure: `05_figures/figure17_tac_high_caf_epi_lr_bridge.png`. Source data: `04_results/ligand_receptor/tmem158_tac_high_caf_epi_lr_pair_tests.csv;04_results/ligand_receptor/tmem158_tac_high_caf_epi_lr_pair_scores.csv;04_results/ligand_receptor/tmem158_tac_high_caf_epi_lr_pair_catalog.csv`. Boundary: Ligand-receptor scores nominate candidate bridges, not causal cell-cell signalling.

**Supplementary Figure S17. Main Figure 5 panel D source.** Candidate bridge axis scores Source figure: `05_figures/figure18_tac_high_caf_epi_lr_axis_scores.png`. Source data: `04_results/ligand_receptor/tmem158_tac_high_caf_epi_lr_axis_tests.csv;04_results/ligand_receptor/tmem158_tac_high_caf_epi_lr_axis_scores.csv;04_results/ligand_receptor/tmem158_tac_high_caf_epi_lr_axis_correlations.csv`. Boundary: Ligand-receptor scores nominate candidate bridges, not causal cell-cell signalling.

**Supplementary Figure S18. Main Figure 6 panel A source.** Independent GSE221561 fibroblast-dominant TAC context Source figure: `05_figures/figure19_gse221561_tac_context_validation.png`. Source data: `04_results/gse221561/tmem158_gse221561_tac_compartment_paired_tests.csv;04_results/gse221561/tmem158_gse221561_tac_group_scores.csv;04_results/gse221561/tmem158_gse221561_tac_target_gene_coverage.csv`. Boundary: Independent context layers support CAF-rich ecology while preserving immune, survival and spatial-validation boundaries.

**Supplementary Figure S19. Main Figure 6 panel B source.** GSE221561 fibroblast subtype context Source figure: `05_figures/figure20_gse221561_tac_subtype_signature_context.png`. Source data: `04_results/gse221561/tmem158_gse221561_tac_subtype_signature_summary.csv;04_results/gse221561/tmem158_gse221561_tac_matched_sample_scores.csv;04_results/gse221561/tmem158_gse221561_tac_matched_sample_correlations.csv`. Boundary: Independent context layers support CAF-rich ecology while preserving immune, survival and spatial-validation boundaries.

**Supplementary Figure S20. Main Figure 6 panel C source.** Public spatial-progression fibroblast/alpha-SMA context Source figure: `05_figures/figure21_spatial_progression_source_context.png`. Source data: `04_results/spatial_progression/tmem158_spatial_progression_stage_tests.csv;04_results/spatial_progression/tmem158_spatial_progression_key_tests.csv;04_results/spatial_progression/tmem158_spatial_progression_context_status.csv;04_results/spatial_progression/natcomm2023_spatial_source_extract_status.csv`. Boundary: Independent context layers support CAF-rich ecology while preserving immune, survival and spatial-validation boundaries.

**Supplementary Figure S21. Main Figure 6 panel D source.** Single-cell immune-boundary analysis Source figure: `05_figures/figure10_scrna_tac_high_immune_boundary.png`. Source data: `04_results/immune/tmem158_scrna_rule_state_immune_tests.csv;04_results/immune/tmem158_scrna_rule_state_counts.csv`. Boundary: Independent context layers support CAF-rich ecology while preserving immune, survival and spatial-validation boundaries.

**Supplementary Figure S22. AlphaFold topology context for TMEM158.** Figure file: `05_figures/figure25_tmem158_alphafold_topology_context.png`. Source data: `04_results/structure/tmem158_alphafold_model_summary.csv;04_results/structure/tmem158_alphafold_topology_segments.csv;04_results/structure/tmem158_alphafold_residue_confidence.csv;04_results/qc/tmem158_alphafold_topology_context_status.csv`. Boundary: AlphaFold/UniProt support membrane-topology plausibility, especially TM1; they do not prove ER localization, physical interaction with Ca2/UPR nodes, ECM binding or ESCC protein validation.

## Supplementary Tables

**Supplementary Table S1. source data inventory.** File: `08_submission_strategy/source_data_and_supplementary_inventory.csv`. Status: `self_generated`.

**Supplementary Table S2. repository deposit manifest.** File: `08_submission_strategy/repository_deposit_manifest.csv`. Status: `ready`.

**Supplementary Table S3. submission readiness gate.** File: `04_results/qc/tmem158_submission_readiness_gate.csv`. Status: `ready`.

**Supplementary Table S4. literature readiness status.** File: `04_results/qc/tmem158_literature_readiness_status.csv`. Status: `ready`.

**Supplementary Table S5. main figure visual QA.** File: `04_results/qc/main_figure_visual_qa.csv`. Status: `ready`.

**Supplementary Table S6. negative results and claim boundaries.** File: `04_results/qc/negative_results.csv`. Status: `ready`.

**Supplementary Table S7. structural follow-up prioritization.** File: `08_submission_strategy/tmem158_structural_followup_prioritization.csv`. Status: `ready`.

**Supplementary Table S8. LR compartment-expression feasibility audit.** File: `08_submission_strategy/tmem158_lr_compartment_expression_audit.csv`. Status: `ready`.

## Claim Boundaries Preserved In Supplementary Files

- TMEM158 is a lead computational entry point, not a validated causal driver.
- TAC_high is a public-data stress-ecology state, not a clinically validated subtype.
- Survival analyses in TCGA and GSE53625 do not support a prognostic claim.
- CAF-to-epithelial ligand-receptor scoring nominates candidate bridges but does not prove signalling causality.
- Public spatial source data support CAF-rich tissue context but do not directly validate spatial TMEM158/TAC_high activation.
- AlphaFold/UniProt topology context supports membrane-structure plausibility but does not prove ER localization, physical interaction, ECM binding or ESCC protein validation.
- Structural follow-up prioritization ranks candidate pair/model/assay targets; it does not demonstrate physical interaction or receptor activation.
- LR compartment-expression auditing checks fibroblast-ligand and epithelial-receptor feasibility only; it does not demonstrate spatial adjacency, protein abundance or cell-cell communication.
- Drug-efflux, proteostasis and therapy-pressure results remain computational and hypothesis-generating.
