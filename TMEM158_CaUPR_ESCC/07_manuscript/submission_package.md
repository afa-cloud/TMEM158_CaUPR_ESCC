# TMEM158-CaUPR-CAF ESCC Submission Package Draft

## 中文结果摘要

本分支不再把 TMEM158 写成单基因预后标志或已验证驱动因子，而是把论文中心放在 `TAC_high` 规则型应激生态状态：TMEM158-high、Ca2/PERK-core-high 与 CAF-high 共同出现。该状态在 4 个 bulk 队列均可定义，并与 proteostasis score 和 cell-survival transcriptional score 呈跨队列复现关联。全转录组 meta 显示 TAC_high-vs-other 主要是 ECM/CAF/EMT 程序，核心基因包括 POSTN、COL6A3、COL1A2、TMEM158 和 FAP；core-high x CAF-high 交互项没有单基因 FDR 阳性，但 pathway 层支持 translation、OXPHOS、MYC targets、N-linked glycosylation 和膜蛋白共翻译靶向。新增 CAF-adjusted stress test 显示，连续 CAF score 调整后，TAC_high 仍有 1,944 个正向 meta-FDR<0.10 基因，并转向 MYC targets、OXPHOS、KEAP1/NFE2L2、chemical stress 和 translation 程序；但自定义 CAF/ECM、ER-proteostasis 和 drug-efflux 模块不再 FDR 阳性，说明这层支持“CAF 生态定位 + 残余 stress/protein-biogenesis/redox 程序”，不支持肿瘤细胞内在因果。GSE53625 通过 targeted Agilent probe-sequence reannotation 补成 179 对 tumour-normal 的外部临床校准层，覆盖 64/67 个 TMEM158/TAC 目标基因；TMEM158、ECM-integrin bridge 和 residual-stress 在肿瘤中升高，TAC_high-like 肿瘤保留 ECM-integrin、proteostasis 和 residual-stress 差异，但 TMEM158、full TAC score 和 TAC_high status 对 OS 均不显著，因此它增强状态校准但不支持预后验证。GSE160269 原始单细胞区室签名定位显示 TAC_high meta-signatures 最强定位于 fibroblast/CAF pseudo-bulk，进一步支持 CAF/ECM-dominant stress ecology，而不是纯肿瘤细胞内在机制。进一步的 matched pseudo-bulk ligand/receptor bridge 分析显示 82 个候选 CAF-to-epithelial pairs 中 12 个 TAC_high-higher FDR 阳性，主信号为 POSTN/COL/FN1-integrin 和 MIF->CXCR4；ECM-integrin 与 MIF/SPP1 轴为正向，IL6-family 和 growth-factor 轴不是正向支持。新增 GSE221561 治疗背景单细胞外部验证解析 7/11 个 raw libraries，覆盖 124/124 个 TMEM158/TAC_high/ECM-integrin 目标基因；6 个 matched tumour libraries 中 TAC meta-ECM 信号最高仍为 fibroblast pseudo-bulk，Fibroblast vs Epithelial paired delta=3.149，P=0.031；但 bridge correlation 仅描述性。新增公开空间进展 Source Data 校准层显示 ESCC 进展中 DSP fibroblast abundance 与 alpha-SMA fibroblast IF 均显著上升，支持 CAF-rich tissue context；但完整 WTA 空间矩阵受控，不能直接重算 TMEM158/TAC_high 空间分数。TCGA 和 GSE53625 临床 OS 均阴性，GSE160269 单细胞 pseudo-bulk 不支持 T-cell exhaustion、Treg 或 suppressive-myeloid 强结论。cBioPortal 不支持简单 CNV 扩增或启动子甲基化沉默解释。UniProt/QuickGO/HPA 支持 TMEM158 作为膜蛋白候选和公共抗体背景，但不支持直接 ER 定位或 ESCC 蛋白验证。

## Ten English Title Options

1. A TMEM158-associated Ca2/UPR-CAF stress ecology state defines proteostasis-linked adaptation in esophageal squamous cell carcinoma
2. Public multi-cohort profiling identifies a TMEM158-linked Ca2/UPR-CAF stress ecology state in ESCC
3. A rule-defined TMEM158-Ca2/UPR-CAF state marks proteostasis adaptation in esophageal squamous cell carcinoma
4. Axis-first public-data screening identifies TMEM158 as a lead entry point into Ca2/UPR-CAF stress ecology in ESCC
5. TMEM158-associated branch-state remodeling links Ca2/UPR activity, CAF ecology and proteostasis readouts in ESCC
6. Defining a TMEM158-associated Ca2/PERK-CAF tumour ecology state in esophageal squamous cell carcinoma
7. Public transcriptomic and multi-omics evidence nominates TAC_high as a proteostasis-linked ESCC stress ecology state
8. A Ca2/UPR branch-state framework reveals a TMEM158-CAF proteostasis ecology in ESCC
9. TMEM158 marks a Ca2/UPR-CAF stress ecology state without robust clinical survival or immune-exhaustion claims in ESCC
10. Multi-cohort public-data discovery of a TMEM158-associated proteostasis ecology state in esophageal squamous cell carcinoma

