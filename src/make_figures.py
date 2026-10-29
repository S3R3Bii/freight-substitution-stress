"""Original figures; scenario parameters are assumptions, not measured capacity."""

import csv, hashlib, json
from fractions import Fraction as Q
from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

COMMODITIES = [5, 17, 34, 36]
NAMES = {5: "Meat / seafood", 17: "Gasoline", 34: "Machinery", 36: "Motorized vehicles"}
STATES = [6, 48, 36, 53]
SHORT = {6: "CA", 48: "TX", 36: "NY", 53: "WA"}
COLORS = ["#126789", "#b95c29", "#5e7d37", "#805b94"]


def read(root):
    return {
        (
            int(r["commodity"]),
            int(r["closed_state"]),
            r["delta"],
            r["beta"],
            r["support"],
        ): r
        for r in csv.DictReader(
            (Path(root) / "results/held.csv").open(encoding="utf-8", newline="")
        )
    }


def contrast(rgb):
    linear = [
        v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in rgb[:3]
    ]
    luminance = sum(a * b for a, b in zip(linear, [0.2126, 0.7152, 0.0722]))
    return (1.05 / (luminance + 0.05), (luminance + 0.05) / 0.05)


def build(root="."):
    rows = read(root)
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "pdf.fonttype": 42,
            "svg.fonttype": "none",
        }
    )
    figs = {}
    artists = {}
    values = np.array(
        [
            [
                100
                * float(Q(rows[k, s, "1/4", "1", "strict"]["recovery_fraction_exact"]))
                for s in STATES
            ]
            for k in COMMODITIES
        ]
    )
    fig, ax = plt.subplots(figsize=(8.1, 4.8))
    image = ax.imshow(values, cmap="Blues", vmin=0, vmax=100, aspect="auto")
    texts = []
    for i in range(4):
        for j in range(4):
            white, black = contrast(image.cmap(image.norm(values[i, j])))
            texts.append(
                ax.text(
                    j,
                    i,
                    f"{values[i,j]:.1f}%",
                    ha="center",
                    va="center",
                    color="white" if white >= black else "black",
                    fontsize=11,
                )
            )
    ax.set_xticks(range(4), [SHORT[s] for s in STATES])
    ax.set_yticks(range(4), [NAMES[k] for k in COMMODITIES])
    ax.set_xlabel("Hypothetically closed entry state")
    ax.set_title(
        "Conditional recovery varies by commodity and entry state",
        loc="left",
        fontweight="bold",
        pad=14,
    )
    fig.colorbar(
        image,
        ax=ax,
        label="Recoverable share of affected estimated tonnage (%)",
        pad=0.03,
    )
    fig.text(
        0.02,
        0.025,
        "Held commodities | 2022 FAF6.0 estimates | 25% assumed headroom, strict support, corridor factor 1",
        fontsize=8.5,
        color="#333333",
    )
    fig.tight_layout(rect=[0, 0.06, 1, 1])
    figs["primary_recovery"] = fig
    artists["primary_recovery"] = (image, texts)
    fig, axes = plt.subplots(2, 2, figsize=(9, 6.9), sharex=True, sharey=True)
    lines = []
    h = ["0", "1/4", "1/2", "1"]
    x = [0, 25, 50, 100]
    for ax, k in zip(axes.flat, COMMODITIES):
        for color, s in zip(COLORS, STATES):
            for support, style in [("strict", "-"), ("pooled", "--")]:
                y = [
                    100
                    * float(
                        Q(rows[k, s, delta, "1", support]["recovery_fraction_exact"])
                    )
                    for delta in h
                ]
                (line,) = ax.plot(
                    x,
                    y,
                    color=color,
                    linestyle=style,
                    marker="o" if support == "strict" else None,
                    markersize=3,
                    linewidth=1.6,
                )
                lines.append((k, s, support, line))
        ax.set_title(NAMES[k], loc="left", fontweight="bold")
        ax.set_ylim(0, 103)
        ax.set_xlim(0, 100)
        ax.set_xticks(x)
        ax.grid(axis="y", alpha=0.18)
    fig.supylabel("Recoverable share of affected estimated tonnage (%)")
    fig.supxlabel(
        "Hypothetical additional gateway headroom (% of baseline flow)", y=0.10
    )
    legend = [
        Line2D([0], [0], color=c, label=SHORT[s]) for c, s in zip(COLORS, STATES)
    ] + [
        Line2D([0], [0], color="#333333", linestyle="-", label="Strict support"),
        Line2D([0], [0], color="#333333", linestyle="--", label="Pooled support"),
    ]
    fig.legend(
        handles=legend,
        loc="lower center",
        ncol=6,
        frameon=False,
        bbox_to_anchor=(0.5, 0.025),
        fontsize=9,
    )
    fig.suptitle(
        "Capacity and corridor support assumptions change feasible recovery",
        x=0.07,
        ha="left",
        fontweight="bold",
        fontsize=13,
    )
    fig.tight_layout(rect=[0.02, 0.15, 1, 0.95])
    figs["headroom_sensitivity"] = fig
    artists["headroom_sensitivity"] = lines
    fig, ax = plt.subplots(figsize=(8.6, 6.4))
    labels = []
    gaps = []
    for k in COMMODITIES:
        for s in STATES:
            labels.append(NAMES[k] + " / " + SHORT[s])
            gaps.append(float(Q(rows[k, s, "1/4", "1", "strict"]["gap_exact"])))
    bars = ax.barh(range(16), gaps, color="#126789", height=0.62)
    ax.set_yticks(range(16), labels, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlim(0, max(gaps) * 1.27)
    ax.grid(axis="x", alpha=0.18)
    ax.set_axisbelow(True)
    for y, q in enumerate(gaps):
        ax.text(q + max(gaps) * 0.015, y, f"{q:.3f}", va="center", fontsize=9)
    ax.set_xlabel(
        "Optimal recovery minus deterministic greedy recovery (thousand short tons)"
    )
    ax.set_title(
        "Allocation gains are conditional on the same hypothetical constraints",
        loc="left",
        fontweight="bold",
        pad=14,
    )
    fig.text(
        0.02,
        0.018,
        "Primary held settings; zeros retained. Decimal arithmetic does not imply physical measurement precision.",
        fontsize=8.5,
        color="#333333",
    )
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    figs["greedy_gap"] = fig
    artists["greedy_gap"] = bars
    return figs, artists


def main(root="."):
    root = Path(root)
    out = root / "figures"
    out.mkdir(exist_ok=True)
    figs, _ = build(root)
    hashes = {}
    for name, fig in figs.items():
        for suffix in ["pdf", "svg", "png"]:
            p = out / (name + "." + suffix)
            fig.savefig(p, dpi=170, bbox_inches="tight")
            if suffix == "svg":
                p.write_bytes(
                    (
                        "\n".join(
                            line.rstrip()
                            for line in p.read_text(encoding="utf-8").splitlines()
                        )
                        + "\n"
                    ).encode("utf-8")
                )
            hashes[p.relative_to(root).as_posix()] = hashlib.sha256(
                p.read_bytes()
            ).hexdigest()
        plt.close(fig)
    (out / "MANIFEST.json").write_text(
        json.dumps(hashes, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"original_figures": len(figs), "files": len(hashes)}))


if __name__ == "__main__":
    main()
