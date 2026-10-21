# Replay Integrity Lab

A reproducible exploratory computer-science study of selective workflow replay under missing dependencies. Author: Matthew Looney, Magnexis, [ORCID](https://orcid.org/0009-0007-0025-8000).

Status: an in-memory pilot and a controlled on-disk file-processing experiment have been executed; manuscript draft v0.2; no submission, DOI, peer review, or real-project validation. The repository is initially private for author review. The correctness argument is standard and narrowly scoped. Novelty has not been established.

## Run

Python 3.10+ on Windows, macOS or Linux. No dependencies, account, GPU, or paid API required.

```sh
python -m unittest discover -v
python experiment.py
python file_benchmark.py
```

The fixed pilot generates 480 synthetic scenarios and 2,400 policy rows. The controlled file-processing experiment generates 96 scenarios and 384 policy rows using only temporary generated files. Results are overwritten deterministically. Unit-cost task counts are not measured application speedups. Neither benchmark executes imported scripts or external workflows.

## Files

- `experiment.py`: in-memory DAG generation, missing-edge injection, replay and fresh-execution audits.
- `file_benchmark.py`: controlled on-disk workload with real temporary input/output files and elapsed-time recording.
- `test_experiment.py`, `test_file_benchmark.py`: behavior and regression tests.
- `results/`: trial data, aggregate results and checksum manifest.
- `paper.md`, `paper.pdf`: manuscript source and reading copy.
- `PROTOCOL.md`: future validation design, written after seeing pilot results.
- `SUBMISSION.md`: venue and author-review requirements.

## Pilot finding

At 5% missing edges, the in-memory 10% audit reduces incorrect runs from 74/160 to 46/160 at 70.7% mean task work; the controlled file run reduces 13/32 to 7/32 at 79.3%. At 20% omission, the controlled file run reduces 22/32 to 7/32 but costs 105.6% of full task work. The combined result rejects a blanket claim that sparse auditing makes incomplete dependency data safe.

## Architecture and security

The declared dependency graph schedules selective work; the actual graph evaluates tasks and supplies the reference. Fresh audits recompute sampled cached tasks and their actual ancestors in a separate memoized context. A detected mismatch triggers full replay using that fresh context. Overlapping candidate and audit execution counts twice. Audit recursion is suitable only for these small synthetic graphs. No external commands, network calls, telemetry, secret storage, or untrusted imports are used by the experiment. A future real runner requires isolated, side-effect-free tasks and explicit input tracking.

## License and contribution status

No distribution license has been selected by the author yet. Do not interpret a public repository as a grant of reuse rights. Select software and manuscript/data licenses before a public archival deposit. Contributions should preserve deterministic seeds, report all outcomes, and keep prospective validation separate from this pilot.
