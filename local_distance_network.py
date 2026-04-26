"""
Local Distance Network — click-to-isolate, dark theme.

Top panel: distance-ladder network. All routes are drawn statically;
click a legend entry, a route line, or an H₀-panel row to spotlight
one route (and its branches) while fading the rest. Click again to
clear.

Bottom panel: per-route H₀ error bars, with consensus + Planck CMB
reference lines.

Controls (top of figure):
    Save PNG — timestamped snapshot
"""

import os
import subprocess
import sys
import tkinter as tk
import webbrowser
from datetime import datetime
from tkinter import scrolledtext

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.patches as mpatches
import matplotlib.transforms as mtransforms
from matplotlib.widgets import Button, Slider


# --------------------------------------------------------------------------
# Data
# --------------------------------------------------------------------------

NODES = {
    # Geometry tier (left column) — DEB sits exactly on the hub y so the
    # hub→DEB connector is perfectly horizontal
    'masers':    (0.70, 3.00, 'MASERs'),
    'deb':       (0.70, 1.80, 'DEB'),
    'parallax':  (0.70, 0.85, 'Parallax'),

    # Stellar candles — Cepheids pulled RIGHT (and slightly lower) so the
    # middle column has a small zigzag, as in the reference diagram
    'trgb':      (2.30, 3.40, 'TRGB'),
    'jagb':      (2.30, 2.40, 'JAGB'),
    'miras':     (2.30, 1.40, 'Miras'),
    'cepheids':  (2.60, 0.30, 'Cepheids'),

    # Long-range indicators — alternating stagger (SBF/SNeIa/SNeII pulled
    # LEFT, FP/TF on the right) matching the reference diagram
    'sbf':       (4.15, 3.40, 'SBF'),
    'fp':        (4.90, 2.65, 'FP'),
    'snia':      (4.15, 1.90, 'SNeIa'),
    'tf':        (4.45, 1.10, 'TF'),
    'sneii':     (4.15, 0.30, 'SNeII'),

    # Outside-the-tiers node (EPM / direct SN II method)
    'sneii_epm': (3.80, -0.60, 'SNeII\nEPM'),

    # H₀ target (yellow circle, far right) — sits at x=6.05 so MCP and
    # adh0cc paths arrive on a vertical line.
    'h0':        (6.05, 1.90, r'$H_0$'),

    # MCP waypoints — straight vertical climb from masers, horizontal
    # traverse above all boxes, then vertical drop to H₀.
    'mcp_top':       (0.70, 4.35, ''),
    'mcp_far_right': (6.05, 4.35, ''),
    # Waypoint used by adh0cc to skirt the long-range box on the right.
    'adh0cc_right':  (6.05, -0.60, ''),
    # SH0ES bends — parallax→cepheids drops at 45° from parallax to (1.25, 0.30)
    # and then runs horizontally into Cepheids; DEB→cepheids drops vertically
    # a short distance, then angles down at 45° to meet the horizontal line.
    # Masers→cepheids drops vertically to just above DEB, then 45° down to
    # Cepheids.
    'sh0es_par_bend':    (1.25, 0.30, ''),
    'sh0es_deb_bend':    (0.70, 1.50, ''),
    'sh0es_deb_angle':   (1.90, 0.30, ''),
    'sh0es_masers_bend': (0.70, 2.20, ''),
    # CF4 TRGB→TF bend: vertical down (only partway to JAGB), then 45°,
    # then horizontal into TF.
    'cf4_trgb_drop':       (2.30, 2.80, ''),
    'cf4_trgb_angle':      (4.00, 1.10, ''),
    # CF4 TF→H0 bend: short horizontal out of TF, then 45° up to H₀.
    'cf4_tf_h0_angle':     (5.25, 1.10, ''),
    # CF4 Cepheids→TF bend: horizontal out of Cepheids, then 45° up to TF.
    'cf4_ceph_tf_angle':   (3.65, 0.30, ''),
    # Pop-Mix bends: Cepheids→SBF goes vertical up, 45° up, vertical up;
    # TRGB→SNeII goes vertical down, 45° down, vertical down.
    'popmix_ceph_drop':    (2.60, 0.85, ''),
    'popmix_ceph_angle':   (4.15, 2.40, ''),
    'popmix_trgb_drop':    (2.30, 3.00, ''),
    'popmix_trgb_angle':   (4.15, 1.15, ''),
    # Baseline Miras→SNeIa bend: 45° up out of Miras, then horizontal into SNeIa.
    'baseline_miras_angle':(2.80, 1.90, ''),
    # DESI FP→H0 bend: short horizontal out of FP, then 45° down to H₀.
    'desi_fp_h0_angle':    (5.30, 2.65, ''),
    # JAGB chain bends: 45° from MASERs to JAGB row, then horizontal to JAGB,
    # then 45° from JAGB down to SNeIa row, then horizontal to SNeIa.
    'masers_jagb_angle':   (1.30, 2.40, ''),
    'jagb_snia_angle':     (2.80, 1.90, ''),
    # CCHP/EDD bends: 45° up out of masers to TRGB level, then horizontal
    # to TRGB, horizontal short bit, 45° down to SNeIa.
    'cchp_masers_angle': (1.10, 3.40, ''),
    'cchp_snia_angle':   (2.65, 3.40, ''),
    # Pop-II shares CCHP's masers→TRGB path; the divided-highway look at
    # startup is created later via parallel-offset decoration overlays.
    'popii_h0_angle':     (4.55, 3.40, ''),
    # Pop-I bend: short horizontal from SNeII, then 45° up to H₀.
    'popi_h0_angle':      (4.45, 0.30, ''),
}

