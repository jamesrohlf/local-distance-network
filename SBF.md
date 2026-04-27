SBF — Surface Brightness Fluctuations


WHAT IT IS

A galaxy's surface brightness is built from finite numbers of stars
per pixel. Closer galaxies show more pixel-to-pixel variance because
each pixel samples fewer giants; farther galaxies look smoother. The
amplitude of these fluctuations, properly normalized, scales as
1/distance — once calibrated against galaxies whose distances are
known by other means. Tonry & Schneider (1988) pioneered the method;
modern HST/WFC3 and JWST imaging reach E/S0 SN Ia hosts well into
the Hubble flow. SBF is uniquely matched to the bright, smooth, old
populations of ellipticals — exactly the galaxies Cepheid distances
can't reach.


ROLE IN H0DN

SBF enters the baseline through two files: sbf_calib.dat
(calibrators tied to TRGB or Cepheid hosts) and sbf_hf.dat (Hubble-
flow galaxies that contribute directly to the H0 fit). Variant V14
("Baseline without SBF") drops both, plus the related groups.dat,
forcing the network onto SNe Ia and other indicators. SBF acts as
the primary E/S0 bridge in the network — it's the route that lets
TRGB calibration reach into the elliptical hosts where SH0ES-style
Cepheid calibration cannot.
