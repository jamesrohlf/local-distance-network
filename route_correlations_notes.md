# Route correlation estimates — rationale

The pairwise correlation coefficients fall into two regimes:

1. **H0DN-internal block (5 routes)** — `baseline`, `v01`, `v02`,
   `v06`, and `desi` are direct variants in the H0DN release code
   (V00, V01, V02, V06, V03 respectively). Their cross-correlations
   are *derived* from the Δσ-style nested-estimator formula used in
   Casertano et al. (2026) Table 4. See **"H0DN-internal block"**
   below.

2. **External routes (8 routes)** — `sh0es`, `cchp_edd`, `popii`,
   `mcp`, `popi`, `cf4`, `popmix`, `adh0cc` are independent analyses
   by other teams. Their entries remain domain-expert estimates of
   shared inputs (geometric anchors, calibrators, supernova samples,
   peculiar-velocity models) — not formal covariances. Replace with
   computed values as they become available.


## H0DN-internal block (derived)

H0DN treats every variant as a nested estimator on a common dataset:
each variant either adds an independent dataset to V00 or removes a
piece of it. The paper's Δσ column in Table 4 is

    Δσ = (H0_V − H0_V00) / sqrt(|σ_V00² − σ_V²|)

which only matches their tabulated values if pairs are nested. From
that nested structure:

- For V₀ ↔ V_i (one nests the other):
      ρ = σ_min / σ_max
- For V_i ↔ V_j (both extend V₀ with disjoint extra data):
      ρ = σ_i · σ_j / σ_₀²

Using σ from Casertano et al. (2026) Table 4
(σ_V00 = 0.809, σ_V01 = 0.807, σ_V02 = 0.809, σ_V03 = 0.798,
σ_V06 = 0.787 km/s/Mpc):

| pair | computed ρ | stored (capped 0.99) |
|---|---|---|
| baseline ↔ v01 | 0.998 | 0.99 |
| baseline ↔ v02 | 1.000 | 0.99 |
| baseline ↔ v06 | 0.973 | 0.97 |
| baseline ↔ desi | 0.986 | 0.99 |
| v01 ↔ v02 | 0.998 | 0.99 |
| v01 ↔ v06 | 0.970 | 0.97 |
| v01 ↔ desi | 0.984 | 0.98 |
| v02 ↔ v06 | 0.973 | 0.97 |
| v02 ↔ desi | 0.986 | 0.99 |
| v06 ↔ desi | 0.960 | 0.96 |

ρ values exactly equal to 1 would make the 2×2 sub-covariance
singular (σ_i ≠ σ_j to higher precision than the paper quotes), so
off-diagonal entries are capped at 0.99.

Source: Casertano et al. (2026), A&A vol. 708, A166.
Repository: https://github.com/StefCas789/H0DN/


## Shared-input cheat sheet

| Input | Used by |
|---|---|
| NGC 4258 maser anchor | baseline, v01, v02, v06, sh0es, cchp_edd, popii, mcp (measures it), popmix |
| LMC DEB anchor | baseline, v01, v02, v06, sh0es, cchp_edd, popmix |
| Gaia parallaxes | baseline, v01, v02, v06, sh0es, popmix |
| HST Cepheid photometry | baseline, v01, v02, v06, desi, sh0es, popi (calib), popmix |
| Pantheon+ SNe Ia | baseline, v01, v02, v06, desi, sh0es, cchp_edd, popmix |
| TRGB calibration | baseline, v01, v02, v06, desi, cchp_edd, popii |
| SBF | baseline, v01, v02, v06, desi, popii |
| TF | v06, cf4 |
| FP | desi (V03 adds DESI FP on top of the full baseline ladder) |
| SN II SCM / EPM | popi (SCM), adh0cc (EPM) |


## Per-block rationale

### H0DN-internal (baseline / v01 / v02 / v06 / desi)

