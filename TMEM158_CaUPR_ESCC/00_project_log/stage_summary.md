# Stage Summary

<!-- 2026-06-20 author metadata submission refresh -->
- Author metadata and submission declarations are now supplied and synchronized. Yang Haoshui and Ma Yuqing are listed on the manuscript; Ma Yuqing is the corresponding author with `yuqingm0928@126.com`. Funding, competing interests, author contributions, acknowledgements and AI-assisted tool disclosure are filled. Code repository deposition is deferred before initial submission by author decision. The machine package remains clear; final upload is still gated only by publisher preview and final claim-boundary read.

<!-- 2026-06-19 protein topology claim audit targeted refresh -->
- Protein-topology claim audit added and targeted-refresh passed. Integrated UniProt/QuickGO/HPA plus AlphaFold evidence now supports only TMEM158 membrane/topology plausibility and assayability. It explicitly does not support direct ER localization, Ca2/UPR physical binding, ECM binding or ESCC-specific protein validation. Targeted final gap audit: 19 rows, machine rows needing revision=0, final machine clearance=pass. Scientific Reports bundle: 83 required files, 0 missing, machine bundle clearance=pass. Later full rerun was intentionally interrupted at user request; do not treat the final log line as a true analysis failure.

TMEM158-CaUPR branch status after ecology-state module:

- First-pass TMEM158 expression, axis-coupling, single-cell ecology and survival analyses completed.
- Second-pass composite-state analysis completed.
- Rule-defined `TAC_high` ecology subtype is present in all four bulk cohorts with at least three samples.
- `TAC_high` versus other states shows replicated proteostasis-score and survival-score elevation across cohorts.
- TCGA clinical survival remains negative and must not be used as a primary claim.
- Main publishable direction is TMEM158-associated Ca2/UPR-CAF stress ecology, not TMEM158 prognostic biomarker or direct Ca2 activation.

<!-- 2026-06-19 tmem158 alphafold topology context -->
- AlphaFold topology context added as a structural plausibility/boundary layer, not as causality or physical-interaction evidence.

<!-- 2026-06-19 submission archive/source-data package -->
- 2026-06-19 submission archive/source-data package: Source-data inventory, Supplementary Information draft, repository manifest, checksum file and repository release README are now generated. Author metadata/funding/contributions/competing-interest disclosures are now supplied. The remaining non-pass submission gates are publisher upload preview and final claim-boundary read; public GitHub repository deposition is complete at `https://github.com/afa-cloud/TMEM158_CaUPR_ESCC`.

<!-- 2026-06-19 standalone repository release package -->
- Standalone repository release package complete. The package excludes raw-data caches, publisher/full-text gate files, logs, local upload dry-run bundles and generated submission ZIPs while retaining code, processed results, figures, manuscripts and QC evidence.

<!-- 2026-06-19 scientific reports submission bundle dry run -->
- Scientific Reports submission bundle dry run complete. Required files are copied into a stable bundle folder, checksums and ZIP are generated, and final upload remains gated by publisher upload preview and final claim-boundary read.
<!-- 2026-06-19 structural follow-up prioritization targeted layer -->
- Structural follow-up prioritization complete as a targeted layer. `POSTN->ITGA5` is the top defined-partner/proximity follow-up candidate, followed by FN1/POSTN/collagen-integrin candidates and `MIF->CXCR4`. This layer ranks validation priorities only and does not prove physical interaction, receptor activation, CAF-to-epithelial causality or TMEM158 binding. No full pipeline rerun was performed.

<!-- 2026-06-19 lr compartment expression audit targeted layer -->
- LR compartment-expression feasibility audit complete as a targeted layer. Top structural candidates were checked for fibroblast/CAF ligand expression and epithelial receptor detectability in GSE160269 pseudo-bulk compartments. `POSTN->ITGA5` and `FN1->ITGA5` are the clearest expression-feasible candidates, while several ITGB3/ITGA1 and MIF-CXCR4 candidates require expression-boundary wording. No full pipeline rerun was performed.

<!-- 2026-06-19 reviewer risk response pack -->
- Reviewer-risk response pack complete: likely objections around novelty, public-data-only design, CAF confounding, prognosis, causality, single-cell LR bridges, spatial context and drug-resistance boundaries are mapped to current evidence files.
<!-- 2026-06-19 manuscript numeric consistency audit -->
- Added a machine-readable audit linking key manuscript numeric claims back to current result tables.

<!-- 2026-06-19 claim-boundary text audit -->

- Claim-boundary text audit is now generated for public-facing manuscript/submission files. Machine claim-boundary clearance is `pass`; author metadata/declarations are supplied, and final upload clearance now depends on publisher preview plus final claim-boundary read.

<!-- 2026-06-19 scientific reports citation coverage audit -->
- Scientific Reports citation coverage audit complete. Clearance: `pass`.
<!-- 2026-06-19 scientific reports submission system fields -->
- Scientific Reports submission-system fields are now extracted into Markdown/CSV, with human-gated metadata isolated in a final task table.
<!-- 2026-06-19 lr expression maintext integration targeted refresh -->
- LR compartment-expression feasibility evidence is now integrated into the main manuscript and submission-facing files. The manuscript states that 11/20 top structural candidates passed the expected fibroblast-ligand plus detectable epithelial-receptor pattern, with `POSTN->ITGA5` and `FN1->ITGA5` as expression-feasible follow-up candidates. `POSTN->ITGA5` values are fibroblast POSTN median expression=1.753, epithelial ITGA5 median expression=0.094 and LR score FDR=0.033. The layer remains bounded to expression feasibility and does not prove receptor activation, spatial contact, physical communication or TMEM158 binding. No full pipeline rerun was performed; targeted manuscript/DOCX/submission refresh passed.

<!-- 2026-06-19 official scirep policy audit -->
- Official policy/readiness layer added: Scientific Reports formatting checks, Nature Portfolio Reporting Summary working draft and editorial policy checklist are now tracked as submission-engineering evidence.
