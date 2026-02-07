# Creative Journal: Pi Bauhaus Poster

## Project Intent
Create a high-resolution A3+ generative poster from Pi decimals, with a strict Bauhaus visual language, vector-first output, and print-ready exports.

## Process Summary

### 1) Base System
- Implemented a Python generator using `pycairo` (primary) and `matplotlib` fallback.
- Used `mpmath` for decimal generation and mapped each decimal to:
  - shape family,
  - Bauhaus color,
  - size scaling.
- Added dual export targets: SVG and 300 DPI PNG.

### 2) Core Visual Grammar
- Built a strict grid and then switched to borderless coverage for full-bleed printing.
- Added a large semi-transparent `π` overlay.
- Added optional in-shape labels for digits.

### 3) Data Correctness
- Verified indexing and corrected the Feynman highlight offset.
- Final Feynman location uses decimal index `761..766` (zero-based on the decimal stream) for `999999`.

### Feynman Point Placement
- The Feynman block is **not manually placed** at the center.
- Position is an emergent result of sequential mapping (left-to-right, top-to-bottom) from the Pi stream into the poster cells.
- The visual emphasis (gold fill + larger/outlined label style) is intentional, but the XY placement comes from data order, not an explicit centering rule.

### 4) Typography Iterations
- Added font presets for labels: `inter`, `jetbrains-mono`, `sans`.
- Switched Feynman labels to high-contrast white with black contour only.
- Synced the `π` glyph font with the selected digit font preset.

### 5) Overlay Iterations
- Explored an L-system botanical fill, then replaced it per direction.
- Final overlay: semi-transparent `π` with internal two-tone Bauhaus tiling (quarter-circles + triangles), designed to preserve legibility of underlying digits.

### 6) Perspective Zone (Bottom)
- Added an “infinite perspective” region at the bottom:
  - increasing visible digits per row,
  - shrinking motif size and vertical spacing,
  - preserving vertical axis symmetry.
- Tuned convergence speed and start position based on iterative feedback.

### 7) Final Print Finishing
- Added a subtle white fade over the last 2 cm at page bottom.

## Verification & Tests
- Added unit tests in `tests/test_pi_digits.py` for:
  - decimal stream correctness,
  - Feynman sequence correctness,
  - cell-to-digit mapping correctness,
  - external reference validation against 100k Pi decimals.
- Improved HTTP headers in the external test to avoid transient `403` blocks.

## Fonts, References, and Licenses

### Fonts referenced in presets
- Inter
  - Reference: https://rsms.me/inter/
  - Source repo: https://github.com/rsms/inter
  - License: SIL Open Font License 1.1 (OFL-1.1)

- JetBrains Mono
  - Reference: https://www.jetbrains.com/lp/mono/
  - Source repo: https://github.com/JetBrains/JetBrainsMono
  - License: SIL Open Font License 1.1 (OFL-1.1)

- DejaVu Sans / DejaVu Sans Mono (fallback chain)
  - Source repo: https://github.com/dejavu-fonts/dejavu-fonts
  - License: DejaVu Fonts License (derived from Bitstream Vera terms; see repository `LICENSE`)

- Fira Code (fallback candidate in monospace preset)
  - Source repo: https://github.com/tonsky/FiraCode
  - License: SIL Open Font License 1.1 (OFL-1.1)

- Arial (system fallback)
  - Reference: https://learn.microsoft.com/en-in/typography/font-list/arial
  - Licensing note: proprietary Monotype/Microsoft distribution; not redistributed by this repository.

## External Numeric Reference
- 100k Pi decimals (used by test): https://calculat.io/storage/pi/100k.txt
