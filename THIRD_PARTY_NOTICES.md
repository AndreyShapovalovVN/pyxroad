# Third-party notices and redistribution

## Scope

pyxroad is licensed under MIT. Its dependencies retain their own licenses and
copyright notices. The normal pyxroad wheel and source distribution contain
pyxroad and these attribution materials; dependencies are installed separately.
Including a license here does not relicense pyxroad or imply that the corresponding
component's code is bundled in its wheel.

[licenses.md](licenses.md) inventories all 15 runtime dependencies in `uv.lock`,
including the Python-version-dependent async-timeout package. The original license,
NOTICE and author files are preserved in `third_party/licenses/`, with paths and
SHA-256 digests in `third_party/manifest.json`. That manifest also records exact
upstream source archive URLs and hashes. These materials accompany both the wheel
and source distribution in the package's license directory.

This snapshot covers the locked versions and the installed Linux CPython 3.12
artifacts. The dependency ranges in pyproject.toml allow other versions. Refresh
this inventory when dependencies change. Use `uv sync --locked`
for the reviewed dependency set declared in pyproject.toml and uv.lock. Development tools, Python itself, operating-system
packages, the Redis server and components of downstream applications are not
shipped by pyxroad and are not included in this runtime inventory.

## Preserved notices

- MIT and BSD components: retain the supplied copyright notices, license conditions
  and disclaimers with redistributed copies. BSD attribution does not grant
  permission to use authors' names to endorse a product.
- Apache-2.0 components: include the Apache license and preserve applicable
  attribution notices. The requests NOTICE is copied verbatim alongside its
  license. If modifying Apache-licensed files, add prominent notices describing
  the modifications and retain required notices from the original files.
- setuptools: its vendored libraries have separate licenses; the supplied vendor
  license files and configuration NOTICE files are included with their original
  relative paths.
- lxml: preserve LICENSE.txt, LICENSES.txt, ElementTree notices and the resource
  notices. Its upstream GPL test-runner license is included for completeness;
  that test-runner is not part of the pyxroad wheel. It does not change pyxroad's
  license. Notices for libxml2 2.14.6 and libxslt 1.1.43, reported by the installed
  lxml binary, are included in `third_party/licenses/supplemental/`.

## certifi: source availability under MPL-2.0

certifi 2026.5.20 includes Mozilla-derived certificate data under MPL-2.0. Its
original notice and the full MPL-2.0 text are included. Recipients can obtain the
exact upstream source, including the certificate bundle, from:

[certifi-2026.5.20.tar.gz](https://files.pythonhosted.org/packages/f3/ce/ee2ecad540810a79593028e88299baeae54d346cc7a0d94b6199988b89b1/certifi-2026.5.20.tar.gz)

SHA-256: `69dea482ab64caa7b9f6aba1c6bf48bb6a5448d1c0f1b17ab42ad8c763a5344d`

The source archive was retrieved and its hash checked against uv.lock when this
snapshot was prepared. This project does not patch certifi. If distributing a
modified MPL-covered component, provide the corresponding modified source under
MPL-2.0 and tell recipients where to obtain it; the unmodified upstream link alone
is then insufficient. Retain this source-availability notice with redistributed
certifi binaries and ensure the referenced source remains available to recipients.

## Release maintenance

1. Resolve the intended release environment from uv.lock. For a bundle, inventory
   every shipped component, including native libraries and operating-system files.
2. Copy original license, NOTICE and attribution files from the exact distributions;
   include licenses of vendored components and notices embedded in resources.
   Record the origin and SHA-256 of each copied file in third_party/manifest.json.
3. Update licenses.md, source archive URLs/hashes and this document. Provide source
   for modified MPL-covered files and record changes to Apache-licensed files.
4. Run `uv run --locked python scripts/check_licenses.py`, build both release formats, then run
   `uv run --locked python scripts/check_licenses.py --dist-dir dist` to check their contents.
5. For a container, frozen executable, or a different platform, review the actual
   artifacts before distribution. The lxml upstream inventory identifies
   RNG2Schtrn.xsl and XSD2Schtrn.xsl as unlicensed; attribution alone cannot grant
   redistribution rights for them. Resolve their permission status or exclude them
   after checking application functionality before bundling those resources.
   Also review native dependencies of the particular lxml wheel; the two native
   library notices here are not a complete cross-platform binary audit.

The applicable license texts control. Official references:
[Apache-2.0 section 4](https://www.apache.org/licenses/LICENSE-2.0.html) and
[MPL-2.0 section 3](https://www.mozilla.org/en-US/MPL/2.0/).
