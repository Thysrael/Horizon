# Opt-in trafilatura concurrency probe

This is a bounded, offline diagnostic, **not a regular CI test**. It compares
concurrent `trafilatura.extract()`, Horizon's locked `_extract_text()`, and serial
`trafilatura.extract()` in fresh subprocesses. Every mode receives the same eight
jobs, three HTML inputs per job (24 extractions per subprocess). The concurrent
modes synchronize workers before each extraction. HTTP fetching is not involved.

The lock is a temporary mitigation for the concurrent-extraction native failures
reported in [trafilatura #925](https://github.com/adbar/trafilatura/issues/925).
It serializes the **whole extraction**, not just initial HTML parsing, while
Horizon still fetches articles concurrently and offloads extraction from the event
loop. It does not guarantee protection against unrelated native crashes.

## Fixed inputs and reproducible commands

`fixtures.json` records SHA-256 hashes, byte lengths and public source URLs for
three Python 3.13.5 documentation pages. Their license is documented by the
[Python Software Foundation](https://docs.python.org/release/3.13.5/license.html).
HTML is downloaded only in this explicit preparation step; the probe itself
reads local files, verifies every hash, and performs no network or model calls.
If a source stops serving the recorded bytes, the hash check must fail; do not
silently substitute new content.

From the repository root on Linux with CPython 3.13.5:

```sh
python3.13 -m venv /tmp/horizon-trafilatura-repro
/tmp/horizon-trafilatura-repro/bin/pip install -r docs/debug/trafilatura-concurrency/requirements.txt
/tmp/horizon-trafilatura-repro/bin/python - <<'PY'
import hashlib, json, urllib.request
from pathlib import Path
out = Path('/tmp/horizon-trafilatura-fixtures')
out.mkdir(exist_ok=True)
for item in json.loads(Path('docs/debug/trafilatura-concurrency/fixtures.json').read_text()):
    data = urllib.request.urlopen(item['url'], timeout=30).read()
    assert hashlib.sha256(data).hexdigest() == item['sha256'], item['file']
    (out / item['file']).write_bytes(data)
PY
PYTHONDONTWRITEBYTECODE=1 /tmp/horizon-trafilatura-repro/bin/python scripts/reproduce_trafilatura_concurrency.py \
  --fixtures-dir /tmp/horizon-trafilatura-fixtures \
  --runs 12 --workers 8 --iterations 3 --timeout 15 --output /tmp/trafilatura-results.json
```

Each child has a wall-clock timeout and core dumps disabled. Argument bounds
limit runs to 40 per mode, workers to 16, iterations to 10 and timeout to 30s.
With the command above the timeout budget is approximately nine minutes;
healthy runs finish sooner. Native signals, Python failures and timeouts are
recorded separately in the JSON (negative return codes denote POSIX signals).
Controls are interleaved. Output includes each child's stdout/stderr; local
repository/virtualenv paths are replaced with placeholders, not diagnostic text.

`requirements.txt` is the exact package snapshot of this isolated test
environment, not a proposed change to Horizon's runtime dependencies. Wheel,
architecture, OS and Python differences can still affect native crashes.

## Fresh, auditable results

`results.json` is the output of the command above with its environment and input
hashes. Environment: CPython 3.13.5, Linux x86_64, trafilatura 2.1.0,
lxml 6.1.1, libxml2 2.14.6.

| Mode | Successful processes | Native crashes | Python failures | Timeouts |
| --- | ---: | ---: | ---: | ---: |
| Concurrent, unguarded | 12/12 | 0 | 0 | 0 |
| Concurrent, Horizon lock | 12/12 | 0 | 0 | 0 |
| Serial, unguarded | 12/12 | 0 | 0 | 0 |

Every successful process returned 24 nonempty results. **This fresh dataset did
not reproduce a native crash**, so it does not measure a crash-rate improvement
or establish the exact cause of any earlier failure. The reproducibility claim
is limited to the inputs, commands and recorded observations, not a guaranteed
crash on another host. The separate deterministic unit tests check the intended
serialization contract across extractor instances and lock release after an
exception; the synthetic real-HTML unit test is only a smoke test.

The earlier reported 40-run experiment's original harness, input bytes and raw
logs were unavailable for this follow-up. Its numbers are not reconstructed here
and have been removed from the PR's auditable evidence. This is a new experiment
with different, explicitly fixed inputs, not a recreation of that historical run.

As checked for this follow-up, trafilatura's parser-per-call change
[#1092](https://github.com/adbar/trafilatura/pull/1092) is merged, but the latest
GitHub/PyPI release, 2.3.1, predates it and still has the shared parser. The lock
can be revisited after a release containing that change is available and tested.

## Focused tests without live DNS

The extractor tests mock HTTP clients, but one pre-existing test also traverses
SSRF DNS validation. The following substitutes only its resolver, avoiding any
live DNS request; it does not change production code or the committed tests:

```sh
PYTHONDONTWRITEBYTECODE=1 /tmp/horizon-trafilatura-repro/bin/python - <<'PY'
import pytest
from unittest.mock import AsyncMock, patch
with patch('src.url_security._resolve_hostname', new=AsyncMock(return_value={'93.184.216.34'})):
    raise SystemExit(pytest.main([
        '-p', 'no:cacheprovider',
        'tests/test_extractors_trafilatura.py', 'tests/test_extractors_registry.py',
        'tests/test_rss.py', 'tests/test_rss_concurrency.py',
    ]))
PY
```

Result: **76 passed**, with one optional urllib3 SOCKS-support warning. No model
API calls, scheduled jobs or deployment workflows were run.
