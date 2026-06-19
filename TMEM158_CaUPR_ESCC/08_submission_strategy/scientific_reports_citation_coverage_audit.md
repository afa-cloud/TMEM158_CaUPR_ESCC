# Scientific Reports Citation Coverage Audit

Generated: 2026-06-20 00:55:42

## Scope

This audit checks the current Scientific Reports manuscript for sequential square-bracket numeric references, full reference coverage, out-of-range citations and abstract citation leakage. It is a manuscript-quality-control layer only.

## Official Style Surface

- Scientific Reports submission guidelines: https://www.nature.com/srep/author-instructions/submission-guidelines
- Machine assumption used here: references should be numerical, sequential by first appearance and placed in square brackets.

## Summary

- Reference count: `25`
- Citation groups: `17`
- Unique cited references: `25`
- Uncited references: `none`
- Out-of-range citations: `none`
- First appearance order: `1;2;3;4;5;6;7;8;9;10;11;12;13;14;15;16;17;18;19;20;21;22;23;24;25`
- Abstract reference pattern: `none`
- Citation coverage clearance: `pass`

## Machine Interpretation

The manuscript has machine-clear citation coverage: all 25 references are cited, first appearances run sequentially from 1 to 25, no out-of-range citation numbers were detected and the abstract remains citation-free.

## Audit Table

| Check | Area | Observed | Status | Notes |
|---|---|---|---|---|
| references_section_present | reference_structure | present | pass | Manuscript must include a References section. |
| reference_count | reference_structure | 25 | pass | Numbered references detected after the References heading. |
| references_contiguous | reference_structure | 1;2;3;4;5;6;7;8;9;10;11;12;13;14;15;16;17;18;19;20;21;22;23;24;25 | pass | Reference list should be contiguous from 1 to N. |
| citation_groups_in_text | in_text_citations | 17 | pass | Square-bracket numeric citation groups detected before References. |
| unique_references_cited | in_text_citations | 1;2;3;4;5;6;7;8;9;10;11;12;13;14;15;16;17;18;19;20;21;22;23;24;25 | pass | Every reference in the list should be cited at least once. |
| uncited_references | in_text_citations | none | pass | Listed references without any in-text citation. |
| out_of_range_citations | in_text_citations | none | pass | In-text citation numbers that do not exist in the reference list. |
| first_appearance_order | numbering_order | 1;2;3;4;5;6;7;8;9;10;11;12;13;14;15;16;17;18;19;20;21;22;23;24;25 | pass | Nature-style numeric references should run sequentially by first citation. |
| abstract_reference_pattern | abstract | none | pass | Scientific Reports asks for an unstructured abstract without references. |
| citation_coverage_clearance | clearance | pass | pass | Pass requires cited references to cover all listed references, no out-of-range citations, sequential first appearance and no abstract references. |