Derived from Casertano et al. (2026) Table 4 σ values via the
nested-estimator formula. See "H0DN-internal block (derived)"
section above for values.


### baseline vs externals

- vs sh0es  = 0.65  (Cepheids + Pantheon+ + NGC 4258, but baseline also has TRGB/SBF)
- vs cchp_edd = 0.55  (TRGB + SNe Ia overlap; CCHP avoids Cepheids)
- vs popii  = 0.50  (TRGB→SBF arm of baseline overlaps strongly)
- vs mcp    = 0.20  (NGC 4258 anchor only; otherwise independent)
- vs popi   = 0.20  (Cepheid calibration; SN II is independent)
- vs cf4    = 0.20  (Cepheid calib; TF independent)
- vs popmix = 0.65  (Cepheids+IR+SNe Ia; effectively a v01/v02 variant from outside)
- vs adh0cc = 0.05  (EPM, no shared rungs)


### External vs external

- sh0es ↔ cchp_edd = 0.40 (Pantheon+ + NGC 4258 anchor)
- sh0es ↔ popii    = 0.30 (Pantheon+; different calibration)
- sh0es ↔ mcp      = 0.15 (NGC 4258 anchor indirect)
- sh0es ↔ popi     = 0.30 (Cepheid calibration)
- sh0es ↔ cf4      = 0.15 (Cepheid calib only)
- sh0es ↔ popmix   = 0.65 (same SNe + similar Cepheid program)
- sh0es ↔ adh0cc   = 0.05

- cchp_edd ↔ popii  = 0.40 (TRGB calibration shared)
- cchp_edd ↔ mcp    = 0.15
- cchp_edd ↔ popmix = 0.20 (TRGB vs Cepheid path)
- otherwise         = 0.05–0.10

- popii ↔ popmix    = 0.30 (SNe Ia + SBF/Cepheid mix)
- popii ↔ mcp       = 0.15 (NGC 4258)

- mcp vs others    = 0.05–0.20 (mostly independent geometric)

- popi ↔ adh0cc    = 0.25 (both SN II, different methods)
- popi ↔ popmix    = 0.20 (Cepheid calib)

- adh0cc           = 0.05 with everything else (EPM is essentially standalone)


## Caveats

1. These are *estimates from shared inputs*, not measured correlations.
   Likely accurate to ±0.10–0.15.

2. The H0DN paper handles correlations at the data level (per-supernova
   covariance matrices), not at the route level. A formal route-level Σ
   would require running their tool with overlapping subsets and
   extracting joint Hessians.

3. The matrix is symmetric and positive-definite (verified: minimum
   eigenvalue ≈ 0.005). `_load_correlation_matrix()` symmetrizes and the
   GLS computation falls back gracefully if Σ ever goes singular.

   Note: each external route now has the *same* correlation across all
   five H0DN-internal routes (e.g., sh0es ↔ {baseline,v01,v02,v06,desi}
   are all 0.65). This is forced by transitivity — once the H0DN-internal
   block is ≈ 0.97–0.99, two of those routes can't differ by much in how
   any external sees them, or the matrix breaks PD. Earlier estimates
   like cf4 ↔ v06 = 0.40 (TF sharing) and sh0es ↔ desi = 0.20 (Coma SN
   tie) are subsumed: in the nested-estimator picture, those incremental
   data items live inside the residual ~3% of variance after the H0DN-
   common-mode is removed, and don't move ρ to externals appreciably.

4. baseline / v01 / v02 / v06 / desi are all H0DN VARIANTS (V00 / V01 /
   V02 / V06 / V03), not independent measurements. Treating them as
   separate routes in a GLS combine double-counts data. Include exactly
   one of them in any consensus, not several.


## Robustness

The matrix is technically positive-definite but **not robust** to
perturbation. Key diagnostics:

