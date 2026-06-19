# Manual Download / Audit Instructions For TMEM158 Duplication Gate

The automated VM PubMed/PMC gate and the follow-up local/curated context audit are complete for the current manifest.

Manifest:

- `TMEM158_CaUPR_ESCC/01_literature/manual_download_manifest.csv`

Target folder:

- `TMEM158_CaUPR_ESCC/01_literature/fulltext_gate_files/`

Number of manual items:

- 0 currently unresolved

Current status:

- 40 manifest items total
- 28 items auto-reviewed through VM-routed PMC XML
- 5 local publisher/text/full-text items reviewed
- 7 curated context adjudications
- 0 manual publisher/supplement items unresolved
- Direct TMEM158-ESCC TAC_high/Ca2/UPR/CAF duplicate: none detected

## How to rerun the fallback downloader if new items appear

From the project root:

```sh
python3 TMEM158_CaUPR_ESCC/03_scripts/Python/download_missing_fulltexts.py
```

To retry existing items:

```sh
python3 TMEM158_CaUPR_ESCC/03_scripts/Python/download_missing_fulltexts.py --force
```

If a future rerun adds publisher pages or supplementary files that require browser/proxy access, manually download PDFs, HTML pages, XLS/XLSX/DOCX/ZIP supplements into the listed `target_relative_path` folders.

After downloading future missing items, tell Codex: `已下载，继续审查`.

Codex will then verify file sizes/readability and search the files for:

- TMEM158
- RIS1
- HBBP
- p40BBp / p40BBP
- ENSG00000249992
- TAC_high
- Ca2 / UPR / CAF / ESCC terms
