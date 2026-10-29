"""Exact finite-scenario allocation; capacities are hypothetical conventions."""

import csv, gzip, io, json, math, time
from datetime import datetime, timezone
from collections import defaultdict, deque
from fractions import Fraction
from pathlib import Path


def load_facts(root):
    data = defaultdict(lambda: defaultdict(Fraction))
    for row in csv.DictReader(
        io.StringIO(
            gzip.decompress(
                (Path(root) / "data/source/flows.csv.gz").read_bytes()
            ).decode()
        )
    ):
        data[int(row["sctg2"])][
            (int(row["fr_orig"]), int(row["dms_origst"]), int(row["dms_destst"]))
        ] += Fraction(row["tons_2022"])
    return data


def graph(facts, closed, delta, beta, support):
    scale = 4
    for value in facts.values():
        scale = math.lcm(scale, 4 * value.denominator)
    totals = defaultdict(Fraction)
    origin = defaultdict(Fraction)
    corridor = defaultdict(Fraction)
    demand = {}
    for (o, g, d), value in facts.items():
        totals[g] += value
        origin[o, g] += value
        corridor[g, d] += value
        if g == closed and value > 0:
            demand[o, d] = value
    caps = {}

    def add(u, v, value):
        ticks = value * scale
        assert ticks.denominator == 1 and ticks >= 0 and (u, v) not in caps
        caps[u, v] = int(ticks)

    for g in sorted(totals):
        if g == closed:
            continue
        add("S", f"G{g}", delta * totals[g])
        for o in sorted({o for o, d in demand}):
            if origin[o, g] <= 0:
                continue
            a = f"A{o}:{g}"
            add(f"G{g}", a, origin[o, g])
            for oo, d in sorted(demand):
                if oo != o:
                    continue
                base = (
                    facts.get((o, g, d), Fraction(0))
                    if support == "strict"
                    else corridor[g, d]
                )
                if base > 0:
                    add(a, f"D{o}:{d}", beta * base)
    for (o, d), value in sorted(demand.items()):
        add(f"D{o}:{d}", "T", value)
    return caps, scale, demand


def maximum_flow(caps):
    """Residual level graphs permit reallocation; no floating tolerances."""
    adjacency = defaultdict(list)
    refs = []
    for (u, v), cap in sorted(caps.items()):
        i = len(adjacency[u])
        j = len(adjacency[v])
        adjacency[u].append([v, j, cap])
        adjacency[v].append([u, i, 0])
        refs.append((u, i, v, cap))
    total = 0
    while True:
        level = {"S": 0}
        queue = deque(["S"])
        while queue:
            u = queue.popleft()
            for v, rev, remaining in adjacency[u]:
                if remaining > 0 and v not in level:
                    level[v] = level[u] + 1
                    queue.append(v)
        if "T" not in level:
            break
        cursor = defaultdict(int)

        def send(u, amount):
            if u == "T":
                return amount
            while cursor[u] < len(adjacency[u]):
                edge = adjacency[u][cursor[u]]
                v, rev, remaining = edge
                if remaining > 0 and level.get(v) == level[u] + 1:
                    pushed = send(v, min(amount, remaining))
                    if pushed:
                        edge[2] -= pushed
                        adjacency[v][rev][2] += pushed
                        return pushed
                cursor[u] += 1
            return 0

        while True:
            pushed = send("S", sum(cap for (u, v), cap in caps.items() if u == "S"))
            if not pushed:
                break
            total += pushed
    flows = [
        [u, v, cap - adjacency[u][i][2]]
        for u, i, v, cap in refs
        if cap - adjacency[u][i][2] > 0
    ]
    return total, flows, sorted(level)


def greedy_flow(caps, demand):
    residual = dict(caps)
    value = 0
    flows = defaultdict(int)
    gateways = sorted(int(v[1:]) for u, v in caps if u == "S")
    for o, d in sorted(demand):
        for g in gateways:
            path = [
                ("S", f"G{g}"),
                (f"G{g}", f"A{o}:{g}"),
                (f"A{o}:{g}", f"D{o}:{d}"),
                (f"D{o}:{d}", "T"),
            ]
            amount = min(residual.get(edge, 0) for edge in path)
            if amount:
                for edge in path:
                    residual[edge] -= amount
                    flows[edge] += amount
                value += amount
    return value, [[u, v, q] for (u, v), q in sorted(flows.items())]


def run_phase(root, phase, output):
    root = Path(root)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    cfg = json.loads((root / "protocol.json").read_text(encoding="utf-8"))
    facts = load_facts(root)
    rows = []
    proofs = []
    execution = []
    for k in cfg[phase + "_commodities"]:
        for closed in cfg["closed_entry_states"]:
            for delta_s in cfg["gateway_headroom"]:
                for beta_s in cfg["corridor_multiplier"]:
                    for support in cfg["support"]:
                        started = datetime.now(timezone.utc).isoformat()
                        clock = time.perf_counter()
                        delta, beta = Fraction(delta_s), Fraction(beta_s)
                        caps, scale, demand = graph(
                            facts[k], closed, delta, beta, support
                        )
                        recovered, flow, cut = maximum_flow(caps)
                        greedy, gflow = greedy_flow(caps, demand)
                        total = sum(demand.values(), Fraction(0))
                        r = Fraction(recovered, scale)
                        g = Fraction(greedy, scale)
                        case = f'k{k:02d}-s{closed:02d}-h{delta_s.replace("/","_")}-b{beta_s.replace("/","_")}-{support}'
                        row = dict(
                            phase=phase,
                            case=case,
                            commodity=k,
                            closed_state=closed,
                            delta=delta_s,
                            beta=beta_s,
                            support=support,
                            demand_exact=str(total),
                            recovered_exact=str(r),
                            unmet_exact=str(total - r),
                            recovery_fraction_exact=str(r / total) if total else "NA",
                            greedy_exact=str(g),
                            no_reroute_exact="0",
                            gap_exact=str(r - g),
                            edge_count=len(caps),
                            positive_flow_edges=len(flow),
                            cut_nodes=len(cut),
                        )
                        rows.append(row)
                        proofs.append(
                            dict(
                                case=case,
                                scale=scale,
                                flow=flow,
                                greedy_flow=gflow,
                                source_cut=cut,
                            )
                        )
                        execution.append(
                            dict(
                                case=case,
                                started_utc=started,
                                elapsed_seconds=time.perf_counter() - clock,
                                status="COMPUTED",
                                seed=None,
                            )
                        )
    with (output / (phase + ".csv")).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    packed = json.dumps(proofs, separators=(",", ":"), sort_keys=True).encode()
    (output / (phase + "-certificates.json.gz")).write_bytes(
        gzip.compress(packed, mtime=0)
    )
    (output / (phase + "-execution.json")).write_text(
        json.dumps(execution, indent=2) + "\n", encoding="utf-8"
    )
    return dict(
        phase=phase,
        cases=len(rows),
        certificates=len(proofs),
        claim="Exact optimum of fixed hypothetical network only",
    )
