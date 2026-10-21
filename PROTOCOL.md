# Prospective validation protocol - v0.1

Written October 21, 2026 **after** examining the pilot. Not preregistered or executed. The current `experiment.py` implements the pilot only.

Hypothesis: a 10% cached-node fresh audit can reduce incorrect runs by at least 50% relative to declared transitive replay while requiring mean total task work <= 75% of full replay in the specified primary condition.

Before execution, freeze a commit implementing seeds 40..239, sizes 128/512, fan-in 1/3/6, omission probabilities .01/.05/.20, and separately stratified early/middle/late mutations. Define each region exactly and freeze equal stratum weights. For the primary endpoint, use independent 5% omission, equal weights across size, fan-in and mutation-position strata. Record both threshold decisions; success requires both. Report all strata and all failed conditions.

Use a seed-cluster paired bootstrap with 10,000 resamples and a fixed analysis seed chosen before execution. Report 95% intervals for paired incorrect-run differences, relative reduction (undefined if baseline error is zero), and paired work differences. Do not treat all reused-seed graph variants as independent observations. Formal power analysis is pending; do it before making a confirmatory study claim.

Secondary analyses: clustered omission, omission rate, audit fraction, task-cost heterogeneity, semantically unchanged outputs, and topology. Freeze clustered omission generation and cost distributions before running; neither is implemented yet. Pilot seeds may be used for engineering checks only, not validation tuning.

Required artifacts: exact configuration, source commit/hash, interpreter/OS, raw rows, stratum summaries, analysis code, and all failures. Do not overwrite the pilot files with validation outcomes. Do not describe this protocol as preregistered unless deposited with an independently timestamped registration before validation results are observed.

Next practical experiment: instrument a small pure-task local runner, record file/environment/tool-version inputs, replay real edit histories, and compare with full execution and an established incremental baseline. Repeated side effects are out of scope. No LLM, production workload, or sandbox security claim follows from the synthetic pilot.
