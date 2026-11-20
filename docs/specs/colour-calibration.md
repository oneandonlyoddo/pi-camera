# Colour calibration against the Fuji X100F

Status: final · Updated: 2026-11-20

## Goal
The Pi camera's JPG and preview colour match the user's Fuji X100F film simulations, fitted from colour-chart shots taken with both cameras. Fuji recipes then start from a calibrated film simulation (as on the Fuji) instead of the generic imx477 look, so a recipe copied from fujixweekly looks closer to the real thing.

## Decisions
- **Chart:** borrowed from a photographer friend (ideally a ColorChecker Classic/Passport, 24 patches). Any chart with a regular patch grid works, because the fit is Pi → Fuji and needs no published reference values. Why: the user has none; borrowing is enough for a one-time shoot.
- **Film simulations:** Provia, Pro Neg Std, Velvia, Astia, Classic Chrome, Acros. Why: the user's choice. Provia doubles as the neutral base calibration.
- **Recipe step sizes stay as they are** (`PRESET_*_STEP`, tuned by eye). No extra Fuji shots at different Highlight/Shadow/Color settings. Why: the user's choice.
- **Output per film sim: a 3D LUT as the master, plus an image-processor approximation.** The fit makes (a) a colour-correction matrix and a tone curve that go into the tuning file (free at capture, the preview matches) and (b) a residual 33³ `.cube` LUT that takes the Pi's output with (a) applied and maps it to the Fuji look. This spec makes and ships the LUT but does not apply it. Applying it to the JPG (numpy, in strips) and in a GPU preview are separate specs. Why: the matrix can't do hue-specific twists. A residual LUT stacks on top of either the ISP output or the GPU preview without being refitted.
- **GPU preview can show the LUT** (answered 2026-11-19): on the Zero 2 W (VideoCore IV, GLES2, no 3D textures) the 33³ LUT is packed into a 33×1089 2D texture and the shader blends between neighbouring entries itself. The CM4 (VideoCore VI, GLES 3.1) has real 3D textures. The still image still needs numpy (the grain spec ruled out the GPU for stills).
- **Fit tool: a committed desktop script** `scripts/colour_fit.py`, run with uv (`uv run --with numpy --with rawpy --with colour-science ...`). It never runs on the Pi, and `scripts/` is not copied. Why: repeatable when the user reshoots or borrows a better chart.
- **Plain film presets:** one per film sim with all recipe settings at 0 (`Classic Chr.` because of the 12-character name limit). Why: lets the user compare each sim against the Fuji directly.
- **Lamp not chosen yet:** `K` is a script parameter (`--kelvin`), decided at shoot time. Why: the user doesn't know yet which lamp is available.
- **Indoor shoot, every setting matched between the cameras.** Why: the weather makes indoor easier, and the user wants ISO, WB etc. matched. See the shooting protocol (Requirement 1).

