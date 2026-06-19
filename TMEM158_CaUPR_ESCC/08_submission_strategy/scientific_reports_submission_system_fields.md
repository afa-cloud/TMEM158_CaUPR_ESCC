# Scientific Reports Submission-System Fields

Generated: 2026-06-20 02:03:51

## Machine Summary

- Submission field rows: 27
- Machine submission-fields clearance: `pass`
- Final upload clearance: `not_yet`
- Human-required tasks: 2

## Copy-Ready Fields

### Manuscript

#### article_type

Status: `ready`

Article

Source: `target journal strategy`

Notes: First-pass target-journal format.

#### title

Status: `ready`

TMEM158-associated Ca2/UPR-CAF ecology in oesophageal squamous cell carcinoma

Source: `07_manuscript/manuscript_scientific_reports.md`

Notes: 9 words.

#### running_title

Status: `ready`

TMEM158-associated TAC_high stress ecology in ESCC

Source: `derived from title`

Notes: Short display title; human may adjust if the journal asks for a running title.

#### abstract

Status: `ready`

Calcium homeostasis, unfolded protein response (UPR) branch activity and stromal remodelling are incompletely integrated in oesophageal squamous cell carcinoma (ESCC). We performed an axis-first public-data analysis to identify upstream candidates associated with a Ca2/UPR stress ecology. TMEM158 emerged as a computational entry point, rather than as a standalone prognostic biomarker. We defined TAC_high as the co-occurrence of a high TMEM158-Ca2/PERK core score and a high cancer-associated fibroblast (CAF) score. TAC_high was reproducible across four bulk ESCC cohorts and was associated with proteostasis and cell-survival transcriptional readouts, whereas overall-survival analyses remained negative. Whole-transcriptome meta-analysis identified a dominant extracellular-matrix/CAF programme and CAF-adjusted residual MYC, oxidative phosphorylation, KEAP1/NFE2L2, chemical-stress and translation signatures. GSE53625 calibrated this expression state in 179 paired samples without validating prognosis. Independent single-cell analyses localized TAC_high meta-signatures to fibroblast/CAF pseudo-bulk profiles and nominated expression-feasible POSTN/FN1/collagen-integrin and MIF-CXCR4 candidate CAF-to-epithelial bridges. Public spatial source data supported a fibroblast-rich progression context. These findings support a TMEM158-associated Ca2/UPR-CAF ecology model in ESCC as a public-data biological discovery candidate, while preserving an explicit boundary between association and causality.

Source: `07_manuscript/manuscript_scientific_reports.md`

Notes: 182 words.

#### keywords

Status: `ready`

Oesophageal squamous cell carcinoma; TMEM158; calcium homeostasis; unfolded protein response; cancer-associated fibroblasts; public-data bioinformatics

Source: `07_manuscript/manuscript_scientific_reports.md`

Notes: 6 keywords.

### Editorial

#### editor_significance_statement

Status: `ready_optional`

This public-data study defines a reproducible TMEM158-associated TAC_high Ca2/UPR-CAF stress-ecology state in ESCC, with CAF/fibroblast localization, CAF-adjusted residual stress transcription and explicit negative boundaries for prognosis, causality, immune suppression and treatment resistance.

Source: `derived from manuscript and reviewer-risk pack`

Notes: Use if the submission system requests significance, relevance or editor comments.

#### plain_language_summary

Status: `ready_optional`

The study uses existing public cancer datasets to describe a stress-related tumour ecology pattern in esophageal squamous cell carcinoma. The findings suggest a testable biology state linked to fibroblast-rich tumour context, but they do not prove a treatment target or clinical biomarker.

Source: `derived from manuscript abstract and limitations`

Notes: Use only if requested by the journal system.

#### cover_letter_core_pitch

Status: `ready_author_confirmed`

This manuscript reports a reproducible public-data computational biology study of esophageal squamous cell carcinoma (ESCC). Starting from an axis-first Ca2/UPR regulator screen, we identify TMEM158 as a lead computational entry point and define a rule-based TAC_high state combining TMEM158-Ca2/PERK-core activity with a cancer-associated fibroblast score. Across public bulk cohorts, TAC_high is reproducible and is linked to proteostasis and stress-state transcriptional readouts. Whole-transcriptome and CAF-adjusted analyses distinguish a dominant ECM/CAF programme from residual MYC, oxidative phosphorylation, KEAP1/NFE2L2, chemical-stress and translation signatures. Independent single-cell pseudo-bulk analyses localize TAC_high meta-signatures to fibroblast/CAF profiles and nominate expression-feasible ECM-integrin and MIF-CXCR4 candidate bridges, while GSE53625 provides external expression-state calibration in 179 paired clinical samples.

