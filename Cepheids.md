Cepheids — Classical Cepheid Variables


WHAT IT IS

Young, massive (~5-15 M⊙) supergiants pulsating radially with periods
of 1-100 days. Henrietta Leavitt (1908-1912) discovered that brighter
Cepheids have longer periods. The Leavitt Law gives M ∝ a + b·log(P)
with intrinsic scatter only ~0.1 mag, especially in the near-IR where
metallicity and reddening effects are smaller. Calibrated against
geometric anchors (Gaia parallax to MW Cepheids, DEB to LMC,
maser-distance to NGC 4258), Cepheid distances reach SNe Ia host
galaxies out to ~50 Mpc with HST and JWST.


ROLE IN H0DN

Cepheids are the dominant primary distance indicator in the baseline.
Cepheid host distances populate host_data.dat (the central host
file), and they calibrate the SH0ES-style SNe Ia ladder. Variant V08
("Baseline without Cepheids") excludes them via host_exclude_list =
*ceph*, leaving TRGB and JAGB to carry the calibration. V08B uses a
matched-host custom baseline so the comparison is apples-to-apples.
The contrast between V00 and V08 is one of the cleanest tests of the
Cepheid-vs-non-Cepheid disagreement that drives the SH0ES vs CCHP
debate.
