# TAC_high LR Compartment-Expression Audit

Generated: 2026-06-19 23:32:53

## Bottom Line

This audit checks whether prioritized TAC_high structural follow-up candidates show a compatible single-cell compartment-expression pattern in GSE160269: ligand signal in fibroblast/CAF pseudo-bulk and receptor signal in epithelial pseudo-bulk. It supports expression feasibility for follow-up prioritization, not physical cell-cell communication.

## Top Candidate Audit

| Rank | Candidate | Call | Fibroblast Ligand Median | Epithelial Receptor Median | Ligand Fibroblast-Epithelial | Receptor Epithelial-Fibroblast | LR FDR | Boundary |
|---|---|---|---|---|---|---|---|---|
| 1 | POSTN->ITGA5 | pass_expected_compartment_pattern | 1.753 | 0.094 | 1.735 | -0.382 | 0.033 | Expression feasibility only; this does not prove spatial contact, protein abundance, receptor activation, ligand causality or TMEM158 binding. |
| 2 | FN1->ITGA5 | pass_expected_compartment_pattern | 2.533 | 0.094 | 2.458 | -0.382 | 0.042 | Expression feasibility only; this does not prove spatial contact, protein abundance, receptor activation, ligand causality or TMEM158 binding. |
| 3 | POSTN->ITGB3 | candidate_requires_expression_boundary | 1.753 | 5.92e-04 | 1.735 | -0.013 | 0.039 | Expression feasibility only; this does not prove spatial contact, protein abundance, receptor activation, ligand causality or TMEM158 binding. |
| 4 | COL1A1->ITGA1 | candidate_requires_expression_boundary | 3.997 | 0.015 | 3.830 | -0.296 | 0.073 | Expression feasibility only; this does not prove spatial contact, protein abundance, receptor activation, ligand causality or TMEM158 binding. |
| 5 | POSTN->ITGB1 | pass_expected_compartment_pattern | 1.753 | 0.570 | 1.735 | -0.877 | 0.088 | Expression feasibility only; this does not prove spatial contact, protein abundance, receptor activation, ligand causality or TMEM158 binding. |
| 6 | COL3A1->ITGA1 | candidate_requires_expression_boundary | 3.619 | 0.015 | 3.569 | -0.296 | 0.088 | Expression feasibility only; this does not prove spatial contact, protein abundance, receptor activation, ligand causality or TMEM158 binding. |
| 7 | POSTN->ITGAV | pass_expected_compartment_pattern | 1.753 | 0.268 | 1.735 | -0.325 | 0.039 | Expression feasibility only; this does not prove spatial contact, protein abundance, receptor activation, ligand causality or TMEM158 binding. |
| 8 | COL1A2->ITGA1 | candidate_requires_expression_boundary | 3.805 | 0.015 | 3.729 | -0.296 | 0.083 | Expression feasibility only; this does not prove spatial contact, protein abundance, receptor activation, ligand causality or TMEM158 binding. |
| 9 | FN1->ITGB3 | candidate_requires_expression_boundary | 2.533 | 5.92e-04 | 2.458 | -0.013 | 0.088 | Expression feasibility only; this does not prove spatial contact, protein abundance, receptor activation, ligand causality or TMEM158 binding. |
| 10 | COL1A1->ITGB1 | pass_expected_compartment_pattern | 3.997 | 0.570 | 3.830 | -0.877 | 0.092 | Expression feasibility only; this does not prove spatial contact, protein abundance, receptor activation, ligand causality or TMEM158 binding. |
| 11 | MIF->CXCR4 | candidate_requires_expression_boundary | 2.438 | 0.019 | -0.596 | 0.013 | 0.039 | Expression feasibility only; this does not prove spatial contact, protein abundance, receptor activation, ligand causality or TMEM158 binding. |
| 12 | INHBA->ACVR2A | pass_expected_compartment_pattern | 1.052 | 0.028 | 0.981 | -0.010 | 0.088 | Expression feasibility only; this does not prove spatial contact, protein abundance, receptor activation, ligand causality or TMEM158 binding. |

## Interpretation

- `pass_expected_compartment_pattern` means the public single-cell pseudo-bulk layer supports ligand availability in fibroblast/CAF and receptor detectability in epithelial profiles.
- `pass_with_boundary` or `candidate_requires_expression_boundary` means the pair can remain as a candidate only with explicit expression caveats.
- Low epithelial receptor expression does not invalidate all follow-up, but it shifts priority toward spatial/protein validation and receptor-activation assays.

## Machine QC

- `generated_at`: 2026-06-19 23:32:53 (info) - Local system timestamp
- `input_files_missing`: 0 (pass) - All required LR and compartment-expression inputs are present
- `audited_top_structural_pairs`: 20 (pass) - Top structural follow-up pairs audited for compartment-expression feasibility
- `expected_compartment_pattern_pairs`: 11 (pass) - Pairs with fibroblast ligand and detectable epithelial receptor pattern
- `expression_boundary_pairs`: 9 (pass_boundary) - Pairs retained with expression or compartment caveats
- `top_pair`: POSTN->ITGA5 (pass) - The top structural candidate remains POSTN->ITGA5
- `direct_communication_claim`: not_made (pass) - The report explicitly avoids communication/activation/causality claims
- `machine_lr_compartment_expression_clearance`: pass (pass) - Pass means the expression-feasibility audit is complete and bounded

## Claim Boundary

This audit does not prove ligand-receptor communication, spatial adjacency, receptor activation, ligand causality, TMEM158 binding, ECM binding or Ca2/UPR pathway activation. It only verifies whether the nominated candidates have a compatible public single-cell compartment-expression pattern for follow-up.

Machine LR compartment-expression clearance: `pass`.
