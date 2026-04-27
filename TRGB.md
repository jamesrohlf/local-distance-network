TRGB — Tip of the Red Giant Branch


WHAT IT IS

In the I-band color-magnitude diagram of any old (> ~2 Gyr) stellar
population, low-mass red giants pile up at a sharp upper luminosity
boundary set by the helium flash at a critical degenerate-core mass
(~0.47 M⊙). Because the flash physics depends on degenerate-electron
pressure rather than progenitor mass or composition, the maximum
I-band magnitude is nearly universal: M_I ≈ –4.05, with small
calibratable color/metallicity corrections. Distance is read directly
from the apparent magnitude of the tip detected with a Sobel-like
edge filter on a halo CMD, no curve fitting required.


ROLE IN H0DN

TRGB is the principal Cepheid alternative for primary distances in
the baseline. TRGB host distances live in host_data.dat alongside
Cepheids; the variant V09 ("Baseline without TRGB") removes them
(host_exclude_list = *trgb*) and forces the network onto Cepheids.
Because SBF and group distances are calibrated against TRGB hosts,
they are dropped automatically with V09. Comparing V00 ↔ V09 ↔ V08
isolates the Cepheid-versus-TRGB component of the H0 discrepancy
without changing geometric anchors.
