# Decision Record

<!-- 2026-06-20 author metadata submission refresh -->
Decision: treat author metadata and declarations as completed for the current Scientific Reports initial-submission package, while deferring public code repository deposition by author decision.

Reason: the user supplied the remaining author-level information, including Ma Yuqing's corresponding-author email, funding/no-conflict/contribution statements and AI-assisted tool disclosure. The repository release package remains ready, but the author chose not to upload code before initial submission. Final upload cannot be called complete until publisher preview and final claim-boundary read are performed in the journal system.

<!-- 2026-06-19 protein topology claim audit targeted refresh -->
Decision: add an integrated TMEM158 protein-topology claim audit and stop routine full-pipeline reruns after every small evidence-layer change.

Reason: UniProt/QuickGO/HPA and AlphaFold strengthen TMEM158 membrane/topology plausibility but do not provide direct ER localization, physical binding, ECM interaction or ESCC protein validation. The useful output is therefore a claim-boundary audit and submission-defense table, not another broad exploratory analysis layer. Full `run_all.R` reruns are reserved for final target completion and packaging.

Decision: continue pure bioinformatics manuscript construction by pivoting from SMIM14-core to TMEM158 lead-candidate plus Ca2/UPR branch-state.

Reason: prior final decision branch selected TMEM158 as lead candidate, and the user explicitly wants continued pure-bioinformatics progress toward an original SCI paper.

<!-- 2026-06-19 tmem158 alphafold topology context -->
Decision: add AlphaFold/UniProt predicted topology context to strengthen TMEM158 membrane-protein plausibility while preserving the boundary that no ER localization or physical interaction has been demonstrated.

<!-- 2026-06-19 submission archive/source-data package -->
Decision: add a submission archive and source-data layer before any further ordinary bioinformatics expansion.

Reason: the current TMEM158/TAC_high public-data evidence already supports a bounded Scientific Reports-style discovery manuscript. The practical gap is traceability of figures, source tables and repository files. The new archive files improve editor/reviewer auditability without strengthening claims beyond public-data association.

<!-- 2026-06-19 standalone repository release package -->
Decision: keep a separate public repository-release ZIP instead of asking authors to upload the local Scientific Reports submission dry-run bundle.

Reason: the public repository should be reproducible and audit-friendly without redistributing publisher/full-text gate files, local raw caches, logs or self-referential upload archives.

<!-- 2026-06-19 scientific reports submission bundle dry run -->
Decision: treat the next machine-side finish line as a local Scientific Reports upload dry run rather than additional ordinary bioinformatics analysis.

Reason: evidence/readiness gates already support a bounded public-data manuscript; the remaining machine task is proving that manuscript, figure, source-data, supplement, repository and QC files can be collected into one auditable upload package.
<!-- 2026-06-19 structural follow-up prioritization targeted layer -->
Decision: add a bounded structural follow-up prioritization layer and avoid another full `run_all.R` rerun.

Reason: the useful next evidence layer is not more generic bioinformatics correlation but a defensible bridge between TMEM158 topology context and CAF-to-epithelial LR candidates. The output should guide POSTN/FN1/collagen-integrin and MIF-CXCR4 defined-partner/proximity assays while explicitly avoiding physical-interaction, receptor-activation or TMEM158-binding claims.

<!-- 2026-06-19 lr compartment expression audit targeted layer -->
Decision: add a bounded LR compartment-expression audit and continue avoiding full `run_all.R` reruns until final packaging.

Reason: structural follow-up candidates need an expression-feasibility check in the same single-cell compartment context. The audit supports POSTN/FN1-integrin follow-up prioritization but must not be used as proof of spatial communication, receptor activation, ligand causality or TMEM158 binding.

<!-- 2026-06-19 reviewer risk response pack -->
Decision: add reviewer-risk stress testing after machine bundle clearance.

Reason: for a pure public-data SCI submission, the strongest remaining machine-side need is not another weak data layer but a defensible, evidence-linked answer to predictable reviewer objections.
<!-- 2026-06-19 manuscript numeric consistency audit -->
Decision: add manuscript numeric consistency as a final machine QC layer before treating the submission package as internally coherent.

Reason: after many manuscript and evidence-layer regenerations, stale numeric claims are a realistic submission risk.

<!-- 2026-06-19 claim-boundary text audit -->

Decision: add automated claim-boundary text auditing before final submission.

Reason: the current manuscript is public-data-only and must avoid causal, prognostic, immune-suppression, spatial-validation, ligand-receptor-causality and therapy-resistance overclaims. A reproducible audit reduces drift across manuscript, supplement, README and submission files.

<!-- 2026-06-19 scientific reports citation coverage audit -->
Decision: treat inline citation coverage as a formal manuscript-readiness gate before final upload.

Reason: the manuscript already contains formal references; without numbered in-text citations, it does not meet Nature-style submission expectations.
<!-- 2026-06-19 scientific reports submission system fields -->
Decision: after machine bundle clearance, add a submission-system fields pack so final blockers are explicit and not confused with missing analysis artifacts. After author metadata was supplied, the remaining required blockers are publisher upload preview and final claim-boundary read; public code repository deposition is deferred by author decision before initial submission.
<!-- 2026-06-19 lr expression maintext integration targeted refresh -->
Decision: synchronize LR compartment-expression feasibility into manuscript and submission files using targeted downstream refresh only, not a full `run_all.R` rerun.

Reason: the changed layer is text, reviewer-risk, DOCX and submission-package synchronization. Upstream matrices, LR scoring and main figures were not changed. Targeted audits are the appropriate verification surface unless the final goal is complete and a full reproducibility rerun is being prepared.

Implementation note: `build_final_sci_submission_gap_audit.py` now accepts any positive DOCX page count with passing render metrics, instead of requiring exactly `17 pages`; this prevents false needs-review flags when manuscript length changes but layout QA still passes.

<!-- 2026-06-19 official scirep policy audit -->
Decision: treat official journal-policy audit and Reporting Summary preparation as the final machine-side submission-readiness layer.

Reason: journal instructions add non-biological requirements that can cause desk-return even when scientific figures are ready; these requirements must be separated from biological evidence.
