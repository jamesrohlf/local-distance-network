# Route correlation estimates — rationale

These are domain-expert estimates of pairwise correlation coefficients
between the H₀ measurements shown in the figure. They reflect shared
inputs (geometric anchors, calibrators, supernova samples, peculiar-
velocity models) — not formal covariances from a joint analysis.

Replace with computed values from H0DN authors as they become available.


## Shared-input cheat sheet

| Input | Used by |
|---|---|
| NGC 4258 maser anchor | baseline, v01, v02, v06, sh0es, cchp_edd, popii, mcp (measures it), popmix |
| LMC DEB anchor | baseline, v01, v02, v06, sh0es, cchp_edd, popmix |
| Gaia parallaxes | baseline, v01, v02, v06, sh0es, popmix |
| HST Cepheid photometry | baseline, v01, v02, v06, sh0es, popi (calib), popmix |
| Pantheon+ SNe Ia | baseline, v01, v02, v06, sh0es, cchp_edd, popmix |
| TRGB calibration | baseline, v01, v02, v06, cchp_edd, popii |
| SBF | baseline, v01, v02, v06, popii |
| TF | v06, cf4 |
| FP | desi |
| SN II SCM / EPM | popi (SCM), adh0cc (EPM) |


## Per-block rationale

### H0DN-internal (baseline / v01 / v02 / v06)

Variants of the same fit; they share most data. Each variant adds one
extra dataset to the baseline.

- baseline ↔ v01 = 0.95 (just adds JAGB)
- baseline ↔ v02 = 0.95 (just adds Miras)
- baseline ↔ v06 = 0.85 (TF brings genuinely new data)
- v01 ↔ v02   = 0.90 (both add IR calibrators, distinct sources)
- v01 ↔ v06   = 0.80
- v02 ↔ v06   = 0.80


### baseline vs externals

- vs sh0es  = 0.65  (Cepheids + Pantheon+ + NGC 4258, but baseline also has TRGB/SBF)
- vs cchp_edd = 0.55  (TRGB + SNe Ia overlap; CCHP avoids Cepheids)
- vs popii  = 0.50  (TRGB→SBF arm of baseline overlaps strongly)
- vs mcp    = 0.20  (NGC 4258 anchor only; otherwise independent)
- vs popi   = 0.20  (Cepheid calibration; SN II is independent)
- vs cf4    = 0.20  (Cepheid calib; TF independent)
- vs popmix = 0.65  (Cepheids+IR+SNe Ia; effectively a v01/v02 variant from outside)
- vs desi   = 0.25  (Coma SN tie + peculiar-velocity model)
- vs adh0cc = 0.05  (EPM, no shared rungs)


### External vs external

- sh0es ↔ cchp_edd = 0.40 (Pantheon+ + NGC 4258 anchor)
- sh0es ↔ popii    = 0.30 (Pantheon+; different calibration)
- sh0es ↔ mcp      = 0.15 (NGC 4258 anchor indirect)
- sh0es ↔ popi     = 0.30 (Cepheid calibration)
- sh0es ↔ cf4      = 0.15 (Cepheid calib only)
- sh0es ↔ popmix   = 0.65 (same SNe + similar Cepheid program)
- sh0es ↔ desi     = 0.20 (Coma SN tie)
- sh0es ↔ adh0cc   = 0.05

- cchp_edd ↔ popii  = 0.40 (TRGB calibration shared)
- cchp_edd ↔ mcp    = 0.15
- cchp_edd ↔ popmix = 0.20 (TRGB vs Cepheid path)
- cchp_edd ↔ desi   = 0.15
- otherwise        = 0.05–0.10

- popii ↔ popmix    = 0.30 (SNe Ia + SBF/Cepheid mix)
- popii ↔ mcp       = 0.15 (NGC 4258)

- mcp vs others    = 0.05–0.20 (mostly independent geometric)

- popi ↔ adh0cc    = 0.25 (both SN II, different methods)
- popi ↔ popmix    = 0.20 (Cepheid calib)

- cf4 ↔ desi       = 0.20 (peculiar-velocity model overlap)
- cf4 ↔ v06        = 0.40 (TF data shared)

- adh0cc           = 0.05 with everything else (EPM is essentially standalone)


## Caveats

1. These are *estimates from shared inputs*, not measured correlations.
   Likely accurate to ±0.10–0.15.

2. The H0DN paper handles correlations at the data level (per-supernova
   covariance matrices), not at the route level. A formal route-level Σ
   would require running their tool with overlapping subsets and
   extracting joint Hessians.

3. The matrix is symmetric and (I believe) positive-definite for these
   values, but `_load_correlation_matrix()` symmetrizes and the GLS
   computation falls back gracefully if Σ is singular.

4. v01/v02/v06 are H0DN VARIANTS not independent measurements; treating
   them as separate routes in the GLS combine double-counts data. Either
   include the baseline OR a variant, not both.
