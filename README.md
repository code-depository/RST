# RST
Beyond gate-count: Rough set theory as a certificate of variable redundancy in Boolean circuit minimization
# Beyond Gate Count: RST as a Certificate of Variable Redundancy
## Reproducibility repository for the letter manuscript

This repository reproduces every figure and numeric claim made in
the letter *"Beyond Gate Count: Rough Set Theory as a Certificate of
Variable Redundancy in Boolean Circuit Minimization,"* containing the
modules and scripts needed to independently regenerate and verify the
letter's figures and cited numeric results. The script that assembles
these into the submitted manuscript document itself is not included
here, as it produces no evidentiary result and is not needed to check
reproducibility; the manuscript is submitted separately as the paper.

## Requirements

- Python 3.10+
- `pip install -r requirements.txt`

`pyeda` provides the compiled Espresso binary used for every Espresso
comparison in the letter (the real minimizer, not a reimplementation).
`matplotlib` renders Figures 1-4.

Note: `module_1.py`, `module_4.py`, and `module_6.py` also each contain
a `docx`-table-generating function used by the companion full-length
manuscript's reproducibility package. These functions are not called
by anything in this repository (`letter_demo.py`, `generate_figure4.py`,
or `module_8.py`), so `python-docx` is not required to run anything
here despite appearing inside those files.

## Repository structure

```
module_1.py     -- Decision Information System, QMC, Proposition 1
module_2.py     -- Boundary-region / don't-care machinery, Proposition 2
module_3.py     -- Attribute-level reducts, Proposition 3, greedy mode
module_4.py     -- Benchmarking harness: Espresso (real binary), ILP-exact
                    covering, correctness verification
module_6.py     -- Circuit generators: comparator cascade cell,
                    16-input priority encoder, BCD-to-7-segment decoder
module_8.py     -- Greedy-vs-exact reduct quality comparison
                    (source of the "84/84 instances" claim in the
                    letter's Scalability Limits section)

letter_demo.py         -- Generates Figures 1-3 and re-verifies every
                           numeric claim used in the text
generate_figure4.py    -- Generates Figure 4 (minimization pipeline and
                           method comparison)
generate_figure5.py    -- Generates Figure 5 (exact/greedy verification
                           boundary, 12- vs. 16-input encoder)

results_encoder_decoder.json    -- Cached w=16 priority-encoder results
                                    (Espresso/RST-greedy; QMC is
                                    infeasible at this scale, see the
                                    letter's Scalability Limits section)
results_structured_n4.json      -- Cached structured-benchmark results,
                                    source of the single boundary-case
                                    instance discussed in the letter
```

## Quick start

```bash
pip install -r requirements.txt

# Regenerate Figures 1-3 and re-verify every claim from scratch
python letter_demo.py

# Regenerate Figure 4
python generate_figure4.py

# Regenerate Figure 5 (takes roughly 1-2 minutes: computes exact
# reducts at n=12 for four instances plus four random n=12 functions)
python generate_figure5.py

# Independently reproduce the "84/84 instances" claim
python module_8.py
```

The commands above may be run in any order; only the
`pip install` step must come first.

Expected final lines of `letter_demo.py`:

```
Gathering BCD-to-7-segment data (with Proposition 2 verification)...
  seg_a: gates=7, reduct=4/4, tied=True, verified=True, proposition2=True
  seg_b: gates=7, reduct=3/4, tied=True, verified=True, proposition2=True
  ...
Done. Data cached to letter_data.json.
```

Mid-run (after the encoder section, before Figure 1 is generated),
`letter_demo.py` also prints the irredundancy check:

```
Verifying greedy reduct irredundancy (w=16)...
  y0: size=8, irredundant=True
  y3: size=15, irredundant=True
```

## What each figure demonstrates, and how it is verified

- **Figure 1** (comparator cascade cell): reduct membership for the `gt`
  and `eq` outputs. `eq`'s reduct excluding `gt_in` is verified via exact
  reduct computation (`module_3.all_reducts`), independent of the
  Espresso/QMC gate counts reported alongside it.
- **Figure 2** (16-input priority encoder): gate count (RST vs. Espresso,
  tied at every output) plotted against reduct size. At this scale exact
  reduct computation is intractable, so RST uses greedy mode
  (`module_3.greedy_reduct`) with an Espresso fallback for the two
  largest reducts -- documented explicitly in the letter's Scalability
  Limits section, not silently substituted.
- **Figure 3** (BCD-to-7-segment decoder): gate count and reduct size per
  segment, with Proposition 2 (`module_2.check_proposition2`) verified
  directly on each segment's decision information system -- the claim
  that codes 10-15 form "exactly the rough-set boundary region" is
  code-verified, not only asserted.
- **Figure 4** (minimization pipeline and method comparison): a
  categorical schematic summarizing the pattern established by Figures
  1-3 and `module_8.py`'s greedy-quality result, not a new computation.
  RST's scalability-beyond-n=10 cell is deliberately qualified
  ("greedy, unverified quality") rather than stated as flatly
  equivalent to Espresso's, matching the letter's Scalability
  Limits section exactly -- this figure does not overclaim what has actually
  been checked. Its footnote additionally reports that greedy's
  reducts at y0 and y3 are confirmed irredundant
  (`letter_demo.verify_greedy_irredundancy`), though global minimality
  at n=16 remains unverified.
- **Figure 5** (exact/greedy verification boundary): a genuinely new
  test, not a re-plot of existing data. Exact reduct computation
  (`module_3.all_reducts`) is run directly at n=12 for all four
  12-input encoder outputs plus four random 12-variable functions (8
  instances total), completing in 6-36 seconds each and exactly
  matching greedy's reduct size in every case -- proving, not just
  suggesting, that greedy is optimal at this scale. This is contrasted
  against the cached n=16 data (`results_encoder_decoder.json`), where
  exact computation is intractable and only the weaker irredundancy
  check (Figure 4's footnote) is available. The n=13-15 boundary
  itself is untested and not characterized by this repository.
- **Boundary-case instance** (Scalability Limits / "Boundary Case"
  section): the one instance among all tested structured benchmarks
  where RST's cover exceeds Espresso's is independently reconstructed
  from its original random seed and re-benchmarked from scratch by
  `letter_demo.find_and_reverify_boundary_case()`, which also asserts
  it is the *only* such instance -- if this ever stopped being true,
  the script fails loudly rather than let the manuscript's "exactly one
  instance" claim go stale.

## Citation

If you use this code, please cite the letter (details to be added on
publication).

## License

To be determined by the authors prior to public release.
