# Source projection

flows.csv.gz contains only the eight fixed commodities from the FAF6.0 2022 state CSV, import trade, arrival by water, domestic truck. Every selected source dimension and exact published tonnage string is retained. source_row is the one-based CSV record position including the header; source_fields_sha256 joins ten original fields with U+001F. Monetary values are excluded. Compressed bytes, archive/member hashes, full row count, selected counts and source URL are in the manifest. Full archives and source workbooks remain outside Git.

Labels are attributed code/name facts from the included FAF6 metadata. Missing origin-entry-destination cells are **zero published support within this selected matrix**, not proof a real route cannot operate. Tiny estimated values and decimal digits are not physical measurement precision. No extra rounding, censoring, imputation or flow-value filtering is applied.
