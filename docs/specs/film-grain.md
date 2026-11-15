# Film grain

Status: draft · Updated: 2026-11-15

## Goal
Realistic film grain on the saved JPG, as part of a preset (film simulation), so a shot looks like a scanned negative and not like digital noise.

## Decisions
- **Part of the presets feature:** grain is one more recipe value, not a separate feature. Why: FEATURES.md already lists grain as "not yet" under Presets; Fuji recipes treat it the same way.
- **JPG only, never the DNG.** Why: same as every other preset value; the DNG stays the untouched negative.
- **Controls are Fuji steps:** `grain`: `off` / `weak` / `strong` and `grain_size`: `small` / `large` in a preset in `presets.json`. Why: recipes from Fuji sources (docs/presets/) can be copied 1:1.
- **Runs inline in `capture_photo()`, measured first.** Applied between `make_image()` and `save()` on the camera loop. If the measured cost is too high, a background save worker is a separate spec, together with Known issue 1. Why: simplest; no new thread. GPU was ruled out for the still: VideoCore IV is GLES2 with a 2048 px texture limit, readback is slow, and it shares the CMA memory that already runs out during capture.
- **Luma-only grain for every preset.** One random field added equally to R, G and B. Why: the dctl defaults to monochrome mode, and Fuji's Grain Effect (the recipe source) is luminance grain.
- **GLSL-portable algorithm.** Each output pixel is a formula of its own value and position (value noise + midtone weight), with no whole-image passes. The numpy version is the reference, and the same math can later run as a shader in the GPU preview, also on 3 MP stills (2028x1520 fits the 2048 px texture limit). Why: the user plans GLSL filters.
- **Starting values as proposed** (Requirements 4–5), tunable in `settings.py`. Why: accepted by the user; tuning against reference shots can come later.
- **No time budget yet: measure and report.** Why: the user wants to plan first and optimise later. The memory limit (Requirement 8) still applies, because running out of memory crashes the capture.
- **No grain in the preview for now.** Why: live grain needs an OpenGL preview instead of picamera2's DRM preview. The user wants that anyway for GLSL filters later, so it gets its own spec (GPU preview) rather than being squeezed in here.

