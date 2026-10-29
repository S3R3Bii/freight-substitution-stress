"""Independent exact graph reconstruction and primal/cut optimality witnesses.

Does not import the solver, production graph builder or production greedy routine.
"""

import argparse, csv, gzip, itertools, json
from collections import defaultdict, deque
from fractions import Fraction as Q
from pathlib import Path
from verify_source import verify as verify_source


def reference_edges(cells, k, closed, h, b, support):
    records = [(o, g, d, Q(q)) for kk, o, g, d, q, n in cells if kk == k]
    by_gate = defaultdict(Q)
    by_origin_gate = defaultdict(Q)
    by_gate_dest = defaultdict(Q)
    individual = defaultdict(Q)
    demands = defaultdict(Q)
    for o, g, d, q in records:
        by_gate[g] += q
        by_origin_gate[o, g] += q
        by_gate_dest[g, d] += q
        individual[o, g, d] += q
        if g == closed and q:
            demands[o, d] += q
    edges = {}
    for g, total in sorted(by_gate.items()):
        if g == closed:
            continue
        edges["S", f"G{g}"] = Q(h) * total
        for o in sorted(set(o for o, d in demands)):
            if by_origin_gate[o, g] == 0:
                continue
            node = f"A{o}:{g}"
            edges[f"G{g}", node] = by_origin_gate[o, g]
            for oo, d in sorted(demands):
                if oo != o:
                    continue
                cap = Q(b) * (
                    individual[o, g, d] if support == "strict" else by_gate_dest[g, d]
                )
                if cap:
                    edges[node, f"D{o}:{d}"] = cap
    edges.update({(f"D{o}:{d}", "T"): q for (o, d), q in demands.items()})
    return edges, demands


def check_witness(edges, proof_flows, scale, expected, cut=None):
    assert isinstance(scale, int) and scale > 0
    balance = defaultdict(Q)
    flows = {}
    checks = 0
    for u, v, ticks in proof_flows:
        assert isinstance(ticks, int) and ticks > 0 and (u, v) not in flows
        q = Q(ticks, scale)
        assert (u, v) in edges and q <= edges[u, v]
        flows[u, v] = q
        balance[u] -= q
        balance[v] += q
        checks += 4
    for node, q in balance.items():
        assert q == (-expected if node == "S" else expected if node == "T" else 0)
        checks += 1
    assert -balance["S"] == balance["T"] == expected
    checks += 2
    for edge, cap in edges.items():
        assert 0 <= flows.get(edge, 0) <= cap
        checks += 1
    if cut is not None:
        left = set(cut)
        nodes = {n for edge in edges for n in edge} | {"S", "T"}
        assert (
            len(left) == len(cut) and "S" in left and "T" not in left and left <= nodes
        )
        checks += 4
        capacity = sum(
            (cap for (u, v), cap in edges.items() if u in left and v not in left), Q(0)
        )
        assert capacity == expected
        checks += 1
        residual = defaultdict(set)
        for (u, v), cap in edges.items():
            q = flows.get((u, v), Q(0))
            if cap > q:
                residual[u].add(v)
            if q:
                residual[v].add(u)
        reachable = {"S"}
        queue = deque(["S"])
        while queue:
            for v in residual[queue.popleft()]:
                if v not in reachable:
                    reachable.add(v)
                    queue.append(v)
        assert reachable == left
        checks += 1
    return checks, flows


def independent_greedy(edges, demands):
    used = defaultdict(Q)
    picked = defaultdict(Q)
    value = Q(0)
    gates = sorted(int(v[1:]) for u, v in edges if u == "S")
    for origin, destination in sorted(demands):
        for gateway in gates:
            path = (
                ("S", f"G{gateway}"),
                (f"G{gateway}", f"A{origin}:{gateway}"),
                (f"A{origin}:{gateway}", f"D{origin}:{destination}"),
                (f"D{origin}:{destination}", "T"),
            )
            available = [edges.get(e, Q(0)) - used[e] for e in path]
            q = min(available)
            if q > 0:
                value += q
                for e in path:
                    used[e] += q
                    picked[e] += q
    return value, {e: q for e, q in picked.items() if q}