ROUTES = [
    {'id': 'baseline','name': 'Baseline', 'color': '#ffffff', 'h0': 73.50, 'err': 0.81,
     'ref': 'H0DN: A&A, 708, A166 (2026)',
     'arxiv': 'https://arxiv.org/abs/2510.23823',
     'path': ['sbf', 'popii_h0_angle', 'h0'],
     'branches': [
         ['masers', 'cchp_masers_angle', 'trgb', 'sbf'],
         ['trgb', 'cchp_snia_angle', 'snia'],
         ['masers',   'sh0es_masers_bend', 'cepheids', 'snia'],
         ['deb',      'sh0es_deb_bend', 'sh0es_deb_angle', 'cepheids'],
         ['parallax', 'sh0es_par_bend', 'cepheids'],
         ['snia',     'h0'],
     ]},
    {'id': 'v01',    'name': 'Baseline + JAGB',  'color': '#ff5577',
     'h0': 73.49, 'err': 0.82,
     'path': ['masers', 'masers_jagb_angle', 'jagb',
              'jagb_snia_angle', 'snia'],
     'branches': [
         {'nodes': ['sbf', 'popii_h0_angle', 'h0'],
          'color': '#ffffff', 'lw': 1.4, 'alpha': 0.65},
         {'nodes': ['masers', 'cchp_masers_angle', 'trgb', 'sbf'],
          'color': '#ffffff', 'lw': 1.4, 'alpha': 0.65},
         {'nodes': ['trgb', 'cchp_snia_angle', 'snia'],
          'color': '#ffffff', 'lw': 1.4, 'alpha': 0.65},
         {'nodes': ['masers', 'sh0es_masers_bend', 'cepheids', 'snia'],
          'color': '#ffffff', 'lw': 1.4, 'alpha': 0.65},
         {'nodes': ['deb', 'sh0es_deb_bend', 'sh0es_deb_angle', 'cepheids'],
          'color': '#ffffff', 'lw': 1.4, 'alpha': 0.65},
         {'nodes': ['parallax', 'sh0es_par_bend', 'cepheids'],
          'color': '#ffffff', 'lw': 1.4, 'alpha': 0.65},
         {'nodes': ['snia', 'h0'],
          'color': '#ffffff', 'lw': 1.4, 'alpha': 0.65},
     ]},
    {'id': 'v02',    'name': 'Baseline + Miras', 'color': '#a00000',
     'h0': 73.51, 'err': 0.81,
     'path': ['masers', 'miras', 'baseline_miras_angle', 'snia'],
     'branches': [
         {'nodes': ['sbf', 'popii_h0_angle', 'h0'],
          'color': '#ffffff', 'lw': 1.4, 'alpha': 0.65},
         {'nodes': ['masers', 'cchp_masers_angle', 'trgb', 'sbf'],
          'color': '#ffffff', 'lw': 1.4, 'alpha': 0.65},
         {'nodes': ['trgb', 'cchp_snia_angle', 'snia'],
          'color': '#ffffff', 'lw': 1.4, 'alpha': 0.65},
         {'nodes': ['masers', 'sh0es_masers_bend', 'cepheids', 'snia'],
          'color': '#ffffff', 'lw': 1.4, 'alpha': 0.65},
         {'nodes': ['deb', 'sh0es_deb_bend', 'sh0es_deb_angle', 'cepheids'],
          'color': '#ffffff', 'lw': 1.4, 'alpha': 0.65},
         {'nodes': ['parallax', 'sh0es_par_bend', 'cepheids'],
          'color': '#ffffff', 'lw': 1.4, 'alpha': 0.65},
         {'nodes': ['snia', 'h0'],
          'color': '#ffffff', 'lw': 1.4, 'alpha': 0.65},
     ]},
    {'id': 'v03',    'name': 'Baseline + TF', 'color': '#a892d4',
     'h0': 73.96, 'err': 0.79,
     'path': ['trgb', 'cf4_trgb_drop', 'cf4_trgb_angle', 'tf',
              'cf4_tf_h0_angle', 'h0'],
     'branches': [
         # CF4-style cepheids → TF branch (also lavender)
         ['cepheids', 'cf4_ceph_tf_angle', 'tf'],
         # baseline calibration ladder — white
         {'nodes': ['sbf', 'popii_h0_angle', 'h0'],
          'color': '#ffffff', 'lw': 1.4, 'alpha': 0.65},
         {'nodes': ['masers', 'cchp_masers_angle', 'trgb', 'sbf'],
          'color': '#ffffff', 'lw': 1.4, 'alpha': 0.65},
         {'nodes': ['trgb', 'cchp_snia_angle', 'snia'],
          'color': '#ffffff', 'lw': 1.4, 'alpha': 0.65},
         {'nodes': ['masers', 'sh0es_masers_bend', 'cepheids', 'snia'],
          'color': '#ffffff', 'lw': 1.4, 'alpha': 0.65},
         {'nodes': ['deb', 'sh0es_deb_bend', 'sh0es_deb_angle', 'cepheids'],
          'color': '#ffffff', 'lw': 1.4, 'alpha': 0.65},
         {'nodes': ['parallax', 'sh0es_par_bend', 'cepheids'],
          'color': '#ffffff', 'lw': 1.4, 'alpha': 0.65},
         {'nodes': ['snia', 'h0'],
          'color': '#ffffff', 'lw': 1.4, 'alpha': 0.65},
     ]},
    {'id': 'sh0es',   'name': 'SH0ES',    'color': '#2a5fd9', 'h0': 73.04, 'err': 1.04,
     'ref': 'Riess et al. 2022b',
     'arxiv': 'https://arxiv.org/abs/2112.04510',
     'path': ['deb', 'sh0es_deb_bend', 'sh0es_deb_angle', 'cepheids', 'snia', 'h0'],
     'branches': [
         ['masers', 'sh0es_masers_bend', 'cepheids'],
         ['parallax', 'sh0es_par_bend', 'cepheids'],
     ]},
    {'id': 'cchp_edd','name': 'CCHP/EDD', 'color': '#a09428', 'h0': 70.39, 'err': 1.81,
     'ref': 'Freedman et al. 2025',
     'arxiv': 'https://arxiv.org/abs/2408.06153',
     'path': ['masers', 'cchp_masers_angle', 'trgb',
              'cchp_snia_angle', 'snia', 'h0']},
    {'id': 'popii',   'name': 'Pop-II',   'color': '#d12b8a', 'h0': 73.8,  'err': 2.40,
     'ref': 'Jensen et al. 2025',
     'arxiv': 'https://arxiv.org/abs/2502.15935',
     'path': ['masers', 'cchp_masers_angle', 'trgb',
              'sbf', 'popii_h0_angle', 'h0']},
    {'id': 'mcp',     'name': 'MCP',      'color': '#2f8a40', 'h0': 73.9,  'err': 3.0,
     'ref': 'Pesce et al. 2020a',
     'arxiv': 'https://arxiv.org/abs/2001.09213',
     'path': ['masers', 'mcp_top', 'mcp_far_right', 'h0']},
    {'id': 'popi',    'name': 'Pop-I',    'color': '#ee7a2a', 'h0': 75.4,  'err': 3.8,
     'ref': 'de Jaeger et al. 2022',
     'arxiv': 'https://arxiv.org/abs/2203.08974',
     'path': ['cepheids', 'sneii', 'popi_h0_angle', 'h0'],
     'branches': [
         # geometric-anchor calibrators — drawn dashed white to match Baseline
         {'nodes': ['masers',   'sh0es_masers_bend', 'cepheids'],
          'color': '#ffffff', 'ls': '-', 'lw': 1.4, 'alpha': 0.65},
         {'nodes': ['deb',      'sh0es_deb_bend', 'sh0es_deb_angle', 'cepheids'],
          'color': '#ffffff', 'ls': '-', 'lw': 1.4, 'alpha': 0.65},
         {'nodes': ['parallax', 'sh0es_par_bend', 'cepheids'],
          'color': '#ffffff', 'ls': '-', 'lw': 1.4, 'alpha': 0.65},
     ]},
    {'id': 'cf4',     'name': 'CF4',      'color': '#a892d4', 'h0': 75.1,  'err': 3.01,
     'ref': 'Kourkchi et al. 2020',
     'arxiv': 'https://arxiv.org/abs/2009.00733',
     'path': ['trgb', 'cf4_trgb_drop', 'cf4_trgb_angle', 'tf',
              'cf4_tf_h0_angle', 'h0'],
     'branches': [
         {'nodes': ['cepheids', 'cf4_ceph_tf_angle', 'tf'], 'ls': '-'},
         # geometric-anchor calibrators — white dashed, routed via the
         # SH0ES bend waypoints (and the CCHP masers→TRGB bend).
         {'nodes': ['masers',   'cchp_masers_angle', 'trgb'],
          'color': '#ffffff', 'ls': '-', 'lw': 1.4, 'alpha': 0.65},
         {'nodes': ['parallax', 'sh0es_par_bend', 'cepheids'],
          'color': '#ffffff', 'ls': '-', 'lw': 1.4, 'alpha': 0.65},
         {'nodes': ['deb',      'sh0es_deb_bend', 'sh0es_deb_angle', 'cepheids'],
          'color': '#ffffff', 'ls': '-', 'lw': 1.4, 'alpha': 0.65},
         {'nodes': ['masers',   'sh0es_masers_bend', 'cepheids'],
          'color': '#ffffff', 'ls': '-', 'lw': 1.4, 'alpha': 0.65},
     ]},
    {'id': 'popmix',  'name': 'Pop-Mix',  'color': '#ff8dc7', 'h0': 72.6,  'err': 2.0,
     'ref': 'Riess et al. 2024',
     'arxiv': 'https://arxiv.org/abs/2408.11770',
     'path': ['cepheids', 'popmix_ceph_drop', 'popmix_ceph_angle', 'sbf'],
     'branches': [
         # Pop-Mix-specific TRGB→SNeII link, dashed pink (inherits popmix branch_ls)
         ['trgb', 'popmix_trgb_drop', 'popmix_trgb_angle', 'sneii'],
         # Pop-I lines (orange, solid) — routed via Pop-I's angled path
         {'nodes': ['cepheids', 'sneii', 'popi_h0_angle', 'h0'],
          'color': '#ee7a2a', 'ls': '-'},
         {'nodes': ['masers',   'sh0es_masers_bend', 'cepheids'],
          'color': '#ee7a2a', 'ls': '-'},
         {'nodes': ['deb',      'sh0es_deb_bend', 'sh0es_deb_angle', 'cepheids'],
          'color': '#ee7a2a', 'ls': '-'},
         {'nodes': ['parallax', 'sh0es_par_bend', 'cepheids'],
          'color': '#ee7a2a', 'ls': '-'},
         # Pop-II lines (magenta, solid) — routed via Pop-II's angled path
         {'nodes': ['masers', 'cchp_masers_angle', 'trgb',
                    'sbf', 'popii_h0_angle', 'h0'],
          'color': '#d12b8a', 'ls': '-'},
     ]},
    {'id': 'desi',    'name': 'DESI',     'color': '#55cc55', 'h0': 73.6,  'err': 0.80,
     'ref': 'Said et al. 2025',
     'arxiv': 'https://arxiv.org/abs/2408.13842',
     'path': ['sbf', 'fp', 'desi_fp_h0_angle', 'h0'],
     'branches': [
         ['snia', 'fp'],
         # baseline calibration ladder — hidden until DESI is isolated.
         # Drawn white dashed via the same waypoints as Baseline.
         {'nodes': ['masers', 'cchp_masers_angle', 'trgb', 'sbf'],
          'color': '#ffffff', 'ls': '-', 'lw': 1.4, 'alpha': 0.65,
          'only_when_isolated': True},
         {'nodes': ['trgb', 'cchp_snia_angle', 'snia'],
          'color': '#ffffff', 'ls': '-', 'lw': 1.4, 'alpha': 0.65,
          'only_when_isolated': True},
         {'nodes': ['masers', 'sh0es_masers_bend', 'cepheids', 'snia'],
          'color': '#ffffff', 'ls': '-', 'lw': 1.4, 'alpha': 0.65,
          'only_when_isolated': True},
         {'nodes': ['deb', 'sh0es_deb_bend', 'sh0es_deb_angle', 'cepheids'],
          'color': '#ffffff', 'ls': '-', 'lw': 1.4, 'alpha': 0.65,
          'only_when_isolated': True},
         {'nodes': ['parallax', 'sh0es_par_bend', 'cepheids'],
          'color': '#ffffff', 'ls': '-', 'lw': 1.4, 'alpha': 0.65,
          'only_when_isolated': True},
     ]},
    {'id': 'adh0cc',  'name': 'adh0cc',   'color': '#e0a070', 'h0': 74.83, 'err': 1.85,
     'ref': 'Vogl et al. 2025',
     'arxiv': 'https://arxiv.org/abs/2411.04968',
     'path': ['sneii_epm', 'adh0cc_right', 'h0']},
]

CONSENSUS = {'value': 73.99, 'err': 0.70}
CMB       = {'value': 67.24, 'err': 0.35}

N = len(ROUTES)

# Dark-theme palette
BG       = '#0a0a18'
PANEL_BG = '#0f101d'
TEXT     = '#d8dce8'
TEXT_DIM = '#9aa0b0'
SPINE    = '#3a3e52'
GRID     = '#1c1e30'


# --------------------------------------------------------------------------
# Figure
# --------------------------------------------------------------------------

fig = plt.figure(figsize=(13, 10), facecolor=BG)
fig.canvas.manager.set_window_title('Local Distance Network (animated)')

gs = fig.add_gridspec(2, 1, height_ratios=[2.4, 1.5], hspace=0.15,
                      left=0.06, right=0.82, top=0.88, bottom=0.22)
ax_net = fig.add_subplot(gs[0])
ax_h0  = fig.add_subplot(gs[1])
for a in (ax_net, ax_h0):
    a.set_facecolor(PANEL_BG)
    for s in a.spines.values():
        s.set_color(SPINE)
    a.tick_params(colors=TEXT_DIM)

# Title centered over the main diagram (which spans left=0.06 → right=0.82)
fig.text((0.06 + 0.82) / 2, 0.915,
         r'The Local Distance Network to $H_0$',
         ha='center', va='center',
         fontsize=15, fontweight='bold', color=TEXT)


# --------------------------------------------------------------------------
# Network diagram (top)
# --------------------------------------------------------------------------

# Tier background bands (subtle, dark-theme friendly)
tier_specs = [
    (0.0,  0.15, 1.0,  3.7, '#4a3240', 'Geometric anchors        ', '#ffcc88'),
    (1.3,  0.15, 2.1,  3.7, '#2e3d66', 'Stellar candles',       '#9cc6ff'),
    (3.65, 0.15, 2.05, 3.7, '#3a3e4e', 'Long-range indicators', '#c9c9c9'),
]
for x, y, w, h, fill, label, tcolor in tier_specs:
    ax_net.add_patch(mpatches.Rectangle(
        (x, y), w, h, facecolor=fill, alpha=0.75, edgecolor='none', zorder=0))
    ax_net.text(x + w/2, 4.0, label, ha='center', va='bottom',
                fontsize=10, color=tcolor, fontweight='medium')

# Vertical "Geometry" sidebar on the left of the geometric-anchors tier
ax_net.text(-0.48, (0.15 + 3.85) / 2, "Geometry",
            ha='center', va='center', rotation=90,
            fontsize=20, fontweight='bold', color='#ffcc88', zorder=1)

# Anchor-junction node — faint static connectors tying Parallax, DEB
# and Masers to a single hub node on the far left.  Routes that
# originate at a geometric anchor pass through this hub, so clicking
# them lights the line all the way back here.
ANCHOR_HUB_XY = (-0.10, 2.0)
NODES['hub'] = (ANCHOR_HUB_XY[0], ANCHOR_HUB_XY[1], '')
for _anchor in ('parallax', 'deb', 'masers'):
    _ax_x, _ax_y, _ = NODES[_anchor]
    ax_net.plot([_ax_x, ANCHOR_HUB_XY[0]], [_ax_y, ANCHOR_HUB_XY[1]],
                color='#ffffff', lw=2.0, alpha=0.70, zorder=1,
                solid_capstyle='round')
