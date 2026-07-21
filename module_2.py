"""
module_2.py
Section IV -- Don't-Care Conditions as the Boundary Region

Implements the lower/upper approximation and boundary-region computation
for an incompletely specified Boolean function (Section IV.A), verifies
Proposition 2 (BND(X+) = DC, Section IV.B), and verifies Corollary 1
(implicant validity via approximation bounds, Section IV.C) against
QMC-generated prime implicants from module_1.py.

Depends on module_1.py (same directory): reuses DecisionInformationSystem
and qmc_prime_implicants as the independent source of "real" implicants
to check Corollary 1 against -- Corollary 1 is not tested against itself.

No external dependencies. Run this file directly to execute the
randomized verification sweep.
"""

import random
from typing import FrozenSet, List, Set, Tuple

from module_1 import DecisionInformationSystem, qmc_prime_implicants

Literal = Tuple[int, int]


# ---------------------------------------------------------------------
# Lower / upper approximation and boundary region  (Section IV.A-B)
# ---------------------------------------------------------------------

def lower_approximation(dis: DecisionInformationSystem) -> Set[int]:
    """LOW(X+) = X+ (Section IV.A)."""
    return set(dis.onset)


def upper_approximation(dis: DecisionInformationSystem) -> Set[int]:
    """UPP(X+) = X+ u DC (Section IV.A)."""
    return set(dis.onset) | set(dis.dc)


def boundary_region(dis: DecisionInformationSystem) -> Set[int]:
    """BND(X+) = UPP(X+) \\ LOW(X+) (Section IV.A)."""
    return upper_approximation(dis) - lower_approximation(dis)


def check_proposition2(dis: DecisionInformationSystem) -> bool:
    """Verifies BND(X+) = DC (Proposition 2, Section IV.B)."""
    return boundary_region(dis) == set(dis.dc)


# ---------------------------------------------------------------------
# Implicant coverage and Corollary 1 validity check  (Section IV.C)
# ---------------------------------------------------------------------

def implicant_coverage(term: FrozenSet[Literal], n: int) -> Set[int]:
    """cov(T): the set of minterms covered by product term T."""
    covered = set()
    for m in range(2 ** n):
        bits = format(m, f"0{n}b")
        if all(bits[a] == str(v) for a, v in term):
            covered.add(m)
    return covered


def is_valid_implicant(dis: DecisionInformationSystem, term: FrozenSet[Literal]) -> bool:
    """Corollary 1: T is a valid, non-vacuous implicant of f iff
    cov(T) subset-of UPP(X+) and cov(T) intersect LOW(X+) != empty.
    """
    cov = implicant_coverage(term, dis.n)
    upp = upper_approximation(dis)
    low = lower_approximation(dis)
    return cov.issubset(upp) and len(cov & low) > 0


# ---------------------------------------------------------------------
# Verification harness
# ---------------------------------------------------------------------

def random_truth_table(n: int, dc_fraction: float, seed: int):
    random.seed(seed)
    total = 2 ** n
    minterms = list(range(total))
    random.shuffle(minterms)
    n_dc = int(round(dc_fraction * total))
    dc = sorted(minterms[:n_dc])
    remaining = minterms[n_dc:]
    split = len(remaining) // 2
    return sorted(remaining[:split]), sorted(remaining[split:]), dc


def verify_instance(n: int, dc_fraction: float, seed: int):
    """Returns (prop2_holds, corollary1_holds, n_pis_checked, negative_control_ok)."""
    onset, offset, dc = random_truth_table(n, dc_fraction, seed)
    if not onset:
        return None  # degenerate: constant-0 function, skip
    dis = DecisionInformationSystem(n=n, onset=onset, offset=offset, dc=dc)

    prop2 = check_proposition2(dis)

    # Corollary 1, positive check: every QMC prime implicant computed WITH
    # dc minterms available for combining must be a valid implicant.
    pis = qmc_prime_implicants(n, onset, dc)
    corollary1 = all(is_valid_implicant(dis, pi) for pi in pis)

    # Corollary 1, negative control: a term built from a single offset
    # minterm's full literal assignment must be REJECTED (cov(T) not
    # subset of UPP(X+), since it covers an offset minterm).
    negative_control_ok = True
    if offset:
        bad_term = frozenset((a, int(format(offset[0], f"0{n}b")[a])) for a in range(n))
        if is_valid_implicant(dis, bad_term):
            negative_control_ok = False

    return prop2, corollary1, len(pis), negative_control_ok


if __name__ == "__main__":
    print("=== Worked check: BCD-to-7-segment-style DC structure (n=4) ===")
    # A representative DC pattern: 6 of 16 minterms don't-care (37.5%),
    # matching the BCD-to-7-segment case study referenced in Section IV.E.
    onset = [0, 2, 3, 5, 6, 7, 8, 9]      # example segment onset (illustrative)
    dc = [10, 11, 12, 13, 14, 15]         # invalid BCD codes
    offset = [m for m in range(16) if m not in onset and m not in dc]
    dis = DecisionInformationSystem(n=4, onset=onset, offset=offset, dc=dc)
    print("Proposition 2 (BND(X+) = DC):", check_proposition2(dis))
    print("BND(X+):", sorted(boundary_region(dis)))
    print("DC:     ", sorted(dis.dc))

    print("\n=== Randomized sweep: Proposition 2 and Corollary 1 ===")
    n_values = [3, 4, 5, 6]
    dc_fractions = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
    instances = 10

    total, prop2_pass, cor1_pass, neg_ctrl_pass = 0, 0, 0, 0
    for n in n_values:
        for dcf in dc_fractions:
            for seed in range(instances):
                result = verify_instance(n, dcf, seed=seed * 131 + n)
                if result is None:
                    continue
                prop2, corollary1, n_pis, neg_ok = result
                total += 1
                prop2_pass += int(prop2)
                cor1_pass += int(corollary1)
                neg_ctrl_pass += int(neg_ok)
                if not (prop2 and corollary1 and neg_ok):
                    print(f"  FAILURE at n={n}, dc={dcf}, seed={seed}: "
                          f"prop2={prop2}, corollary1={corollary1}, neg_ctrl={neg_ok}")

    print(f"Proposition 2 confirmed:  {prop2_pass}/{total} instances")
    print(f"Corollary 1 confirmed:    {cor1_pass}/{total} instances")
    print(f"Negative control correct: {neg_ctrl_pass}/{total} instances "
          f"(offset-covering terms correctly rejected)")
