# Target Journal Strategy: Scientific Reports First Pass

## Recommendation

Primary target for the current pure public-data manuscript package:

- **Scientific Reports**
- Article type: **Article**
- Rationale: the manuscript is a technically reproducible computational biology and oncology study with public multi-cohort data, formal novelty checks, six main figures, data/code availability and explicit association-not-causality boundaries.

## Why Not BMC Cancer As The Primary First Target

BMC Cancer is scientifically adjacent, but it is a high-risk first target for this manuscript because its current official author guidance states that manuscripts consisting solely of bioinformatics, computational analysis or public-database predictions without accompanying validation will not be considered. Its biomarker guidance also expects independent validation and biological validation for marker studies. The present study has extensive public-data validation and calibration, but no new wet-lab or in vitro/in vivo validation by design.

Use BMC Cancer only if the manuscript is reframed after wet-lab validation or if an editor explicitly confirms that the public single-cell/spatial/GSE53625 validation layer is sufficient for their current standard.

Official pages checked on 2026-06-19:

- BMC Cancer submission guidelines: https://link.springer.com/journal/12885/submission-guidelines
- BMC Cancer aims and scope: https://link.springer.com/journal/12885/aims-and-scope
- BMC Cancer research article requirements: https://link.springer.com/journal/12885/submission-guidelines/research-article
- Scientific Reports submission guidelines: https://www.nature.com/srep/author-instructions/submission-guidelines
- Nature Portfolio data/code availability policy: https://www.nature.com/nature-portfolio/editorial-policies/reporting-standards

## Current Fit For Scientific Reports

| Requirement or expectation | Current status | Evidence |
|---|---|---|
| Article title concise and scientifically descriptive | Pass | `manuscript_scientific_reports.md` title has 15 words |
| Abstract <=200 words | Pass | Current target abstract has 172 words |
| Main text organized with Introduction, Results, Discussion, Methods | Pass | `manuscript_scientific_reports.md` |
| Display items within Scientific Reports limit | Pass | Six main figures; extended figures can move to Supplementary Information |
| Data availability statement | Present, needs final accession detail polishing | `manuscript_scientific_reports.md` |
| Code availability statement | Present, but needs repository/DOI before final submission if possible | `manuscript_scientific_reports.md` |
| Author contributions | Placeholder | Requires human author information |
| Competing interests | Placeholder | Requires all-author confirmation |
| Ethics declaration | Present | Public de-identified datasets only |
| AI-assisted tool disclosure | Present | Needs human author approval before submission |
| Full-text/supplement novelty gate | Pass | `tmem158_literature_readiness_status.csv`, `risk_of_duplication.md`, `novelty_statement.md` |
| Main figure visual QA | Pass | `main_figure_visual_qa.csv`: 6/6 |

## Submission Framing

Recommended title:

**A TMEM158-associated Ca2/UPR-CAF stress ecology state defines proteostasis-linked adaptation in esophageal squamous cell carcinoma**

Recommended one-sentence editor-facing frame:

This study uses reproducible public multi-cohort transcriptomics, single-cell pseudo-bulk analysis, targeted external clinical calibration and spatial source-data context to define a TMEM158-associated Ca2/UPR-CAF stress ecology state in ESCC, while explicitly avoiding unsupported causal, prognostic or treatment-response claims.

## Claims To Keep

- `TAC_high` is a rule-defined, reproducible ESCC stress-ecology state.
- The strongest transcriptomic signal is ECM/CAF/EMT, with CAF-adjusted residual MYC/OXPHOS/NFE2L2/translation stress programmes.
- GSE53625 supports external expression-state and ECM/residual-stress calibration, not prognosis.
- GSE160269 and GSE221561 support fibroblast/CAF-dominant TAC meta-signature localization.
- Candidate bridges include POSTN/collagen/FN1-integrin and MIF-CXCR4, interpreted as hypotheses.

## Claims To Avoid

- TMEM158 is a validated causal driver.
- TAC_high is a validated clinical prognostic subtype.
- TAC_high causes immune suppression or CD8 exhaustion.
- TAC_high proves cisplatin resistance.
- TAC_high is tumour-cell-intrinsic.
- Public spatial source data directly validate TMEM158/TAC_high spatial activation.
- HPA/UniProt/QuickGO data are ESCC protein or ER-localization validation.

## Final Human Inputs Required

- Author names, affiliations and corresponding author.
- Funding statement.
- Competing interests statement for each author.
- Author contributions.
- Final decision on whether to deposit code/results in Zenodo, OSF, GitHub or another citable repository before submission.
- Final visual inspection of PDFs/SVGs in the submission system preview.

<!-- 2026-06-19 official scirep policy audit -->
## 2026-06-19 Official Scientific Reports/Nature Portfolio Policy Audit

- Official sources checked: Scientific Reports submission guidelines; Nature Portfolio reporting standards; Scientific Reports editorial policies; Nature Portfolio competing interests policy.
- Current manuscript title count: 14 words.
- Current abstract count: 175 words.
- Current keyword count: 6.
- Main display items: 6 composite figures.
- Machine-auditable formatting status: pass, with human-gated items separated.
- Reporting Summary: working draft generated at `08_submission_strategy/nature_portfolio_reporting_summary_working_draft.md`; final official form remains human-gated if requested by the journal workflow.
- Remaining human gates: all-author agreement, official Reporting Summary form if requested, publisher upload-system preview and final claim-boundary read; repository DOI/permanent URL only if later deposited or requested.
