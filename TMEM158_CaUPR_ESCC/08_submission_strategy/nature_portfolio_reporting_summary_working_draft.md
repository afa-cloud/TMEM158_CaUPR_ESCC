# Nature Portfolio Reporting Summary Working Draft

Generated: 2026-06-20 01:46:23

This is a machine-prepared working draft to help complete the official Nature Portfolio Reporting Summary if the manuscript is sent for review. It is not a signed final publisher form.

## Manuscript

- Title: TMEM158-associated Ca2/UPR-CAF ecology in oesophageal squamous cell carcinoma
- Article type target: Scientific Reports Article
- Study type: Retrospective public-data computational biology and oncology analysis
- Primary organism: Human
- Disease context: Esophageal squamous cell carcinoma
- New experimental data: None

## Experimental Design

- Public datasets only were analysed. No new human specimens, animal experiments, wet-lab experiments or prospective recruitment were performed.
- The analysis was rebuilt around a Ca2/UPR axis-first strategy after the original SMIM14-centred model was demoted.
- The lead computational entry point is TMEM158, interpreted as a state-associated membrane-protein candidate, not a validated causal driver.
- The rule-defined TAC_high state combines high TMEM158-Ca2/PERK core score with high CAF score within each cohort.

## Sample Size And Replication

- Sample sizes are determined by available public cohorts and usable public raw files, not by prospective power calculation.
- Bulk discovery and validation use TCGA/GDC-compatible ESCC context and GEO cohorts listed in the manuscript and source-data inventory.
- GSE53625 is used as independent targeted clinical calibration after probe-sequence reannotation.
- GSE160269 and GSE221561 are used for single-cell pseudo-bulk localization and external context.
- Public spatial source-data tables from Liu et al., Nature Communications 2023 are used for fibroblast-rich progression context, not direct TMEM158/TAC_high spatial rescoring.

## Data Exclusions And Missing Data

- Dataset inclusion, corrupted raw-library handling and restricted-source boundaries are documented in the manuscript, QC outputs and source-data inventory.
- In GSE221561, seven of eleven listed raw libraries were usable; corrupted gzip members were retained in QC and not treated as silently absent.
- The public spatial Source Data did not contain the complete WTA matrix, so TMEM158, TAC_high and Ca2/UPR spatial scores were not directly recomputed.

## Randomization And Blinding

- Randomization and blinding are not applicable to this retrospective public-data computational study.
- Cohort-preserving random-label testing was used as a statistical specificity stress test for TAC_high, not as experimental randomization.

## Statistical Methods

- Sample-level scores were standardized within cohorts.
- Wilcoxon tests, Benjamini-Hochberg FDR correction, signed Stouffer meta-analysis, limma models, Cox proportional-hazards models and pseudo-bulk single-cell summaries were used as described in Methods.
- Negative or underpowered survival, immune, drug-resistance, spatial and causality layers are retained as claim boundaries rather than removed.

## Software And Reproducibility

- Main workflow: `TMEM158_CaUPR_ESCC/03_scripts/R/run_all.R`
- Helper scripts: `TMEM158_CaUPR_ESCC/03_scripts/R/` and `TMEM158_CaUPR_ESCC/03_scripts/Python/`
- Source-data inventory: `TMEM158_CaUPR_ESCC/08_submission_strategy/source_data_and_supplementary_inventory.csv`
- Repository manifest: `TMEM158_CaUPR_ESCC/08_submission_strategy/repository_deposit_manifest.csv`
- Checksums: `TMEM158_CaUPR_ESCC/08_submission_strategy/repository_file_checksums.sha256`

## Human Research Ethics

- All datasets used were public and de-identified.
- No new ethics approval or informed consent was required for this secondary public-data analysis, subject to final author and institutional confirmation.

## Human-Gated Completion Items

- Complete the official Nature Portfolio Reporting Summary form if requested by the submission workflow.
- Confirm author names, affiliations, corresponding author and all-author agreement.
- Confirm competing interests, funding, acknowledgements and author contributions.
- Use the public GitHub repository URL in the submission system: https://github.com/afa-cloud/TMEM158_CaUPR_ESCC. Add a DOI only if the journal requests an archival identifier.
- Inspect the final journal-system converted manuscript and figure previews.

## Manuscript Abstract For Reference

Calcium homeostasis, unfolded protein response (UPR) branch activity and stromal remodelling are incompletely integrated in esophageal squamous cell carcinoma (ESCC). We performed an axis-first public-data analysis to identify upstream candidates associated with Ca2/UPR stress ecology. TMEM158 emerged as a lead computational entry point, but not as a standalone prognostic biomarker. We defined TAC_high as the co-occurrence of high TMEM158-Ca2/PERK core score and high cancer-associated fibroblast (CAF) score. TAC_high was reproducible across four bulk ESCC cohorts and associated with proteostasis and survival-transcriptional readouts, while overall-survival analyses remained negative. Whole-transcriptome meta-analysis showed a dominant extracellular-matrix/CAF programme and CAF-adjusted residual MYC, oxidative phosphorylation, KEAP1/NFE2L2, chemical-stress and translation signatures. GSE53625 externally calibrated the expression state in 179 paired samples without validating prognosis. Independent single-cell analyses localized TAC_high meta-signatures to fibroblast/CAF pseudo-bulk profiles and nominated expression-feasible POSTN/FN1/collagen-integrin and MIF-CXCR4 candidate CAF-to-epithelial bridges. Public spatial source data supported a fibroblast-rich progression context. These results define a TMEM158-associated Ca2/UPR-CAF stress ecology state in ESCC as a public-data biological discovery candidate, while preserving an explicit boundary between association and causality.

## Methods Section Anchor

### Study design

This study used only publicly available datasets and did not involve newly collected human specimens, animal experiments, or wet-lab experiments. The workflow was designed as a pure public-data, hypothesis-generating ESCC bioinformatics analysis.

### Candidate selection

The project was rebuilt from an axis-first regulator screen after the original SMIM14-core model failed to support strong causal or prognostic claims. Candidate scoring integrated TCGA axis-CAF discovery, GSE45670 validation, GSE160269 epithelial and CAF pseudo-bulk evidence, DepMap ESCC expression context, public proteogenomics coverage and PubMed novelty gates. TMEM158 was selected as the lead computational candidate, while CORO1C and selected transporter/proteostasis genes were retained as secondary program members.

### Bulk expression and score analysis

Processed TCGA and GEO expression matrices from the existing project were reused. TMEM158 tumour-normal differences were tested within each cohort. Ca2-axis genes, UPR branch genes, CAF markers, proteostasis genes, cell-survival genes and drug-efflux genes were scored at the sample level using standardized expression summaries. Cohort-specific z-scores were used to reduce platform effects when constructing composite states.

### TAC_high state definition

Within each bulk cohort, TMEM158, Ca2-axis score, PERK-bias index and CAF score were standardized. The TMEM158-Ca2/PERK core was defined as the mean of z(TMEM158), z(Ca2-axis score) and z(PERK-bias index). Samples high for this core and high for CAF score were labelled TAC_high. Samples high only for the core were labelled Axis_only, samples high only for CAF were labelled CAF_only, and samples low for both were labelled TAC_low.

### Reproducibility and statistics

Within-cohor...
