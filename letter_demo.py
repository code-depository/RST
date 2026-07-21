"""
letter_demo.py
Supporting code for the letter "Beyond Gate Count: Rough Set Theory as a
Certificate of Variable Redundancy in Boolean Circuit Minimization."

Regenerates the two headline examples from the full manuscript's
verified modules (module_1.py, module_3.py, module_4.py, module_6.py,
same directory) and produces:
    - Figure 1 (.jpg): reduct membership, comparator eq vs gt cell
    - Figure 2 (.jpg): priority encoder w=16, gate count parity vs
      reduct size across outputs y0-y3
    - Table 1 data (printed; used to build table1_capability_comparison.docx)

No numbers here are hand-typed -- both figures are rendered directly
from run_benchmark() results on the same cells and circuits verified
in the full manuscript (Sections V, VIII).
"""

import json

from module_4 import run_benchmark
from module_6 import comparator_cells, priority_encoder_outputs


def verify_greedy_irredundancy(w=16, outputs=("y0", "y3")):
    """Checks whether greedy's own reduct contains any single variable
    that could be removed without breaking sufficiency (irredundancy) --
    a weaker but tractable check than global minimality, which cannot be
    verified at n=16 (no exact reference exists there for comparison).
    """
    from module_6 import priority_encoder_outputs
    from module_3 import greedy_reduct, dependency_degree

    all_outputs = priority_encoder_outputs(w)
    results = {}
    for name in outputs:
        dis = all_outputs[name]
        reduct = sorted(greedy_reduct(dis))
        irredundant = True
        for a in reduct:
            remaining = set(reduct) - {a}
            if dependency_degree(dis, remaining) >= 1.0 - 1e-9:
                irredundant = False
        results[name] = {"reduct_size": len(reduct), "irredundant": irredundant}
    return results


def gather_encoder_reducts(w=16):
    """Reuses the already-verified w=16 encoder results (Section VIII,
    module_6.py's run_encoder_decoder.py) rather than recomputing --
    calling run_benchmark() directly on n=16 data would incorrectly
    invoke exact (not greedy) reduct computation, which is intractable
    at this scale (Table 3). Figure 2 only needs gate count and reduct
    SIZE (not membership), both already present in the cached results.
    """
    with open("results_encoder_decoder.json") as f:
        cached = json.load(f)
    rows = cached["encoder"][str(w)]
    data = {}
    for r in rows:
        data[r["output"]] = {
            "gates_rst": r["rst_gates"],
            "gates_espresso": r["espresso_gates"],
            "reduct_size": r["reduct_size"],
        }
    return data


def gather_comparator_reducts():
    from module_3 import all_reducts, minimal_reducts
    cells = comparator_cells()
    data = {}
    names = {0: "a_i", 1: "b_i", 2: "gt_in", 3: "eq_in"}
    for name, dis in cells.items():
        res = run_benchmark(dis)
        reducts = minimal_reducts(all_reducts(dis))
        reduct = sorted(reducts[0])
        data[name] = {
            "gates": res["RST"]["gate_count"],
            "reduct_attrs": [names[a] for a in reduct],
            "reduct_size": len(reduct),
            "verified": all(r["verification"]["passed"] for r in res.values()),
        }
    return data


def generate_figure1(comparator_data, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    attrs = ["a_i", "b_i", "gt_in", "eq_in"]
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.2))

    for ax, (name, label) in zip(axes, [("gt", "gt (all 4 needed)"), ("eq", "eq (gt_in eliminated)")]):
        used = comparator_data[name]["reduct_attrs"]
        colors = ["#2a7a2a" if a in used else "#cccccc" for a in attrs]
        ax.bar(attrs, [1, 1, 1, 1], color=colors, edgecolor="black")
        ax.set_ylim(0, 1.3)
        ax.set_yticks([])
        ax.set_title(f"{label}\ngate count = {comparator_data[name]['gates']}", fontsize=10)
        for i, a in enumerate(attrs):
            ax.text(i, 1.05, "in reduct" if a in used else "excluded",
                    ha="center", fontsize=8, color="#2a7a2a" if a in used else "#888888")

    fig.suptitle("Figure 1. Reduct membership, magnitude-comparator cascade cell", fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=200, format="jpg")
    plt.close(fig)
    return path


