"""Independently check displayed primary rows, scoped claims and bounded PDF actions."""

import csv, hashlib, json, re, unicodedata
from decimal import Decimal, localcontext, ROUND_HALF_EVEN
from fractions import Fraction as Q
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]


def display(text, n=3):
    q = Q(text)
    with localcontext() as ctx:
        ctx.prec = 60
        value = (Decimal(q.numerator) / Decimal(q.denominator)).quantize(
            Decimal(1).scaleb(-n), rounding=ROUND_HALF_EVEN
        )
        return format(value, ",." + str(n) + "f")


def verify():
    root = ROOT
    tex = (root / "paper/main.tex").read_text(encoding="utf-8")
    summary = (root / "DECISION_SUMMARY.md").read_text(encoding="utf-8")
    checks = 0
    rows = list(
        csv.DictReader((root / "results/held.csv").open(encoding="utf-8", newline=""))
    )
    primary = [
        r
        for r in rows
        if r["delta"] == "1/4" and r["beta"] == "1" and r["support"] == "strict"
    ]
    assert len(primary) == 16
    checks += 1
    names = {
        5: "Meat/seafood",
        17: "Gasoline",
        34: "Machinery",
        36: "Motorized vehicles",
    }
    states = {6: "CA", 48: "TX", 36: "NY", 53: "WA"}
    for r in primary:
        share = display(str(100 * Q(r["recovery_fraction_exact"])), 1)
        fields = [
            names[int(r["commodity"])],
            states[int(r["closed_state"])],
            display(r["demand_exact"]),
            display(r["recovered_exact"]),
            display(r["unmet_exact"]),
            share,
            display(r["gap_exact"]),
        ]
        assert " & ".join(fields) + " " + chr(92) * 2 in tex
        checks += 7
        md = "| " + " | ".join(fields[:5] + [share + "%", fields[-1]]) + " |"
        assert md in summary
        checks += 7
    assert (
        min(Q(r["recovery_fraction_exact"]) for r in primary) == 0
        and max(Q(r["recovery_fraction_exact"]) for r in primary) == 1
    )
    checks += 2
    assert (
        sum(Q(r["gap_exact"]) > 0 for r in rows) == 27
        and sum(Q(r["gap_exact"]) > 0 for r in primary) == 3
    )
    checks += 2
    assert display(str(max(Q(r["gap_exact"]) for r in rows))) == "70.630"
    checks += 1
    must = [
        "thousand short tons",
        "hypothetical",
        "not peer reviewed",
        "operational feasibility",
        "rather than a representative sample",
        "No commodity, state, factor, outcome or baseline was selected from held summaries",
        "Separate commodity solves omit competition",
        "source accuracy",
        "1,747,549",
        "759,047",
        "2,304",
    ]
    for phrase in must:
        assert phrase.lower() in tex.lower(), phrase
        checks += 1
    scope = json.loads(
        (root / "paper/PUBLICATION_SCOPE.json").read_text(encoding="utf-8")
    )
    assert (
        scope["scope"] == "independent-program-study"
        and scope["formal_submission_target"] is False
        and len(scope["public_files"]) == 5
    )
    checks += 3
    for name, digest in scope["public_files"].items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
        checks += 1
    reader = PdfReader(root / "paper/manuscript.pdf")
    assert len(reader.pages) == 7
    checks += 1
    text = unicodedata.normalize(
        "NFKC", " ".join(p.extract_text() for p in reader.pages)
    )
    normal = re.sub(r"\s+", " ", text)
    for phrase in [
        "Decision brief",
        "70.630",
        "1,747,549",
        "759,047",
        "thousand short tons",
        "not peer reviewed",
        "Reproduction commands",
    ]:
        assert phrase.lower() in normal.lower(), phrase
        checks += 1
    for cmd in [
        "python -m pip install -r requirements.txt",
        "python -m unittest discover -s tests -v",
        "python src/check_reproduction.py",
        "python src/verify_figures.py",
        "python src/verify_paper.py",
        "python src/verify_public_package.py",
    ]:
        assert cmd in normal, cmd
        checks += 1
    forbidden = [
        "/JavaScript",
        "/JS",
        "/Launch",
        "/EmbeddedFiles",
        "/RichMedia",
        "/AcroForm",
        "/AA",
    ]
    pdfs = [
        root / "paper/manuscript.pdf",
        *sorted((root / "paper/images").glob("*.pdf")),
    ]
    for path in pdfs:
        doc = PdfReader(path)
        catalog = doc.trailer["/Root"]
        assert not any(k in catalog for k in forbidden)
        assert "/EmbeddedFiles" not in catalog.get("/Names", {})
        action = catalog.get("/OpenAction")
        if hasattr(action, "get"):
            assert action.get("/S") not in ["/JavaScript", "/Launch"]
        for page in doc.pages:
            assert not any(k in page for k in forbidden)
            for annotation in page.get("/Annots", []):
                a = annotation.get_object()
                assert not any(k in a for k in ["/AA", "/RichMedia"])
                if "/A" in a:
                    assert a["/A"].get("/S") == "/URI"
        checks += 1
    return dict(
        status="PASS",
        independent_paper_checks=checks,
        displayed_primary_rows=16,
        pdf_pages=7,
        pdf_active_content_checks=len(pdfs),
        scope="Bounded numeric/source/claim/hash/action checks; rendered pages and source rights reviewed separately.",
    )


if __name__ == "__main__":
    result = verify()
    (ROOT / "paper/VERIFICATION.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result))
