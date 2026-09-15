# Component licenses

Snapshot of runtime dependencies resolved in `uv.lock`. The MIT license of pyxroad does not replace component licenses. Full original notices are in [third_party/licenses](third_party/licenses/); see [redistribution guidance](THIRD_PARTY_NOTICES.md).

| Component | Locked version | License / notices |
|---|---|---|
| [async-timeout](third_party/licenses/async-timeout/5.0.1/) | 5.0.1 | Apache-2.0 |
| [attrs](third_party/licenses/attrs/26.1.0/) | 26.1.0 | MIT |
| [certifi](third_party/licenses/certifi/2026.5.20/) | 2026.5.20 | MPL-2.0 |
| [charset-normalizer](third_party/licenses/charset-normalizer/3.4.7/) | 3.4.7 | MIT |
| [idna](third_party/licenses/idna/3.18/) | 3.18 | BSD-3-Clause |
| [isodate](third_party/licenses/isodate/0.7.2/) | 0.7.2 | BSD-3-Clause |
| [lxml](third_party/licenses/lxml/6.1.1/) | 6.1.1 | BSD-3-Clause; additional upstream notices |
| [platformdirs](third_party/licenses/platformdirs/4.10.0/) | 4.10.0 | MIT |
| [redis](third_party/licenses/redis/8.0.1/) | 8.0.1 | MIT (Python client) |
| [requests](third_party/licenses/requests/2.33.0/) | 2.33.0 | Apache-2.0 |
| [requests-file](third_party/licenses/requests-file/3.0.1/) | 3.0.1 | Apache-2.0 |
| [requests-toolbelt](third_party/licenses/requests-toolbelt/1.0.0/) | 1.0.0 | Apache-2.0 |
| [setuptools](third_party/licenses/setuptools/78.1.1/) | 78.1.1 | MIT; vendored components have separate licenses |
| [urllib3](third_party/licenses/urllib3/2.7.0/) | 2.7.0 | MIT |
| [zeep](third_party/licenses/zeep/4.3.3/) | 4.3.3 | MIT |

`async-timeout` is required by redis on Python < 3.11.3. Development-only tools are not bundled in the pyxroad release and are outside this runtime inventory.

The installed lxml binary reports libxml2 2.14.6 and libxslt 1.1.43; their notices are included under `third_party/licenses/supplemental/`. Other platforms/builds need an inventory of their actual native libraries.

Exact source archive URLs and SHA-256 digests from the lockfile, and provenance and digests for every copied notice, are recorded in [third_party/manifest.json](third_party/manifest.json).