# (hub circle is drawn later by the NODES loop — keyed as 'hub')

# Route lines — all visible from the start (static layout).  Pop-Mix
# rendered with a dashed pattern to match the reference figure.  A
# route may have `branches` — extra node-sequences (e.g. SH0ES's three
# anchor calibrations feeding into Cepheids) that are drawn in the
# same colour and grouped with the main path for isolation.
route_lines = {}        # id → list of Line2D (first = main path, rest = branches)
line_to_id  = {}        # Line2D → route id (for pick_event dispatch)
line_alpha  = {}        # Line2D → native alpha (so reset restores per-branch values)
line_lw     = {}        # Line2D → native linewidth
background_lines = set()  # Line2Ds that should never be brightened by isolation
hidden_lines     = set()  # Line2Ds that are invisible unless their route is isolated
FULL_ALPHA = 0.80
for r in ROUTES:
    # Pop-Mix is dashed everywhere; Pop-I keeps a solid main path but
    # dashed anchor→cepheids branches (they're weak/indirect calibrations).
    # Baseline draws dashed-ghost by default (calibration web).
    main_ls   = r.get('main_ls',
                      '--' if r['id'] == 'popmix'
                      else '-')
    branch_ls = r.get('branch_ls',
                      '--' if r['id'] == 'popmix'
                      else '-')
    main_lw    = r.get('main_lw',    1.4 if r['id'] == 'baseline' else 2.8)
    main_alpha = r.get('main_alpha', 0.65 if r['id'] == 'baseline' else FULL_ALPHA)
    branch_lw_default    = 1.4  if r['id'] == 'baseline' else 2.8
    branch_alpha_default = 0.65 if r['id'] == 'baseline' else FULL_ALPHA
    lines = []
    # main path — this is the one that ends up in the legend
    xs = [NODES[n][0] for n in r['path']]
    ys = [NODES[n][1] for n in r['path']]
    _ref = r.get('ref', '')
    _label = f"{r['name']}  ({r['h0']:.2f} ± {r['err']:.2f})"
    if _ref:
        _label += f"   {_ref}"
    _zmain = 3 if r['id'] == 'sh0es' else 2
    main, = ax_net.plot(
        xs, ys, color=r['color'], linewidth=main_lw, alpha=main_alpha,
        solid_capstyle='round', solid_joinstyle='round',
        linestyle=main_ls, zorder=_zmain,
        label=_label)
    main.set_picker(True); main.set_pickradius(8)
    line_to_id[main] = r['id']
    line_alpha[main] = main_alpha
    line_lw[main]    = main_lw
    lines.append(main)
    # extra branches (same colour, no legend entry).  Each entry is
    # either a list of node ids (inherits branch_ls) or a dict with
    # 'nodes' and an optional per-branch 'ls'.
    for br in r.get('branches', []):
        if isinstance(br, dict):
            br_nodes = br['nodes']
            br_ls    = br.get('ls', branch_ls)
            br_color = br.get('color', r['color'])
            br_lw    = br.get('lw', branch_lw_default)
            br_alpha = br.get('alpha', branch_alpha_default)
            br_bg    = br.get('background', False)
            br_hide  = br.get('only_when_isolated', False)
        else:
            br_nodes, br_ls = br, branch_ls
            br_color, br_lw, br_alpha, br_bg, br_hide = (
                r['color'], branch_lw_default, branch_alpha_default, False, False)
        xs = [NODES[n][0] for n in br_nodes]
        ys = [NODES[n][1] for n in br_nodes]
        # zorder: SH0ES wins overlaps with other routes
        z = 3 if r['id'] == 'sh0es' else 2
        b, = ax_net.plot(
            xs, ys, color=br_color, linewidth=br_lw,
            alpha=0.0 if br_hide else br_alpha,
            solid_capstyle='round', solid_joinstyle='round',
            linestyle=br_ls, zorder=z)
        if not br_bg:
            b.set_picker(True); b.set_pickradius(8)
            line_to_id[b] = r['id']
        line_alpha[b] = br_alpha
        line_lw[b]    = br_lw
        if br_bg:
            background_lines.add(b)
        if br_hide:
            hidden_lines.add(b)
        lines.append(b)
    route_lines[r['id']] = lines

# Nodes — always visible on top.
# Capture each node's Circle into node_artists so click can open a
# per-node info popup loaded from a local text file.
node_artists = {}    # node_id → Circle artist
for nid, (x, y, label) in NODES.items():
    if nid == 'h0':
        # H₀ destination — sits above the divided-highway overlays.
        c = mpatches.Circle((x, y), 0.22, facecolor='#FAC775',
                            edgecolor='#ffd88f', linewidth=1.4, zorder=5)
        ax_net.add_patch(c)
        ax_net.text(x, y, r'$H_0$', ha='center', va='center',
                    fontsize=14, fontweight='bold',
                    color='#2a1a00', zorder=6)
        node_artists[nid] = c
    elif nid == 'hub':
        # Solid-yellow geometry-anchor hub (not clickable)
        ax_net.add_patch(mpatches.Circle(
            (x, y), 0.13, facecolor='#ffcc44', edgecolor='#ffdd77',
            linewidth=1.4, zorder=3))
    elif nid in ('mcp_top', 'mcp_far_right', 'adh0cc_right',
                 'sh0es_par_bend', 'sh0es_deb_bend', 'sh0es_deb_angle',
                 'sh0es_masers_bend',
                 'cf4_trgb_drop', 'cf4_trgb_angle',
                 'cf4_tf_h0_angle', 'cf4_ceph_tf_angle',
                 'popmix_ceph_drop', 'popmix_ceph_angle',
                 'popmix_trgb_drop', 'popmix_trgb_angle',
                 'baseline_miras_angle',
                 'desi_fp_h0_angle',
                 'masers_jagb_angle', 'jagb_snia_angle',
                 'cchp_masers_angle', 'cchp_snia_angle',
                 'popii_h0_angle', 'popi_h0_angle'):
        # pure waypoints — no dot, no label
        continue
    elif nid == 'sneii_epm':
        # outside-the-tier node (below the diagram)
        c = mpatches.Circle((x, y), 0.10, facecolor=PANEL_BG,
                            edgecolor=TEXT, linewidth=1.2, zorder=3)
        ax_net.add_patch(c)
        ax_net.text(x - 0.30, y, label, ha='right', va='center',
                    fontsize=9.5, fontweight='medium',
                    color=TEXT, zorder=4)
        node_artists[nid] = c
    else:
        # Bump SNeIa and MASER above the divided-highway overlays so
        # the 2-lane decorations don't hide their circle/label.
        _z = 5 if nid in ('snia', 'masers') else 3
        c = mpatches.Circle((x, y), 0.10, facecolor=PANEL_BG,
                            edgecolor=TEXT, linewidth=1.2, zorder=_z)
        ax_net.add_patch(c)
        ax_net.text(x, y + 0.22, label, ha='center', va='bottom',
                    fontsize=9.5, fontweight='medium',
                    color=TEXT, zorder=_z + 1)
        node_artists[nid] = c

# Per-route segment labels, shown only when that route is isolated.
# Each entry: (route_id, x, y, text, color, rotation_deg)
import math as _math

def _seg_label(a_node, b_node, t=0.5, dy_off=0.14):
    ax, ay, _ = NODES[a_node]
    bx, by, _ = NODES[b_node]
    return (ax + t * (bx - ax), ay + t * (by - ay) + dy_off,
            _math.degrees(_math.atan2(by - ay, bx - ax)))

route_labels = {}   # route_id → list[Text]

_desi_color = next(r['color'] for r in ROUTES if r['id'] == 'desi')
_x, _y, _rot = _seg_label('desi_fp_h0_angle', 'h0', t=0.5)
route_labels['desi'] = [
    ax_net.text(
        _x, _y, 'via Coma', ha='center', va='bottom',
        fontsize=7.5, fontstyle='italic', color=_desi_color,
        rotation=_rot, rotation_mode='anchor', zorder=4, visible=False),
]

_popii_color = next(r['color'] for r in ROUTES if r['id'] == 'popii')
_x, _y, _rot = _seg_label('trgb', 'sbf', t=0.5)
route_labels['popii'] = [ax_net.text(
    _x, _y, 'via Fornax & Virgo', ha='center', va='bottom',
    fontsize=7.5, fontstyle='italic', color=_popii_color,
    rotation=_rot, rotation_mode='anchor', zorder=4, visible=False)]

_mcp_color = next(r['color'] for r in ROUTES if r['id'] == 'mcp')
_x, _y, _rot = _seg_label('mcp_top', 'mcp_far_right', t=0.5, dy_off=0.12)
route_labels['mcp'] = [ax_net.text(
    _x, _y, 'Megamaser Cosmology Project', ha='center', va='bottom',
    fontsize=8.5, fontstyle='italic', color=_mcp_color,
    rotation=_rot, rotation_mode='anchor', zorder=4, visible=False)]

_adh0cc_color = next(r['color'] for r in ROUTES if r['id'] == 'adh0cc')
_x, _y, _rot = _seg_label('sneii_epm', 'adh0cc_right', t=0.5, dy_off=0.14)
route_labels['adh0cc'] = [ax_net.text(
    _x, _y, 'Astrophysically modeled', ha='center', va='bottom',
    fontsize=7.5, fontstyle='italic', color=_adh0cc_color,
    rotation=_rot, rotation_mode='anchor', zorder=4, visible=False)]

# Divided-highway overlay: masers→TRGB and the short horizontal stub out
# of TRGB (TRGB→cchp_snia_angle) are shared by CCHP/EDD and Pop-II.
# Render two parallel-offset colored lanes on top of the route lines so
# both colors show at startup. Hidden when any single route is isolated.
_hwy_xs = [NODES['masers'][0], NODES['cchp_masers_angle'][0],
           NODES['trgb'][0], NODES['cchp_snia_angle'][0]]
_hwy_ys = [NODES['masers'][1], NODES['cchp_masers_angle'][1],
           NODES['trgb'][1], NODES['cchp_snia_angle'][1]]
_lane_lw   = 2.8
_lane_off  = 2.5  # display-pixel offset for each lane
_trans_up  = mtransforms.offset_copy(ax_net.transData, fig=fig, y=+_lane_off, units='dots')
_trans_dn  = mtransforms.offset_copy(ax_net.transData, fig=fig, y=-_lane_off, units='dots')
_lane_pop  = ax_net.plot(_hwy_xs, _hwy_ys, color='#d12b8a', linewidth=_lane_lw,
                         alpha=FULL_ALPHA, solid_capstyle='butt',
                         solid_joinstyle='miter', transform=_trans_up,
                         zorder=2.5)[0]
