# A TMEM158-associated Ca2/UPR-CAF stress ecology state defines proteostasis-linked adaptation in esophageal squamous cell carcinoma

Yang Haoshui^1 and Ma Yuqing^1*

^1 The First Affiliated Hospital of Xinjiang Medical University, Xinjiang Medical University, Urumqi, Xinjiang, China.

*Correspondence and requests for materials should be addressed to Ma Yuqing (yuqingm0928@126.com).

## Abstract

Calcium homeostasis, unfolded protein response (UPR) branch activity and stromal remodelling are incompletely integrated in esophageal squamous cell carcinoma (ESCC). We performed an axis-first public-data analysis to identify upstream candidates associated with Ca2/UPR stress ecology. TMEM158 emerged as a lead computational entry point, but not as a standalone prognostic biomarker. We defined TAC_high as the co-occurrence of high TMEM158-Ca2/PERK core score and high cancer-associated fibroblast (CAF) score. TAC_high was reproducible across four bulk ESCC cohorts and associated with proteostasis and survival-transcriptional readouts, while overall-survival analyses remained negative. Whole-transcriptome meta-analysis showed a dominant extracellular-matrix/CAF programme and CAF-adjusted residual MYC, oxidative phosphorylation, KEAP1/NFE2L2, chemical-stress and translation signatures. GSE53625 externally calibrated the expression state in 179 paired samples without validating prognosis. Independent single-cell analyses localized TAC_high meta-signatures to fibroblast/CAF pseudo-bulk profiles and nominated expression-feasible POSTN/FN1/collagen-integrin and MIF-CXCR4 candidate CAF-to-epithelial bridges. Public spatial source data supported a fibroblast-rich progression context. These results define a TMEM158-associated Ca2/UPR-CAF stress ecology state in ESCC as a public-data biological discovery candidate, while preserving an explicit boundary between association and causality.

## Keywords

Esophageal squamous cell carcinoma; TMEM158; calcium homeostasis; unfolded protein response; cancer-associated fibroblasts; public-data bioinformatics

## Introduction

Molecular studies of ESCC indicate that tumour progression is shaped by stress adaptation and tumour-microenvironment remodelling [1]. Calcium homeostasis and endoplasmic-reticulum stress are central to proteostasis, apoptosis and therapy-pressure responses in cancer [2,3]. The UPR is not a single linear pathway; PERK, IRE1 and ATF6 branches can diverge according to stress duration, cellular lineage and microenvironmental context [4]. Fibroblast biology provides a parallel framework for understanding how stromal programmes shape cancer-state phenotypes [5]. This branch-level complexity creates an opportunity for public multi-cohort analyses that move beyond generic ER-stress signatures and instead define reproducible tumour states.

Our previous SMIM14-focused public-data analysis did not support SMIM14 as a strong core driver, prognostic marker or treatment-resistance determinant. We therefore rebuilt the project around a Ca2/UPR axis-first strategy. Candidate prioritization selected TMEM158 as the lead computational upstream candidate, with CORO1C and several transporter/proteostasis-related genes retained as secondary program members. TMEM158 is a transmembrane protein with reported roles in senescence and non-ESCC cancer contexts but limited ESCC-specific Ca2/UPR literature overlap, making it suitable as an entry point for an axis-centred, public-data discovery study [6-8].

Here we asked whether TMEM158 marks a reproducible Ca2/UPR-CAF stress ecology state in ESCC. We deliberately avoided framing TMEM158 as a validated causal driver. Instead, we tested tumour-normal expression, Ca2/UPR branch coupling, CAF ecology, rule-based TAC_high state reproducibility, single-cell immune/stromal boundaries, TCGA multi-omics context and public protein/localization support.

## Results

### Figure 1. TMEM158 is elevated in several public ESCC tumour cohorts but is not a standalone clinical survival marker

TMEM158 was higher in tumour than normal samples in TCGA-ESCA/ESCC-compatible analysis (184 tumours, 13 normals; median difference 2.660; FDR=1.69e-4), GSE20347 (17 tumours, 17 normals; median difference 1.279; FDR=0.0382) and GSE26886 (9 tumours, 19 normals; median difference 3.830; FDR=0.00260). GSE45670 showed no significant tumour-normal shift (28 tumours, 10 normals; median difference 0.052; FDR=0.987), indicating that TMEM158 expression is not uniformly elevated across all platforms [1,9].

Consistent with a state-marker rather than a prognostic-biomarker interpretation, TCGA overall-survival models were negative. In ecology-state survival analyses, the TAC_high subtype term had HR=1.326 with FDR=0.982, and all tested continuous or grouped ecology-state models had FDR=0.982. TMEM158 should therefore not be presented as a validated OS prognostic marker.

### Figure 2. TMEM158 is associated with a Ca2/UPR-CAF ecology rather than a uniform Ca2 activation signal

Axis-first screening supported TMEM158 as the lead candidate for the Ca2/UPR-CAF programme. Candidate scoring incorporated public proteogenomic and molecular-subtype context for ESCC [10,11]. Cross-layer evidence showed a TCGA axis-CAF discovery rho of 0.668, GSE45670 validation rho of 0.475 and DepMap ESCC basal branch rho of 0.403. In the recomputed TMEM158 branch, TCGA tumour-internal correlations were positive for Ca2 axis, PERK-bias and CAF scores, with CAF representing the most stable ecological component.

The external pattern was not a simple universal Ca2 activation model. GSE45670 showed positive CAF coupling but a negative Ca2-axis correlation, and smaller GEO cohorts had heterogeneous Ca2/UPR branch directions. These findings motivated a branch-state and ecology-state model instead of a single-direction pathway claim.

### Figure 3. A rule-defined TAC_high state is reproducible across bulk ESCC cohorts

We defined TAC_high as the rule-based state in which a sample was high for the TMEM158-Ca2/PERK core and high for CAF score within its cohort. This definition was chosen because it is interpretable, tied to the biological model and reproducible across cohorts. Gene-set and cohort-level score construction followed standard single-sample pathway-scoring and batch-aware expression-analysis principles [12,13]. The TAC_high state was present in all four bulk cohorts: GSE20347 (n=5), GSE26886 (n=4), GSE45670 (n=8) and TCGA (n=58).

