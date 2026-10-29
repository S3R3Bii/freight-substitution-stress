# State-entry substitution under hypothetical freight constraints

## Decision and scope

Which of four fixed US entry-state closures creates the greatest unmet water-import-to-truck tonnage under explicitly hypothetical alternative-flow constraints? This uses FAF6.0 2022 state-level estimates. An entry state is an entire state, not an individual port or road node. The model allocates substitute origin-entry-destination flows; it does not reconstruct vehicle routes or simulate a documented disruption.

## Prospective design

The authoritative constants are in protocol.json. Before retrieving the flow archive, fix development SCTG commodities 02 cereal grains, 12 gravel, 24 plastics/rubber and 32 base metals; held commodities 05 meat/seafood, 17 gasoline/aviation turbine fuel/ethanol, 34 machinery and 36 motorized vehicles. These span types without inspecting their measured flows. No claim of representativeness follows. Close California (06), Texas (48), New York (36) and Washington (53) separately. Retain every case, including zero affected demand with undefined recovery fraction. Filter imports (trade type 2), arrival by water (foreign mode 3), domestic truck (mode 1), all eight foreign origins and 51 state/DC destinations. Public projection contains only eligible estimated-flow facts, row locators and hashes; original files and source documents remain private outside Git.

For commodity k, let F[o,g,d] be published thousand-ton estimates, summed over any remaining documented dimensions. Close entry g0 and retain demand D[o,d]=F[o,g0,d]. Alternatives g exclude g0. Construct directed edges:

- source -> gateway g, capacity delta * sum(o,d) F[o,g,d]; this is additional hypothetical shared headroom, not measured unused capacity;
- gateway g -> foreign-origin/gateway (o,g), capacity sum(d) F[o,g,d], a fixed additional-flow convention;
- (o,g) -> origin/destination (o,d), capacity beta * F[o,g,d] under strict support, or beta * sum(o) F[o,g,d] under pooled support; both require a positive origin/gateway relationship and destination demand;
- (o,d) -> sink, capacity D[o,d].

Delta = 0, 1/4, 1/2, 1; beta = 1/4, 1; strict and pooled support. Thus 512 cases: 256 development and 256 held. Primary setting is delta=1/4, beta=1, strict. All factors are untuned illustrative assumptions. Baseline no rerouting recovers zero. A deterministic feasible greedy comparator visits numeric foreign origins, destinations and alternative gateway states in ascending order, respecting every remaining capacity. Exact maximum flow reports recoverable and unmet tonnage, demand, recovery fraction and greedy gap. No selection by development outcomes; development checks implementation. Freeze all analysis dependencies and verify fixtures/development before exposing held analytical summaries. Raw inputs and source quality are visible; no blinding or predictive-generalization claim.

## Computation and checks

Use original decimal strings as exact rational numbers, including factors. Dinic-style level/residual computation produces feasible flows and reachable-source cut certificates. An independent implementation reconstructs edges from source-derived facts without importing production graph/metric helpers, verifies capacity and node conservation, and requires exact flow value = cut capacity for every case. This certifies finite-model optimality, not real-world capacity. Tiny fixtures use exhaustive cuts plus known flows, including a case requiring residual reallocation. Independently reconstruct greedy allocations. Check monotonicity when delta, beta or support expands; full output lattice and zero-demand cases are mandatory. Source verification independently parses the original CSV and selected fields/locators and aggregates with SQL plus exact arithmetic. Replay must reproduce every result/certificate. No learned model, p-value, bootstrap, calibrated probability, cost, transit-time, savings or novelty claim.

## Acceptance and release

Required gates: exact source/version/rights, data schema/quality/reconciliation, fixed dependency freeze before held outcomes, fixture and independent flow/cut/baseline checks, isolated replay, figure coordinates/labels, rendered manuscript, public-file/privacy audit, exact-head Linux CI and matching merge/tag. Each required gate is pass/fail/unknown, grade 4 only when supported. The executive layer must state the planning decision, conditional finding, practical next evidence and limits. Max three substantive review rounds, 45 active review minutes and 60 review-specific calls; execution time separately recorded. Preserve failures. Formal-publication projects, including Azure, are excluded from this public independent program manuscript.

The source lacks actual spare capacity, port/road topology, scheduling, carrier contracts, disruption behavior and uncertainty intervals. Operational feasibility remains unknown and is outside the finite-model claim. Obtain operator and infrastructure evidence before any action. The original broader freight proposal remains historical context; this executable design narrows it prospectively to the documented source.
