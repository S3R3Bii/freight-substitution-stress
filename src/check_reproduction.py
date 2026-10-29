"""Recompute in an isolated source copy and compare all exact result/proof fields."""

import csv, gzip, json, shutil, subprocess, sys, tempfile
from pathlib import Path
from verify_freeze import verify as verify_freeze
from verify_results import verify as verify_results


def count_fields(value):
    if isinstance(value, dict):
        return sum(count_fields(v) for v in value.values())
    if isinstance(value, list):
        return sum(count_fields(v) for v in value)
    return 1


def check(root="."):
    root = Path(root).resolve()
    freeze = verify_freeze(root)
    checks = 0
    outcomes = []
    with tempfile.TemporaryDirectory(prefix="freight-replay-") as folder:
        isolated = Path(folder) / "source"
        isolated.mkdir()
        for name in ["src", "data", "tests"]:
            shutil.copytree(
                root / name,
                isolated / name,
                ignore=shutil.ignore_patterns("__pycache__"),
            )
        for name in [
            "protocol.json",
            "PROTOCOL.md",
            "SOURCE_SCHEMA.md",
            "SOURCES.md",
            "FREEZE.json",
        ]:
            shutil.copy2(root / name, isolated / name)
        for phase in ["development", "held"]:
            subprocess.run(
                [sys.executable, "src/run_analysis.py", phase],
                cwd=isolated,
                check=True,
                capture_output=True,
            )
            observed = list(
                csv.reader(
                    (isolated / f"results/{phase}.csv").open(
                        encoding="utf-8", newline=""
                    )
                )
            )
            expected = list(
                csv.reader(
                    (root / f"results/{phase}.csv").open(encoding="utf-8", newline="")
                )
            )
            assert observed == expected, phase
            checks += sum(map(len, expected))
            actual = json.loads(
                gzip.decompress(
                    (isolated / f"results/{phase}-certificates.json.gz").read_bytes()
                )
            )
            reference = json.loads(
                gzip.decompress(
                    (root / f"results/{phase}-certificates.json.gz").read_bytes()
                )
            )
            assert actual == reference, phase
            checks += count_fields(reference)
            outcomes.append(verify_results(isolated, phase))
    return dict(
        status="PASS",
        exact_csv_and_certificate_scalar_fields=checks,
        protected_dependencies=freeze["dependencies"],
        phases=outcomes,
        execution_timing="Original per-case UTC/runtime records retained; replay timing is variable and excluded from exact identity.",
    )


if __name__ == "__main__":
    result = check()
    Path("REPRODUCTION_CHECK.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result))