Compared with all other rule-defined states, TAC_high was associated with higher proteostasis score by signed meta-analysis (signed z=2.841, meta-FDR=0.0113, two FDR-positive cohorts) and higher cell-survival transcriptional score (signed z=2.490, meta-FDR=0.0213, two FDR-positive cohorts). Drug-efflux score showed a meta-positive but less replicated boundary signal (signed z=4.079, meta-FDR=2.26e-4, one FDR-positive cohort).

### Figure 4. Composite TMEM158-CaUPR-CAF scoring improves the biological-state signal

Composite ecology scores were more informative than TMEM158 alone. The full TMEM158-CaUPR-CAF high-vs-low contrast was replicated-positive for proteostasis score (signed z=3.639, meta-FDR=0.00214, two FDR-positive cohorts). This result supports the manuscript's central claim: the discovery is a composite stress ecology state, not a conventional single-gene prognostic signature.

We further tested whether the TAC_high signal exceeded random state assignment within each cohort. Cohort-preserving permutation analysis showed the strongest specificity for drug-efflux transcriptional readout (weighted median delta=0.543, empirical two-sided P=0.00350, empirical FDR=0.0105). Proteostasis showed a positive but not FDR-confirmed specificity trend (delta=0.349, empirical two-sided P=0.0815, empirical FDR=0.122), whereas survival score was not random-label specific (delta=0.147, empirical two-sided P=0.434, empirical FDR=0.434). Component contrasts supported TAC_high above Axis_only for proteostasis and above TAC_low for survival and drug-efflux readouts. These data refine the biological interpretation toward a transport/efflux-proteostasis adaptation state rather than a validated clinical-survival subtype.

Unsupervised clustering did not provide a stronger main result. NMF was unavailable in the local R environment, and k-means fallback showed weak structure with negative silhouette quality. Therefore, the interpretable rule-defined TAC_high state is retained as the primary state model, while unsupervised clustering is treated as exploratory quality control.

### Extended Data Figure 2. TAC_high has a data-driven ECM/CAF transcriptome and a protein-biogenesis interaction signal

To reduce dependence on pre-specified score panels, we tested TAC_high using whole-transcriptome limma models within each bulk cohort followed by signed Stouffer meta-analysis [14]. TAC_high versus all other states was completed in four cohorts and produced a strong data-driven stromal programme. The leading meta genes included POSTN, COL6A3, COL1A2, TMEM158, CHST7, COL3A1, FAP, SULF1, COL1A1 and COL6A2. Gene-set enrichment was dominated by HALLMARK_EPITHELIAL_MESENCHYMAL_TRANSITION, extracellular-matrix organization, collagen formation, ECM proteoglycans and syndecan interactions [15,16].

We then modelled the interaction between core-high and CAF-high status to ask whether TAC_high exceeded the additive components of axis-high and CAF-high states. This interaction model was testable in three cohorts. It did not identify individual genes at FDR<0.10, so it should not be interpreted as a single-gene synergy signature. However, pathway-level analysis showed positive enrichment for translation, oxidative phosphorylation, MYC targets, rRNA processing, N-linked glycosylation and SRP-dependent cotranslational protein targeting to membrane. Custom gene sets were directionally supportive for ER proteostasis (FDR=0.033), PERK branch genes (FDR=0.081), CAF/ECM (FDR=0.082), TGF-beta CAF signalling (FDR=0.099) and drug-efflux transporters as a weaker boundary signal (FDR=0.148). These results refine the discovery as a CAF/ECM-dominant TAC_high state with a pathway-level protein-biogenesis/proteostasis interaction layer, not as a validated drug-resistance or survival subtype.

### Extended Data Figure 3. CAF-adjusted models separate stromal localisation from residual stress-state transcription

Because TAC_high explicitly includes a CAF-high component, we added a stromal-confounding stress test. At the score level, TAC_high compared with CAF_only after continuous CAF residualization did not retain FDR-confirmed proteostasis or drug-efflux differences (proteostasis meta-FDR=0.410; drug-efflux meta-FDR=0.332). This result prevents overclaiming that the score-level proteostasis or efflux signals are independent of CAF abundance. However, continuous core-axis score retained a CAF-adjusted positive association with drug-efflux score (meta-FDR=0.00435), supporting a narrower axis-linked transport readout after accounting for CAF.

At the whole-transcriptome level, limma models that included continuous CAF score and TAC_high status were completed in all four bulk cohorts, covering 12,380 genes and 238 tumour samples. After CAF adjustment, TAC_high retained 1,944 positive and 672 negative meta-FDR<0.10 genes. The leading positive genes included CHST7, TMEM158, PTDSS1, MAFG, ABCC1, NFE2L2, TALDO1, OSGIN1 and TOMM22. Pathway enrichment shifted away from the unadjusted ECM/CAF programme toward MYC targets, cell cycle, oxidative phosphorylation, mTORC1 signalling, cellular response to chemical stress, KEAP1/NFE2L2 signalling and translation. Custom CAF/ECM was no longer FDR-positive after adjustment (FDR=0.374), and custom ER-proteostasis and drug-efflux modules were also not FDR-positive as predefined sets (FDR=0.290 and 0.254). This analysis supports a two-layer interpretation: TAC_high is tissue-localized within a CAF/ECM ecology, but after adjusting for continuous CAF abundance it retains a residual proliferation, oxidative-metabolic, NFE2L2/chemical-stress and protein-biogenesis programme. It still does not prove tumour-cell-intrinsic causality.

### Extended Data Figure 4. GSE53625 externally calibrates the TMEM158/TAC_high state in a 179-pair clinical cohort

We next tested whether the TMEM158/TAC_high interpretation could be observed in a larger external clinical ESCC cohort. GSE53625 provides 179 paired tumour-normal samples and 179 tumour samples with survival annotations, but its GPL18109 matrix requires probe-sequence reannotation. Using a targeted Agilent probe-to-GENCODE v19/v36 transcript matching workflow, we recovered 64 of 67 requested TMEM158/TAC target genes. The scored signatures were missing ORAI1 and PDPN, so GSE53625 was treated as external clinical calibration rather than full axis replication.