Source: `08_submission_strategy/scientific_reports_cover_letter_draft.md`

Notes: Corresponding-author name, affiliation and email are filled.

### Author Metadata

#### author_list

Status: `ready`

Yang Haoshui; Ma Yuqing

Source: `08_submission_strategy/human_submission_metadata_template.md`

Notes: Author order supplied by the submitting author.

#### affiliations

Status: `ready`

The First Affiliated Hospital of Xinjiang Medical University; Xinjiang Medical University

Source: `08_submission_strategy/human_submission_metadata_template.md`

Notes: Department-level detail can be added if the journal system requires it.

#### corresponding_author

Status: `ready`

Ma Yuqing

Source: `08_submission_strategy/human_submission_metadata_template.md`

Notes: Corresponding author supplied by the user.

#### corresponding_author_email

Status: `ready_author_confirmed`

yuqingm0928@126.com

Source: `08_submission_strategy/human_submission_metadata_template.md`

Notes: Corresponding-author email supplied by the user.

#### orcid

Status: `ready_partial`

Yang Haoshui: 0009-0008-6805-3893; Ma Yuqing: not provided

Source: `08_submission_strategy/human_submission_metadata_template.md`

Notes: Ma Yuqing ORCID is optional unless the journal system requires it.

### Availability

#### data_availability

Status: `ready_public_repository`

All data analysed in this study were obtained from public resources, including TCGA/GDC or cBioPortal, GEO, DepMap-derived public resources, UniProt, QuickGO, the Human Protein Atlas and the AlphaFold Protein Structure Database [1,9,17,18,22-25]. No new patient-level dataset was generated in this study. Processed intermediate tables and analysis outputs are available in the public GitHub repository at https://github.com/afa-cloud/TMEM158_CaUPR_ESCC, with an initial-submission release at https://github.com/afa-cloud/TMEM158_CaUPR_ESCC/releases/tag/v1.0-initial-submission.

Source: `07_manuscript/manuscript_scientific_reports.md`

Notes: Processed outputs are deposited in the public GitHub repository: https://github.com/afa-cloud/TMEM158_CaUPR_ESCC; initial-submission release: https://github.com/afa-cloud/TMEM158_CaUPR_ESCC/releases/tag/v1.0-initial-submission.

#### code_availability

Status: `ready_public_repository`

The reproducible workflow was implemented in TMEM158_CaUPR_ESCC/03_scripts/R/run_all.R, with helper scripts under TMEM158_CaUPR_ESCC/03_scripts/R/ and TMEM158_CaUPR_ESCC/03_scripts/Python/. The code is publicly available in the GitHub repository at https://github.com/afa-cloud/TMEM158_CaUPR_ESCC, with an initial-submission release at https://github.com/afa-cloud/TMEM158_CaUPR_ESCC/releases/tag/v1.0-initial-submission.

Source: `07_manuscript/manuscript_scientific_reports.md`

Notes: Analysis code is deposited in the public GitHub repository: https://github.com/afa-cloud/TMEM158_CaUPR_ESCC; initial-submission release: https://github.com/afa-cloud/TMEM158_CaUPR_ESCC/releases/tag/v1.0-initial-submission.

### Declarations

#### ethics_statement

Status: `ready`

All datasets used in this study were public and de-identified. No new human specimens, animal experiments or wet-lab experiments were performed, and no new ethics approval or informed consent was required for this secondary analysis.

Source: `07_manuscript/manuscript_scientific_reports.md`

Notes: Public de-identified secondary analysis only.

#### competing_interests

Status: `ready_author_confirmed`

The author(s) declare no competing interests.

Source: `08_submission_strategy/human_submission_metadata_template.md`

Notes: User confirmed no competing interests.

#### funding

Status: `ready_author_confirmed`

This research received no specific grant from any funding agency in the public, commercial or not-for-profit sectors.

Source: `08_submission_strategy/human_submission_metadata_template.md`

Notes: User confirmed no external funding.

#### author_contributions

Status: `ready_author_confirmed`

Y.H. conceived the study, curated the data, performed the formal analysis, investigation, methodology implementation, software workflow construction and visualization, and wrote the original draft. Y.H. reviewed and edited the manuscript. Y.M. supervised the study. No author received funding acquisition support for this work.