- **Eigenvalue spectrum** (sorted): 0.005, 0.010, 0.018, 0.046, 0.28,
  0.52, 0.62, 0.72, 0.90, 0.95, 1.00, 1.25, 6.67. Three eigenvalues
  hug zero; condition number ≈ 1380.

- **Almost-null direction**: the eigenvector at the smallest eigenvalue
  is dominated by `+0.51 baseline + 0.51 v02 − 0.47 v01 − 0.51 desi`
  (other entries ≈ 0). The matrix is correctly identifying the H0DN-
  internal variants as a near-degenerate subspace — exactly what
  caveat #4 warns about — and the closeness to singularity is a
  faithful reflection of that physics.

- **Single-entry perturbation budget**: how many of the 156 off-diagonal
  ±δ moves break PD?

  | δ | entries that break PD |
  |---|---|
  | ±0.01 | 2 / 156 |
  | ±0.02 | 4 / 156 |
  | ±0.05 | 13 / 156 |
  | ±0.10 | 61 / 156 (≈ 39%) |

  Caveat #1 quotes ±0.10–0.15 estimation accuracy. At ±0.10, almost
  40% of single-entry bumps break the matrix. The matrix as stored
  is the only consistent point — slight deviations rarely are.

- **Tightest entry**: `baseline ↔ cchp_edd` (currently 0.55) tolerates
  only about ±0.05 before the matrix goes non-PD. This is also the
  single most influential entry in the sensitivity report (largest
  ΔH₀ when perturbed).

**Operational guidance.**

1. **Don't combine 2+ H0DN-internal routes** in any GLS consensus
   (caveat #4). If you respect that, the fragility never bites — the
   custom-set click flow already encourages this.

2. **Don't bootstrap-perturb this matrix** to estimate uncertainty.
   Random ±0.05–0.10 noise on entries flips it non-PD almost
   universally. For uncertainty-on-uncertainty, run the H0DN
   `h0_constrainer` tool with resampled data instead.

3. **Adding a new route requires re-checking PD** for the resulting
   matrix; one entry's value can interact with the H0DN-internal
   block via transitivity.

If you want a more forgiving matrix, soften the H0DN-internal block
from 0.97–0.99 down to ≈ 0.90. That falsifies the strict nested-
estimator math but yields a matrix that survives ±0.10 single-entry
moves comfortably.


### Combining two non-H0DN routes — error accuracy

GLS combines of any 2 of the 8 external routes are **far more robust**
than the H0DN-internal block, because the external 8×8 sub-block has
no near-singular direction (no nested-estimator transitivity coupling).

Propagating the ±0.10–0.15 estimation accuracy of caveat #1 through
the GLS formula

    σ²_comb = σ_i² σ_j² (1 − ρ²) / (σ_i² + σ_j² − 2 ρ σ_i σ_j)

over all 28 external pairs gives:

| ρ uncertainty | median Δσ_comb | max Δσ_comb | 90th-pct |
|---|---|---|---|
| ±0.10 | 4.2% | 4.9% | 4.8% |
| ±0.15 | ~6% | ~8% | ~7% |

So a 2-external GLS combine reporting σ_comb = 1.025 km/s/Mpc carries
an additional ~5% (relative) uncertainty from ρ-estimation alone — i.e.
quote it as ≈ 1.03 ± 0.05 to be honest about the correlation budget.

The central H₀ value is much less affected; perturbing ρ shifts it by
only a small fraction of σ_comb.

**Caveats:**

- Combining 3+ externals compounds the ρ uncertainty across multiple
  pairs; the 5% rule no longer applies and a Monte Carlo on the ρ
  estimates is the right tool.

- The ~5% applies to the correlation budget *only*. The σ values each
  external team published carry their own systematic and statistical
  uncertainties that are independent of and on top of this.

- Pairs where both σ values are large and ρ is small
  (e.g. `mcp ↔ cf4`, `popii ↔ cf4`) have σ_comb ≈ σ_min / √2 regardless
  of ρ, so are insensitive to correlation choice.