## Requirements
1. **Shooting protocol** (written into the script's `--help` and the spec):
   - One light source only, no window light mixed in: a high-CRI lamp (CRI ≥ 90, ideally ≥ 95) at a known colour temperature `K`, lighting the chart evenly at about 45°. Tripod, chart filling the middle third of the frame, no glare on the patches.
   - **Fuji X100F:** RAW+JPG; ISO 200 (base); WB fixed to `K` (Kelvin setting), shift 0/0; DR100; Highlight 0, Shadow 0, Color 0, Sharpness 0, NR 0; Grain off. Expose so the white patch is near, but not at, clipping (check the histogram). Shoot once, then make one JPG per film simulation with the X100F's in-camera RAW conversion, so the exposure and framing are identical across the sims.
   - **Pi:** format JPG+RAW, 12MP, preset none (stock tuning), gain 1x (lowest), WB fixed to the same `K`. Same exposure goal (white patch not clipped). One shot is enough: the Pi side is the same for every film sim.
   - Repeat at the same distance for a second, different shot (e.g. moved or rotated chart) as a check that the fit isn't learning the one frame.
2. **Inputs:** the Fuji JPGs (one per film sim), the Pi DNG and JPG, the chart grid size (default 6×4), the lamp's colour temperature `--kelvin`, and the four chart corners per camera (`--fuji-corners`, `--pi-corners`, pixel coordinates; one set is valid for all Fuji sims because the framing is identical). The script samples the middle 50 % of each patch (median). The shots live in a git-ignored local folder `calibration/` (never committed, never copied to the Pi).
3. **Fit per film sim** (all in linear light unless stated):
   - Exposure normalisation: scale the Pi data so its mid-grey patch matches the Fuji's luminance.
   - **Tone curve:** from the grey patches of the Fuji JPG, a monotonic curve, written as `rpi.contrast.gamma_curve` (same format and point count as the stock one). Recipe Highlight/Shadow keep acting on top of it (`presets._tone`).
   - **Colour matrix:** a 3×3 correction `C` with rows that sum to 1 (keeps white white), fitted by minimising mean ΔE2000 between the Pi patches (DNG → stock WB gains at `K` → stock CCM at `K` → `C`) and the Fuji patches linearised through the inverse of the fitted tone curve. On the Pi `C` is multiplied onto every stock CCM (`C @ ccm` for each colour temperature in `rpi.ccm`). Acros: the fit gives a matrix with three equal rows (a mono channel mix), and saturation stays 0 from `mono`.
   - **Residual LUT:** 33³ `.cube` (Adobe/Resolve format), input = Pi output with `C` and the curve applied (sRGB-encoded, 0..1), output = the Fuji look. Fitted on the patches, smoothly interpolated (e.g. RBF/thin-plate spline) and clamped to the identity far from the data, so colours the chart doesn't cover change gently.
4. **Report** per film sim: mean and max ΔE2000 for stock vs Fuji, ISP approx (`C` + curve) vs Fuji, and approx + LUT vs Fuji, on the fitted shot and on the check shot. Printed, and saved next to the data.
5. **Output files**, committed, one folder per film sim: `films/<slug>/film.json` (`ccm`: 3×3, `gamma_curve`: flat list, shoot info: `K`, date, chart, ΔE report) and `films/<slug>/<slug>.cube`. Slugs: `provia`, `pro_neg_std`, `velvia`, `astia`, `classic_chrome`, `acros`.
6. **Pi side:** a new preset key `"film": "<slug>"`. `presets.tuning()` applies the film's `ccm` and `gamma_curve` before the recipe's Highlight/Shadow and WB shift. Unknown slug or a broken `film.json` → the preset is skipped with a warning, as for other invalid presets. No `film` = the stock look (as today). The `.cube` is not read on the Pi in this spec.
7. **Presets:** `Chrome` and `Portra` get `"film": "classic_chrome"`, `Acros` gets `"film": "acros"`. New plain presets with only a `film` (recipe settings at 0): `Provia`, `Velvia`, `Astia`, `Pro Neg Std`, `Classic Chr.`. A film whose `films/<slug>/` doesn't exist yet makes its preset invalid (skipped with a warning), so the presets can be added before every sim is fitted.
8. **No change to capture time or memory:** the film data only changes the tuning file, which the preset switch already rebuilds.

## Out of scope
- The DNG: stays the untouched negative, as for every preset value.
- Applying the LUT to the JPG or to the preview: separate specs (JPG LUT, GPU preview).
- Grain: own spec (docs/specs/film-grain.md).
- Calibrating the recipe step sizes (user's choice, see Decisions).
- X-Trans IV features the X100F can't shoot as a reference: Classic Negative, Eterna, Color Chrome Effect (+Blue), Clarity. Reggie's Portra uses Color Chrome; that part stays approximate.
- Acros +Ye/+R/+G filter variants (the user didn't pick them; a later fit can add them with the same script).

## Constraints and risks
- **What the ISP can do** (VC4 on the Zero 2 W): a 3×3 CCM per colour temperature (`rpi.ccm`), the tone curve (`rpi.contrast.gamma_curve`), saturation and AWB. No 3D LUT stage.
- **A 3×3 matrix is linear:** it can't mute blues and greens while keeping skin tones (Classic Chrome) or push only some hues (Velvia). The ΔE report shows how much is left for the LUT.
- **24 patches are few for a 33³ LUT:** most of the LUT is interpolation. The smooth fit plus the check shot guard against overfitting. A larger chart (ColorChecker SG, 140 patches) would help if one can be borrowed.
- **One light, one colour temperature:** `C` is fitted at `K` and applied at every colour temperature. Daylight shots may differ slightly; the check is a person looking at real scenes.
- **The script simulates the ISP from the DNG:** lens shading, denoise and the adaptive contrast stage (`rpi.contrast.ce_enable`) are not simulated. Verification shoots the chart on the Pi with each film preset and measures the real ΔE.
- **R1:** desktop-only dependencies (numpy, rawpy, colour-science via uv). The Pi gets only data files. No new apt package.
- **R4:** `films/` is resolved from `PROJECT_ROOT`.
- **R6:** no runtime cost beyond the existing preset reopen (~1.6 s).
- **Repo size:** six `.cube` files at 33³ are about 1 MB each as text, so about 6 MB in git and on the Pi.

## Verification
- Script: runs on the shots and prints the ΔE report (Requirement 4).
- `/on-device`: `--test` (film loading, invalid slug skipped, `C @ ccm` applied, curve replaced), `--check`, switch to each film preset, `--shoot` JPG + DNG.
- Chart shot on the Pi with each film preset, measured with the script against the Fuji JPG: the real-ISP ΔE should be close to the simulated "ISP approx" value.
- Needs a person: real scenes side by side, Pi vs X100F.

## Open questions
- None. Deferred: the lamp and its `K` are chosen by the user at shoot time. The script takes `--kelvin`, so nothing in the code depends on it.

## Notes
- Existing preset mapping: `presets.py` (Saturation, Sharpness, ExposureValue controls; gamma curve for Highlight/Shadow; AWB sensitivity for the WB shift). A preset with `""` = stock tuning (`digital_camera.py`).
- Reference recipes: `docs/presets/`.
- Rejected alternative: real-scene image pairs instead of a chart. The two lenses and fields of view differ, so the pixels can't be aligned reliably.
- The X100F in-camera RAW conversion makes every film sim from one exposure, which removes exposure drift between sims.