## Recommended Title

A TMEM158-associated Ca2/UPR-CAF stress ecology state defines proteostasis-linked adaptation in esophageal squamous cell carcinoma

## Main Figure Set

1. `05_figures/main_figure1_tmem158_axis_discovery.*`
2. `05_figures/main_figure2_tac_high_bulk_state.*`
3. `05_figures/main_figure3_tac_high_transcriptome.*`
4. `05_figures/main_figure4_gse53625_clinical_calibration.*`
5. `05_figures/main_figure5_scrna_caf_bridge.*`
6. `05_figures/main_figure6_independent_context_and_boundaries.*`

Panel map and legends:

- `06_tables/tmem158_main_figure_panel_map.csv`
- `07_manuscript/main_figure_package_legends.md`

Extended evidence:

- `05_figures/figure12_tac_high_state_specificity.*` shows cohort-preserving random-label specificity testing. It supports drug-efflux transcriptional specificity, a directional proteostasis trend and non-specific survival score.
- `05_figures/figure13_tac_high_transcriptome_programs.*` shows data-driven TAC_high pathway programmes: ECM/CAF/EMT for TAC_high-vs-other and translation/OXPHOS/glycosylation/membrane-targeting for the core-by-CAF interaction model.
- `05_figures/figure14_tac_high_interaction_gene_heatmap.*` shows that the core-by-CAF interaction is pathway-level rather than single-gene FDR-confirmed.
- `05_figures/figure22_stromal_adjusted_tac_score_specificity.*` and `05_figures/figure23_stromal_adjusted_tac_transcriptome.*` stress-test stromal confounding. They show weak score-level CAF-adjusted TAC_high-vs-CAF_only specificity but strong CAF-adjusted transcriptome programmes including MYC, OXPHOS, NFE2L2/chemical stress and translation.
- `05_figures/figure24_gse53625_tmem158_tac_external_validation.*` adds a 179-pair GSE53625 external clinical calibration layer after targeted probe-sequence reannotation. It supports tumour-elevated TMEM158, ECM-integrin and residual-stress scores plus TAC_high-like ECM/proteostasis/residual-stress differences, but not OS prognostic validation.
- `05_figures/figure15_tac_high_scrna_signature_compartments.*` and `05_figures/figure16_tac_high_scrna_state_signature_mapping.*` show independent GSE160269 compartment localization of TAC_high meta-signatures, with fibroblast/CAF dominance and TAC_high-state elevation in fibroblast profiles.
- `05_figures/figure17_tac_high_caf_epi_lr_bridge.*` and `05_figures/figure18_tac_high_caf_epi_lr_axis_scores.*` show a candidate CAF-to-epithelial bridge dominated by POSTN/collagen/FN1-integrin pairs and a positive ECM-integrin axis in TAC_high; the companion compartment-expression audit supports expression feasibility but not signalling causality.
- `05_figures/figure19_gse221561_tac_context_validation.*` and `05_figures/figure20_gse221561_tac_subtype_signature_context.*` provide independent therapy-context single-cell support that TAC meta-ECM signal is fibroblast-dominant, while preserving partial-library and small-n boundaries.
- `05_figures/figure21_spatial_progression_source_context.*` provides public spatial-progression source-data context showing fibroblast and alpha-SMA enrichment from NE/LGIN/HGIN to ESCC; it is a CAF-rich tissue-context calibration layer, not direct TAC_high spatial rescoring.

## Submission Fields

Target-journal first pass:

- Primary formatting target: Scientific Reports Article.
- Targeted manuscript draft: `07_manuscript/manuscript_scientific_reports.md`.
- Editable targeted manuscript DOCX: `07_manuscript/manuscript_scientific_reports.docx`.
- Target strategy: `08_submission_strategy/target_journal_scientific_reports_strategy.md`.
- Submission checklist: `08_submission_strategy/scientific_reports_submission_checklist.md`.
- Cover letter draft: `08_submission_strategy/scientific_reports_cover_letter_draft.md`.
- Submission file manifest: `06_tables/scientific_reports_submission_file_manifest.csv`.
- Format QC: `04_results/qc/scientific_reports_format_qc.csv`.
- DOCX build/render QA: `04_results/qc/scientific_reports_docx_build_qc.csv`, `04_results/qc/scientific_reports_docx_qa.csv`, `04_results/qc/scientific_reports_docx_render_metrics.csv`.

