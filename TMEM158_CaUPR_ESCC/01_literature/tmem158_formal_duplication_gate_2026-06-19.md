# TMEM158/TAC_high Formal Duplication Gate

Date: 2026-06-19

Status note: this formal gate records the first VM-routed PubMed/PMC stage. It has been superseded by the completed local scan and curated context adjudication recorded in `tmem158_literature_readiness_status.csv`, `downloaded_fulltext_local_scan_summary.md`, `manual_context_adjudication.csv`, `risk_of_duplication.md` and `novelty_statement.md`. Current status: GO for the bounded ESCC-specific TAC_high stress-ecology framing, manual_unresolved_items=0.

## Decision

Stage decision at the time: **Conditional GO for manuscript construction; not final submission clearance**.

The public-data manuscript could continue under the `TAC_high` Ca2/UPR-CAF stress-ecology framing at this stage. The gate did **not** support a generic TMEM158 biomarker paper. The later full-text/local/context adjudication layer resolved the remaining manual items without detecting a no-go duplicate.

## Route

- PubMed and PMC E-utilities were queried through the UTM VM route.
- PMC open full-text XML was retrieved through the UTM VM route.
- Scripts:
  - `03_scripts/Python/query_tmem158_duplication_gate_vm.py`
  - `03_scripts/Python/scan_tmem158_pmc_fulltext_vm.py`

## PubMed Title/Abstract Gate

| Query layer | Count |
|---|---:|
| TMEM158 aliases + ESCC | 0 |
| TMEM158 aliases + ESCC + Ca2/UPR | 0 |
| TMEM158 aliases + ESCC + CAF/stroma | 0 |
| TMEM158 aliases + ESCC + prognosis/immune/signature/multi-omics | 0 |
| TMEM158 aliases + pan-cancer + prognosis/immune/signature/multi-omics | 27 |
| TMEM158 aliases + cancer + Ca2/UPR | 0 |
| TMEM158 aliases + cancer + CAF/stroma | 7 |
| TMEM158/TMEM review-like records | 3 |

Interpretation: there is no PubMed title/abstract evidence of a direct TMEM158-ESCC or TMEM158-ESCC-Ca2/UPR/CAF paper. There is substantial non-ESCC TMEM158 cancer literature.

## PMC Full-Text Index Gate

The initial PMC index returned many hits because full-text search captures review text, reference lists, abbreviation collisions and unrelated sections. The final query split exact TMEM158 aliases from guarded RIS1 aliases.

| PMC query layer | Count |
|---|---:|
| Exact TMEM158 aliases + ESCC | 67 |
| Exact TMEM158 aliases + ESCC + Ca2/UPR | 34 |
| Exact TMEM158 aliases + ESCC + CAF/stroma | 49 |
| Exact TMEM158 aliases + ESCC + signature/prognosis/immune | 67 |
| Guarded RIS1 + ESCC | 6 |
| Guarded RIS1 + ESCC + Ca2/UPR | 5 |
| Guarded RIS1 + ESCC + CAF/stroma | 6 |

Interpretation: PMC index hits require term-level review rather than direct rejection. The index does not distinguish an ESCC-focused TMEM158 paper from a broad review or unrelated reference section.

## PMC Full-Text XML Term Scan

The first 39 unique PMC records from the gate were fetched and scanned as full-text XML.

| Scan class | Count |
|---|---:|
| Records scanned | 39 |
| Records with exact TMEM158 alias | 33 |
| Exact alias and ESCC anywhere in the same article | 19 |
| Exact alias near ESCC within the scan window | 6 |
| High-priority manual review: exact alias near ESCC context | 6 |
| Exact alias and ESCC in same article but not near | 13 |
| Exact alias non-ESCC/review context | 14 |
| RIS1-only noise or legacy context | 1 |
| No alias after XML fetch | 2 |
| XML fetch failed and needs manual file review | 3 |

High-priority manual-review records:

