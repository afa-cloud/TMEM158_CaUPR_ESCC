# TMEM158 Protein Topology Claim Audit

Generated: 2026-06-19 23:09:17

## Bottom Line

TMEM158 can be described as a reviewed membrane-protein candidate with public membrane/topology support and a predicted AlphaFold topology context. This strengthens biological plausibility and assayability, but it must not be written as direct ER localization, direct Ca2/UPR-protein binding, ECM binding, ESCC-specific protein validation or mechanism proof.

## Machine QC

- `generated_at`: 2026-06-19 23:09:17 (info) - Local system timestamp
- `input_files_missing`: 0 (pass) - All required protein/topology evidence tables are present
- `uniprot_quickgo_direct_er_term`: absent (pass_boundary) - Absence supports boundary that direct ER localization is not established
- `alphafold_global_plddt`: 56.66 (pass_boundary) - Moderate/low global confidence means no interaction-proof claim
- `alphafold_tm1_mean_plddt`: 76.13 (pass) - TM1 provides the strongest topology support
- `alphafold_tm2_mean_plddt`: 43.96 (pass_boundary) - TM2 is an annotated but lower-confidence segment
- `protein_audit_rows`: 9 (pass) - Evidence interpretation rows written
- `rows_needing_revision`: 0 (pass) - Machine-actionable issues in protein-topology audit
- `machine_protein_topology_claim_clearance`: pass (pass) - Use as topology/assayability support only; no ER, binding, ECM or ESCC protein validation claim

## Evidence Interpretation Table

| Layer | Evidence Item | Claim Status | Evidence Value | Allowed Claim | Disallowed Claim |
|---|---|---|---|---|---|
| UniProt | Reviewed protein identity | support | Q8WZ71; Transmembrane protein 158; 300 aa | Reviewed transmembrane-protein candidate and assayable public protein entry. | Experimentally validated ESCC protein expression or mechanism. |
| UniProt | Membrane/topology annotation | support_with_boundary | ; Multi-pass membrane protein | Membrane/multi-pass topology plausibility. | Direct ER localization or ER-resident functional mechanism. |
| QuickGO/UniProt | Cellular-component terms | boundary | UniProt:GO:0016020:membrane:IEA:UniProtKB-SubCell; QuickGO:GO:0016020::IEA | Public membrane cellular-component context. | Direct endoplasmic-reticulum localization. |
| HPA | Protein class and antibody context | context | Predicted membrane proteins; antibody=HPA074974; IH=Approved | Atlas-level antibody/IHC context for future validation planning. | New IHC validation, ESCC-specific protein validation or localization. |
| HPA | Protein and subcellular evidence boundary | boundary | protein tissue distribution=Not detected; IF main location=not available | A transparent protein-context limitation. | HPA-confirmed ER localization or ESCC TMEM158 protein expression. |
| AlphaFold DB | Canonical predicted model | support_with_boundary | AF-Q8WZ71-F1; coverage=1-300; model_version=6; global_plddt=56.66 | Predicted topology rationale and experiment prioritization. | High-confidence mechanism, binding or localization proof. |
| AlphaFold + UniProt | UniProt_Transmembrane_1 | support | 231-251; mean_pLDDT=76.13; hydropathy19=1.835; call=confident | Segment-level topology support, with confidence explicitly stated. | Specific Ca2/UPR or ECM protein interface. |
| AlphaFold + UniProt | UniProt_Transmembrane_2 | boundary | 273-293; mean_pLDDT=43.96; hydropathy19=1.255; call=very_low | Segment-level topology support, with confidence explicitly stated. | Specific Ca2/UPR or ECM protein interface. |
| Integrated claim ceiling | Direct ER / physical-interaction boundary | boundary | direct ER evidence=boundary; AlphaFold main_interpretation=AlphaFold/UniProt support membrane-topology plausibility, especially TM1, but do not prove ER localization or physical interaction | Localization, membrane fraction, proximity-labelling, co-IP and defined-partner co-modelling are justified as next experiments. | TMEM158 directly binds Ca2/UPR proteins, directly interacts with ECM components, or is ER-localized in ESCC. |

## Recommended Manuscript Wording

Acceptable: TMEM158 is a public, reviewed transmembrane-protein candidate with membrane/topology plausibility and AlphaFold-supported structural rationale for follow-up localization and interaction assays.

Avoid: TMEM158 is ER-localized, physically interacts with Ca2/UPR proteins, binds ECM components or has ESCC-specific protein validation.

## Practical Use

Use this layer to justify follow-up localization, membrane-fractionation, proximity-labelling, co-immunoprecipitation, crosslinking-MS or explicitly defined partner co-modelling. Do not use it to raise the claim ceiling of the public-data manuscript.

## Clearance

Machine protein-topology claim clearance: `pass`.
