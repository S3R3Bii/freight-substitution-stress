# Freight entry-state substitution

FAF6.0 estimates help frame freight continuity questions, but actual spare transport capacity requires operator evidence. This study keeps those two claims separate through a fixed scenario lattice and exact allocation certificates.

Under the declared primary assumptions, conditional recovery ranges from **0% to 100% across 16 held cases**. All **512** fixed scenarios passed exact feasible-flow and matching-cut checks. These are hypothetical entry-state substitution results on 2022 estimated flows; they establish neither an observed disruption nor operational capacity, cost or savings.

Start with the [decision summary and all primary cases](DECISION_SUMMARY.md), then inspect the [protocol](PROTOCOL.md), [constants](protocol.json), [sources](SOURCES.md), [freeze](FREEZE.json), [complete results](results) and [independent manuscript](paper/manuscript.pdf). The next practical step is to obtain facility, route and carrier evidence before committing to a transport plan.

![Conditional recovery](figures/primary_recovery.png)

## Evidence

- 8,563 selected facts reconciled to the 599,529-row official archive; 102,756 independent selected-field/locator comparisons.
- Twelve fixtures, 17 protected dependencies frozen before held summaries, 1,747,549 independent exact result checks and 2,304 monotonicity checks.
- Isolated replay of 759,047 exact CSV/certificate fields; three original figures with actual artist, annotation and contrast checks.
- All 512 cases, original per-case runtime records, flow/cut certificates, display-rounded tables and exact rational values retained.

```text
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python src/check_reproduction.py
python src/verify_figures.py
python src/verify_paper.py
python src/verify_public_package.py
```

Source estimates, capacity assumptions and physical feasibility have different evidential status. Read the limitations before reuse. Independent program research; not peer reviewed; no new algorithm or novelty claim. Formal-publication projects such as Azure remain private.