BMC Cancer was not selected as the first target because its current official research-article guidance creates high risk for public-database-only bioinformatics manuscripts without biological validation.

### Study Type

Retrospective public-dataset bioinformatics analysis; no newly collected specimens, animal experiments or wet-lab experiments.

### Core Claim

TMEM158-associated TAC_high is a reproducible Ca2/UPR-CAF stress ecology state with a dominant ECM/CAF transcriptome, CAF-adjusted residual MYC/OXPHOS/NFE2L2/translation stress programme, GSE53625 external clinical calibration, fibroblast/CAF single-cell localization in GSE160269 and GSE221561, ECM-integrin candidate bridge, public spatial-progression CAF-rich context and a pathway-level protein-biogenesis/proteostasis interaction signal in ESCC.

### Claims Not Made

- TMEM158 is not claimed as a validated causal driver.
- TMEM158 is not claimed as a validated clinical prognostic marker.
- TAC_high is not claimed to drive T-cell exhaustion or myeloid immune suppression.
- TAC_high is not claimed as a cisplatin-resistance mechanism.
- TAC_high is not claimed as a purely tumour-cell-intrinsic programme.
- CAF-adjusted residual programmes are not claimed as proof of tumour-cell origin or TMEM158 causality.
- Candidate ligand-receptor bridges are not claimed as proven physical signalling or causality.
- Public spatial progression source data are not claimed as direct TMEM158/TAC_high spatial validation.
- Public protein context is not claimed as new IHC, IF, ER-localization or ESCC protein validation.

### Reviewer Risk Notes

- Main novelty depends on TAC_high as a state discovery, not on TMEM158 alone.
- Clinical survival is negative and should be discussed openly.
- Ca2 direction is not uniformly positive across all cohorts; use branch-state remodeling language.
- HPA protein tissue distribution is not detected; use TMEM158 protein context as assayability support only.
- Figure12-specificity results refine the claim: TAC_high is stronger as a transport/efflux-proteostasis adaptation state than as a clinical-survival subtype.
- Figure13-Figure14 transcriptome results refine the claim again: the strongest data-driven programme is ECM/CAF/EMT, while core-by-CAF interaction is pathway-level protein biogenesis/proteostasis, not a single-gene mechanistic synergy.
- Figure22-Figure23 add stromal-confounding stress tests. They strengthen originality by showing a CAF-adjusted residual MYC/OXPHOS/NFE2L2/translation programme, but they also downgrade score-level CAF-independent proteostasis and efflux claims.
- Figure24 adds a larger GSE53625 external clinical calibration layer, but it is targeted probe-reannotated rather than full-transcriptome and does not support OS prognostic claims. Do not write it as clinical validation.
- Figure15-Figure16 single-cell signature localization strengthens the CAF/ECM ecology claim but also limits the wording: avoid tumour-cell-autonomous or direct TMEM158-driving language.
- Figure17-Figure18 strengthen mechanism plausibility through ECM-integrin candidate bridging, while IL6-family and growth-factor axes are not TAC_high-higher support. Do not write broad cytokine or growth-factor activation.
- Figure19-Figure20 strengthen independent single-cell context through GSE221561, but this dataset has partial raw-library recovery and only six matched tumour libraries for bridge context. Do not write it as definitive validation, therapy-response proof or ligand-receptor causality.
- Figure21 adds a public spatial-progression context layer, but it uses graph-level Source Data rather than the complete WTA matrix. Do not write it as direct spatial validation of TMEM158, TAC_high, Ca2/UPR activation or ligand-receptor causality.

### Duplication Gate Status

Current label: **GO for novelty boundary; target-journal manuscript/DOCX package complete; final submission clearance still depends on author-level submission metadata and final upload preview**.

Latest submission-readiness audit: **9/10 gates pass**. Passing gates include reproducible full run, six composite main figures, manuscript sections, formal references, full-text/supplementary duplication gate, novelty decision, GSE53625 clinical calibration, claim-boundary checklist and data/code provenance. The only remaining non-pass gate is final submission clearance.

The formal VM-routed PubMed/PMC gate on 2026-06-19 found 0 PubMed title/abstract records for direct TMEM158-ESCC, TMEM158-ESCC-Ca2/UPR, TMEM158-ESCC-CAF/stroma, or TMEM158-ESCC-signature overlap. PMC full-text XML review resolved or boundary-classified 28/40 manifest items, local publisher/full-text scanning resolved 5 additional items, and curated context adjudication resolved the remaining 7 items. No manual publisher/full-text or supplementary-table items remain unresolved, and no direct TMEM158-ESCC TAC_high/Ca2/UPR/CAF duplication signal was detected.

Therefore, the paper should be framed as an ESCC-specific `TAC_high` stress-ecology state discovery, not as a generic TMEM158 biomarker or pan-cancer TMEM158 paper.