TMEM158 was significantly higher in tumours than paired normal tissues (paired median delta=0.466, FDR=1.05e-5). ECM-integrin bridge score was strongly tumour-elevated (paired delta=1.062, FDR<0.001), and the CAF-adjusted residual-stress score also increased modestly in tumours (paired delta=0.109, FDR=0.019). In tumour-only state analysis, 60 of 179 tumours met the TAC_high-like rule. TAC_high-like tumours showed higher ECM-integrin bridge score than other tumours (delta=0.558, FDR=1.80e-17), higher residual-stress score (delta=0.618, FDR=1.68e-9), higher proteostasis score (delta=0.758, FDR=1.96e-12) and higher CAF score (delta=0.687, FDR=1.62e-18). Drug-efflux score was not higher in TAC_high-like tumours. Survival remained negative: continuous TMEM158 (P=0.646), full TAC score (P=0.564) and TAC_high status (P=0.776) were not associated with overall survival. Thus, GSE53625 independently supports the expression-state and ECM/residual-stress calibration of TAC_high while reinforcing that the manuscript should not be written as a prognostic-subtype paper.

### Figure 5. Multi-omics context argues against simple genomic or methylation-driven explanations

TCGA/cBioPortal multi-omics analysis matched 184 TCGA samples, including 181 copy-number values, seven TMEM158 methylation probes and zero TMEM158 mutation records [17,18]. TMEM158 copy number was not consistent with a simple amplification-driven model. TMEM158_log2CNA was negatively correlated with TMEM158 expression (rho=-0.237, FDR=0.00530) and with the full-axis ecology score (rho=-0.264, FDR=0.00252). Promoter methylation was positively, not negatively, correlated with TMEM158 expression (rho=0.182, FDR=0.0406) and with the full-axis ecology score (rho=0.177, FDR=0.0426).

These results do not identify the upstream regulatory mechanism of TMEM158. They instead exclude simple overinterpretations: TAC_high is unlikely to be explained by frequent TMEM158 mutation, straightforward amplification-driven overexpression or classic promoter-methylation silencing.

### Figure 6. Single-cell and public protein context define the biological boundary of TAC_high

In GSE160269 single-cell pseudo-bulk data, rule-defined TAC_high could be mapped across 60 matched tumour samples (TAC_high=14, Axis_only=16, CAF_only=16, TAC_low=14). However, TAC_high was not accompanied by robust immune-suppression signals after FDR correction. Treg score, suppressive-myeloid score, inflammatory-myeloid score, T-cell exhaustion score and T-cell cytotoxicity score all had FDR=0.938. Thus, TAC_high should not be described as a T-cell exhaustion or suppressive-myeloid state [19].

We next asked whether the data-driven TAC_high meta-signatures were preferentially localized to tumour epithelial, fibroblast/CAF, T-cell or myeloid compartments. From raw GSE160269 single-cell matrices, 392 unique TAC_high signature genes were extracted and scored across 60 tumour samples. All three tested signatures were fibroblast-dominant. Fibroblast scores were higher than epithelial, myeloid and T-cell scores in all nine paired Fibroblast-vs-other comparisons at FDR<0.10. The strongest TAC_high sample-state contrast was observed for the TAC_high-positive top50 signature in fibroblasts (delta=0.371, FDR=0.003). This result independently supports a CAF/ECM-dominant interpretation of TAC_high and argues against presenting TAC_high as a purely tumour-cell-intrinsic transcriptional state.

Because the TAC_high programme localized to fibroblast/CAF pseudo-bulk profiles, we performed a conservative candidate CAF-to-epithelial ligand-receptor bridge analysis. We curated 82 interpretable CAF ligand and epithelial receptor pairs spanning ECM-integrin, laminin-integrin, TGF-beta/activin, IL6-family, chemokine, MIF/SPP1, growth-factor and developmental axes. Twelve pairs were higher in TAC_high at FDR<0.10, led by POSTN->ITGA5 (delta=0.921, FDR=0.033), POSTN->ITGAV, POSTN->ITGB3, POSTN->ITGB1, FN1->ITGA5, collagen->ITGA1/ITGB1 pairs, INHBA->ACVR2A and MIF->CXCR4. At pathway level, ECM-integrin (delta=0.269, FDR=0.044) and MIF/SPP1 (delta=0.304, FDR=0.090) were higher in TAC_high. A follow-up compartment-expression audit of the top 20 structural candidates found 11 pairs with the expected fibroblast-ligand and detectable epithelial-receptor pattern. POSTN->ITGA5 and FN1->ITGA5 passed this expression-feasibility check; for POSTN->ITGA5, fibroblast POSTN median expression was 1.753, epithelial ITGA5 median expression was 0.094 and the LR score FDR was 0.033. Because ITGA5 was detectable but not epithelial-specific, these results support expression-feasible bridge prioritization rather than receptor activation or physical communication. IL6-family and growth-factor axes were not TAC_high-higher and should not be used as broad support.

To test whether the CAF/ECM localization was specific to GSE160269, we added an independent therapy-context single-cell validation layer from GSE221561 [20]. The existing raw archive allowed partial recovery of 7 of 11 listed libraries; four gzip members remained corrupted and were retained as a boundary. All 124 requested TMEM158/TAC_high/ECM-integrin target genes were covered in the parsed libraries. Among six tumour libraries with paired epithelial and fibroblast pseudo-bulk profiles, the TAC meta-ECM programme again localized most strongly to fibroblasts. Fibroblast-versus-epithelial TAC meta-ECM delta was 3.149 (paired Wilcoxon P=0.031), and the highest subtype-level TAC meta-ECM scores were observed in fibroblast subclusters, led by Fib-MMP1, Fib-MKI67, Fib-CFD, Fib-HTRA1, Fib-MCAM and Fib-ACTA2. A matched TAC-like context score correlated descriptively with the ECM-integrin bridge score (rho=0.371, P=0.468, n=6) and more strongly with epithelial proteostasis score (rho=0.943, FDR=0.029). This layer provides independent single-cell support for the CAF/ECM localization of TAC_high, but not statistical proof of ligand-receptor signalling or therapy resistance.

We next added a public spatial progression source-data calibration layer from a Nature Communications 2023 ESCC spatial whole-transcriptome study [21]. The public Source Data did not contain the complete WTA expression matrix, so TMEM158, Ca2/UPR and TAC_high could not be directly rescored in spatial ROIs. However, the published DSP and IF source tables supported a fibroblast-rich progression context: DSP fibroblast abundance increased across histological stages (ESCC-minus-NE median delta=3.297; stage-trend rho=0.789; FDR<0.001), and alpha-SMA fibroblast IF also increased from NE to ESCC (delta=13.891; stage-trend rho=0.639; FDR<0.001). This source-data layer supports the tissue-level plausibility of a CAF/ECM-rich ESCC progression context, but remains a calibration layer rather than direct spatial validation of TAC_high or TMEM158 causality.