_lane_cchp = ax_net.plot(_hwy_xs, _hwy_ys, color='#a09428', linewidth=_lane_lw,
                         alpha=FULL_ALPHA, solid_capstyle='butt',
                         solid_joinstyle='miter', transform=_trans_dn,
                         zorder=2.5)[0]
divided_highway_lines = [_lane_pop, _lane_cchp]

# Pop-I and CF4 overlap on the horizontal Cepheids→cf4_ceph_tf_angle stub.
_hwy2_xs = [NODES['cepheids'][0], NODES['cf4_ceph_tf_angle'][0]]
_hwy2_ys = [NODES['cepheids'][1], NODES['cf4_ceph_tf_angle'][1]]
_lane_popi = ax_net.plot(_hwy2_xs, _hwy2_ys, color='#ee7a2a', linewidth=_lane_lw,
                         alpha=FULL_ALPHA, solid_capstyle='butt',
                         solid_joinstyle='miter', transform=_trans_up,
                         zorder=2.5)[0]
_lane_cf4  = ax_net.plot(_hwy2_xs, _hwy2_ys, color='#a892d4', linewidth=_lane_lw,
                         alpha=FULL_ALPHA, solid_capstyle='butt',
                         solid_joinstyle='miter', transform=_trans_dn,
                         zorder=2.5)[0]
divided_highway_lines += [_lane_popi, _lane_cf4]

# (Static JAGB-pink and Miras-red decorations are now provided by the
# V01 and V02 routes themselves — they appear at startup as those
# routes' main paths and brighten on isolation.)


def _two_lane(xs, ys, color_up, color_dn, z=3.6):
    """Helper: draw a divided-highway pair of offset parallel lines."""
    up = ax_net.plot(xs, ys, color=color_up, linewidth=_lane_lw,
                     alpha=FULL_ALPHA, solid_capstyle='butt',
                     solid_joinstyle='miter', transform=_trans_up,
                     zorder=z)[0]
    dn = ax_net.plot(xs, ys, color=color_dn, linewidth=_lane_lw,
                     alpha=FULL_ALPHA, solid_capstyle='butt',
                     solid_joinstyle='miter', transform=_trans_dn,
                     zorder=z)[0]
    return [up, dn]

# JAGB chain (salmon) + Miras chain (dark red) — overlap on the 45°
# down out of MASER (shared corridor before JAGB peels off horizontally).
divided_highway_lines += _two_lane(
    [NODES['masers'][0], NODES['masers_jagb_angle'][0]],
    [NODES['masers'][1], NODES['masers_jagb_angle'][1]],
    color_up='#ff5577', color_dn='#a00000')

# Same pair overlap on the horizontal at y=1.90 from x=2.80 (where both
# rejoin) into SNeIa.
divided_highway_lines += _two_lane(
    [NODES['jagb_snia_angle'][0], NODES['snia'][0]],
    [NODES['jagb_snia_angle'][1], NODES['snia'][1]],
    color_up='#ff5577', color_dn='#a00000')

# Pop-II + DESI overlap on the 45° from (5.30, 2.65) to H₀.
divided_highway_lines += _two_lane(
    [NODES['desi_fp_h0_angle'][0], NODES['h0'][0]],
    [NODES['desi_fp_h0_angle'][1], NODES['h0'][1]],
    color_up='#d12b8a', color_dn='#55cc55')

# SH0ES + CCHP overlap on the horizontal SNeIa→H₀ at y=1.90.
divided_highway_lines += _two_lane(
    [NODES['snia'][0], NODES['h0'][0]],
    [NODES['snia'][1], NODES['h0'][1]],
    color_up='#2a5fd9', color_dn='#a09428')

ax_net.set_xlim(-0.65, 6.3)
ax_net.set_ylim(-1.3, 4.6)
ax_net.set_aspect('equal')
ax_net.axis('off')


# --------------------------------------------------------------------------
# Acronym legend (bottom-left of figure)
# --------------------------------------------------------------------------

ACRONYMS = [
    ('MASER', 'Microwave Amp. by Stim. Emis. of Rad.'),
    ('DEB',   'Detached Eclipsing Binaries'),
    ('TRGB',  'Tip of the Red Giant Branch'),
    ('JAGB',  'J-region Asymptotic Giant Branch'),
    ('SBF',   'Surface Brightness Fluctuations'),
    ('FP',    'Fundamental Plane'),
    ('TF',    'Tully–Fisher'),
    ('SNeIa', 'Supernovae Type Ia'),
    ('SNeII', 'Supernovae Type II'),
    ('EPM',   'Expanding Photosphere Method'),
]
# Render each acronym as its own Text artist so we can highlight
# individually when a route is isolated. A FancyBboxPatch behind the
# block reproduces the original framed look.
_acro_x   = 0.020
_acro_top = 0.88
_acro_lh  = 0.0140      # figure-y per line for monospace fontsize=8
_acro_pad = 0.006
_acro_w   = 0.275       # bbox width
_acro_h   = len(ACRONYMS) * _acro_lh + 2 * _acro_pad
fig.add_artist(mpatches.FancyBboxPatch(
    (_acro_x - _acro_pad, _acro_top - _acro_h + _acro_pad),
    _acro_w, _acro_h,
    boxstyle='round,pad=0.0',
    facecolor=PANEL_BG, edgecolor=SPINE, linewidth=0.6,
    transform=fig.transFigure, zorder=0))

acronym_texts = {}
for _i, (_k, _v) in enumerate(ACRONYMS):
    _t = fig.text(_acro_x, _acro_top - _acro_pad - _i * _acro_lh,
                  f"{_k:<5s} {_v}",
                  ha='left', va='top',
                  family='monospace', fontsize=8.0, color=TEXT_DIM)
    acronym_texts[_k] = _t


# --------------------------------------------------------------------------
# H0 comparison panel (bottom)
# --------------------------------------------------------------------------

# Consensus band + line
ax_h0.axvspan(CONSENSUS['value'] - CONSENSUS['err'],
              CONSENSUS['value'] + CONSENSUS['err'],
              color='#1D9E75', alpha=0.22, zorder=0)
# Vertical spacing between error-bar rows (>1 leaves whitespace).
ROW_STEP = 1.0
_y_top  = (N + 0.75) * ROW_STEP
_y_lab  = (N + 1.15) * ROW_STEP
ax_h0.plot([CONSENSUS['value'], CONSENSUS['value']], [-0.3, _y_top],
           color='#6dd4af', linewidth=1.3, linestyle='--', zorder=1)
ax_h0.text(CONSENSUS['value'], _y_lab,
           f"Everything Available {CONSENSUS['value']:.2f} ± {CONSENSUS['err']:.2f}",
           ha='center', fontsize=9.5, color='#6dd4af', fontweight='medium')

# CMB band + line
ax_h0.axvspan(CMB['value'] - CMB['err'],
              CMB['value'] + CMB['err'],
              color='#ff8787', alpha=0.22, zorder=0)
ax_h0.plot([CMB['value'], CMB['value']], [-0.3, _y_top],
           color='#ff8787', linewidth=1.3, linestyle='--', zorder=1)
ax_h0.text(CMB['value'], _y_lab,
           f"CMB {CMB['value']:.2f} ± {CMB['err']:.2f}",
           ha='center', fontsize=9.5, color='#ff8787', fontweight='medium')

# Tension readout — shown in the top-right corner of the H0 panel only
# while a route is isolated.  σ_T = (H0 - CMB) / sqrt(err² + CMB_err²)
tension_text = ax_h0.text(
    0.99, 0.97, '', transform=ax_h0.transAxes,
    ha='right', va='top',
    fontsize=11, fontweight='bold', color='#ff8787',
    visible=False)


def _update_tension_display(route_id):
    if route_id is None:
        tension_text.set_visible(False)
        return
    r = next((rr for rr in ROUTES if rr['id'] == route_id), None)
    if r is None:
        tension_text.set_visible(False)
        return
    sigma = abs(r['h0'] - CMB['value']) / (r['err']**2 + CMB['err']**2) ** 0.5
    if sigma >= 3.0:
        col = '#ff8787'
    elif sigma >= 2.0:
        col = '#ffcc66'
    else:
        col = '#6dd4af'
    tension_text.set_text(f"{sigma:.1f}σ from CMB")
    tension_text.set_color(col)
    tension_text.set_visible(True)

# Error bars — all created invisible, revealed by animation.
# Also make the errorbar markers, route-name labels, and an invisible
# row-background rectangle pickable so the whole row in the H0 panel
# acts as a clickable isolation target.
h0_bars = {}
h0_pick = {}      # artist → route_id
h0_value_text_by_id = {}    # route_id → H0 value Text (right column)
h0_name_text_by_id  = {}    # route_id → route-name Text (left column)
for i, r in enumerate(ROUTES):
    y = (N - i - 0.5) * ROW_STEP
    eb = ax_h0.errorbar(
        r['h0'], y, xerr=r['err'], fmt='o',
        color=r['color'], ecolor=r['color'],
        markersize=7, capsize=4.5, capthick=1.8,
        elinewidth=2.3, zorder=3)
    line, caps, bars = eb
    # Static version — visible from the start
    # pickable marker
    line.set_picker(True); line.set_pickradius(10)
    h0_pick[line] = r['id']
    h0_bars[r['id']] = eb

    # Route-name text (pickable)
    nm = ax_h0.text(64.3, y, r['name'], ha='right', va='center',
                    fontsize=10, fontweight='medium', color=TEXT,
                    picker=True)
    h0_pick[nm] = r['id']
    h0_name_text_by_id[r['id']] = nm
    # value text
    h0_value_text_by_id[r['id']] = ax_h0.text(
        81.2, y, f"{r['h0']:.2f} ± {r['err']:.2f}",
        ha='left', va='center', fontsize=9, color=TEXT_DIM)
    # transparent clickable rectangle spanning the row for easier hitting
    rect = mpatches.Rectangle((63, y - 0.5 * ROW_STEP), 19.5, ROW_STEP,
                              facecolor='none', edgecolor='none',
                              picker=True, zorder=0)
    ax_h0.add_patch(rect)
    h0_pick[rect] = r['id']

ax_h0.set_xlim(63, 82.5)
ax_h0.set_ylim(-0.3, (N + 1.7) * ROW_STEP)
ax_h0.set_yticks([])
ax_h0.set_xlabel(r'$H_0$ (km s$^{-1}$ Mpc$^{-1}$)',
                 fontsize=11, color=TEXT)
for side in ('top', 'right', 'left'):
    ax_h0.spines[side].set_visible(False)
ax_h0.tick_params(axis='x', labelsize=10, colors=TEXT_DIM)
ax_h0.grid(axis='x', color=GRID, linewidth=0.4)


# --------------------------------------------------------------------------
# Legend (right of the network)
# --------------------------------------------------------------------------

