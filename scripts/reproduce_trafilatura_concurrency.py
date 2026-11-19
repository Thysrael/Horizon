#!/usr/bin/env python3
"""Opt-in offline native-crash probe. Never imported by the regular test suite."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import resource
import subprocess
import sys
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
MANIFEST = ROOT / "docs/debug/trafilatura-concurrency/fixtures.json"


def bounded(low, high):
    def parse(value):
        number = int(value)
        if not low <= number <= high:
            raise argparse.ArgumentTypeError(f"must be between {low} and {high}")
        return number
    return parse


def fixtures(directory):
    pages = []
    for item in json.loads(MANIFEST.read_text()):
        data = (directory / item["file"]).read_bytes()
        if hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise ValueError(f"Fixture hash mismatch: {item['file']}")
        pages.append(data.decode("utf-8"))
    return pages


def child(args, pages):
    # Keep native crashes bounded and do not leave large core dumps behind.
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    import faulthandler
    faulthandler.enable()
    import trafilatura
    from src.extractors.trafilatura import _extract_text

    workers = 1 if args.child == "serial" else args.workers
    barrier = threading.Barrier(workers, timeout=args.timeout)

    def extract(worker):
        for iteration in range(args.iterations):
            html = pages[(worker + iteration) % len(pages)]
            barrier.wait()
            if args.child == "locked":
                text = _extract_text(trafilatura, html, False, False)
            else:
                text = trafilatura.extract(html, favor_precision=False, favor_recall=False)
            if not isinstance(text, str) or not text.strip():
                raise AssertionError("Expected non-empty article text")
        return args.iterations

    with ThreadPoolExecutor(max_workers=workers) as pool:
        # Keep identical jobs, fixture sequence and total calls in all modes;
        # the serial control only changes the number of executing threads.
        calls = sum(pool.map(extract, range(args.workers)))
    print(json.dumps({"calls": calls, "nonempty_results": calls}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures-dir", required=True, type=Path)
    parser.add_argument("--runs", type=bounded(1, 40), default=12)
    parser.add_argument("--workers", type=bounded(2, 16), default=8)
    parser.add_argument("--iterations", type=bounded(1, 10), default=3)
    parser.add_argument("--timeout", type=bounded(1, 30), default=15)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--child", choices=("concurrent", "locked", "serial"), help=argparse.SUPPRESS)
    args = parser.parse_args()
    pages = fixtures(args.fixtures_dir)
    if args.child:
        child(args, pages)
        return
    if not args.output:
        parser.error("--output is required for the parent process")

    from lxml import etree
    report = {
        "environment": {
            "python": platform.python_version(), "system": platform.system(),
            "machine": platform.machine(),
            "trafilatura": importlib.metadata.version("trafilatura"),
            "lxml": importlib.metadata.version("lxml"),
            "libxml2": list(etree.LIBXML_VERSION),
        },
        "parameters": {k: getattr(args, k) for k in ("runs", "workers", "iterations", "timeout")},
        "fixtures": json.loads(MANIFEST.read_text()),
        "runs": [],
    }
    command = [sys.executable, str(Path(__file__).resolve()),
               "--fixtures-dir", str(args.fixtures_dir.resolve()),
               "--workers", str(args.workers), "--iterations", str(args.iterations),
               "--timeout", str(args.timeout)]
    # Interleave controls to reduce ordering/environment bias. Each run starts
    # a fresh interpreter; no web requests or model/API calls are made.
    for run in range(args.runs):
        for mode in ("concurrent", "locked", "serial"):
            try:
                result = subprocess.run(command + ["--child", mode], capture_output=True,
                                        text=True, timeout=args.timeout)
                entry = {"run": run + 1, "mode": mode, "returncode": result.returncode,
                         "stdout": result.stdout, "stderr": result.stderr}
            except subprocess.TimeoutExpired as exc:
                def text(value):
                    return value.decode(errors="replace") if isinstance(value, bytes) else (value or "")
                entry = {"run": run + 1, "mode": mode, "timeout": True,
                         "stdout": text(exc.stdout), "stderr": text(exc.stderr)}
            # Preserve diagnostic content without publishing local install paths.
            for key in ("stdout", "stderr"):
                entry[key] = entry[key].replace(str(ROOT), "<repository>").replace(sys.prefix, "<venv>")
            report["runs"].append(entry)
            args.output.write_text(json.dumps(report, indent=2) + "\n")
            print(f"{run + 1}/{args.runs} {mode}: {entry.get('returncode', 'timeout')}", flush=True)
    for mode in ("concurrent", "locked", "serial"):
        entries = [r for r in report["runs"] if r["mode"] == mode]
        print(mode, {"ok": sum(r.get("returncode") == 0 for r in entries),
                     "failed": sum(r.get("returncode") not in (None, 0) for r in entries),
                     "timeouts": sum(bool(r.get("timeout")) for r in entries)})


if __name__ == "__main__":
    main()
