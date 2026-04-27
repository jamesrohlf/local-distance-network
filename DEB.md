DEB — Detached Eclipsing Binaries


WHAT IT IS

A DEB is a pair of stars in a wide enough orbit that neither one
distorts or accretes from the other ("detached"), seen at an
inclination that produces eclipses. From the eclipse light curve plus
radial velocities you get each star's mass, radius, and effective
temperature directly from Newtonian and stellar-atmosphere physics —
no calibration ladder. Their absolute luminosities follow from L =
4πR²σT⁴, and the comparison with apparent magnitudes yields a
distance accurate to ~1 %. In the Magellanic Clouds, eight to a few
dozen late-type DEBs anchor the LMC and SMC distances at this
precision.


ROLE IN H0DN

DEBs are the LMC anchor, encoded in anchors.dat. They calibrate
Cepheid and TRGB zero-points in the LMC, which then transfer to
extragalactic hosts through host_data.dat. Variant V11 ("Baseline
without DEB, LMC, SMC") removes them entirely (host_exclude_list =
*LMC*, SMC, ...) to test how dependent the H0 result is on the LMC
anchor. Combined with V10 (no Gaia parallax / MW) and V12 (no NGC
4258), this triplet probes the geometric foundation independently.