Source: `08_submission_strategy/human_submission_metadata_template.md`

Notes: Roles supplied by the user and formatted for the manuscript.

#### acknowledgements

Status: `ready_author_confirmed`

Yang Haoshui's ORCID is 0009-0008-6805-3893. The authors acknowledge the First Affiliated Hospital of Xinjiang Medical University and Xinjiang Medical University for academic support. Correspondence and requests for materials should be addressed to Ma Yuqing (yuqingm0928@126.com).

Source: `08_submission_strategy/human_submission_metadata_template.md`

Notes: Institutional acknowledgement and ORCID/correspondence note supplied by the user.

#### ai_assisted_tool_use

Status: `ready_author_confirmed`

The authors used ChatGPT (OpenAI) and Codex for language editing, code assistance, and manuscript drafting. All scientific interpretations, analyses, and conclusions were reviewed and verified by the authors.

Source: `08_submission_strategy/human_submission_metadata_template.md`

Notes: User approved AI-assisted tool disclosure.

### Repository

#### repository_doi_or_permanent_url

Status: `ready_public_repository_url`

https://github.com/afa-cloud/TMEM158_CaUPR_ESCC/releases/tag/v1.0-initial-submission

Source: `08_submission_strategy/repository_deposit_manifest.csv`

Notes: Public GitHub repository created before submission at https://github.com/afa-cloud/TMEM158_CaUPR_ESCC; this field uses the versioned release URL. DOI can be minted later through Zenodo if required.

### Reviewer Metadata

#### suggested_reviewers

Status: `optional_human_required`

OPTIONAL_HUMAN_REQUIRED: add only if the journal requests suggested reviewers.

Source: `human author decision`

Notes: Must avoid conflicts of interest.

#### opposed_reviewers

Status: `optional_human_required`

OPTIONAL_HUMAN_REQUIRED: add only if necessary and journal allows exclusions.

Source: `human author decision`

Notes: Must be justified and conflict-aware.

### Claim Boundary

#### public_data_boundary

Status: `ready`

This study used only publicly available datasets and did not involve newly collected human specimens, animal experiments or wet-lab experiments.

Source: `Methods / ethics statement`

Notes: Keep this statement in submission metadata if a study-design field is requested.

#### claims_not_made

Status: `ready`

The manuscript does not claim that TMEM158 is a validated causal driver, a clinical prognostic biomarker, a cisplatin-resistance mechanism, a direct immune-suppression mechanism, a directly spatially validated programme or an experimentally validated ESCC protein/ER-localization finding.

Source: `claim-boundary audit and reviewer-risk pack`

Notes: Use for cover letter, editor comments or reviewer response preparation.

#### limitations_summary

Status: `ready`

This study used retrospective public datasets and is subject to database heterogeneity, batch effects, platform differences and incomplete clinical annotation. Some GEO cohorts are small. TCGA-ESCA also contains histological-mixing risk, even when used as ESCC-compatible context. Survival analyses were underpowered for some state contrasts and did not support a clinical OS claim. GSE53625 provides a larger paired clinical cohort, but it required targeted probe-sequence reannotation and did not support OS prognostic claims. It should therefore be treated as external calibration, not clinical validation. Several analyses reduce overinterpretation but cannot remove it. CAF-adjusted transcriptome models reduce stromal-composition confounding but cannot identify the cellular origin of each residual gene programme. Single-cell analyses used pseudo-bulk and compartment-level signature summaries, so they cannot prove cell-cell causality, ligand-receptor signalling origin or tumour-cell-autonomous regulation. The compartment-expression audit confirms ligand and receptor detectability for prioritized candidates, but ...

Source: `07_manuscript/manuscript_scientific_reports.md`

Notes: Condensed from manuscript limitations.

## Human-Gated Final Tasks

- `human_01` suggested_reviewers (optional): OPTIONAL_HUMAN_REQUIRED: add only if the journal requests suggested reviewers.
- `human_02` opposed_reviewers (optional): OPTIONAL_HUMAN_REQUIRED: add only if necessary and journal allows exclusions.
- `human_03` final_upload_preview (yes): Inspect final manuscript DOCX/PDF and figure previews in the journal upload system.
- `human_03` final_claim_boundary_read (yes): Confirm no causal, prognostic, immune-suppression, spatial-validation or treatment-resistance claim was introduced during metadata editing.

## Boundary

This file is a submission-engineering artifact. It does not upgrade the manuscript beyond a public-data, association-based and hypothesis-generating ESCC stress-ecology discovery study.
