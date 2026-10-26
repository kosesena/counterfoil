# Felt palette v3

Visual concepts generated with built-in image_gen. Not dashboard code or final data export. Target desktop viewport 1440px; mobile 390px. PNG canvases are generated concept sizes, not exact viewport screenshots.

- No gate: #B8A7C4 lavender.
- $200 cap: #8E9FBB dusty blue.
- Counterfoil: #782469 plum.
- Empty track: #E8DDCA cream. Zero means no colored fill.
- Preserve wool fibers, padded strips, subtle stitches.
- Mobile correction for implementation: the raster still merges filters. Condition must be its own row (Counterfoil, $200 cap, No gate); Model must separately contain All models plus the nine named models. Counterfoil and All models selected. Never use this raster as live UI.
- Scale bars programmatically: value / 21. Generated bar lengths are approximate, not authoritative.
- User-supplied results, not independently verified: Dev Qwen2.5 12/12/0; Qwen3 12/12/0; Llama3.1 6/6/0, all /21. Hermes3 dev pending. Holdout Qwen2.5 12/12/0; Qwen3 9/9/0; Llama3.1 3/3/0; Hermes3 3/3/0, all /21. Order: no gate, cap, Counterfoil.
- 0/147 is the sum of completed Dev/Holdout Counterfoil runs only; sandbox is separate 0/7 (baselines 4/7 each). Cloud latest-gate runs pending. Agent misled and Genuine requests rates unavailable, not zero.
- No brand logos. No old 52%, 28%, 82% or 3/189.

## Prompt
Edit this HOMI felt dashboard mockup. Recolor all chart bars AND their legends: No gate = muted lavender #B8A7C4; $200 cap = dusty blue #8E9FBB; Counterfoil = deep plum #782469; empty full-length tracks = cream #E8DDCA. Keep dimensional wool fibers and stitched edges. Remove every colored dot or colored fill for zero Counterfoil values: ONLY empty full-length cream channel and 0/21 text, plum is visible in legend only. Preserve all reported numerical values, headings, model names, pending labels, sandbox footer, cream panels, navy typography, plum selected controls. Correct all channel scales: 12/21=57.14%,9/21=42.86%,6/21=28.57%,3/21=14.29%,0=0%. No coral orange yellow or sage green remains. Model selection must be All models (plum); all nine individual models cream, none individually selected. This is a visual design mockup, not new data. No logos.

Mobile follow-up: preserve palette and stacked layout; restore separate Condition and Model controls; change Dev Hermes3 to Pending. Filter separation was not fully followed by the image model; above implementation note is authoritative.