Official public protein/context resources supported TMEM158 as a measurable membrane-protein candidate [22-24]. UniProt annotated TMEM158 as reviewed accession Q8WZ71, Transmembrane protein 158, 300 amino acids, with membrane and multi-pass membrane protein annotations. QuickGO/UniProt cellular-component evidence was limited to membrane (GO:0016020). HPA mapped TMEM158 to ENSG00000249992, classified it as a predicted membrane protein, provided protein-level evidence and listed an approved IHC antibody (HPA074974). HPA did not provide subcellular IF localization, reported protein tissue distribution as not detected and did not establish ESCC-specific protein validation. These findings support assayability and membrane-protein plausibility but not ER localization or Ca2/UPR causality.

AlphaFold Protein Structure Database analysis added predicted-structure support for this membrane-topology interpretation [25]. The canonical Q8WZ71 model covered residues 1-300 (model version 6) with global pLDDT 56.66. UniProt feature annotation defined two helical transmembrane regions at residues 231-251 and 273-293. The first segment had higher AlphaFold confidence (mean pLDDT 76.13), whereas the second segment remained low-confidence (mean pLDDT 43.96). Thus, AlphaFold strengthens the structural rationale that TMEM158 is a membrane-topology candidate with an interpretable C-terminal transmembrane region, but it does not establish direct ER localization, binding to Ca2/UPR proteins, interaction with ECM components, or ESCC-specific protein validation. This topology layer is therefore used to prioritize localization and interaction experiments rather than to infer a direct TMEM158-Ca2/UPR or TMEM158-ECM interface.

## Discussion

This study identifies TAC_high as a reproducible, rule-defined ESCC stress ecology state that links TMEM158, Ca2/PERK-core activity and CAF context to proteostasis and cell-survival transcriptional readouts. The main biological finding is not that TMEM158 alone is a prognostic biomarker, nor that TMEM158 directly activates Ca2/UPR signalling. Rather, TMEM158 provides a computational entry point into a broader Ca2/UPR-CAF ecology that is reproducible across public cohorts and biologically interpretable.

The TAC_high result has several advantages over a conventional single-gene biomarker story. First, the state is constructed from mechanistically coherent layers: membrane/upstream candidate expression, Ca2/PERK branch activity and CAF ecology. Second, the proteostasis and cell-survival readouts are reproduced across independent bulk datasets. Third, negative and boundary layers are explicitly retained. Clinical OS was not significant in TCGA or in the larger GSE53625 external clinical calibration cohort; immune-exhaustion claims were not supported; independent single-cell compartment analysis in GSE160269 and GSE221561 localized the TAC_high/TAC meta-ECM programme mainly to fibroblast/CAF profiles rather than proving tumour-cell-intrinsic activation; cBioPortal data did not support simple mutation, amplification or methylation explanations; and public protein resources did not prove ER localization or ESCC-specific protein expression.

The whole-transcriptome layer further clarifies the nature of TAC_high. The state is not merely an abstract score-defined class: its data-driven programme is anchored by ECM and CAF genes such as POSTN, COL6A3, COL1A2 and FAP. At the same time, the interaction between Ca2/PERK-core-high and CAF-high status points to translation, oxidative phosphorylation, N-linked glycosylation and membrane-protein targeting pathways. CAF-adjusted models add an important stress test. They show that the strongest unadjusted ECM/CAF programme is partly stromal by design, but that TAC_high retains a CAF-adjusted transcriptome enriched for MYC, oxidative phosphorylation, mTORC1, KEAP1/NFE2L2, chemical-stress and translation programmes. The GSE53625 external clinical layer adds an orthogonal calibration surface: TMEM158, ECM-integrin bridge score and residual-stress score are tumour-elevated in 179 paired samples, and TAC_high-like tumours retain strong ECM-integrin, proteostasis and residual-stress differences, but OS remains negative. This result makes the paper more defensible than a simple CAF marker story, while also narrowing the score-level claims because CAF-adjusted TAC_high-versus-CAF_only proteostasis and drug-efflux contrasts are not FDR-confirmed. Single-cell ligand-receptor scoring and compartment-expression auditing link these observations through expression-feasible POSTN/FN1-integrin and boundary-ranked collagen-integrin and MIF-CXCR4 candidates between fibroblast/CAF and epithelial pseudo-bulk profiles, and GSE221561 independently places the TAC meta-ECM signal in fibroblast subpopulations. Public spatial-progression source data add a tissue-architecture calibration layer by showing fibroblast and alpha-SMA enrichment during ESCC progression. This pattern is biologically consistent with a tumour-stromal stress ecology in which CAF/ECM context is accompanied by residual epithelial stress, redox and protein-biogenesis programmes. It also imposes an important boundary: because the interaction model lacks FDR-significant single genes, CAF adjustment does not prove cellular origin, the GSE53625 validation is targeted rather than full-transcriptome, the ligand-receptor analysis is pseudo-bulk, epithelial receptor detectability does not prove receptor activation, GSE221561 bridge correlations are underpowered and the public spatial source data lack a full WTA matrix, the result should be framed as pathway-level transcriptional architecture and expression-feasible bridge hypotheses rather than definitive mechanistic interaction.

The literature boundary further supports this positioning. A VM-routed PubMed/PMC duplication gate found no PubMed title/abstract record directly combining TMEM158 aliases with ESCC, ESCC-Ca2/UPR, ESCC-CAF/stroma or ESCC-signature framing. PMC full-text XML scanning identified broader TMEM158 and TMEM-family cancer literature, including several exact-alias-near-ESCC contexts that require manual full-text and supplementary-table review before submission. Therefore, the novelty claim is deliberately centred on the ESCC-specific TAC_high state rather than on generic TMEM158 cancer biology.

These boundaries are important for positioning the manuscript. The study supports a public-data biological discovery hypothesis, suitable for a pure bioinformatics paper focused on stress-state ecology. It does not support treatment recommendations, causal pathway claims or clinical biomarker implementation. Future experimental work should test whether perturbing TMEM158 changes Ca2 dynamics, SOCE, PERK/IRE1/ATF6 branch proteins, proteostasis and CAF-interacting mediators in ESCC models.

## Limitations

