"""Controlled on-disk replay benchmark. Python 3.10+, standard library only.

Each task reads its own input file plus its actual parent outputs and writes a
digest. The declared graph used for scheduling can omit actual reads. This is
not an arbitrary code executor and does not process user files.
"""
from __future__ import annotations

import csv
import hashlib
import json
import random
import shutil
import statistics
import tempfile
import time
import platform
import sys
from pathlib import Path

SEEDS = range(8)
SIZES = (32, 128)
FAN_INS = (1, 3)
MISSING = (0.0, 0.05, 0.20)


def sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def closure(graph: list[list[int]], roots: set[int]) -> set[int]:
    affected = set(roots)
    for node, parents in enumerate(graph):
        if affected.intersection(parents):
            affected.add(node)
    return affected


def build_graph(seed: int, size: int, fan_in: int, missing: float) -> tuple[list[list[int]], list[list[int]], int]:
    rng = random.Random(seed)
    actual = [sorted(rng.sample(range(i), min(i, fan_in))) for i in range(size)]
    mask = random.Random(seed + 100000)
    declared = [[parent for parent in parents if mask.random() >= missing] for parents in actual]
    return actual, declared, rng.randrange(max(1, size // 4))


def write_inputs(root: Path, size: int, changed: int | None = None) -> None:
    inputs = root / "inputs"
    inputs.mkdir(parents=True, exist_ok=True)
    for node in range(size):
        salt = 1 if node == changed else 0
        (inputs / f"{node:04}.txt").write_text(f"node={node};salt={salt}\n", encoding="utf-8")


def execute(root: Path, actual: list[list[int]], prior: Path | None, selected: set[int] | None,
            target_name: str) -> tuple[Path, int, float]:
    target = root / target_name
    target.mkdir(exist_ok=True)
    started = time.perf_counter()
    count = 0
    for node, parents in enumerate(actual):
        out = target / f"{node:04}.out"
        if selected is not None and node not in selected:
            if prior is None:
                raise ValueError("selected execution requires prior outputs")
            shutil.copyfile(prior / f"{node:04}.out", out)
            continue
        payload = (root / "inputs" / f"{node:04}.txt").read_text(encoding="utf-8")
        payload += "".join((target / f"{parent:04}.out").read_text(encoding="utf-8") for parent in parents)
        out.write_text(sha(payload) + "\n", encoding="utf-8")
        count += 1
    return target, count, time.perf_counter() - started


def outputs(path: Path, size: int) -> list[str]:
    return [(path / f"{node:04}.out").read_text(encoding="utf-8") for node in range(size)]


def audit(root: Path, actual: list[list[int]], candidate: Path, selected: set[int],
          seed: int, fraction: float) -> tuple[Path, int, float, bool]:
    cached = sorted(set(range(len(actual))) - selected)
    rng = random.Random(seed + 200000)
    sample_n = min(len(cached), max(1, round(len(cached) * fraction))) if cached else 0
    sampled = rng.sample(cached, sample_n)
    fresh_needed: set[int] = set()
    def add_ancestors(node: int) -> None:
        if node in fresh_needed:
            return
        fresh_needed.add(node)
        for parent in actual[node]:
            add_ancestors(parent)
    for node in sampled:
        add_ancestors(node)
    fresh, fresh_count, elapsed = execute(root, actual, candidate, fresh_needed, "fresh")
    mismatch = any((fresh / f"{node:04}.out").read_bytes() != (candidate / f"{node:04}.out").read_bytes()
                   for node in sampled)
    if mismatch:
        shutil.rmtree(fresh)
        fresh, full_count, full_elapsed = execute(root, actual, None, None, "fresh")
        return fresh, fresh_count + full_count, elapsed + full_elapsed, True
    return candidate, fresh_count, elapsed, False


def one_trial(seed: int, size: int, fan_in: int, missing: float, work_root: Path) -> list[dict]:
    actual, declared, changed = build_graph(seed, size, fan_in, missing)
    root = work_root / f"s{seed}-n{size}-f{fan_in}-m{int(missing*100)}"
    root.mkdir()
    write_inputs(root, size)
    before, _, _ = execute(root, actual, None, None, "before")
    write_inputs(root, size, changed)
    reference, ref_work, ref_time = execute(root, actual, None, None, "reference")
    reference_values = outputs(reference, size)
    selected = closure(declared, {changed})
    rows: list[dict] = []
    policies = [("full", set(range(size))), ("transitive", selected)]
    for policy, nodes in policies:
        path, work, elapsed = execute(root, actual, before, nodes, policy)
        stale = sum(a != b for a, b in zip(outputs(path, size), reference_values))
        rows.append(dict(policy=policy, task_work=work, elapsed_seconds=elapsed, stale=stale, detected=False))
    candidate, candidate_work, candidate_time = execute(root, actual, before, selected, "candidate")
    for fraction in (0.02, 0.10):
        fresh = root / "fresh"
        if fresh.exists(): shutil.rmtree(fresh)
        result, audit_work, audit_time, detected = audit(root, actual, candidate, selected, seed, fraction)
        stale = sum(a != b for a, b in zip(outputs(result, size), reference_values))
        rows.append(dict(policy=f"audit-{fraction:.2f}", task_work=candidate_work + audit_work,
                         elapsed_seconds=candidate_time + audit_time, stale=stale, detected=detected))
    shutil.rmtree(root)
    return [dict(seed=seed, size=size, fan_in=fan_in, missing=missing, changed=changed,
                 full_reference_work=ref_work, full_reference_seconds=ref_time, **row) for row in rows]


def run(destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    temporary_parent = destination / ".file-benchmark-tmp"
    temporary_parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="replay-integrity-", dir=temporary_parent) as temporary:
        work_root = Path(temporary)
        rows = []
        total = len(SIZES) * len(FAN_INS) * len(MISSING) * len(SEEDS)
        completed = 0
        for size in SIZES:
            for fan_in in FAN_INS:
                for missing in MISSING:
                    for seed in SEEDS:
                        rows.extend(one_trial(seed, size, fan_in, missing, work_root))
                        completed += 1
                        if completed % 12 == 0 or completed == total:
                            print(f"completed {completed}/{total} scenarios", flush=True)
    with (destination / "file_trials.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    summary = []
    for missing in MISSING:
        for policy in ("full", "transitive", "audit-0.02", "audit-0.10"):
            group = [r for r in rows if r["missing"] == missing and r["policy"] == policy]
            summary.append(dict(missing=missing, policy=policy, trials=len(group),
                incorrect_runs=sum(r["stale"] > 0 for r in group),
                mean_task_work_fraction=statistics.mean(r["task_work"] / r["size"] for r in group),
                median_elapsed_seconds=statistics.median(r["elapsed_seconds"] for r in group)))
    (destination / "file_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "version": "1.0.0",
        "seeds": list(SEEDS), "sizes": list(SIZES), "fan_in": list(FAN_INS),
        "missing": list(MISSING), "scenarios": len(rows) // 4, "rows": len(rows),
        "python": sys.version, "platform": platform.platform(),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "trials_sha256": hashlib.sha256((destination / "file_trials.csv").read_bytes()).hexdigest(),
    }
    (destination / "file_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    run(Path(__file__).parent / "results")
