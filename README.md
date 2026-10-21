# Replay Integrity Lab

A reproducible exploratory computer-science study of selective workflow replay under missing dependencies. Author: Matthew Looney, Magnexis, [ORCID](https://orcid.org/0009-0007-0025-8000).

Status: pilot implemented and executed; manuscript draft; no submission, DOI, peer review, or real-project validation. The repository is initially private for author review. The correctness argument is standard and narrowly scoped. Novelty has not been established.

## Run

Python 3.10+ on Windows, macOS or Linux. No dependencies, account, GPU, or paid API required.

```sh
python -m unittest discover -v
python experiment.py
```

The fixed pilot generates 480 synthetic scenarios and 2,400 policy rows. Results are overwritten deterministically. Unit-cost task counts are simulated work, not measured application speedups. The benchmark does not execute imported scripts or external workflows.

## Files

- `experiment.py`: DAG generation, missing-edge injection, replay and fresh-execution audits.
- `test_experiment.py`: behavior and regression tests.
- `results/`: trial data, aggregate results and checksum manifest.
- `paper.md`, `paper.pdf`: manuscript source and reading copy.
- `PROTOCOL.md`: future validation design, written after seeing pilot results.
- `SUBMISSION.md`: venue and author-review requirements.

## Pilot finding

At 5% missing edges, 10% auditing reduces incorrect runs from 74/160 to 46/160, with mean work equal to 70.7% of full replay. This fails the proposed goal of halving errors below 75% work. At 20% missing edges it halves errors but exceeds the work goal. Neither result establishes safe replay.

## Architecture and security

The declared dependency graph schedules selective work; the actual graph evaluates tasks and supplies the reference. Fresh audits recompute sampled cached tasks and their actual ancestors in a separate memoized context. A detected mismatch triggers full replay using that fresh context. Overlapping candidate and audit execution counts twice. Audit recursion is suitable only for these small synthetic graphs. No external commands, network calls, telemetry, secret storage, or untrusted imports are used by the experiment. A future real runner requires isolated, side-effect-free tasks and explicit input tracking.

## License and contribution status

No distribution license has been selected by the author yet. Do not interpret a public repository as a grant of reuse rights. Select software and manuscript/data licenses before a public archival deposit. Contributions should preserve deterministic seeds, report all outcomes, and keep prospective validation separate from this pilot.
