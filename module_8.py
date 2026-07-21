"""
module_8.py
Section X -- Limitations and Future Work

Empirically compares RST-greedy reduct size against the exact minimal
reduct size, at n <= 10 where exact computation remains feasible as a
reference (Section X.B). This is the source of the "84/84 instances,
no gap observed" claim reported in Section X -- generated here, not
hand-typed, so the claim is independently reproducible.

IMPORTANT CAVEAT (stated in the manuscript text, repeated here in code):
this comparison is only possible at n <= 10. At the n > 10 sizes where
greedy mode is actually deployed (Section VIII, w=12/16 case studies),
there is no tractable exact reduct to compare against -- greedy's
quality at the scale that matters remains uncharacterized by this
experiment. A "no gap observed" result here is not a general optimality
guarantee: greedy forward-selection is a form of greedy set-cover, a
class of heuristic with known worst-case suboptimality on adversarially
constructed instances, even when it performs well on typical instances.

Depends on module_1.py, module_3.py (same directory).
"""

from typing import Dict, List

from module_1 import DecisionInformationSystem, random_truth_table
from module_3 import all_reducts, minimal_reducts, greedy_reduct, structured_truth_table

N_VALUES = [4, 6, 8, 10]
RANDOM_INSTANCES_PER_N = 15


def compare_random(n: int, instances: int = RANDOM_INSTANCES_PER_N) -> List[Dict]:
    rows = []
    for seed in range(instances):
        onset, offset, dc = random_truth_table(n, 0.0, seed=seed * 23 + n)
        if not onset or not offset:
            continue
        dis = DecisionInformationSystem(n=n, onset=onset, offset=offset, dc=[])
        exact_size = min(len(r) for r in minimal_reducts(all_reducts(dis)))
        greedy_size = len(greedy_reduct(dis))
        rows.append({
            "n": n, "type": "random", "seed": seed,
            "exact_size": exact_size, "greedy_size": greedy_size,
            "matched": greedy_size == exact_size,
        })
    return rows


def compare_structured(n: int) -> List[Dict]:
    rows = []
    for k in range(1, n):
        onset, offset = structured_truth_table(n, list(range(k)), seed=k * 17 + n)
        if not onset or not offset:
            continue
        dis = DecisionInformationSystem(n=n, onset=onset, offset=offset, dc=[])
        exact_size = min(len(r) for r in minimal_reducts(all_reducts(dis)))
        greedy_size = len(greedy_reduct(dis))
        rows.append({
            "n": n, "type": "structured", "k_relevant": k, "seed": k,
            "exact_size": exact_size, "greedy_size": greedy_size,
            "matched": greedy_size == exact_size,
        })
    return rows


def run_full_comparison() -> List[Dict]:
    all_rows = []
    for n in N_VALUES:
        all_rows.extend(compare_random(n))
        all_rows.extend(compare_structured(n))
    return all_rows


def summarize(rows: List[Dict]) -> Dict:
    total = len(rows)
    matched = sum(1 for r in rows if r["matched"])
    mismatches = [r for r in rows if not r["matched"]]
    overhead = [r["greedy_size"] - r["exact_size"] for r in mismatches]
    return {
        "total": total,
        "matched": matched,
        "match_rate": matched / total if total else 0.0,
        "n_mismatches": len(mismatches),
        "mean_overhead": sum(overhead) / len(overhead) if overhead else 0.0,
        "max_overhead": max(overhead) if overhead else 0,
    }


if __name__ == "__main__":
    rows = run_full_comparison()
    s = summarize(rows)
    print(f"Greedy vs. exact reduct comparison, n in {N_VALUES} "
          f"(random + structured instances):")
    print(f"  {s['matched']}/{s['total']} instances: greedy matched exact minimal reduct size")
    if s["n_mismatches"]:
        print(f"  {s['n_mismatches']} mismatches: mean overhead={s['mean_overhead']:.2f} "
              f"attributes, max={s['max_overhead']}")
    else:
        print("  No mismatches observed in this sweep.")
        print("  NOTE: this does not constitute a general optimality guarantee for")
        print("  RST-greedy -- see Section X.B for the full caveat. This comparison")
        print("  is only possible at n<=10; greedy's quality at n>10 (where it is")
        print("  actually used, Section VIII) remains uncharacterized.")
