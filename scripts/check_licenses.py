"""Check runtime inventory, notice integrity, and built license payloads (Python 3.11+)."""

import argparse
import hashlib
import json
from pathlib import Path
import tarfile
import tomllib
import zipfile


def runtime_versions(packages):
    runtime = set()
    pending = ['pyxroad']
    while pending:
        name = pending.pop()
        if name in runtime:
            continue
        runtime.add(name)
        pending.extend(d['name'] for d in packages[name].get('dependencies', []))
    runtime.remove('pyxroad')
    return {name: packages[name]['version'] for name in runtime}


def check_inventory(manifest, packages, expected):
    actual = {p['name']: p['version'] for p in manifest['packages']}
    if actual != expected:
        raise ValueError('Runtime license inventory differs from uv.lock; refresh notices')
    for package in manifest['packages']:
        if package['source'] != packages[package['name']]['sdist']:
            raise ValueError(f"Source provenance changed: {package['name']}")


def check_notices(root, manifest, expected):
    expected_paths = {entry['path'] for entry in manifest['files']}
    actual_paths = {str(p.relative_to(root)) for p in (root / 'third_party/licenses').rglob('*') if p.is_file()}
    if expected_paths != actual_paths:
        raise ValueError('Notice files differ from the provenance manifest')
    for entry in manifest['files']:
        if hashlib.sha256((root / entry['path']).read_bytes()).hexdigest() != entry['sha256']:
            raise ValueError(f"Notice modified: {entry['path']}")
    for name, version in expected.items():
        prefix = f'third_party/licenses/{name}/{version}/'
        if not any(path.startswith(prefix) for path in expected_paths):
            raise ValueError(f'No notices for {name}=={version}')
    return expected_paths


def check_wheel(root, path, payload):
    with zipfile.ZipFile(path) as archive:
        prefix = next(
            n.split('/')[0] for n in archive.namelist() if '.dist-info/' in n
        ) + '/licenses/'
        for relative in payload:
            if archive.read(prefix + relative) != (root / relative).read_bytes():
                raise ValueError(f'Incorrect wheel payload: {relative}')


def check_sdist(root, path, payload):
    with tarfile.open(path) as archive:
        prefix = archive.getnames()[0].split('/')[0] + '/'
        for relative in payload | {'scripts/check_licenses.py', 'uv.lock'}:
            if archive.extractfile(prefix + relative).read() != (root / relative).read_bytes():
                raise ValueError(f'Incorrect sdist payload: {relative}')


def check_distributions(root, dist_dir, notice_paths):
    wheels = list(dist_dir.glob('*.whl'))
    sources = list(dist_dir.glob('*.tar.gz'))
    if not wheels or not sources:
        raise ValueError('Build both wheel and sdist before checking')
    payload = notice_paths | {
        'LICENSE', 'THIRD_PARTY_NOTICES.md', 'licenses.md', 'third_party/manifest.json'
    }
    for path in wheels:
        check_wheel(root, path, payload)
    for path in sources:
        check_sdist(root, path, payload)


def check(root, dist_dir=None):
    manifest = json.loads((root / 'third_party/manifest.json').read_text())
    lock = tomllib.loads((root / 'uv.lock').read_text())
    packages = {p['name']: p for p in lock['package']}
    expected = runtime_versions(packages)
    check_inventory(manifest, packages, expected)
    notice_paths = check_notices(root, manifest, expected)
    if dist_dir is not None:
        check_distributions(root, dist_dir, notice_paths)
    print(
        f'License checks passed: {len(expected)} runtime dependencies, '
        f'{len(notice_paths)} notice files'
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dist-dir', type=Path)
    args = parser.parse_args()
    check(Path(__file__).resolve().parents[1], args.dist_dir)