This study used retrospective public datasets and is subject to database heterogeneity, batch effects, platform differences and incomplete clinical annotation. Some GEO cohorts are small, and TCGA-ESCA contains histological-mixing risk even when used as ESCC-compatible context. Survival analyses were underpowered for some state contrasts and did not support a clinical OS claim. GSE53625 provides a larger paired clinical cohort, but it required targeted probe-sequence reannotation and did not support OS prognostic claims; it should therefore be treated as external calibration, not clinical validation. CAF-adjusted transcriptome models reduce but cannot eliminate stromal-composition confounding, because expression matrices do not directly identify the cellular origin of each residual gene programme. Single-cell analyses used pseudo-bulk and compartment-level signature summaries and therefore cannot prove cell-cell causality, cellular origin of ligand-receptor signalling or tumour-cell-autonomous regulation. The compartment-expression audit confirms ligand and receptor detectability for prioritized candidates, but it does not establish spatial adjacency, protein abundance, receptor activation or physical communication. The GSE221561 validation layer had partial raw-library recovery and only six matched tumour libraries for epithelial-fibroblast bridge context; it was therefore interpreted as independent localization support, not as a definitive validation cohort. The spatial progression source-data layer used published graph-level DSP, IF and selected ROI marker tables rather than the restricted complete WTA matrix, so it cannot directly validate TMEM158, TAC_high or Ca2/UPR spatial activation. Public HPA/UniProt/QuickGO protein context is database-level evidence, not new protein validation. All findings are associations and computational hypotheses rather than experimentally validated mechanisms.

## Methods

### Study design

This study used only publicly available datasets and did not involve newly collected human specimens, animal experiments, or wet-lab experiments. The workflow was designed as a pure public-data, hypothesis-generating ESCC bioinformatics analysis.

### Candidate selection

The project was rebuilt from an axis-first regulator screen after the original SMIM14-core model failed to support strong causal or prognostic claims. Candidate scoring integrated TCGA axis-CAF discovery, GSE45670 validation, GSE160269 epithelial and CAF pseudo-bulk evidence, DepMap ESCC expression context, public proteogenomics coverage and PubMed novelty gates. TMEM158 was selected as the lead computational candidate, while CORO1C and selected transporter/proteostasis genes were retained as secondary program members.

### Bulk expression and score analysis

Processed TCGA and GEO expression matrices from the existing project were reused. TMEM158 tumour-normal differences were tested within each cohort. Ca2-axis genes, UPR branch genes, CAF markers, proteostasis genes, cell-survival genes and drug-efflux genes were scored at the sample level using standardized expression summaries. Cohort-specific z-scores were used to reduce platform effects when constructing composite states.

### TAC_high state definition

Within each bulk cohort, TMEM158, Ca2-axis score, PERK-bias index and CAF score were standardized. The TMEM158-Ca2/PERK core was defined as the mean of z(TMEM158), z(Ca2-axis score) and z(PERK-bias index). Samples high for this core and high for CAF score were labelled TAC_high. Samples high only for the core were labelled Axis_only, samples high only for CAF were labelled CAF_only, and samples low for both were labelled TAC_low.

### Reproducibility and statistics

Within-cohort high-vs-low or subtype-vs-other comparisons used Wilcoxon tests when sample sizes were adequate. P-values were adjusted by Benjamini-Hochberg FDR. Cross-cohort evidence was summarized using signed Stouffer meta-analysis, weighted by effective sample size. A result was promoted as replicated-positive only when the signed meta-analysis was significant and at least two cohorts showed FDR-positive effects in the expected direction.

### Survival analysis

TCGA overall survival was analysed using Cox proportional hazards models for continuous ecology scores, grouped ecology scores and rule-defined subtypes. Survival was treated as a boundary and secondary readout because no tested term achieved FDR significance.

### Data-driven transcriptome programme analysis

Whole-transcriptome TAC_high models were fitted within each bulk cohort using limma. The first model compared TAC_high against all other rule-defined states. The second model used a core-high by CAF-high interaction term to test whether TAC_high exceeded additive core-axis and CAF components. Cohort-level statistics were combined using signed Stouffer meta-analysis. Gene-set enrichment used Hallmark, Reactome and custom Ca2/UPR/CAF/proteostasis/transport signatures against the combined gene-level statistics. The interaction analysis was interpreted at pathway level when no single gene reached FDR significance.

### CAF-adjusted TAC_high stress test

To test whether TAC_high was fully explained by stromal/CAF abundance, two CAF-adjusted analyses were added. First, sample-level proteostasis, survival, drug-efflux and UPR branch scores were standardized within cohorts and residualized against continuous CAF score. TAC_high was compared with TAC_low, CAF_only and Axis_only using Wilcoxon tests, and cross-cohort results were summarized by signed Stouffer meta-analysis. Linear models also tested continuous core-axis score and TAC_high status with continuous CAF score in the same model. Second, whole-transcriptome limma models were fitted within each bulk cohort using `expression ~ continuous CAF score + TAC_high status`. The TAC_high coefficient from each cohort was combined by signed Stouffer meta-analysis, followed by Hallmark, Reactome and custom gene-set enrichment. These analyses were interpreted as stromal-confounding stress tests, not as proof of tumour-cell-intrinsic causality.

### GSE53625 external clinical calibration

GSE53625 was analysed as an independent targeted clinical calibration cohort. Because the GPL18109 matrix uses numeric feature identifiers, a representative raw Agilent file was parsed to recover probe sequences. Targeted probe sequences for TMEM158, Ca2/UPR genes, CAF/ECM markers, proteostasis, survival, drug-efflux, ECM-integrin bridge and CAF-adjusted residual-stress genes were matched exactly against GENCODE v19 and v36 protein-coding transcripts. Matched probes were aggregated to gene symbols by mean log2 expression. Sample metadata were parsed from the GEO series matrix to identify paired tumour and normal tissues, survival time, death status and clinical covariates. Tumour-normal differences used paired Wilcoxon tests. Tumour-only TAC_high-like states were defined by median high TMEM158-Ca2/PERK core and median high CAF score within GSE53625 tumours. State contrasts used Wilcoxon tests with Benjamini-Hochberg FDR correction. Continuous TMEM158, full TAC score, TAC_high status and selected programme scores were tested by Cox proportional-hazards models. This cohort was interpreted as external clinical calibration because only targeted probe-reannotated genes were scored.

### Single-cell pseudo-bulk boundary analysis

