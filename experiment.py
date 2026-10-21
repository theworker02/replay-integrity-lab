"""Synthetic selective replay benchmark. Python 3.10+, standard library only."""
from __future__ import annotations
import csv
import hashlib
import json
import random
import statistics
import platform
import sys
from pathlib import Path

VERSION = '0.1.0'
SEEDS = range(40)

def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, separators=(',', ':')).encode()).hexdigest()

def closure(parents: list[list[int]], roots: set[int]) -> set[int]:
    affected = set(roots)
    for node, dependencies in enumerate(parents):
        if affected.intersection(dependencies):
            affected.add(node)
    return affected

def evaluate(parents: list[list[int]], salts: list[int], old: list[str] | None = None,
             selected: set[int] | None = None) -> list[str]:
    values = list(old) if old is not None else [''] * len(parents)
    for node, dependencies in enumerate(parents):
        if selected is None or node in selected:
            values[node] = digest([node, salts[node], [values[p] for p in dependencies]])
    return values

def audited(parents: list[list[int]], salts: list[int], candidate: list[str],
            cached: list[int], seed: int, fraction: float) -> tuple[list[str], set[int], bool]:
    """Freshly execute sampled cached nodes and their actual ancestors, then fallback."""
    rng = random.Random(seed)
    count = min(len(cached), int(len(cached) * fraction + 0.999999))
    samples = rng.sample(cached, count)
    fresh: dict[int, str] = {}
    def visit(node: int) -> str:
        if node not in fresh:
            fresh[node] = digest([node, salts[node], [visit(p) for p in parents[node]]])
        return fresh[node]
    detected = any(visit(node) != candidate[node] for node in samples)
    if detected:
        for node in range(len(parents)):
            visit(node)
        return [fresh[i] for i in range(len(parents))], set(fresh), True
    return candidate, set(fresh), False

def trial(seed: int, size: int, fan_in: int, missing: float) -> list[dict]:
    rng = random.Random(seed)
    parents = [sorted(rng.sample(range(i), min(i, fan_in))) for i in range(size)]
    # Separate random stream makes declared graphs nested across omission rates.
    masking = random.Random(seed + 100000)
    declared = [[p for p in ps if masking.random() >= missing] for ps in parents]
    salts = [0] * size
    before = evaluate(parents, salts)
    changed = {rng.randrange(max(1, size // 4))}
    salts[next(iter(changed))] = 1
    reference = evaluate(parents, salts)
    selected = closure(declared, changed)
    direct = changed | {i for i, ps in enumerate(declared) if changed.intersection(ps)}
    candidate = evaluate(parents, salts, before, selected)
    rows = []
    for policy, nodes in [('full', set(range(size))), ('direct', direct), ('transitive', selected)]:
        result = evaluate(parents, salts, before, nodes)
        rows.append(dict(policy=policy, work=len(nodes), stale=sum(a != b for a,b in zip(result, reference)), detected=False))
    for fraction in (0.02, 0.10):
        result, fresh, detected = audited(parents, salts, candidate,
            sorted(set(range(size)) - selected), seed + 200000, fraction)
        # Audit executes in a separate fresh context; overlapping work counts twice.
        rows.append(dict(policy=f'audit-{fraction:.2f}', work=len(selected)+len(fresh),
            stale=sum(a != b for a,b in zip(result, reference)), detected=detected))
    return [dict(seed=seed, size=size, fan_in=fan_in, missing=missing,
        affected=len(closure(parents, changed)), **row) for row in rows]

def run(destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    rows = [row for n in (64, 256) for fan in (1, 3) for missing in (0.0, 0.05, 0.2)
            for seed in SEEDS for row in trial(seed, n, fan, missing)]
    with (destination / 'trials.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader(); writer.writerows(rows)
    summary = []
    for missing in (0.0, 0.05, 0.2):
        for policy in ('full', 'direct', 'transitive', 'audit-0.02', 'audit-0.10'):
            group = [r for r in rows if r['missing'] == missing and r['policy'] == policy]
            bad = sum(r['stale'] > 0 for r in group)
            summary.append(dict(missing=missing, policy=policy, trials=len(group),
                incorrect_runs=bad, incorrect_fraction=bad/len(group),
                mean_work_fraction=statistics.mean(r['work']/r['size'] for r in group)))
    (destination / 'summary.json').write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
    manifest = dict(version=VERSION, seeds=list(SEEDS), sizes=[64,256], fan_in=[1,3],
        missing=[0,.05,.2], rows=len(rows),
        python=sys.version, platform=platform.platform(),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        trials_sha256=hashlib.sha256((destination/'trials.csv').read_bytes()).hexdigest())
    (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(summary, indent=2))

if __name__ == '__main__':
    run(Path(__file__).parent / 'results')
