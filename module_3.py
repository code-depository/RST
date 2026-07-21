"""
module_3.py
Section V -- Variable Redundancy Detection

Implements attribute-level reduct computation (exact, via CNF->DNF) and
verifies Proposition 3: a variable is a dummy (functionally irrelevant)
variable of f if and only if it is excluded from a reduct of f's induced
DIS. Ground truth for "dummy variable" is computed by brute-force
truth-table inspection, independent of the reduct machinery, so this is
a genuine cross-check rather than a self-consistency test.

Depends on module_1.py (same directory) for DecisionInformationSystem
and the _absorb subsumption routine's logic (reimplemented locally in
plain-attribute form, since module_1's cnf_to_dnf includes a literal
polarity-conflict check that does not apply to attribute-only sets).

No external dependencies. Run this file directly to execute the
randomized verification sweep.
"""

import random
from typing import Dict, FrozenSet, List, Set

from module_1 import DecisionInformationSystem


# ---------------------------------------------------------------------
# Attribute-level discernibility and reduct computation  (Section II.C)
# ---------------------------------------------------------------------

def attribute_discernibility_matrix(dis: DecisionInformationSystem) -> List[FrozenSet[int]]:
    """Non-empty attribute-level discernibility cells over onset-offset
    pairs (dc minterms excluded, per Section IV.D)."""
    clauses = []
    for mi in dis.onset:
        bi = dis.bits(mi)
        for mj in dis.offset:
            bj = dis.bits(mj)
            attrs = frozenset(a for a in range(dis.n) if bi[a] != bj[a])
            if attrs:
                clauses.append(attrs)
    return clauses


def _absorb(terms) -> Set[FrozenSet[int]]:
    ordered = sorted(terms, key=len)
    kept: List[FrozenSet[int]] = []
    for t in ordered:
        if not any(k <= t for k in kept):
            kept.append(t)
    return set(kept)


def cnf_to_dnf_attributes(clauses: List[FrozenSet[int]]) -> List[FrozenSet[int]]:
    """CNF -> DNF for plain attribute sets (no literal polarity, so no
    conflict check is needed -- any attribute may appear in any term)."""
    if not clauses:
        return [frozenset()]
    terms: Set[FrozenSet[int]] = {frozenset([a]) for a in clauses[0]}
    for clause in clauses[1:]:
        new_terms: Set[FrozenSet[int]] = set()
        for term in terms:
            for a in clause:
                new_terms.add(frozenset(term | {a}))
        terms = _absorb(new_terms)
    return list(terms)


def all_reducts(dis: DecisionInformationSystem) -> List[FrozenSet[int]]:
    clauses = attribute_discernibility_matrix(dis)
    return cnf_to_dnf_attributes(clauses)


def minimal_reducts(reducts: List[FrozenSet[int]]) -> List[FrozenSet[int]]:
    if not reducts:
        return [frozenset()]
    m = min(len(r) for r in reducts)
    return [r for r in reducts if len(r) == m]


# ---------------------------------------------------------------------
# Greedy reduct (n > 10 dispatch, per Table 3 / Section VI.C feasibility)
# ---------------------------------------------------------------------

def dependency_degree(dis: DecisionInformationSystem, attrs) -> float:
    """gamma_B(d): fraction of the (onset+offset) universe whose
    equivalence class under `attrs` is decision-consistent."""
    groups = {}
    onset_set, offset_set = set(dis.onset), set(dis.offset)
    for m in list(dis.onset) + list(dis.offset):
        key = tuple(dis.bits(m)[a] for a in sorted(attrs)) if attrs else ()
        groups.setdefault(key, []).append(m)
    consistent = 0
    for members in groups.values():
        labels = {("+" if m in onset_set else "-") for m in members}
        if len(labels) == 1:
            consistent += len(members)
    total = len(dis.onset) + len(dis.offset)
    return consistent / total if total else 1.0


def greedy_reduct(dis: DecisionInformationSystem) -> FrozenSet[int]:
    """Greedy forward reduct selection for n > 10 (Table 3). Does not
    guarantee minimality -- flagged as a limitation (Section X).

    Implemented via incremental partition refinement (start with one
    group containing the whole universe; at each step, refine by the
    candidate attribute that yields the purest split) rather than
    recomputing groupings from scratch per candidate per iteration --
    the naive version does not scale past n~12 in practice.
    """
    onset_set = set(dis.onset)
    universe = list(dis.onset) + list(dis.offset)
    bitcache = {m: dis.bits(m) for m in universe}
    labels = {m: (m in onset_set) for m in universe}
    total = len(universe)

    groups = [universe]  # current partition, as list of member-lists
    remaining = set(range(dis.n))
    selected = []

    def purity(parts):
        consistent = 0
        for g in parts:
            first_label = labels[g[0]]
            if all(labels[m] == first_label for m in g):
                consistent += len(g)
        return consistent / total

    current_purity = purity(groups)
    full_purity = 1.0  # deterministic function => fully consistent using all attrs

    while remaining and current_purity < full_purity:
        best_attr, best_groups, best_purity = None, None, -1.0
        for a in remaining:
            new_groups = []
            for g in groups:
                by_bit = {}
                for m in g:
                    by_bit.setdefault(bitcache[m][a], []).append(m)
                new_groups.extend(by_bit.values())
            p = purity(new_groups)
            if p > best_purity:
                best_attr, best_groups, best_purity = a, new_groups, p
        selected.append(best_attr)
        remaining.discard(best_attr)
        groups = best_groups
        current_purity = best_purity

    return frozenset(selected)


