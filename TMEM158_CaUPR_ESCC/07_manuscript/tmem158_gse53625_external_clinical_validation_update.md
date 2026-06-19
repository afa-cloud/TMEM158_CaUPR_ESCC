# GSE53625 TMEM158/TAC External Clinical Validation

## Purpose

GSE53625 was added as a large external ESCC clinical calibration cohort for the TMEM158-associated TAC_high model. Probe sequences from a representative raw Agilent file were reannotated against GENCODE v19/v36 protein-coding transcripts, reusing the validated GSE53625 route from the earlier SMIM14 branch.

## Coverage

- Mapped target genes: 64 of 62.
- Probe-map target coverage: 64 of 67; missing probe targets: ORAI1, PDPN, TALDO1.
- Scored signature missing genes: ORAI1;PDPN.
- This is a targeted external clinical calibration layer, not full transcriptome reanalysis.

## Main Results

- Samples: 358 total; 179 tumours and 179 paired normals.
- TMEM158 paired tumour-normal median delta = 0.466; FDR=1.05e-05.
- Residual stress score paired delta = 0.109; FDR=0.019.
- ECM-integrin bridge score paired delta = 1.062; FDR=0.00e+00.
- TAC_high tumours: 60 of 179.
- TAC_high vs other residual stress median delta = 0.618; FDR=1.68e-09.
- TAC_high vs other ECM-integrin bridge median delta = 0.558; FDR=1.80e-17.
- Tumour-only TMEM158 Cox P=0.646; full TAC score Cox P=0.564; TAC_high indicator Cox P=0.776.

## Interpretation Boundary

This layer strengthens external clinical calibration because it tests TMEM158/TAC-like scores in an independent 179-pair ESCC cohort with survival annotations. It should be written as public-data external calibration. It must not be described as causal validation, clinical utility, treatment prediction, or definitive prognostic subtype validation.

## Outputs

- `05_figures/figure24_gse53625_tmem158_tac_external_validation.*`
- `02_data/processed/tmem158_gse53625_clinical_sample_scores.csv`
- `02_data/processed/tmem158_gse53625_tumor_tac_scores_survival.csv`
- `04_results/validation/tmem158_gse53625_signature_coverage.csv`
- `04_results/validation/tmem158_gse53625_paired_tumor_normal_tests.csv`
- `04_results/validation/tmem158_gse53625_tac_state_contrasts.csv`
- `04_results/survival/tmem158_gse53625_survival_cox.csv`
