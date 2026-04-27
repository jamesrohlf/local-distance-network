SNe Ia — Type Ia Supernovae


WHAT IT IS

Thermonuclear detonations of CO white dwarfs in close binaries.
After light-curve and color corrections (stretch, x1; color, c) the
peak B-band luminosity is standardizable to ~0.12 mag scatter — about
6 % in distance. Calibrated against galaxies with primary distances
(Cepheids, TRGB, Miras), SNe Ia are then observed at z = 0.01–0.10
where peculiar-velocity noise is small and pure Hubble flow
dominates. They are the most precise of the long-range indicators
and the central rung of the SH0ES-style ladder. Multiple light-curve
fitters (SALT3, BayesSN, CSPDR3, "Pantheon+") give slightly different
calibrations and covariances.


ROLE IN H0DN

SNe Ia dominate the long-range arm of the baseline. The default uses
sn1a_calib.dat, sn1a_hf_pp.dat (Pantheon+ HF sample), and the
sn1a_covar_pp.dat covariance matrix; alternative compilations are
available (SALT3, CSP, BayesSN, J/H bands). Variant V13 ("Baseline
without SNe Ia") removes all of them, leaving only SBF and other
indicators to anchor the long-range Hubble flow — a useful test of
how much of the H0 result rides on SNe Ia.