legend = ax_net.legend(
    loc='upper left', bbox_to_anchor=(1.04, 1.0),
    fontsize=9, frameon=True, fancybox=True, borderpad=0.8,
    title='Routes', title_fontsize=10,
    facecolor=PANEL_BG, edgecolor=SPINE, labelcolor=TEXT)
legend.get_title().set_color(TEXT)

for leg_line in legend.get_lines():
    leg_line.set_picker(True)
    leg_line.set_pickradius(14)
    leg_line.set_linewidth(3.6)

legend_to_id = {ll: r['id'] for ll, r in zip(legend.get_lines(), ROUTES)}
# Map route_id → arxiv URL (if any), used for the side-arrow clicks
# and for embedding in saved PDF/SVG via Text.set_url().
route_arxiv = {r['id']: r.get('arxiv') for r in ROUTES if r.get('arxiv')}
# Per-route maps so we can highlight on isolation.
legend_text_by_id = {}
legend_line_by_id = {r['id']: ll for ll, r in zip(legend.get_lines(), ROUTES)}
# Make legend texts pickable too, so clicking the label row (not just
# the colour swatch) also isolates.
for lt, r in zip(legend.get_texts(), ROUTES):
    lt.set_picker(True)
    legend_to_id[lt] = r['id']
    legend_text_by_id[r['id']] = lt
    if r.get('arxiv'):
        lt.set_url(r['arxiv'])     # clickable in saved PDF/SVG

# Route-acronym legend on the right, below the Routes legend
ROUTE_ACRONYMS = [
    ('SH0ES',  r'Supernovae $H_0$ for the Equation of State of dark energy'),
    ('CCHP',   'Carnegie–Chicago Hubble Program'),
    ('EDD',    'Extragalactic Distance Database'),
    ('Pop',    'Population stellar tracers'),
    ('MCP',    'Megamaser Cosmology Project'),
    ('CF4',    'Cosmicflows-4th release'),
    ('DESI',   'Dark Energy Spectroscopic Instrument'),
    ('adh0cc', r'ad hoc $H_0$ from core-collapse'),
]

# Overlay a clickable "↗" beside each legend entry that has an arxiv
# URL. We need the legend text positions, which only exist after the
# canvas has been drawn once.
arxiv_links = {}     # arrow Text artist → URL
fig.canvas.draw()

# Place the route-acronym box just below the Routes legend
_leg_bbox = legend.get_window_extent(fig.canvas.get_renderer())
_inv_fig = fig.transFigure.inverted()
_lx, _ly = _inv_fig.transform((_leg_bbox.x0, _leg_bbox.y0))
# Render each route-acronym as its own Text so we can highlight by route.
_racro_x   = _lx
_racro_top = _ly - 0.012
_racro_lh  = 0.0150    # figure-y per line for fontsize=8 (proportional)
_racro_pad = 0.006
_racro_w   = 0.260     # bbox width (fits longest SH0ES line)
_racro_h   = len(ROUTE_ACRONYMS) * _racro_lh + 2 * _racro_pad
fig.add_artist(mpatches.FancyBboxPatch(
    (_racro_x - _racro_pad, _racro_top - _racro_h + _racro_pad),
    _racro_w, _racro_h,
    boxstyle='round,pad=0.0',
    facecolor=PANEL_BG, edgecolor=SPINE, linewidth=0.6,
    transform=fig.transFigure, zorder=0))

route_acronym_texts = {}
for _i, (_k, _v) in enumerate(ROUTE_ACRONYMS):
    _t = fig.text(_racro_x, _racro_top - _racro_pad - _i * _racro_lh,
                  f"{_k}  =  {_v}",
                  ha='left', va='top',
                  fontsize=8.0, color=TEXT_DIM)
    route_acronym_texts[_k] = _t
_inv = fig.transFigure.inverted()
for lt, r in zip(legend.get_texts(), ROUTES):
    url = r.get('arxiv')
    if not url:
        continue
    bbox = lt.get_window_extent(fig.canvas.get_renderer())
    x_disp = bbox.x1 + 6
    y_disp = (bbox.y0 + bbox.y1) / 2
    fx, fy = _inv.transform((x_disp, y_disp))
    arrow = fig.text(fx, fy, '↗', ha='left', va='center',
                     color='#9ad9ff', fontsize=11, fontweight='bold')
    arrow.set_picker(True)
    arrow.set_url(url)
    arxiv_links[arrow] = url
active = {'id': None}


# --------------------------------------------------------------------------
# Isolation helpers (click a legend entry or H₀ row to spotlight one route)
# --------------------------------------------------------------------------

def _set_errorbar_alpha(eb, alpha):
    line, caps, bars = eb
    line.set_alpha(alpha)
    for a in list(caps) + list(bars):
        a.set_alpha(alpha)


# Map physical-node id → list of acronym keys touched in the lower-left
# acronym box. (sneii_epm contributes both SNeII and EPM.)
NODE_TO_ACRO = {
    'masers':    ['MASER'],
    'deb':       ['DEB'],
    'trgb':      ['TRGB'],
    'jagb':      ['JAGB'],
    'sbf':       ['SBF'],
    'fp':        ['FP'],
    'tf':        ['TF'],
    'snia':      ['SNeIa'],
    'sneii':     ['SNeII'],
    'sneii_epm': ['SNeII', 'EPM'],
}

# Map route_id → list of route-acronym keys (right side panel).
ROUTE_TO_RACRO = {
    'baseline': [],
    'sh0es':    ['SH0ES'],
    'cchp_edd': ['CCHP', 'EDD'],
    'popii':    ['Pop'],
    'mcp':      ['MCP'],
    'popi':     ['Pop'],
    'cf4':      ['CF4'],
    'popmix':   ['Pop'],
    'desi':     ['DESI'],
    'adh0cc':   ['adh0cc'],
}


def _route_acros_used(route_id):
    r = next((rr for rr in ROUTES if rr['id'] == route_id), None)
    if not r:
        return set()
    used = set()
    for n in r['path']:
        used.update(NODE_TO_ACRO.get(n, []))
    for br in r.get('branches', []):
        nodes = br['nodes'] if isinstance(br, dict) else br
        for n in nodes:
            used.update(NODE_TO_ACRO.get(n, []))
    return used


# Reverse index: acronym key → set of route_ids that pass through any
# node mapped to that acronym.  Used by the acronym-hover feature.
ACRO_TO_ROUTES = {}
for _r in ROUTES:
    for _k in _route_acros_used(_r['id']):
        ACRO_TO_ROUTES.setdefault(_k, set()).add(_r['id'])


def _highlight_acronyms(route_id):
    used = _route_acros_used(route_id)
    rused = set(ROUTE_TO_RACRO.get(route_id, []))
    for k, t in acronym_texts.items():
        if k in used:
            t.set_color(TEXT)
            t.set_fontweight('bold')
        else:
            t.set_color(TEXT_DIM)
            t.set_fontweight('normal')
    for k, t in route_acronym_texts.items():
        if k in rused:
            t.set_color(TEXT)
            t.set_fontweight('bold')
        else:
            t.set_color(TEXT_DIM)
            t.set_fontweight('normal')


def _reset_acronym_highlight():
    for t in acronym_texts.values():
        t.set_color(TEXT_DIM)
        t.set_fontweight('normal')
    for t in route_acronym_texts.values():
        t.set_color(TEXT_DIM)
        t.set_fontweight('normal')


def _highlight_route(route_id):
    """Bold/brighten the matching route's legend entry, H0 panel name,
    and H0 value label; dim the others."""
    for rid, lt in legend_text_by_id.items():
        if rid == route_id:
            lt.set_color(TEXT)
            lt.set_fontweight('bold')
        else:
            lt.set_color(TEXT_DIM)
            lt.set_fontweight('normal')
    for rid, ll in legend_line_by_id.items():
        ll.set_linewidth(5.5 if rid == route_id else 2.4)
        ll.set_alpha(1.0 if rid == route_id else 0.45)
    for rid, t in h0_value_text_by_id.items():
        if rid == route_id:
            t.set_color(TEXT)
            t.set_fontweight('bold')
        else:
            t.set_color(TEXT_DIM)
            t.set_fontweight('normal')
    for rid, t in h0_name_text_by_id.items():
        if rid == route_id:
            t.set_color(TEXT)
            t.set_fontweight('bold')
        else:
            t.set_color(TEXT_DIM)
            t.set_fontweight('normal')


def _reset_route_highlight():
    for lt in legend_text_by_id.values():
        lt.set_color(TEXT)
        lt.set_fontweight('normal')
    for ll in legend_line_by_id.values():
        ll.set_linewidth(3.6)
        ll.set_alpha(1.0)
    for t in h0_value_text_by_id.values():
        t.set_color(TEXT_DIM)
        t.set_fontweight('normal')
    for t in h0_name_text_by_id.values():
        t.set_color(TEXT)
        t.set_fontweight('medium')


def info(msg):
    status.set_text(msg)


# --------------------------------------------------------------------------
# Controls
# --------------------------------------------------------------------------

def mkax(x, y, w, h, fc=PANEL_BG):
    a = fig.add_axes([x, y, w, h]); a.set_facecolor(fc); return a

def mkbtn(x, y, w, h, label):
    a = mkax(x, y, w, h, '#2a2f4a')
    b = Button(a, label, color='#2a2f4a', hovercolor='#3d4470')
    b.label.set_color(TEXT); b.label.set_fontsize(9)
    return b

# Buttons: Save PNG, Save PDF (vector with clickable arXiv links), Reset, Tour
btn_save     = mkbtn(0.06, 0.952, 0.10, 0.028, 'Save PNG')
btn_save_pdf = mkbtn(0.17, 0.952, 0.10, 0.028, 'Save PDF')
btn_clear    = mkbtn(0.28, 0.952, 0.09, 0.028, 'Reset')
btn_tour     = mkbtn(0.38, 0.952, 0.09, 0.028, 'Tour')
btn_fig1     = mkbtn(0.67, 0.905, 0.12, 0.025, 'H0DN Fig. 1')
btn_tab4     = mkbtn(0.80, 0.905, 0.12, 0.025, 'H0DN Tab. 4')

# Tour speed slider — interval (ms) between routes.  Higher = slower.
fig.text(0.485, 0.967, 'Tour ms', color=TEXT_DIM, fontsize=8,
         ha='left', va='center')
speed_ax = fig.add_axes([0.525, 0.961, 0.08, 0.014], facecolor='#10121f')
speed_slider = Slider(speed_ax, '', 40, 1200, valinit=180, valstep=20,
                      color='#5588cc', track_color=GRID,
                      initcolor='none')
speed_slider.valtext.set_color(TEXT_DIM)
speed_slider.valtext.set_fontsize(8)
speed_slider.poly.set_edgecolor('none')

