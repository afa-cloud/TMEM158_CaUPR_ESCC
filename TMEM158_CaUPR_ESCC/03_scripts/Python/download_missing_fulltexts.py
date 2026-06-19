#!/usr/bin/env python3
import argparse
import csv
import urllib.request
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--manifest', default='TMEM158_CaUPR_ESCC/01_literature/manual_download_manifest.csv')
parser.add_argument('--force', action='store_true')
parser.add_argument('--all', action='store_true', help='Try every manifest row, including rows already auto-reviewed.')
args = parser.parse_args()

manifest = Path(args.manifest)
project_root = Path.cwd()
failed = []

with manifest.open(newline='', encoding='utf-8') as handle:
    rows = list(csv.DictReader(handle))

for row in rows:
    status = row.get('download_status', '').strip()
    if not args.all and status and not status.startswith('manual_required'):
        continue
    url = row.get('url', '').strip()
    target_dir = project_root / 'TMEM158_CaUPR_ESCC' / row.get('target_relative_path', '').strip()
    target_dir.mkdir(parents=True, exist_ok=True)
    suffix = '.html'
    if url.lower().endswith('.pdf'):
        suffix = '.pdf'
    elif 'ncbi.nlm.nih.gov/pmc/' in url.lower():
        suffix = '.html'
    out = target_dir / (row.get('expected_filename', 'downloaded_file') + suffix)
    if out.exists() and out.stat().st_size > 0 and not args.force:
        print('skip existing', out)
        continue
    if not url:
        failed.append((row.get('item_id'), 'missing URL'))
        continue
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Codex manual fulltext downloader'})
        with urllib.request.urlopen(req, timeout=60) as response:
            data = response.read()
        out.write_bytes(data)
        print('downloaded', out, len(data), 'bytes')
    except Exception as exc:
        failed.append((row.get('item_id'), str(exc)))

if failed:
    print('\nFailed items:')
    for item_id, reason in failed:
        print(item_id, reason)
    raise SystemExit(1)
