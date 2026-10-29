"""Compare actual artist arrays, lines, bars and annotations to independent CSV fractions."""

import csv, hashlib, json, math
from fractions import Fraction
from pathlib import Path
import matplotlib.pyplot as plt
from make_figures import build, contrast


def verify(root="."):
    root = Path(root)
    data = list(
        csv.DictReader((root / "results/held.csv").open(encoding="utf-8", newline=""))
    )
    lookup = {
        (
            int(r["commodity"]),
            int(r["closed_state"]),
            r["delta"],
            r["beta"],
            r["support"],
        ): r
        for r in data
    }
    figures, artists = build(root)
    count = 0
    annotations = 0
    contrasts = 0
    image, texts = artists["primary_recovery"]
    array = image.get_array()
    assert image.get_clim() == (0, 100)
    expected = []
    for i, k in enumerate([5, 17, 34, 36]):
        for j, state in enumerate([6, 48, 36, 53]):
            q = 100 * float(
                Fraction(
                    lookup[k, state, "1/4", "1", "strict"]["recovery_fraction_exact"]
                )
            )
            expected.append(q)
            assert math.isclose(float(array[i, j]), q, rel_tol=0, abs_tol=1e-12)
            count += 1
            text = texts[4 * i + j]
            assert text.get_position() == (j, i) and text.get_text() == f"{q:.1f}%"
            annotations += 1
            white, black = contrast(image.cmap(image.norm(q)))
            ratio = white if text.get_color() == "white" else black
            assert ratio >= 4.5
            contrasts += 1
    for k, state, support, line in artists["headroom_sensitivity"]:
        assert list(line.get_xdata()) == [0, 25, 50, 100]
        count += 4
        values = [
            100
            * float(
                Fraction(lookup[k, state, h, "1", support]["recovery_fraction_exact"])
            )
            for h in ["0", "1/4", "1/2", "1"]
        ]
        for actual, q in zip(line.get_ydata(), values):
            assert math.isclose(float(actual), q, rel_tol=0, abs_tol=1e-12)
            count += 1
        assert line.get_linestyle() == ("-" if support == "strict" else "--")
    for bar, (k, state) in zip(
        artists["greedy_gap"],
        [(k, s) for k in [5, 17, 34, 36] for s in [6, 48, 36, 53]],
    ):
        q = float(Fraction(lookup[k, state, "1/4", "1", "strict"]["gap_exact"]))
        assert math.isclose(bar.get_width(), q, rel_tol=0, abs_tol=1e-12)
        count += 1
    hashes = json.loads((root / "figures/MANIFEST.json").read_text(encoding="utf-8"))
    for name, digest in hashes.items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
    for fig in figures.values():
        plt.close(fig)
    return dict(
        status="PASS",
        actual_artist_values=count,
        heatmap_annotations=annotations,
        contrast_checks=contrasts,
        min_required_annotation_contrast=4.5,
        export_hashes=len(hashes),
        visual_review="Recorded separately; coordinate checks alone are not accessibility conformance.",
    )


if __name__ == "__main__":
    result = verify()
    Path("figures/VERIFICATION.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result))