GSE160269 pseudo-bulk scores were used to map rule-defined TAC_high states and test immune-context differences. Treg, suppressive-myeloid, inflammatory-myeloid, T-cell exhaustion and T-cell cytotoxicity scores were compared between TAC_high and all other rule-defined states with FDR correction.

For compartment localization, TAC_high-positive meta-signatures were built from the top positive genes of the bulk TAC_high-vs-other meta-analysis, and a separate exploratory core-by-CAF interaction signature was built from the top positive interaction statistics. Matching genes were extracted from raw GSE160269 epithelial, fibroblast, T-cell and myeloid single-cell matrices, summarized as tumour-sample pseudo-bulk means and scored with signed weighted gene-z summaries. Paired Wilcoxon tests compared fibroblast/CAF scores against the other compartments, and TAC_high-vs-other tests were performed within each compartment.

### CAF-to-epithelial ligand-receptor bridge analysis

To generate a bridge hypothesis without claiming causal cell-cell communication, we curated CAF-to-epithelial ligand-receptor pairs across ECM-integrin, laminin-integrin, TGF-beta/activin, IL6-family, chemokine, MIF/SPP1, growth-factor and developmental axes. Ligands were quantified in fibroblast pseudo-bulk profiles and receptors in epithelial pseudo-bulk profiles from raw GSE160269 matrices. For each pair, a ligand-receptor score was computed as the mean of standardized fibroblast ligand expression and standardized epithelial receptor expression. Pair-level and axis-level scores were compared between TAC_high and all other rule-defined states using Wilcoxon tests with FDR correction. Prioritized pairs were then audited for compartment-expression feasibility by checking fibroblast-ligand availability, epithelial-receptor detectability and whether the nominated receptor should be treated as epithelial-detectable rather than epithelial-specific. These analyses were interpreted as candidate bridge prioritization only.

### Independent GSE221561 single-cell therapy-context validation

To test whether the CAF/ECM localization was reproducible outside GSE160269, we extracted TMEM158, Ca2/UPR, TAC_high meta-ECM, CAF/ECM, ECM-integrin bridge, MIF/CXCR4 bridge, proteostasis and immune-boundary genes from the public GSE221561 raw 10X archive. Existing raw files were parsed at gzip-member level; seven of eleven listed libraries were usable and four corrupted members were retained in QC. Target genes were summarized as cell-type and cell-subtype pseudo-bulk mean log1p expression values. TAC meta-ECM, CAF/ECM, ECM-integrin ligand, epithelial receptor, MIF/SPP1, proteostasis and immune-boundary scores were computed from standardized gene summaries. Matched paired Wilcoxon tests compared fibroblast pseudo-bulk scores against epithelial, T-cell, myeloid and endothelial compartments within tumour libraries. Because only six tumour libraries had matched epithelial and fibroblast profiles, bridge correlations were treated as descriptive external context.

### Public spatial progression source-data calibration

To add tissue-architecture context without claiming new spatial experiments, we downloaded the public Source Data XLSX from Liu et al., Nature Communications 2023, an ESCC spatial whole-transcriptome progression study. The workbook was parsed with a reproducible Python helper to extract published DSP cell-deconvolution values, macrophage subtype scores, alpha-SMA/CD68 IF quantification and selected ROI marker expression tables. Because the complete WTA matrix was not present in the public Source Data, TMEM158, Ca2/UPR scores and TAC_high signatures were not directly rescored in spatial ROIs. Stage trends from NE, LGIN, HGIN and ESCC were tested using Spearman correlation against ordinal stage rank, Kruskal-Wallis tests across stages and ESCC-versus-NE Wilcoxon tests when both groups were available. FDR correction was applied across extracted source-data features.

### Multi-omics and public protein context

TCGA/cBioPortal data were downloaded for TMEM158 RNA, GISTIC copy number, log2 copy number, mutations and methylation probes. Spearman correlations tested whether TMEM158 expression or ecology scores were explained by simple copy-number or promoter-methylation patterns. UniProt, QuickGO and HPA official resources were queried for protein identity, localization terms, HPA antibody context and public protein/RNA evidence. AlphaFold Protein Structure Database records for Q8WZ71 were queried through the official EBI API. The canonical model, per-residue pLDDT confidence file and UniProt feature table were used to summarize model coverage, confidence fractions, transmembrane-feature positions, segment-level pLDDT and sequence hydropathy. The analysis was interpreted as predicted structural/topology context only, not as evidence of physical interaction or localization in ESCC.

### AI-assisted drafting and code support

AI-assisted tools were used to support drafting, code generation, formatting and internal consistency checks. The human author(s) remain responsible for reviewing and approving all analyses, generated text, code, figures and interpretations before submission. AI-assisted tools were not treated as authors and did not generate new data.

### Literature duplication gate

PubMed and PMC E-utilities were queried through a UTM VM route for TMEM158, HBBP, p40BBp, p40BBP, transmembrane protein 158, ENSG00000249992 and guarded RIS1 aliases combined with ESCC, Ca2/UPR, CAF/stroma and signature-related terms. PMC full-text XML records were further scanned for exact alias and ESCC term proximity. The gate was used to define novelty boundaries and manual review requirements; it was not treated as biological evidence.

## Figure legends

The submission-facing figure package is organized as six automatically generated composite main figures. The panel map is provided in `06_tables/tmem158_main_figure_panel_map.csv`, and full package legends are provided in `07_manuscript/main_figure_package_legends.md`.

**Main Figure 1. TMEM158 discovery and Ca2/UPR-CAF state entry point.** TMEM158 is tumour-elevated in multiple public ESCC cohorts and is coupled to Ca2/UPR and CAF ecology, supporting an axis-first lead-candidate framework rather than a standalone prognostic marker.

**Main Figure 2. Rule-defined TAC_high bulk state and specificity.** The composite TAC_high state is reproducible across bulk cohorts and has stronger biological-state support than TMEM158 alone, while preserving negative survival boundaries.

**Main Figure 3. Data-driven TAC_high transcriptome and CAF-adjusted residual stress.** Whole-transcriptome and CAF-adjusted analyses separate the dominant ECM/CAF programme from a residual MYC/OXPHOS/NFE2L2/translation stress-state programme.

**Main Figure 4. GSE53625 external clinical calibration.** Targeted probe-sequence reannotation in GSE53625 calibrates TMEM158/TAC_high expression-state, ECM-integrin and residual-stress signals in 179 paired clinical samples, but does not validate OS prognosis.