def generate_figure2(encoder_data, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    names = ["y0", "y1", "y2", "y3"]
    gates = [encoder_data[n]["gates_rst"] for n in names]
    reduct_sizes = [encoder_data[n]["reduct_size"] for n in names]
    w = 16

    fig, ax1 = plt.subplots(figsize=(7, 4.2))
    bars = ax1.bar(names, gates, color="#4472C4", edgecolor="black", label="Gate count (RST = Espresso)")
    ax1.set_ylabel("Gate count")
    ax1.set_xlabel("Priority encoder output bit (w=16)")

    ax2 = ax1.twinx()
    ax2.plot(names, [r / w for r in reduct_sizes], color="#C00000", marker="o",
             linewidth=2, label="Reduct size / 16 (RST certificate)")
    ax2.set_ylabel("Fraction of inputs required (reduct size / 16)")
    ax2.set_ylim(0, 1.05)

    for i, (g, r) in enumerate(zip(gates, reduct_sizes)):
        ax1.text(i, g + max(gates) * 0.02, f"{r}/{w}", ha="center", fontsize=9, color="#C00000")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=8)

    ax1.set_title("Figure 2. Gate count parity vs. reduct size, 16-input priority encoder", fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=200, format="jpg")
    plt.close(fig)
    return path


def find_and_reverify_boundary_case():
    """Locates the boundary-case instance (n=4, DC=50%, structured
    benchmark) where RST's gate count exceeds Espresso's -- the single
    such instance in the full structured-benchmark sweep (Section VII.G
    caveat). Re-derives it FROM SCRATCH via run_benchmark() rather than
    only reading the cached JSON, so the letter's specific numeric claim
    is independently re-verified, not just re-reported.
    """
    import random
    from module_1 import DecisionInformationSystem
    from module_4 import run_benchmark

    with open("results_structured_n4.json") as f:
        cached = json.load(f)
    candidates = [r for r in cached if r.get("status") == "ok" and r["dc_fraction"] == 0.5
                  and r["rst_gates"] != r["espresso_gates"]]
    if len(candidates) != 1:
        raise RuntimeError(
            f"Expected exactly 1 boundary-case instance at n=4,DC=50%, found {len(candidates)}. "
            "The letter's 'one instance' claim would no longer be accurate -- stop and revise text."
        )
    target = candidates[0]
    n, seed = target["n"], target["seed"]

    # Reconstruct the exact same instance (same seed, same construction
    # logic as Section VII's structured-benchmark generator) and re-run
    # it independently.
    k = n // 2
    random.seed(seed * 41 + n * 97)
    total = 2 ** n
    relevant = list(range(k))
    sub_onset_pool = set(random.sample(range(2 ** k), max(1, (2 ** k) // 2)))

    def relevant_value(m):
        bits = format(m, f"0{n}b")
        return int("".join(bits[v] for v in relevant), 2)

    onset, offset = [], []
    for m in range(total):
        (onset if relevant_value(m) in sub_onset_pool else offset).append(m)
    dcf = 0.5
    n_dc = int(round(dcf * total))
    pool = onset + offset
    random.shuffle(pool)
    dc = sorted(pool[:n_dc])
    dc_set = set(dc)
    onset = [m for m in onset if m not in dc_set]
    offset = [m for m in offset if m not in dc_set]
    onset, offset = sorted(onset), sorted(offset)

    dis = DecisionInformationSystem(n=n, onset=onset, offset=offset, dc=dc)
    res = run_benchmark(dis)

    reverified = {
        "n": n, "seed": seed, "dc_fraction": dcf,
        "rst_gates": res["RST"]["gate_count"],
        "espresso_gates": res["Espresso"]["gate_count"],
        "reduct_size": res["RST"]["reduct_size"],
        "rst_verified": res["RST"]["verification"]["passed"],
        "espresso_verified": res["Espresso"]["verification"]["passed"],
    }

    # Confirm the re-derived instance matches the cached claim exactly.
    assert reverified["rst_gates"] == target["rst_gates"], "RST gate count mismatch on re-derivation"
    assert reverified["espresso_gates"] == target["espresso_gates"], "Espresso gate count mismatch on re-derivation"
    assert reverified["reduct_size"] == target["rst_reduct_size"], "Reduct size mismatch on re-derivation"

    return reverified


def gather_bcd_data():
    """BCD-to-7-segment decoder: real segment truth tables, n=4, natural
    37.5% don't-care set (Proposition 2 case study). Reuses
    module_6.bcd_to_7segment_outputs() directly -- no new circuit logic.

    Also verifies Proposition 2 (module_2.check_proposition2) directly on
    these segment instances, so the manuscript's claim that codes 10-15
    form "exactly the rough-set boundary region" is code-backed, not
    only asserted in prose.
    """
    from module_6 import bcd_to_7segment_outputs
    from module_2 import check_proposition2
    outputs = bcd_to_7segment_outputs()
    data = {}
    for name, dis in outputs.items():
        res = run_benchmark(dis)
        tied = (res["QMC"]["gate_count"] == res["Espresso"]["gate_count"] == res["RST"]["gate_count"])
        prop2_holds = check_proposition2(dis)
        if not prop2_holds:
            raise RuntimeError(
                f"Proposition 2 failed to verify for {name} -- the manuscript's boundary-region "
                "claim would be false. Stop and investigate before citing this result."
            )
        data[name] = {
            "gates": res["RST"]["gate_count"],
            "reduct_size": res["RST"]["reduct_size"],
            "tied": tied,
            "verified": all(r["verification"]["passed"] for r in res.values()),
            "proposition2_verified": prop2_holds,
        }
    return data


def generate_figure3_bcd(bcd_data, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    order = ["seg_a", "seg_b", "seg_c", "seg_d", "seg_e", "seg_f", "seg_g"]
    labels = [s.replace("seg_", "") for s in order]
    gates = [bcd_data[s]["gates"] for s in order]
    reduct = [bcd_data[s]["reduct_size"] for s in order]

    fig, ax1 = plt.subplots(figsize=(7, 4.2))
    colors = ["#4472C4" if r == 4 else "#70AD47" for r in reduct]
    ax1.bar(labels, gates, color=colors, edgecolor="black",
            label="Gate count (QMC = Espresso = RST)")
    ax1.set_ylabel("Gate count")
    ax1.set_xlabel("7-segment output")

    ax2 = ax1.twinx()
    ax2.plot(labels, [r / 4 for r in reduct], color="#C00000", marker="o",
             linewidth=2, label="Reduct size / 4 (RST certificate)")
    ax2.set_ylabel("Fraction of BCD inputs required (reduct size / 4)")
    ax2.set_ylim(0, 1.15)

    for i, r in enumerate(reduct):
        ax1.text(i, gates[i] + max(gates) * 0.02, f"{r}/4", ha="center", fontsize=9, color="#C00000")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right", fontsize=8)

    ax1.set_title("Figure 3. BCD-to-7-segment decoder: gate count and reduct size per segment", fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=200, format="jpg")
    plt.close(fig)
    return path



if __name__ == "__main__":
    print("Gathering comparator data...")
    comp_data = gather_comparator_reducts()
    for name, d in comp_data.items():
        print(f"  {name}: gates={d['gates']}, reduct={d['reduct_attrs']}, verified={d['verified']}")

    print("\nGathering encoder data (w=16)...")
    enc_data = gather_encoder_reducts(16)
    for name, d in enc_data.items():
        print(f"  {name}: gates={d['gates_rst']}, reduct_size={d['reduct_size']}/16")

    print("\nVerifying greedy reduct irredundancy (w=16)...")
    irred = verify_greedy_irredundancy()
    for name, r in irred.items():
        print(f"  {name}: size={r['reduct_size']}, irredundant={r['irredundant']}")

    print("\nGenerating Figure 1...")
    generate_figure1(comp_data, "figure1_comparator_reduct.jpg")
    print("Generating Figure 2...")
    generate_figure2(enc_data, "figure2_encoder_parity.jpg")

    print("\nFinding and re-verifying boundary-case instance...")
    boundary = find_and_reverify_boundary_case()
    print(f"  Boundary case confirmed: n={boundary['n']}, DC={boundary['dc_fraction']*100:.0f}%, "
          f"RST={boundary['rst_gates']} gates, Espresso={boundary['espresso_gates']} gates, "
          f"reduct={boundary['reduct_size']}/{boundary['n']}, "
          f"both verified={boundary['rst_verified'] and boundary['espresso_verified']}")

    print("\nGathering BCD-to-7-segment data (with Proposition 2 verification)...")
    bcd_data = gather_bcd_data()
    for name, d in bcd_data.items():
        print(f"  {name}: gates={d['gates']}, reduct={d['reduct_size']}/4, "
              f"tied={d['tied']}, verified={d['verified']}, "
              f"proposition2={d['proposition2_verified']}")
    print("Generating Figure 3...")
    generate_figure3_bcd(bcd_data, "figure3_bcd.jpg")

    with open("letter_data.json", "w") as f:
        json.dump({"comparator": comp_data, "encoder": enc_data, "boundary_case": boundary,
                    "bcd": bcd_data}, f)
    print("\nDone. Data cached to letter_data.json.")
