# The Local Distance Network to H₀

An interactive matplotlib visualization of the local distance ladder
network used to measure the Hubble constant. Routes from geometric
anchors (parallaxes, detached eclipsing binaries, water-maser
distances) through stellar candles (Cepheids, TRGB, JAGB, Miras) and
long-range tracers (SNe Ia, SBF, FP, TF, SNe II) all converge on H₀.

The diagram follows the H0DN Collaboration consensus paper:
*The Local Distance Network: A community consensus report on the
measurement of the Hubble constant at ∼1 % precision*,
A&A **708**, A166 (2026), <https://arxiv.org/abs/2510.23823>.

## Features

- **Click a route name** in the legend to open a per-route info file
  (or the legend entry's `↗` to open the arXiv paper for that route).
- **Click a node** (MASER, DEB, TRGB, JAGB, …) to open a per-node info
  file describing what the technique is.
- **Click anywhere else** on a route line, the colored swatch in the
  legend, or the H₀ row at the bottom to **isolate** a route — its
  full path lights up while the other routes fade. Click again to
  clear.
- The acronym box (top-left) and route-acronym box (right of the
  Routes legend) **highlight** the entries touched by the isolated
  route.
- The bottom panel shows each route's H₀ value with consensus and
  Planck CMB reference bands.
- **Save PNG** writes a timestamped snapshot of the current view.

## Running

Requires Python 3 with `matplotlib` and `tkinter` (the latter is
bundled with most Python distributions).

```bash
pip install matplotlib
python3 local_distance_network.py
```

On macOS you can also double-click `launch.command`.

## Per-node and per-route info files

The script looks in its own directory for files named after each node
or route, e.g. `MASERs.rtf`, `SH0ES.rtf`, `Pop-Mix.rtf`. RTF files are
opened in the OS's default viewer (TextEdit on macOS) so formatting is
preserved; `.txt` and `.md` open in an in-app dark popup. To add or
edit content, just drop a file with the matching name next to the
script.

## Credit

James Rohlf and Claude Opus 4.7 — Boston University Physics.