**Main Figure 5. Single-cell fibroblast localization and candidate CAF-to-epithelial bridge.** Raw single-cell pseudo-bulk analysis localizes TAC_high meta-signatures to fibroblast/CAF compartments and nominates expression-feasible ECM-integrin and MIF/CXCR4 candidate bridges.

**Main Figure 6. Independent single-cell, spatial-context and immune-boundary layers.** GSE221561 and public spatial source data support fibroblast/CAF-rich tissue context, while immune and survival analyses define the negative claim boundaries.

**Figure 1. TMEM158 expression across public ESCC cohorts.** Tumour-normal comparisons in TCGA, GSE20347, GSE26886 and GSE45670. TMEM158 is elevated in three cohorts but not uniformly across all platforms.

**Figure 2. TMEM158 coupling with Ca2/UPR and CAF ecology.** Heatmap and correlation summaries show TMEM158 association with Ca2-axis, PERK-bias and CAF scores, with CAF-coupled ecology more stable than uniform Ca2 activation.

**Figure 3. Cross-cohort validation of composite TMEM158-CaUPR-CAF states.** State-level comparisons show that full TMEM158-CaUPR-CAF high status is associated with proteostasis and cell-survival transcriptional readouts.

**Figure 4. Rule-defined TAC_high ecology subtype.** TAC_high exists in all four bulk cohorts and shows replicated positive association with proteostasis and cell-survival scores, while clinical OS remains negative.

**Figure 5. TCGA/cBioPortal regulatory boundary.** TMEM158 mutation records are absent, and copy-number and methylation patterns do not support simple amplification-driven expression or promoter-methylation silencing.

**Figure 6. Single-cell and public protein boundary context.** GSE160269 pseudo-bulk data map TAC_high but do not support robust T-cell exhaustion or suppressive-myeloid enrichment. UniProt/QuickGO/HPA support TMEM158 membrane-protein plausibility and public antibody context, without direct ER localization or ESCC protein validation.

**Extended Data Figure 1. TAC_high state specificity.** Cohort-preserving random-label testing supports drug-efflux transcriptional specificity of TAC_high, with a directional proteostasis trend and non-specific survival score.

**Extended Data Figure 2. TAC_high whole-transcriptome programme.** TAC_high-vs-other meta-analysis identifies a dominant ECM/CAF/EMT programme, whereas the core-by-CAF interaction model supports pathway-level translation, oxidative phosphorylation, N-linked glycosylation and membrane-protein-targeting signals without FDR-significant single interaction genes.

**Extended Data Figure 3. CAF-adjusted TAC_high programme.** Continuous CAF adjustment shows that score-level TAC_high-versus-CAF_only proteostasis and drug-efflux differences are not FDR-confirmed, while CAF-adjusted transcriptome models retain MYC, oxidative phosphorylation, KEAP1/NFE2L2, chemical-stress and translation programmes. This supports a residual stress-state programme beyond simple CAF abundance without proving cellular causality.

**Extended Data Figure 4. GSE53625 external clinical calibration.** Targeted probe-sequence reannotation in 179 paired ESCC samples shows tumour-elevated TMEM158, ECM-integrin bridge and residual-stress scores. TAC_high-like tumours show higher ECM-integrin, proteostasis and residual-stress scores, while TMEM158, full TAC score and TAC_high status remain non-significant for OS.

**Extended Data Figure 5. Single-cell localization of TAC_high meta-signatures.** Raw GSE160269 compartment matrices localize TAC_high-positive and core-by-CAF interaction signatures most strongly to fibroblast/CAF pseudo-bulk profiles, supporting a CAF/ECM-dominant stress ecology interpretation.

**Extended Data Figure 6. Candidate CAF-to-epithelial ligand-receptor bridge.** Matched GSE160269 pseudo-bulk scoring nominates TAC_high-higher POSTN/collagen/FN1-integrin pairs and MIF->CXCR4, with ECM-integrin and MIF/SPP1 axes higher in TAC_high. Compartment-expression auditing supports POSTN->ITGA5 and FN1->ITGA5 as expression-feasible follow-up candidates, but this is not proof of ligand-receptor signalling, spatial contact or receptor activation.

**Extended Data Figure 7. Independent GSE221561 therapy-context single-cell validation.** Partial raw-library recovery from GSE221561 independently localizes TAC meta-ECM signal to fibroblast pseudo-bulk and fibroblast subclusters. This supports the CAF/ECM interpretation but remains underpowered for ligand-receptor or therapy-response claims.

**Extended Data Figure 8. Public spatial progression source-data calibration.** Published source data from an ESCC spatial whole-transcriptome progression study show increasing DSP fibroblast abundance and alpha-SMA fibroblast IF across histological progression. The complete WTA matrix is restricted and absent from the Source Data, so this figure supports a CAF-rich tissue context but does not directly validate TMEM158, TAC_high or Ca2/UPR spatial activation.

**Extended Data Figure 9. AlphaFold topology context for TMEM158.** The official AlphaFold Q8WZ71 model covers the 300-aa canonical sequence and supports an interpretable first C-terminal transmembrane segment, while the second UniProt transmembrane segment remains lower-confidence. This figure provides predicted topology rationale only and does not prove ER localization, physical interaction with Ca2/UPR nodes, ECM binding or ESCC protein validation.

## Data availability

All data analysed in this study were obtained from public resources, including TCGA/GDC or cBioPortal, GEO, DepMap-derived public resources, UniProt, QuickGO, the Human Protein Atlas and the AlphaFold Protein Structure Database [1,9,17,18,22-25]. No new patient-level dataset was generated in this study. Processed intermediate tables and analysis outputs are available in the public GitHub repository at https://github.com/afa-cloud/TMEM158_CaUPR_ESCC.

## Code availability

The reproducible workflow was implemented in `TMEM158_CaUPR_ESCC/03_scripts/R/run_all.R`, with helper scripts under `TMEM158_CaUPR_ESCC/03_scripts/R/` and `TMEM158_CaUPR_ESCC/03_scripts/Python/`. The code is publicly available in the GitHub repository at https://github.com/afa-cloud/TMEM158_CaUPR_ESCC.

## Ethics statement

All datasets used in this study were public and de-identified. No new human specimens, animal experiments or wet-lab experiments were performed, and no new ethics approval or informed consent was required for this secondary analysis.