## Requirements
1. **Recipe keys** in `presets.json`: `"grain": "off" | "weak" | "strong"` (missing = `off`) and `"grain_size": "small" | "large"` (missing = `small`). `presets._valid` accepts exactly these strings; any other value makes the preset invalid (skipped with a warning, as today).
2. **Where:** in `capture_photo()`, between `helpers.make_image()` and `helpers.save()`, only when the active preset has grain ≠ `off` and a JPG is saved. The DNG and RAW-only shots are unchanged. EXIF is unchanged.
3. **Algorithm** (per pixel, 8-bit RGB in, 8-bit RGB out):
   - `y` = luma of the pixel, Rec.709 weights, in 0..1.
   - `n` = value noise at the pixel position: Gaussian random values on a grid with cell size `c` px, bilinearly blended between grid points, scaled so its standard deviation is 1.
   - `w(y) = 4·y·(1−y)` (1 at mid-grey, 0 at black and white, like the dctl's exposure-driven grain).
   - Every channel: `out = clip(in + 255 · s · w(y) · n, 0, 255)`, the same `n` for R, G and B (luma-only).
   - A new random seed per shot (film is never the same twice). The function takes an optional seed for tests.
4. **Strength `s`** (std of the added value at mid-grey, as a fraction of full scale): `weak` = 0.035, `strong` = 0.07. In `settings.py` (`GRAIN_STRENGTH`).
5. **Grain size `c`** scales with image width so 3 MP and 12 MP look the same: `small` = width/2000 (≈1 px at 3 MP, 2 px at 12 MP), `large` = width/1000. Minimum 1 px; at 1 px it is plain per-pixel noise. In `settings.py` (`GRAIN_CELL_DIVISOR`).
6. **Code:** a pure function, e.g. `grain.apply(image, strength, cell, seed=None)` that takes and returns a PIL image or uint8 array, in its own module without Picamera2 (testable on the Pi with pytest). `presets.py` maps the recipe steps to `strength, cell`.
7. **Preset files:** `presets.json`: Portra `"grain": "weak", "grain_size": "small"`, Chrome `"grain": "weak"`, Acros unchanged (Off), as in `docs/presets/`.
8. **Memory:** no full-frame float copy. Work in horizontal strips (the noise grid for the whole frame is small: (w/c)·(h/c) values), so the extra peak is about one strip, not tens of MB.
9. **Logging:** the capture log line shows the grain step and the time it took (e.g. `grain weak/small 0.4 s`), so the cost can be measured.
10. **Errors:** if grain fails, log a warning and save the JPG without grain. A grain bug must never lose the shot.
11. **UI:** none new. The preset name in the HUD and touch menu is enough; grain is part of the preset.

## Out of scope
- Colour grading / film colour response (the warm tones, lifted blacks and muted sky in the reference "after" shot). That is the "colour matrix / film colour" item of Presets, a separate spec. The tetrahedral-interpolation link (3D LUT lookup) belongs there, not here.
- Halation (red glow around highlights, also visible in the reference). Separate item under Presets.
- Grain in the preview: needs the GPU preview (own spec, planned).
- Speed optimisation and a background save worker: only if the measurement (Requirement 9) shows a need.
- Physical grain model as in the dctl (Poisson/binomial per layer): too heavy for the Pi; Requirement 3 keeps its main behaviour (midtone-weighted, luma).
- Setting grain from the web page or touch menu outside a preset.

## Constraints and risks
- **Where it can run:** everything else in a preset runs in the ISP (tuning file, controls). Grain cannot: libcamera has no grain stage. It has to be numpy work on the JPG image between `helpers.make_image()` and `helpers.save()` in `capture_photo()`.
- **Memory (R6, SPECS "Still capture memory"):** a 12 MP RGB image is 36 MB as uint8, 146 MB as float32. A capture already peaks at ~100 MB and pushes the Pi into swap (~224 MB available). A full-frame float pipeline is not possible; it must work in strips (e.g. 256 rows at a time) in uint8/int16, or on a smaller noise field.
- **Time (R6, Known issue 1, target shot-to-shot 1 s):** runs on the camera loop, so it adds directly to the HUD pause (today 5.8–8.1 s at 12 MP, ≤ 2 s at 3 MP). Not measured yet; rough guess for numpy on the Zero 2 W: 1–3 s at 12 MP, under 0.5 s at 3 MP.
- **No new dependency (R1):** numpy (`python3-numpy`) and Pillow are already installed. No OpenCV/scipy.
- **R11:** grain is applied before the first save; the code never rewrites a saved JPG.
- **Preview:** the preview comes from the ISP at 480x320; grain there is not possible without per-frame CPU work.

## Verification
- `/on-device`: `--shoot` with a grain preset; JPG saved, time from trigger to saved logged, available memory before/after over several shots, DNG unchanged.
- Tests: the grain function on a small synthetic image (shape/dtype kept, strength 0 = identical, luminance dependence, deterministic with a fixed seed).
- Needs a person: whether the grain looks like film at 100 % and on the phone.

## Open questions
- None.

## Notes
- **Reference shots:** Reddit r/postprocessing "Chinatown film emulation after/before" (https://www.reddit.com/r/postprocessing/comments/1nv2fg5/). The "after" grain is fine, mostly luminance, and strongest in the midtones and shadows; most of the look is colour, not grain.
- **thatcherfreeman Film Grain.dctl** (https://github.com/thatcherfreeman/utility-dctls/blob/main/Effects/Film%20Grain.dctl): a physical model. Each pixel holds several layers of grains (default 5 layers × 100 grains). A grain activates with a probability that comes from a Poisson photon count above a threshold; the activated count is binomial, so density follows. Mono mode uses one random draw for all channels. Takeaway: grain variance comes out of the exposure (low in deep shadows and clipped highlights, highest in the midtones), and that is what makes it look like film and not added noise. It is per pixel with no grain size, and too heavy for the Pi as written (many normal draws per pixel per layer).
- **Cheap version of the same idea (adopted, Requirement 3):** noise generated at a lower resolution (grain size), upscaled bilinearly so it clumps, scaled per pixel by a midtone weight `4·y·(1−y)` from the dctl's behaviour, added in strips. A few numpy ops per pixel instead of hundreds of draws.
- **Reddit post** could not be fetched (reddit blocks the fetch tool); only the user's two shots are used.
- **Recipe references:** Reggie's Portra "Grain Effect: Weak, Small"; Classic Chrome "Weak" (no size, so small); Acros "Off".
- **GPU rejected for the still** (2026-11-15): see Decisions. A GPU preview with GLSL filters is a separate planned spec.
- **Tetrahedral interpolation** (MathWorks blog, https://blogs.mathworks.com/steve/2006/11/24/tetrahedral-interpolation-for-colorspace-conversion/): how to look up a 3D colour LUT. Relevant for a film colour LUT, not for grain.
- **saturnix-camera** (https://github.com/Yutani140x/saturnix-camera): Pi Zero 2 W + IMX519, similar idea. Its "film presets" are simple JPEG looks post-processed on the camera; S-MonoX adds grain. The README gives no algorithm. v1 took about a minute per image, which is a warning about full-resolution post-processing on this board. Its "Dynamic Mode" uses preview frames to be fast. Source in `python/` not read yet.
