# Statistical Analysis Plan

## Primary analysis

Outcome: Qualified Success (binary).

Preferred design: matched runs by scenario/model-configuration/scaffold with randomized arm order.

Report:
- successes / attempts;
- absolute percentage-point difference;
- relative risk when meaningful;
- 95% confidence interval;
- scenario-stratified results.

For larger experiments, use a mixed-effects logistic model with scenario and model-configuration/scaffold effects when appropriate.

## Small/pilot experiments

The included `analyze_results.py` reports:
- Wilson confidence intervals per arm;
- raw dimension means;
- matched A0↔A2 differences where pair IDs exist.

Pilot statistics are exploratory.

## Multiple secondary endpoints

Do not search many metrics and report only favorable ones.

Predeclare primary/secondary endpoints. For confirmatory testing across many secondary hypotheses, use a multiple-comparison correction or clearly label results exploratory.

## Repetitions

Agent outputs are stochastic. One run per task is insufficient for strong conclusions.

Run-independent sessions and report variance.

## Missing/failed infrastructure runs

Differentiate:
- agent failure;
- evaluator failure;
- infrastructure failure.

Do not silently rerun only unfavorable agent outcomes.

Predetermine rerun policy.

## Effectiveness threshold before claiming 1.0 validation

The project governance should define this before observing formal benchmark results.

A reasonable candidate criterion is:
- statistically and practically meaningful QS improvement over A0;
- no material regression against A1 on core engineering outcomes;
- lower evaluator-integrity/security failure rate;
- acceptable burden increase;
- replicated across more than one model-configuration/scaffold and more than one benchmark family.

This is a proposal, not yet a normative pass threshold.