## Funding

This research received no specific grant from any funding agency in the public, commercial or not-for-profit sectors.

## Author contributions

Y.H. conceived the study, curated the data, performed the formal analysis, investigation, methodology implementation, software workflow construction and visualization, and wrote the original draft. Y.H. reviewed and edited the manuscript. Y.M. supervised the study. No author received funding acquisition support for this work.

## Competing interests

The author(s) declare no competing interests.

## AI-assisted tool use

The authors used ChatGPT (OpenAI) and Codex for language editing, code assistance, and manuscript drafting. All scientific interpretations, analyses, and conclusions were reviewed and verified by the authors.

## Additional information

Yang Haoshui's ORCID is 0009-0008-6805-3893. The authors acknowledge the First Affiliated Hospital of Xinjiang Medical University and Xinjiang Medical University for academic support. Correspondence and requests for materials should be addressed to Ma Yuqing (yuqingm0928@126.com).

## References

1. The Cancer Genome Atlas Research Network. Integrated genomic characterization of oesophageal carcinoma. *Nature* 541, 169-175 (2017). doi:10.1038/nature20805.
2. Wang, M. & Kaufman, R. J. The impact of the endoplasmic reticulum protein-folding environment on cancer development. *Nature Reviews Cancer* 14, 581-597 (2014). doi:10.1038/nrc3800.
3. Cubillos-Ruiz, J. R., Bettigole, S. E. & Glimcher, L. H. Tumorigenic and immunosuppressive effects of endoplasmic reticulum stress in cancer. *Cell* 168, 692-706 (2017). doi:10.1016/j.cell.2016.12.004.
4. Hetz, C., Chevet, E. & Oakes, S. A. Proteostasis control by the unfolded protein response. *Nature Cell Biology* 17, 829-838 (2015). doi:10.1038/ncb3184.
5. Kalluri, R. The biology and function of fibroblasts in cancer. *Nature Reviews Cancer* 16, 582-598 (2016). doi:10.1038/nrc.2016.73.
6. Barradas, M. et al. Identification of a candidate tumor-suppressor gene specifically activated during Ras-induced senescence. *Experimental Cell Research* 273, 127-137 (2002). doi:10.1006/excr.2001.5434.
7. Fu, Y. et al. TMEM158 promotes pancreatic cancer aggressiveness by activation of TGFbeta1 and PI3K/AKT signaling pathway. *Journal of Cellular Physiology* 235, 2761-2775 (2020). doi:10.1002/jcp.29181.
8. Li, J. et al. TMEM158 promotes the proliferation and migration of glioma cells via STAT3 signaling in glioblastomas. *Cancer Gene Therapy* 29, 822-833 (2022). doi:10.1038/s41417-021-00414-5.
9. Barrett, T. et al. NCBI GEO: archive for functional genomics data sets--update. *Nucleic Acids Research* 41, D991-D995 (2013). doi:10.1093/nar/gks1193.
10. Li, L. et al. Integrative proteogenomic characterization of early esophageal cancer. *Nature Communications* 14, 1666 (2023). doi:10.1038/s41467-023-37440-w.
11. Jiang, G. et al. The integrated molecular and histological analysis defines subtypes of esophageal squamous cell carcinoma. *Nature Communications* 15, 8990 (2024). doi:10.1038/s41467-024-53164-x.
12. Hanzelmann, S., Castelo, R. & Guinney, J. GSVA: gene set variation analysis for microarray and RNA-seq data. *BMC Bioinformatics* 14, 7 (2013). doi:10.1186/1471-2105-14-7.
13. Johnson, W. E., Li, C. & Rabinovic, A. Adjusting batch effects in microarray expression data using empirical Bayes methods. *Biostatistics* 8, 118-127 (2007). doi:10.1093/biostatistics/kxj037.
14. Ritchie, M. E. et al. limma powers differential expression analyses for RNA-sequencing and microarray studies. *Nucleic Acids Research* 43, e47 (2015). doi:10.1093/nar/gkv007.
15. Subramanian, A. et al. Gene set enrichment analysis: a knowledge-based approach for interpreting genome-wide expression profiles. *Proceedings of the National Academy of Sciences of the United States of America* 102, 15545-15550 (2005). doi:10.1073/pnas.0506580102.
16. Liberzon, A. et al. The Molecular Signatures Database (MSigDB) hallmark gene set collection. *Cell Systems* 1, 417-425 (2015). doi:10.1016/j.cels.2015.12.004.
17. Cerami, E. et al. The cBio cancer genomics portal: an open platform for exploring multidimensional cancer genomics data. *Cancer Discovery* 2, 401-404 (2012). doi:10.1158/2159-8290.CD-12-0095.
18. Gao, J. et al. Integrative analysis of complex cancer genomics and clinical profiles using the cBioPortal. *Science Signaling* 6, pl1 (2013). doi:10.1126/scisignal.2004088.
19. Zhang, X. et al. Dissecting esophageal squamous-cell carcinoma ecosystem by single-cell transcriptomic analysis. *Nature Communications* 12, 5291 (2021). doi:10.1038/s41467-021-25539-x.
20. Yang, Z. et al. Single-cell sequencing reveals immune features of treatment response to neoadjuvant immunochemotherapy in esophageal squamous cell carcinoma. *Nature Communications* 15, 9103 (2024). doi:10.1038/s41467-024-52977-0.
21. Liu, X. et al. Spatial transcriptomics analysis of esophageal squamous precancerous lesions and their progression to esophageal cancer. *Nature Communications* 14, 4779 (2023). doi:10.1038/s41467-023-40343-5.
22. UniProt Consortium. UniProt: the Universal Protein Knowledgebase in 2023. *Nucleic Acids Research* 51, D523-D531 (2023). doi:10.1093/nar/gkac1052.
23. Binns, D. et al. QuickGO: a web-based tool for Gene Ontology searching. *Bioinformatics* 25, 3045-3046 (2009). doi:10.1093/bioinformatics/btp536.
24. Uhlen, M. et al. Tissue-based map of the human proteome. *Science* 347, 1260419 (2015). doi:10.1126/science.1260419.
25. Varadi, M. et al. AlphaFold Protein Structure Database in 2024: providing structure coverage for over 214 million protein sequences. *Nucleic Acids Research* 52, D368-D375 (2024). doi:10.1093/nar/gkad1011.
