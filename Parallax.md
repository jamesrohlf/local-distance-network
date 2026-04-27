Parallax — Trigonometric Parallax


WHAT IT IS

The oldest distance method in astronomy. As Earth orbits the Sun,
nearby stars appear to shift against the distant background; the
half-angle of that shift over a 1-AU baseline is the parallax π. The
distance in parsecs is simply 1/π (with π in arcseconds). For Milky
Way stars, the Gaia satellite (DR3) measures parallaxes good to a few
microarcseconds — enough to reach 1 % distances out to ~1 kpc and
useful precision out to several kpc. Parallax is the only distance
method that involves no astrophysical modeling at all: it's pure
geometry from a known baseline.


ROLE IN H0DN

Parallax provides the Milky Way Cepheid and TRGB calibration
zero-points, encoded in anchors.dat. Gaia parallaxes to MW Cepheids
fix the Leavitt Law's absolute magnitude; analogous parallaxes to MW
RGB stars fix the TRGB tip luminosity. Both then transfer outward
through host_data.dat. Variant V10 ("Baseline without Gaia
parallaxes, MW") drops these via host_exclude_list = *MW*, leaving
the geometric scale to rest on the LMC DEBs and NGC 4258 maser
distance alone. The variant tests how much the consensus H0 depends
on the Gaia zero-point chain.