# Status line — sits in the narrow gap between the H0DN buttons /
# title row above and the Routes legend below.
status_ax = mkax(0.40, 0.882, 0.55, 0.020, '#10121f')
status_ax.set_xticks([]); status_ax.set_yticks([])
status = status_ax.text(0.02, 0.5, '', color=TEXT_DIM, fontsize=9,
                        va='center', transform=status_ax.transAxes)


# --------------------------------------------------------------------------
# Callbacks
# --------------------------------------------------------------------------

def on_save(_):
    out = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f'local_distance_network_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
    fig.savefig(out, dpi=150, facecolor=BG, bbox_inches='tight')
    info(f'saved → {os.path.basename(out)}')
    print(f'saved → {out}')


btn_save.on_clicked(on_save)


def on_save_pdf(_):
    out = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f'local_distance_network_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf')
    fig.savefig(out, facecolor=BG, bbox_inches='tight')
    info(f'saved → {os.path.basename(out)}')
    print(f'saved → {out}')


btn_save_pdf.on_clicked(on_save_pdf)


def on_fig1(_):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        'figure1.png')
    if not os.path.isfile(path):
        info('figure1.png not found')
        return
    if _open_externally(path):
        info(f'opened {os.path.basename(path)}')
    else:
        info(f'could not open {os.path.basename(path)}')


btn_fig1.on_clicked(on_fig1)


def on_tab4(_):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        'aa57993-25.pdf')
    if not os.path.isfile(path):
        info('aa57993-25.pdf not found')
        return
    if _open_externally(path):
        info(f'opened {os.path.basename(path)}')
    else:
        info(f'could not open {os.path.basename(path)}')


btn_tab4.on_clicked(on_tab4)


def on_clear(_):
    if active['id'] is not None:
        active['id'] = None
        _reset_isolation()
        info('cleared isolation')
        fig.canvas.draw_idle()
    else:
        info('nothing to clear')


btn_clear.on_clicked(on_clear)


# --- Tour: auto-cycle through every route, end on the full map. -----
_tour_state = {'timer': None, 'queue': []}


def _cancel_tour():
    """Stop a running tour and reset to the full map. Returns True if a
    tour was active."""
    t = _tour_state.get('timer')
    if t is None:
        return False
    try:
        t.stop()
    except Exception:
        pass
    _tour_state['timer'] = None
    _tour_state['queue'] = []
    if active['id'] is not None:
        active['id'] = None
        _reset_isolation()
    fig.canvas.draw_idle()
    return True


def _start_tour(interval_ms=None):
    _cancel_tour()
    if interval_ms is None:
        interval_ms = int(speed_slider.val)
    # Anchor the comparison on the currently-isolated route (if any),
    # otherwise on Baseline.  The tour then steps through every other
    # route paired against the anchor.
    anchor_id = active['id'] or 'baseline'
    anchor = next((r for r in ROUTES if r['id'] == anchor_id), None)
    if anchor is None:
        anchor_id = 'baseline'
        anchor = next(r for r in ROUTES if r['id'] == 'baseline')
    _tour_state['queue'] = [
        (anchor_id, r['id'], f"{anchor['name']} vs {r['name']}")
        for r in ROUTES if r['id'] != anchor_id
    ]
    active['id'] = None
    timer = fig.canvas.new_timer(interval=interval_ms)

    def _step():
        if not _tour_state['queue']:
            timer.stop()
            _tour_state['timer'] = None
            active['id'] = None
            _reset_isolation()
            info(DEFAULT_STATUS)
            fig.canvas.draw_idle()
            return
        rid_a, rid_b, label = _tour_state['queue'].pop(0)
        _highlight_routes((rid_a, rid_b))
        ra = next((r for r in ROUTES if r['id'] == rid_a), None)
        rb = next((r for r in ROUTES if r['id'] == rid_b), None)
        if ra and rb:
            sigma = abs(ra['h0'] - rb['h0']) / (
                ra['err'] ** 2 + rb['err'] ** 2) ** 0.5
            info(f"{label}:  {ra['h0']:.2f} vs {rb['h0']:.2f}  "
                 f"({sigma:.1f}σ)")
        else:
            info(label)
        fig.canvas.draw_idle()

    timer.add_callback(_step)
    timer.start()
    _tour_state['timer'] = timer


def on_tour(_):
    _start_tour()


btn_tour.on_clicked(on_tour)


# Legend click → isolate one route (all its branches stay grouped)
def _reset_isolation():
    for rid, lines in route_lines.items():
        for ln in lines:
            if ln in hidden_lines:
                ln.set_alpha(0.0)
                ln.set_linewidth(line_lw.get(ln, 2.8))
            else:
                ln.set_alpha(line_alpha.get(ln, FULL_ALPHA))
                ln.set_linewidth(line_lw.get(ln, 2.8))
    for rid, eb in h0_bars.items():
        _set_errorbar_alpha(eb, 1.0)
    for labels in route_labels.values():
        for t in labels:
            t.set_visible(False)
    for ln in divided_highway_lines:
        ln.set_visible(True)
    _reset_acronym_highlight()
    _reset_route_highlight()
    _update_tension_display(None)


def _isolate(route_id):
    for rid, lines in route_lines.items():
        hi = (rid == route_id)
        for ln in lines:
            if ln in background_lines:
                # background lines stay at their native dim look
                ln.set_alpha(line_alpha.get(ln, FULL_ALPHA) if hi else 0.0)
                ln.set_linewidth(line_lw.get(ln, 2.8))
            elif ln in hidden_lines:
                # hidden lines only appear when their route is isolated
                ln.set_alpha(1.0 if hi else 0.0)
                ln.set_linewidth(3.6 if hi else line_lw.get(ln, 2.8))
            else:
                # Non-active route lines hide entirely so overlapping
                # shared-path segments don't stack into a visible ghost.
                ln.set_alpha(1.0 if hi else 0.0)
                ln.set_linewidth(3.6 if hi else 2.2)
    # The divided-highway decoration only makes sense in the unisolated map
    for ln in divided_highway_lines:
        ln.set_visible(False)
    _highlight_acronyms(route_id)
    _highlight_route(route_id)
    _update_tension_display(route_id)
    for rid, eb in h0_bars.items():
        _set_errorbar_alpha(eb, 1.0 if rid == route_id else 0.18)
    for rid, labels in route_labels.items():
        for t in labels:
            t.set_visible(rid == route_id)


# The Tour button compares the currently-isolated route (or Baseline,
# if nothing is isolated) against every other route in turn. The pair
# list is built dynamically inside _start_tour so the anchor follows
# the user's selection.


def _highlight_routes(route_ids):
    """Multi-route version of _isolate: every route in the set stays
    fully visible, all others are hidden."""
    matching = set(route_ids)
    for rid, lines in route_lines.items():
        keep = (rid in matching)
        for ln in lines:
            if ln in background_lines:
                ln.set_alpha(line_alpha.get(ln, FULL_ALPHA) if keep else 0.0)
                ln.set_linewidth(line_lw.get(ln, 2.8))
            elif ln in hidden_lines:
                ln.set_alpha(1.0 if keep else 0.0)
                ln.set_linewidth(3.6 if keep else line_lw.get(ln, 2.8))
            else:
                ln.set_alpha(1.0 if keep else 0.0)
                ln.set_linewidth(3.0 if keep else 2.2)
    for ln in divided_highway_lines:
        ln.set_visible(False)
    for rid, eb in h0_bars.items():
        _set_errorbar_alpha(eb, 1.0 if rid in matching else 0.18)
    for rid, labels in route_labels.items():
        for t in labels:
            t.set_visible(False)
    _reset_acronym_highlight()
    for rid, lt in legend_text_by_id.items():
        if rid in matching:
            lt.set_color(TEXT)
            lt.set_fontweight('bold')
        else:
            lt.set_color(TEXT_DIM)
            lt.set_fontweight('normal')
    for rid, ll in legend_line_by_id.items():
        ll.set_alpha(1.0 if rid in matching else 0.45)
        ll.set_linewidth(4.5 if rid in matching else 2.4)
    for rid, t in h0_value_text_by_id.items():
        if rid in matching:
            t.set_color(TEXT)
            t.set_fontweight('bold')
        else:
            t.set_color(TEXT_DIM)
            t.set_fontweight('normal')
    for rid, t in h0_name_text_by_id.items():
        if rid in matching:
            t.set_color(TEXT)
            t.set_fontweight('bold')
        else:
            t.set_color(TEXT_DIM)
            t.set_fontweight('normal')
    tension_text.set_visible(False)


def _toggle_isolation(route_id):
    if route_id not in route_lines:
        return
    if active['id'] == route_id:
        active['id'] = None
        _reset_isolation()
        info('cleared isolation')
    else:
        active['id'] = route_id
        _isolate(route_id)
        info(f"isolated route: {route_id}")
    fig.canvas.draw_idle()


def _route_for(art):
    return (line_to_id.get(art)
            or legend_to_id.get(art)
            or h0_pick.get(art))


def _node_info_path(node_id):
    """Find an info file for the given node in the script directory.
    Stems tried (in order): underscore-joined label (e.g. "SNeII_EPM"),
    space-joined label, the first line of the label (e.g. "Miras"),
    and finally the node id. RTF takes precedence so a user-formatted
    .rtf is picked up if present.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    raw_label = NODES[node_id][2]
    stems = [
        raw_label.replace('\n', '_').strip(),   # "SNeII_EPM"
        raw_label.replace('\n', ' ').strip(),   # "SNeII EPM"
        raw_label.split('\n', 1)[0].strip(),    # "SNeII"
        node_id,                                # "sneii_epm"
    ]
    seen = set()
    candidates = []
    for stem in stems:
        if not stem or stem in seen:
            continue
        seen.add(stem)
        candidates += [stem + '.rtf', stem + '.txt', stem + '.md', stem]
    for fname in candidates:
        path = os.path.join(base_dir, fname)
        if os.path.isfile(path):
            return path
    return None


def _open_externally(path):
    """Open a file in the OS default app (macOS / Windows / Linux)."""
    try:
        if sys.platform == 'darwin':
            subprocess.run(['open', path], check=False)
        elif sys.platform.startswith('win'):
            os.startfile(path)
        else:
            subprocess.run(['xdg-open', path], check=False)
        return True
    except Exception:
        return False


def _show_text_popup(label, path):
    """Render a text/markdown file in a dark scrollable tkinter window."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            body = f.read()
    except Exception as e:
        info(f'could not read {os.path.basename(path)}: {e}')
        return
    win = tk.Toplevel()
    win.title(f'{label} — {os.path.basename(path)}')
    win.geometry('640x440')
    txt = scrolledtext.ScrolledText(win, wrap=tk.WORD,
                                    font=('Helvetica', 11),
                                    bg='#0f101d', fg='#d8dce8',
                                    insertbackground='#d8dce8',
                                    padx=10, pady=8)
    txt.insert('1.0', body)
    txt.config(state='disabled')
    txt.pack(fill='both', expand=True)
    info(f'opened {os.path.basename(path)}')


