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
import matplotlib.patches as mpatches
import matplotlib.transforms as mtransforms
from matplotlib.widgets import Button


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

CONSENSUS = {'value': 73.50, 'err': 0.81}
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
    (0.0,  0.15, 1.0,  3.7, '#4a3240', 'Geometric anchors',     '#ffcc88'),
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
           f"Consensus {CONSENSUS['value']:.2f} ± {CONSENSUS['err']:.2f}",
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

# Error bars — all created invisible, revealed by animation.
# Also make the errorbar markers, route-name labels, and an invisible
# row-background rectangle pickable so the whole row in the H0 panel
# acts as a clickable isolation target.
h0_bars = {}
h0_pick = {}      # artist → route_id
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
    # value text
    ax_h0.text(81.2, y, f"{r['h0']:.2f} ± {r['err']:.2f}",
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
# Make legend texts pickable too, so clicking the label row (not just
# the colour swatch) also isolates.
for lt, r in zip(legend.get_texts(), ROUTES):
    lt.set_picker(True)
    legend_to_id[lt] = r['id']
    if r.get('arxiv'):
        lt.set_url(r['arxiv'])     # clickable in saved PDF/SVG

# Route-acronym legend on the right, below the Routes legend
ROUTE_ACRONYMS = [
    ('SH0ES',  r'Supernovae, $H_0$, for the Equation of State of dark energy'),
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

# Buttons: just Save PNG
btn_save    = mkbtn(0.06, 0.952, 0.10, 0.028, 'Save PNG')

# Status line
status_ax = mkax(0.17, 0.952, 0.79, 0.028, '#10121f')
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
                ln.set_alpha(1.0 if hi else 0.09)
                ln.set_linewidth(3.6 if hi else 2.2)
    # The divided-highway decoration only makes sense in the unisolated map
    for ln in divided_highway_lines:
        ln.set_visible(False)
    _highlight_acronyms(route_id)
    for rid, eb in h0_bars.items():
        _set_errorbar_alpha(eb, 1.0 if rid == route_id else 0.18)
    for rid, labels in route_labels.items():
        for t in labels:
            t.set_visible(rid == route_id)


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


def _open_node_popup(node_id):
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
    if event.button != 1:
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


# --------------------------------------------------------------------------
# Static startup
# --------------------------------------------------------------------------

info('click a route to isolate · click a node for info · click ↗ for the arXiv paper')

# Credit at the top-right of the figure
fig.text(0.994, 0.985, 'Credit: James Rohlf and Claude Opus 4.7',
         ha='right', va='top',
         fontsize=8.5, color='#7a8090', fontstyle='italic', zorder=100)
fig.text(0.994, 0.970, 'Boston University Physics',
         ha='right', va='top',
         fontsize=8.5, color='#7a8090', fontstyle='italic', zorder=100)

# keep widget refs alive
fig._keep = (btn_save,)

plt.show()