def verify(root=".", phase="development", results=None):
    root = Path(root)
    results = Path(results) if results else root / "results"
    source, cells = verify_source(root)
    cfg = json.loads((root / "protocol.json").read_text(encoding="utf-8"))
    rows = list(
        csv.DictReader((results / (phase + ".csv")).open(encoding="utf-8", newline=""))
    )
    certificates = json.loads(
        gzip.decompress((results / (phase + "-certificates.json.gz")).read_bytes())
    )
    proofs = {p["case"]: p for p in certificates}
    assert len(proofs) == len(certificates) == len(rows) == 256
    expected = set(
        itertools.product(
            cfg[phase + "_commodities"],
            cfg["closed_entry_states"],
            cfg["gateway_headroom"],
            cfg["corridor_multiplier"],
            cfg["support"],
        )
    )
    seen = set()
    comparisons = {}
    checks = 0
    flow_edges = 0
    zero_cases = 0
    for row in rows:
        k, closed = int(row["commodity"]), int(row["closed_state"])
        h, b, s = row["delta"], row["beta"], row["support"]
        identity = (k, closed, h, b, s)
        assert identity in expected and identity not in seen and row["phase"] == phase
        seen.add(identity)
        checks += 3
        case = f'k{k:02d}-s{closed:02d}-h{h.replace("/","_")}-b{b.replace("/","_")}-{s}'
        assert row["case"] == case
        proof = proofs[case]
        edges, demands = reference_edges(cells, k, closed, h, b, s)
        demand = sum(demands.values(), Q(0))
        recovered = Q(row["recovered_exact"])
        greedy = Q(row["greedy_exact"])
        assert (
            Q(row["demand_exact"]) == demand
            and Q(row["unmet_exact"]) == demand - recovered
            and Q(row["gap_exact"]) == recovered - greedy
        )
        checks += 3
        assert 0 <= greedy <= recovered <= demand
        checks += 1
        assert row["no_reroute_exact"] == "0"
        checks += 1
        assert row["recovery_fraction_exact"] == (
            str(recovered / demand) if demand else "NA"
        )
        zero_cases += demand == 0
        checks += 1
        count, flow = check_witness(
            edges, proof["flow"], proof["scale"], recovered, proof["source_cut"]
        )
        checks += count
        flow_edges += len(flow)
        count, gflow = check_witness(
            edges, proof["greedy_flow"], proof["scale"], greedy
        )
        checks += count
        reference_value, reference_flow = independent_greedy(edges, demands)
        assert greedy == reference_value and gflow == reference_flow
        checks += 2
        assert (
            len(edges) == int(row["edge_count"])
            and len(flow) == int(row["positive_flow_edges"])
            and len(proof["source_cut"]) == int(row["cut_nodes"])
        )
        checks += 3
        comparisons[identity] = recovered
    assert seen == expected
    monotone = 0
    for (k, c, h, b, s), value in comparisons.items():
        for other_h in cfg["gateway_headroom"]:
            if Q(other_h) >= Q(h):
                assert comparisons[k, c, other_h, b, s] >= value
                monotone += 1
        for other_b in cfg["corridor_multiplier"]:
            if Q(other_b) >= Q(b):
                assert comparisons[k, c, h, other_b, s] >= value
                monotone += 1
        if s == "strict":
            assert comparisons[k, c, h, b, "pooled"] >= value
            monotone += 1
        if Q(h) == 0:
            assert value == 0
            checks += 1
    return dict(
        status="PASS",
        phase=phase,
        cases=len(rows),
        exact_checks=checks,
        monotonicity_checks=monotone,
        positive_flow_edges=flow_edges,
        zero_demand_cases=zero_cases,
        optimality="Every exact feasible flow equals a separately reconstructed cut capacity; residual reachability also checked",
        source_projection_checks=source["projection_checks"],
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("phase", choices=["development", "held"])
    p.add_argument("--root", default=".")
    p.add_argument("--results")
    p.add_argument("--output")
    a = p.parse_args()
    result = verify(a.root, a.phase, a.results)
    if a.output:
        Path(a.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