_cartoon_state = {'artists': [], 'axes': [], 'btns': [], 'card_rect': None}


def _close_cartoon_popup():
    """Remove overlay artists from the main figure."""
    for a in _cartoon_state['artists']:
        try:
            a.remove()
        except Exception:
            pass
    for ax_obj in _cartoon_state['axes']:
        try:
            fig.delaxes(ax_obj)
        except Exception:
            pass
    _cartoon_state['artists'] = []
    _cartoon_state['axes'] = []
    _cartoon_state['btns'] = []
    _cartoon_state['eleonora_artists'] = []
    _cartoon_state['reaction_artists'] = []
    _cartoon_state['card_rect'] = None
    fig.canvas.draw_idle()


def _show_adam_reaction(emoji):
    """Replace the ar.png icon with the reaction emoji at the same spot."""
    for a in _cartoon_state.get('reaction_artists', []):
        try:
            a.remove()
        except Exception:
            pass
    _cartoon_state['reaction_artists'] = []

    # Hide the ar.png axes so the emoji takes its place.
    img_ax = _cartoon_state.get('img_ax')
    if img_ax is not None:
        img_ax.set_visible(False)

    pos = _cartoon_state.get('icon_pos', (0.45, 0.605))
    rxn = fig.text(pos[0], pos[1], emoji, ha='center', va='center',
                   fontsize=44, zorder=215)
    _cartoon_state['reaction_artists'] = [rxn]
    _cartoon_state['artists'].append(rxn)
    fig.canvas.draw_idle()


def _show_eleonora_reply(button_cx, button_top_y):
    """Overlay Eleonora's speech bubble (a regular rounded-rect speech
    balloon with a triangular tail) on top of the thought cloud, with
    the tail pointing down toward the d) button.
    """
    # Remove any prior Eleonora artists so repeated clicks don't stack.
    for a in _cartoon_state.get('eleonora_artists', []):
        try:
            a.remove()
        except Exception:
            pass
    _cartoon_state['eleonora_artists'] = []

    sb_x, sb_y, sb_w, sb_h = 0.31, 0.41, 0.38, 0.10
    sb_top = sb_y + sb_h
    bub_color = '#ffe79a'
    edge_color = '#aa5500'

    # Tail under the bubble, pointing down toward the d) button
    tail_base_lx = button_cx - 0.018
    tail_base_rx = button_cx + 0.018
    tail = mpatches.Polygon(
        [[tail_base_lx, sb_y],
         [tail_base_rx, sb_y],
         [button_cx,    button_top_y + 0.005]],
        transform=fig.transFigure, closed=True,
        facecolor=bub_color, edgecolor=edge_color, linewidth=1.6,
        zorder=219.5, figure=fig)
    fig.add_artist(tail)

    bubble = mpatches.FancyBboxPatch(
        (sb_x, sb_y), sb_w, sb_h,
        boxstyle='round,pad=0.006,rounding_size=0.025',
        transform=fig.transFigure,
        facecolor=bub_color, edgecolor=edge_color, linewidth=1.6,
        zorder=220, figure=fig)
    fig.add_artist(bubble)

    # Hide the segment of the bubble's bottom edge between tail corners
    seam = mpatches.Rectangle(
        (tail_base_lx + 0.001, sb_y - 0.002),
        (tail_base_rx - tail_base_lx) - 0.002, 0.004,
        transform=fig.transFigure,
        facecolor=bub_color, edgecolor='none',
        zorder=220.5, figure=fig)
    fig.add_artist(seam)

    txt = fig.text(0.5, sb_y + sb_h / 2,
                   'Just use the Planck value',
                   ha='center', va='center',
                   fontsize=13, fontweight='bold', color='#222222',
                   zorder=221)

    new_artists = [tail, bubble, seam, txt]
    _cartoon_state['eleonora_artists'] = new_artists
    _cartoon_state['artists'].extend(new_artists)
    info("Eleonora says: 'Just use the Planck value'")
    fig.canvas.draw_idle()


def _open_cartoon_popup():
    """Cartoon speech-bubble overlay drawn directly on the main figure
    so it works under any matplotlib backend without spawning a new
    window or event loop."""
    info("Adam wants to go to H.  Which path should he take?")

    if _cartoon_state['artists'] or _cartoon_state['axes']:
        _close_cartoon_popup()

    artists = []
    axes_list = []
    btns_list = []

    # Dim the background so the bubble pops
    dim = mpatches.Rectangle(
        (0, 0), 1, 1, transform=fig.transFigure,
        facecolor='#000000', alpha=0.45, zorder=200, figure=fig)
    fig.add_artist(dim)
    artists.append(dim)

    # Cartoon yellow card (extended downward to fit choice buttons)
    card_x, card_y, card_w, card_h = 0.27, 0.26, 0.46, 0.40
    _cartoon_state['card_rect'] = (card_x, card_y, card_w, card_h)
    card = mpatches.FancyBboxPatch(
        (card_x, card_y), card_w, card_h,
        boxstyle='round,pad=0.012,rounding_size=0.02',
        transform=fig.transFigure,
        facecolor='#fff8dc', edgecolor='#aa5500', linewidth=2.0,
        zorder=201, figure=fig)
    fig.add_artist(card)
    artists.append(card)

    # Title row — photo (or reaction emoji) supplies the "person" glyph.
    t1 = fig.text(0.51, card_y + card_h - 0.055, '→  H',
                  ha='left', va='center',
                  fontsize=22, fontweight='bold', color='#aa5500',
                  zorder=202)
    artists.append(t1)

    # ar.png as a small icon overlaid just left of the arrow
    bub_x = card_x + 0.03
    bub_w = card_w - 0.06
    bub_y = card_y + card_h - 0.260      # below the icon row, with room
    bub_h = 0.10                         # for the trail circles above
    img_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'ar.png')
    try:
        img = mpimg.imread(img_path)
    except Exception as e:
        print(f"[H0] could not load ar.png: {e}")
        img = None
    icon_cx = 0.45
    icon_cy = card_y + card_h - 0.055
    _cartoon_state['icon_pos'] = (icon_cx, icon_cy)
    _cartoon_state['img_ax'] = None
    if img is not None:
        icon_w = (card_w - 0.06) / 4        # equivalent to old bub_w/2
        icon_h = 0.13 / 2
        img_ax = fig.add_axes(
            [icon_cx - icon_w / 2, icon_cy - icon_h / 2, icon_w, icon_h],
            zorder=210)
        img_ax.imshow(img)
        img_ax.axis('off')
        img_ax.set_facecolor('none')
        axes_list.append(img_ax)
        _cartoon_state['img_ax'] = img_ax

    # Classic cartoon thought cloud: scalloped outline (roundtooth) +
    # trail of shrinking circles leading up toward the speaker.
    bub_l = card_x + 0.04
    bub_w_inner = card_w - 0.08
    bub_b = bub_y
    bub_h_inner = bub_h
    bub_top = bub_b + bub_h_inner

    bubble = mpatches.FancyBboxPatch(
        (bub_l, bub_b), bub_w_inner, bub_h_inner,
        boxstyle='roundtooth,pad=0.012,tooth_size=0.014',
        transform=fig.transFigure,
        facecolor='#ffffff', edgecolor='#aa5500', linewidth=1.5,
        zorder=202, figure=fig)
    fig.add_artist(bubble)
    artists.append(bubble)

    # Aspect-correcting factor so circles look round, not oval, in
    # figure coordinates (figsize is 13x10 → x:y = 1.3).
    _fw, _fh = fig.get_size_inches()
    _ar = _fw / _fh
    for (cx, cy, r) in [
        (0.480, bub_top + 0.020, 0.0085),
        (0.467, bub_top + 0.040, 0.0060),
        (0.458, bub_top + 0.055, 0.0040),
    ]:
        dot = mpatches.Ellipse(
            (cx, cy), width=2 * r, height=2 * r * _ar,
            transform=fig.transFigure,
            facecolor='#ffffff', edgecolor='#aa5500', linewidth=1.2,
            zorder=202, figure=fig)
        fig.add_artist(dot)
        artists.append(dot)

    t2 = fig.text(0.5, bub_b + bub_h_inner / 2,
                  'Adam wants to go to H.\nWhich path should he take?',
                  ha='center', va='center',
                  fontsize=12, color='#222222', zorder=203)
    artists.append(t2)

    # Quiz answer buttons — first three isolate a route, the fourth
    # overlays Eleonora's reply bubble.  Third element of the action
    # tuple is the reaction emoji shown above Adam.
    choices = [
        ('a)  Ask Dillon',   ('isolate', 'sh0es',    '😀')),
        ('b)  Ask Jim',      ('isolate', 'desi',     '😀')),
        ('c)  Ask Wendy',    ('isolate', 'cchp_edd', '😞')),
        ('d)  Ask Eleonora', ('eleonora', None,      '😠')),
    ]
    cb_h = 0.038
    cb_w = 0.10
    cb_gap = 0.008
    cb_total = len(choices) * cb_w + (len(choices) - 1) * cb_gap
    cb_start_x = 0.5 - cb_total / 2
    cb_y = card_y + 0.085

    def _make_choice_cb(action, rid, emoji):
        def _cb(_e):
            if action == 'eleonora':
                _show_eleonora_reply(cb_start_x + 3 * (cb_w + cb_gap)
                                     + cb_w / 2, cb_y + cb_h)
                _show_adam_reaction(emoji)
            else:
                _show_adam_reaction(emoji)
                timer = fig.canvas.new_timer(interval=900)
                def _finish():
                    timer.stop()
                    _close_cartoon_popup()
                    _toggle_isolation(rid)
                timer.add_callback(_finish)
                timer.start()
        return _cb

    for i, (label, (action, rid, emoji)) in enumerate(choices):
        bx = cb_start_x + i * (cb_w + cb_gap)
        bax = fig.add_axes([bx, cb_y, cb_w, cb_h], zorder=204)
        bb = Button(bax, label, color='#ffe79a', hovercolor='#ffc233')
        bb.label.set_color('#222222')
        bb.label.set_fontsize(9)
        bb.label.set_fontweight('bold')
        bb.on_clicked(_make_choice_cb(action, rid, emoji))
        axes_list.append(bax)
        btns_list.append(bb)

    # Close (X) button at top-right of the card
    close_ax = fig.add_axes(
        [card_x + card_w - 0.04, card_y + card_h - 0.04, 0.03, 0.03],
        zorder=204)
    close_btn = Button(close_ax, '✕', color='#fff8dc', hovercolor='#ffc233')
    close_btn.label.set_color('#aa5500')
    close_btn.label.set_fontsize(11)
    close_btn.label.set_fontweight('bold')
    close_btn.on_clicked(lambda _e: _close_cartoon_popup())
    axes_list.append(close_ax)
    btns_list.append(close_btn)

    _cartoon_state['artists'] = artists
    _cartoon_state['axes'] = axes_list
    _cartoon_state['btns'] = btns_list

    fig.canvas.draw_idle()


