# Source, units and rights

Primary source: U.S. Department of Transportation, Bureau of Transportation Statistics (2022), Freight Analysis Framework, FAF6 datasets, DOI https://doi.org/10.21949/fhgm-g335. Version FAF6.0 is the current 2022 benchmark, verified on 29 October 2026 at https://www.bts.gov/faf. This study fixes that version rather than mixing FAF5 releases. Tonnage is in **thousand tons**, not individual tons or observed vehicle counts.

- State CSV archive: https://faf.ornl.gov/faf6/data/Download_Files/ZIP/FAF6.0_State.zip
- Guide: https://faf.ornl.gov/faf6/data/FAF6%20User%20Guide.pdf (July 2026), especially state/entry definitions and data dictionary. Page ii states public-domain reuse with source citation. The full guide/artwork will not be redistributed here.
- Limitations: https://www.bts.gov/faf/faqs. Local detail, local growth and road coverage limit interpretation; consult shippers and operators.
- Metadata: https://faf.ornl.gov/faf6/data/FAF6_Metadata.xlsx
- Established flow optimality: MIT 6.854 lecture 7 (2019), https://courses.csail.mit.edu/6.854/19/Notes/n07-flow_computation.html. Independent feasible-flow and equal-capacity-cut witnesses certify optimality. Original implementation; no copied source code, no new algorithm claim.

Foreign origins 801-808 are broad world regions. Domestic origin for imports is the US entry state; it is not an individual port. Arrival mode 3 includes water; domestic mode 1 is truck. Estimates do not document available capacity or shipping contracts. Source accuracy and operational feasibility are not certified by a replay.

Source/rights gate: PASS for a minimal attributed aggregate fact projection and original derivative analysis, conditional on schema/quality checks. No personal, firm-level, clinical or confidential business records are requested. Raw archive, source documents and unrelated commodities stay outside Git. No agency endorsement.