def compute_reduct(dis: DecisionInformationSystem) -> FrozenSet[int]:
    """Dispatch to exact (n<=10) or greedy (n>10) mode, per Table 3."""
    if dis.n <= 10:
        reducts = all_reducts(dis)
        return min(minimal_reducts(reducts), key=lambda r: (len(r), sorted(r)))
    return greedy_reduct(dis)


# ---------------------------------------------------------------------
# Ground-truth dummy-variable check (independent of reducts)
# ---------------------------------------------------------------------

def full_function_map(dis: DecisionInformationSystem) -> Dict[int, int]:
    """Requires a fully specified function (dc must be empty) -- dummy
    variable status is only well-defined for a total function."""
    if dis.dc:
        raise ValueError("Dummy-variable ground truth requires dc == [] (total function).")
    f = {}
    for m in dis.onset:
        f[m] = 1
    for m in dis.offset:
        f[m] = 0
    return f


def is_dummy_ground_truth(f_map: Dict[int, int], n: int, a: int) -> bool:
    """Brute-force: xa is dummy iff flipping bit a never changes f, for
    every assignment of the other n-1 variables."""
    for m in range(2 ** n):
        flipped = m ^ (1 << (n - 1 - a))  # bit a from the MSB-first bit-string convention
        if f_map[m] != f_map[flipped]:
            return False
    return True


# ---------------------------------------------------------------------
# Verification harness
# ---------------------------------------------------------------------

def structured_truth_table(n: int, relevant_vars: List[int], seed: int):
    """Random total function depending only on `relevant_vars` (Section
    VII structured-benchmark style)."""
    random.seed(seed)
    k = len(relevant_vars)
    sub_onset = set(random.sample(range(2 ** k), max(1, (2 ** k) // 2)))

    def relevant_value(m: int) -> int:
        bits = format(m, f"0{n}b")
        sub_bits = "".join(bits[v] for v in relevant_vars)
        return int(sub_bits, 2)

    onset, offset = [], []
    for m in range(2 ** n):
        (onset if relevant_value(m) in sub_onset else offset).append(m)
    return sorted(onset), sorted(offset)


def random_total_function(n: int, seed: int):
    random.seed(seed)
    total = 2 ** n
    minterms = list(range(total))
    random.shuffle(minterms)
    split = total // 2
    return sorted(minterms[:split]), sorted(minterms[split:])


def check_instance(n: int, onset: List[int], offset: List[int]) -> bool:
    """Checks Proposition 3's iff for every variable a in range(n).
    Returns True iff the equivalence holds for all n variables."""
    dis = DecisionInformationSystem(n=n, onset=onset, offset=offset, dc=[])
    f_map = full_function_map(dis)
    reducts = all_reducts(dis)
    min_reducts = minimal_reducts(reducts)
    # a variable is "excluded from every reduct" -- check against ALL
    # reducts (not just minimal), matching the full three-way equivalence
    # claimed in Proposition 3.
    excluded_from_all = lambda a: all(a not in r for r in reducts)

    ok = True
    for a in range(n):
        dummy = is_dummy_ground_truth(f_map, n, a)
        excluded = excluded_from_all(a)
        if dummy != excluded:
            print(f"    MISMATCH: var {a}, dummy={dummy}, excluded_from_all_reducts={excluded}")
            ok = False
    return ok


if __name__ == "__main__":
    print("=== Worked check: p0 = a0.b0 style function (n=4, vars {2,3} irrelevant) ===")
    onset, offset = structured_truth_table(4, relevant_vars=[0, 1], seed=1)
    dis = DecisionInformationSystem(n=4, onset=onset, offset=offset, dc=[])
    reducts = all_reducts(dis)
    min_r = minimal_reducts(reducts)
    print("Reducts found:", [sorted(r) for r in reducts])
    print("Minimal reduct(s):", [sorted(r) for r in min_r])
    f_map = full_function_map(dis)
    for a in range(4):
        print(f"  x{a}: dummy (ground truth) = {is_dummy_ground_truth(f_map, 4, a)}, "
              f"excluded from all reducts = {all(a not in r for r in reducts)}")

    print("\n=== Randomized sweep: Proposition 3 (structured, planted redundancy) ===")
    total, passed = 0, 0
    for n in [4, 5, 6]:
        for k in range(1, n):  # k relevant variables out of n
            relevant = list(range(k))
            for seed in range(10):
                onset, offset = structured_truth_table(n, relevant, seed=seed * 53 + n * 7 + k)
                if not onset or not offset:
                    continue
                total += 1
                if check_instance(n, onset, offset):
                    passed += 1
    print(f"Structured instances: Proposition 3 confirmed on {passed}/{total}")

    print("\n=== Randomized sweep: Proposition 3 (unstructured, typically no redundancy) ===")
    total2, passed2 = 0, 0
    for n in [3, 4, 5, 6]:
        for seed in range(15):
            onset, offset = random_total_function(n, seed=seed * 71 + n)
            if not onset or not offset:
                continue
            total2 += 1
            if check_instance(n, onset, offset):
                passed2 += 1
    print(f"Unstructured instances: Proposition 3 confirmed on {passed2}/{total2}")