def _open_node_popup(node_id):
    if node_id == 'h0':
        _open_cartoon_popup()
        return
    path = _node_info_path(node_id)
    label = NODES[node_id][2].replace('\n', ' ').strip() or node_id
    if not path:
        info(f'no info file for {label!r}')
        return
    if path.lower().endswith('.rtf'):
        if _open_externally(path):
            info(f'opened {os.path.basename(path)} in default viewer')
        else:
            info(f'could not open {os.path.basename(path)}')
        return
    _show_text_popup(label, path)


def _route_info_path(route_id):
    """Find an info file for the given route in the script directory.
    Tries the route's display name (e.g. 'SH0ES', 'Pop-Mix'), variants
    without dashes/spaces, and finally the route id.
    """
    r = next((rr for rr in ROUTES if rr['id'] == route_id), None)
    if not r:
        return None
    base_dir = os.path.dirname(os.path.abspath(__file__))
    name = r['name']
    stems = [name, name.replace('-', ''), name.replace('-', '_'),
             name.replace('/', '_'), route_id]
    seen = set()
    candidates = []
    for s in stems:
        if not s or s in seen:
            continue
        seen.add(s)
        candidates += [s + '.rtf', s + '.txt', s + '.md', s]
    for fname in candidates:
        path = os.path.join(base_dir, fname)
        if os.path.isfile(path):
            return path
    return None


def _open_route_popup(route_id):
    """Open a route's info file. Returns True if a file was found and
    opened (so the caller can suppress fallback behavior)."""
    path = _route_info_path(route_id)
    if not path:
        return False
    r = next(rr for rr in ROUTES if rr['id'] == route_id)
    if path.lower().endswith('.rtf'):
        if _open_externally(path):
            info(f'opened {os.path.basename(path)} in default viewer')
            return True
        info(f'could not open {os.path.basename(path)}')
        return False
    _show_text_popup(r['name'], path)
    return True


def on_button_press(event):
    """Single click handler — hit-test every pickable artist ourselves
    and pick the topmost-matching route. Clicking an arxiv "↗" arrow
    opens the linked paper. Clicking a node circle opens a per-node
    info popup. Otherwise the click toggles route isolation.
    """
    # If the click lands on a cartoon-popup overlay axes (choice button,
    # close button, image), let that widget handle it and skip the
    # figure-wide hit tests — otherwise the click would also toggle a
    # route under the popup.
    if event.inaxes is not None and event.inaxes in _cartoon_state.get('axes', []):
        return
    # Any user click cancels an in-progress tour.
    _cancel_tour()
    if event.button != 1:
        return
    # Click outside the popup card while it's open → dismiss.
    rect = _cartoon_state.get('card_rect')
    if rect is not None and event.x is not None:
        cx_, cy_, cw_, ch_ = rect
        fx = event.x / fig.bbox.width
        fy = event.y / fig.bbox.height
        if not (cx_ <= fx <= cx_ + cw_ and cy_ <= fy <= cy_ + ch_):
            _close_cartoon_popup()
            return
    # First check arxiv arrow overlays
    for arrow, url in arxiv_links.items():
        try:
            hit, _ = arrow.contains(event)
        except Exception:
            hit = False
        if hit:
            webbrowser.open(url)
            info(f"opened {url}")
            return
    # Then check node circles — clicking a node opens its info popup.
    for nid, art in node_artists.items():
        try:
            hit, _ = art.contains(event)
        except Exception:
            hit = False
        if hit:
            _open_node_popup(nid)
            return
    # Then check legend route-name texts — clicking the name opens
    # the route's info file (if one exists). Falls through to
    # isolation when no file is found.
    for _txt, _r in zip(legend.get_texts(), ROUTES):
        try:
            hit, _ = _txt.contains(event)
        except Exception:
            hit = False
        if hit and _open_route_popup(_r['id']):
            return
    candidates = []
    for art in list(line_to_id) + list(legend_to_id) + list(h0_pick):
        try:
            hit, _ = art.contains(event)
        except Exception:
            hit = False
        if hit:
            rid = _route_for(art)
            if rid:
                candidates.append((art.get_zorder(), rid))
    if not candidates:
        return
    candidates.sort(key=lambda t: t[0], reverse=True)
    _toggle_isolation(candidates[0][1])


fig.canvas.mpl_connect('button_press_event', on_button_press)


def on_key_press(event):
    if event.key == 'escape' and (_cartoon_state.get('artists')
                                  or _cartoon_state.get('axes')):
        _close_cartoon_popup()
        return
    # Up/Down arrows step through routes when one is isolated.
    if event.key in ('up', 'down') and active['id'] is not None:
        ids = [r['id'] for r in ROUTES]
        try:
            idx = ids.index(active['id'])
        except ValueError:
            return
        delta = -1 if event.key == 'up' else 1
        new_id = ids[(idx + delta) % len(ids)]
        active['id'] = new_id
        _isolate(new_id)
        info(f"isolated route: {new_id}")
        fig.canvas.draw_idle()


fig.canvas.mpl_connect('key_press_event', on_key_press)


# --------------------------------------------------------------------------
# Hover tooltips — show route info in the status line on motion over a
# route line, legend entry, or H0-panel marker.
# --------------------------------------------------------------------------

DEFAULT_STATUS = ('click a route to isolate · click a node for info · '
                  'click ↗ for the arXiv paper')
_hover_state = {'rid': None}


def _route_meta_msg(rid):
    r = next((rr for rr in ROUTES if rr['id'] == rid), None)
    if r is None:
        return DEFAULT_STATUS
    msg = f"{r['name']}:  H₀ = {r['h0']:.2f} ± {r['err']:.2f}"
    ref = r.get('ref', '')
    if ref:
        msg += f"   {ref}"
    return msg


_acronym_hover = {'key': None}


def _highlight_routes_using_acronym(key):
    """Multi-route highlight: keep all routes that pass through any
    node mapped to ``key`` visible; hide the rest."""
    matching = ACRO_TO_ROUTES.get(key, set())
    for rid, lines in route_lines.items():
        keep = (rid in matching)
        for ln in lines:
            if ln in background_lines:
                ln.set_alpha(line_alpha.get(ln, FULL_ALPHA) if keep else 0.0)
                ln.set_linewidth(line_lw.get(ln, 2.8))
            elif ln in hidden_lines:
                ln.set_alpha(1.0 if keep else 0.0)
                ln.set_linewidth(3.6 if keep else line_lw.get(ln, 2.8))
            else:
                ln.set_alpha(1.0 if keep else 0.0)
                ln.set_linewidth(3.0 if keep else 2.2)
    for ln in divided_highway_lines:
        ln.set_visible(False)
    for rid, eb in h0_bars.items():
        _set_errorbar_alpha(eb, 1.0 if rid in matching else 0.18)
    for rid, labels in route_labels.items():
        for t in labels:
            t.set_visible(False)
    # Highlight the hovered acronym, dim others.
    for k, t in acronym_texts.items():
        if k == key:
            t.set_color(TEXT)
            t.set_fontweight('bold')
        else:
            t.set_color(TEXT_DIM)
            t.set_fontweight('normal')
    for t in route_acronym_texts.values():
        t.set_color(TEXT_DIM)
        t.set_fontweight('normal')
    # Bold matching legend entries.
    for rid, lt in legend_text_by_id.items():
        if rid in matching:
            lt.set_color(TEXT)
            lt.set_fontweight('bold')
        else:
            lt.set_color(TEXT_DIM)
            lt.set_fontweight('normal')
    for rid, ll in legend_line_by_id.items():
        ll.set_alpha(1.0 if rid in matching else 0.45)
        ll.set_linewidth(4.5 if rid in matching else 2.4)
    # Highlight matching H0-panel rows
    for rid, t in h0_value_text_by_id.items():
        if rid in matching:
            t.set_color(TEXT)
            t.set_fontweight('bold')
        else:
            t.set_color(TEXT_DIM)
            t.set_fontweight('normal')
    for rid, t in h0_name_text_by_id.items():
        if rid in matching:
            t.set_color(TEXT)
            t.set_fontweight('bold')
        else:
            t.set_color(TEXT_DIM)
            t.set_fontweight('normal')
    tension_text.set_visible(False)


def _restore_after_acronym_hover():
    """Return to whatever isolation state was active before the hover."""
    if active['id'] is not None:
        _isolate(active['id'])
    else:
        _reset_isolation()


def on_motion(event):
    # Don't fight the popup's status messages.
    if _cartoon_state.get('artists') or _cartoon_state.get('axes'):
        return

    # Acronym hover: bottom-left list. Hovering an entry highlights
    # every route that passes through any node mapped to that acronym.
    hovered_key = None
    for k, t in acronym_texts.items():
        try:
            hit, _ = t.contains(event)
        except Exception:
            hit = False
        if hit:
            hovered_key = k
            break
    if hovered_key != _acronym_hover['key']:
        _acronym_hover['key'] = hovered_key
        if hovered_key:
            _highlight_routes_using_acronym(hovered_key)
            n = len(ACRO_TO_ROUTES.get(hovered_key, set()))
            info(f"{hovered_key}: used by {n} route" + ('' if n == 1 else 's'))
        else:
            _restore_after_acronym_hover()
        _hover_state['rid'] = None
        fig.canvas.draw_idle()
    if hovered_key:
        return

    # Per-route hover → status line tooltip.
    rid = None
    for art_dict in (line_to_id, legend_to_id, h0_pick):
        for art, _rid in art_dict.items():
            try:
                hit, _ = art.contains(event)
            except Exception:
                hit = False
            if hit:
                rid = _rid
                break
        if rid:
            break
    if rid != _hover_state['rid']:
        _hover_state['rid'] = rid
        info(_route_meta_msg(rid) if rid else DEFAULT_STATUS)
        fig.canvas.draw_idle()


fig.canvas.mpl_connect('motion_notify_event', on_motion)


# --------------------------------------------------------------------------
# Static startup
# --------------------------------------------------------------------------

info(DEFAULT_STATUS)

# Credit at the top-right of the figure
fig.text(0.994, 0.985, 'Credit: James Rohlf and Claude Opus 4.7',
         ha='right', va='top',
         fontsize=8.5, color=TEXT_DIM, fontstyle='italic', zorder=100)
fig.text(0.994, 0.970, 'Boston University Physics',
         ha='right', va='top',
         fontsize=8.5, color=TEXT_DIM, fontstyle='italic', zorder=100)

# keep widget refs alive
fig._keep = (btn_save, btn_save_pdf, btn_clear, btn_tour,
             btn_fig1, btn_tab4)

plt.show()
