# Risk Of Duplication

## Current Decision

- Decision: Conditional GO
- Rationale: VM-routed PubMed title/abstract search found no direct TMEM158-ESCC, TMEM158-ESCC-Ca2/UPR or TMEM158-ESCC-CAF/stroma overlap. PMC XML review did not identify a direct TMEM158-ESCC TAC_high duplication signal.
- Remaining unresolved manual items: 12

## Boundary Risks

- Broad TMEM158 cancer literature exists, including pancreatic, glioma, gastric, ovarian, prostate, lung and TMEM-family review contexts.
- Some PMC XML contexts contain TMEM158 aliases in articles that also mention ESCC/stromal/signature terms, but current automated review classifies them as non-ESCC primary articles, neighbouring squamous-cancer contexts, reviews, or reference/background contexts.
- Supplementary tables remain the main unresolved risk because TMEM158 can be hidden inside signatures or candidate-gene tables.

## Required Before Final Submission

- Resolve all `manual_required_*` rows in `01_literature/manual_download_manifest.csv`.
- Re-run the full-text/supplement scan and submission readiness audit.
- Keep manuscript claims centred on ESCC TAC_high Ca2/UPR-CAF stress ecology rather than generic TMEM158 cancer biology.

Updated: 2026-06-19 22:58:38
