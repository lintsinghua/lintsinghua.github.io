#!/usr/bin/env python3
"""Package a consistent reader and book release for GitHub Pages."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess


def revision(directory):
    return subprocess.check_output(['git', '-C', str(directory), 'rev-parse', 'HEAD'], text=True).strip()


def version(site, book):
    refs = {'site': revision(site), 'book': revision(book)}
    refs['release'] = hashlib.sha256(f"{refs['site']}:{refs['book']}".encode()).hexdigest()
    return refs


def build(site, book, output):
    if output.exists():
        raise ValueError('Output must be a new directory')
    refs = version(site, book)
    source = (site / 'index.html').read_text()
    if source.count('__BOOK_BASE__') != 1 or source.count('__SITE_RELEASE__') != 1:
        raise ValueError('Reader version placeholders must occur exactly once')
    # Ensure every declared chapter exists before publishing a release.
    for declaration in re.findall(r"const CHAPTERS_(ZH|EN)=\[([\s\S]*?)\];", source):
        language, entries = declaration
        base = book / 'en' if language == 'EN' else book
        for filename in re.findall(r"file:'([^']+)'", entries):
            if not (base / filename).is_file():
                raise ValueError(f'Missing chapter: {language}/{filename}')
    if not (book / 'cover.png').is_file():
        raise ValueError('Missing book cover')
    output.mkdir(parents=True)
    # Preserve the site's existing public root files and example reports.
    for file in site.iterdir():
        if file.is_file() and not file.name.startswith('.') and file.name != 'README.md':
            shutil.copy2(file, output / file.name)
    content = output / 'content' / refs['book']
    tracked = subprocess.check_output(['git', '-C', str(book), 'ls-files', '-z'], text=True).split('\0')
    for filename in filter(None, tracked):
        path = Path(filename)
        if any(part.startswith('.') for part in path.parts):
            continue
        if path.parts[0] in {'scripts', 'tests'}:
            continue
        if path.suffix.lower() not in {'.md', '.png', '.jpg', '.jpeg', '.svg', '.webp', '.gif'}:
            continue
        destination = content / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(book / path, destination)
    rendered = source.replace('__BOOK_BASE__', f'./content/{refs["book"]}/').replace('__SITE_RELEASE__', refs['release'])
    (output / 'index.html').write_text(rendered)
    shutil.copy2(book / 'cover.png', output / 'cover.png')
    (output / 'version.json').write_text(json.dumps(refs, sort_keys=True) + '\n')
    (output / '.nojekyll').touch()
    return refs


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--book', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.output:
        result = build(args.site, args.book, args.output)
    else:
        result = version(args.site, args.book)
    print(json.dumps(result, sort_keys=True))
