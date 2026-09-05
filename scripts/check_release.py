#!/usr/bin/env python3
"""Skip deployment when the published site already contains both revisions."""
import argparse
import json
from pathlib import Path
import time
import urllib.error
import urllib.request
from build_site import version

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--book', type=Path, required=True)
parser.add_argument('--site', type=Path, default=Path(__file__).resolve().parents[1])
parser.add_argument('--url', required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
expected = version(args.site, args.book)
try:
    with urllib.request.urlopen(args.url.rstrip('/') + '/version.json?t=' + str(time.time_ns()), timeout=20) as response:
        published = json.load(response)
except (urllib.error.URLError, TimeoutError, ValueError):
    published = {}
changed = published.get('release') != expected['release']
with args.output.open('a') as output:
    output.write(f"changed={'true' if changed else 'false'}\n")
print('New release required' if changed else 'Published release is current')