| PMC ID | Title | Current interpretation |
|---|---|---|
| PMC9395270 | TMEM158 promotes the proliferation and migration of glioma cells via STAT3 signaling in glioblastomas | Non-ESCC TMEM158 functional cancer paper; inspect for hidden ESCC comparison/reference context. |
| PMC12530797 | Research progress on TMEM proteins in cancer progression and chemoresistance | TMEM review; must inspect TMEM158 and ESCC sections before final submission. |
| PMC9663988 | TMEM158 expression is negatively regulated by AR signaling and associated with favorite survival outcomes in prostate cancers | Non-ESCC TMEM158 cancer paper; inspect reference/context. |
| PMC11491687 | CH25H Promotes Autophagy and Regulates the Malignant Progression of Laryngeal Squamous Cell Carcinoma Through the PI3K-AKT Pathway | Laryngeal squamous context; likely signature/reference overlap, not direct ESCC. |
| PMC9351901 | The analysis of tumor-infiltrating immune cell and ceRNA networks in laryngeal squamous cell carcinoma | Laryngeal immune-network context; likely signature/reference overlap, not direct ESCC. |
| PMC12505563 | Emerging role of cancer-associated fibroblasts in the premetastatic niche | Broad CAF review; TMEM158 appears as a CAF/tCAF marker context. |

Manual-required XML failures:

| PMC ID | Title |
|---|---|
| PMC12857762 | The Spatiotemporal Heterogeneity of Tumor-Associated Stromal Cells: Reprogramming Plasticity to Unlock Precision Cancer Immunotherapy |
| PMC7295848 | Role of PI3K/AKT pathway in cancer: the framework of malignant behavior |
| PMC12559857 | Cancer-Associated Fibroblasts: Origin, Classification, Tumorigenicity, and Targeting for Cancer Therapy |

## Novelty Interpretation

The defensible novelty is **not** TMEM158 as a generic cancer biomarker. That territory is already crowded by pancreatic, ovarian, gastric, glioma, prostate, breast, lung, laryngeal and pan-cancer/TMEM-family literature.

The defensible novelty remains:

> A rule-defined ESCC `TAC_high` state linking TMEM158-high, Ca2/PERK-core-high and CAF-high biology to reproducible proteostasis and cell-survival transcriptional readouts, with explicit negative boundaries for clinical survival, immune exhaustion, cisplatin resistance, CNV/methylation causality and ER/protein validation.

## Required Boundary In Manuscript

- Do not claim TMEM158 is a validated ESCC driver.
- Do not claim TAC_high is a prognostic subtype.
- Do not claim TAC_high drives T-cell exhaustion, suppressive myeloid cells or Tregs.
- Do not claim cisplatin-resistance causality.
- Do not describe UniProt/HPA evidence as direct ER localization or ESCC protein validation.
- Cite broader TMEM158 cancer and CAF/tCAF literature as background and distinction.

## Remaining Before Final Submission

The final submission gate remains incomplete until:

1. The 6 high-priority PMC records are manually inspected for main-text, table and supplementary-table overlap.
2. The 3 failed XML records are downloaded or opened and searched.
3. Supplementary files from the manual manifest are searched for TMEM158, RIS1, HBBP, p40BBp, p40BBP and ENSG00000249992.
4. The final label is upgraded to GO, retained as Conditional GO or downgraded.

Generated support files:

- `01_literature/tmem158_duplication_gate_status.csv`
- `01_literature/tmem158_pubmed_pmc_duplication_counts.csv`
- `01_literature/tmem158_pubmed_pmc_duplication_records.csv`
- `01_literature/tmem158_pmc_fulltext_scan_status.csv`
- `01_literature/tmem158_pmc_fulltext_term_scan.csv`
- `01_literature/tmem158_pmc_fulltext_context_hits.csv`
- `01_literature/manual_download_manifest.csv`
- `01_literature/manual_download_instructions.md`
